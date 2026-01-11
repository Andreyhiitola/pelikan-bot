import asyncio
import logging
import os
import json
from datetime import datetime

import aiosqlite
from aiohttp import web
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F, types
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
    WebAppInfo,
)

# ==================== НАСТРОЙКИ ====================

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "123456789").split(",")))
DB_FILE = os.getenv("DB_FILE", "orders.db")
WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT", "8080"))
ALLOWED_ORIGIN = os.getenv(
    "ALLOWED_ORIGIN",
    "https://pelikan-alakol-site-v2.pages.dev",
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher(storage=MemoryStorage())


# ==================== БАЗА ДАННЫХ ====================

async def init_db():
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY,
                client_name TEXT,
                room TEXT,
                telegram_user_id INTEGER,
                telegram_username TEXT,
                items TEXT,
                total INTEGER,
                status TEXT DEFAULT 'принят',
                timestamp TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()
    logger.info("База данных готова")


# ==================== TELEGRAM ХЕНДЛЕРЫ ====================

@dp.message(Command("start"))
async def cmd_start(message: Message):
    caption = "🌊 <b>Пеликан Алаколь</b>\n\nВыберите услугу ↓"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🍸 Бар (еда на заказ)",
                web_app=WebAppInfo(
                    url="https://pelikan-alakol-site-v2.pages.dev/bar.html"
                ),
            ),
            InlineKeyboardButton(
                text="🍴 Столовая",
                web_app=WebAppInfo(
                    url="https://pelikan-alakol-site-v2.pages.dev/index_menu.html"
                ),
            ),
        ],
        [
            InlineKeyboardButton(
                text="🏠 Бронирование номера",
                url="https://pelikan-alakol-site-v2.pages.dev/maxibooking.html",
            ),
            InlineKeyboardButton(
                text="🚗 Трансфер",
                callback_data="transfer",
            ),
        ],
        [
            InlineKeyboardButton(
                text="🎯 Экскурсии",
                callback_data="activities",
            ),
            InlineKeyboardButton(
                text="Задать вопрос",
                url="https://t.me/pelikan_alakol_support",
            ),
        ],
    ])

    photo_url = "https://pelikan-alakol-site-v2.pages.dev/img/welcome-beach.jpg"

    try:
        await message.answer_photo(
            photo=photo_url,
            caption=caption,
            reply_markup=keyboard,
        )
    except Exception as e:
        logger.warning(f"Фото не загрузилось: {e}")
        await message.answer(caption, reply_markup=keyboard)

@dp.callback_query(F.data.in_(["transfer", "activities"]))
async def handle_simple(callback: CallbackQuery):
    if callback.data == "transfer":
        await callback.message.answer(
            "🚗 Для заказа трансфера пиши @pelikan_alakol_support"
        )
    elif callback.data == "activities":
        await callback.message.answer(
            "🎯 Экскурсии — уточняй у @pelikan_alakol_support"
        )
    await callback.answer()


@dp.message(Command("help"))
async def cmd_help(message: Message):
    text = (
        "📖 <b>Помощь</b>\n\n"
        "🍸 Бар — еда и напитки в номер\n"
        "• Нажми кнопку «Бар» внизу слева\n\n"
        "🏠 Бронирование — онлайн на сайте\n"
        "🚗 Трансфер / 🎯 Экскурсии — пиши @pelikan_alakol_support\n\n"
        "Проверка статуса:\n"
        "/status &lt;номер_заказа&gt;\n"
        "Укажи номер комнаты\n\n"
        "Статусы:\n"
        "🟡 Принят\n🟠 Готовится\n🟢 Готов\n✅ Выдан\n\n"
        "Оплата — в баре при получении"
    )
    await message.answer(text)


# ==================== ЛОГИКА ЗАКАЗОВ ====================

async def save_order(order_data: dict) -> dict:
    order_id = order_data.get("orderId") or str(int(datetime.now().timestamp()))

    try:
        async with aiosqlite.connect(DB_FILE) as db:
            await db.execute(
                """
                INSERT INTO orders 
                (order_id, client_name, room, telegram_user_id, telegram_username, items, total, timestamp, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'принят')
                """,
                (
                    order_id,
                    order_data.get("name"),
                    order_data.get("room"),
                    order_data.get("telegram_user_id"),
                    order_data.get("telegram_username"),
                    json.dumps(order_data.get("items", []), ensure_ascii=False),
                    order_data.get("total"),
                    order_data.get("timestamp"),
                ),
            )
            await db.commit()

        logger.info(f"Заказ #{order_id} сохранён")

        await notify_admins_new_order(order_id, order_data)
        await notify_client_order_received(order_id, order_data)

        return {"status": "ok", "order_id": order_id}

    except Exception as e:
        logger.error(f"Ошибка сохранения заказа: {e}")
        return {"status": "error", "message": str(e)}


async def notify_admins_new_order(order_id: str, order_data: dict):
    items_text = "\n".join(
        f"• {item['name']} x{item.get('quantity', 1)} — {item['price']} ₸"
        for item in order_data.get("items", [])
    )

    # корректно собираем контакт
    telegram_user_id = order_data.get("telegram_user_id")
    telegram_username = order_data.get("telegram_username")

    if telegram_username:
        telegram_contact = f"@{telegram_username}"
    elif telegram_user_id:
        telegram_contact = f"ID:{telegram_user_id}"
    else:
        telegram_contact = "не указан"

    admin_message = f"""
<b>🆕 Новый заказ #{order_id}</b>

👤 Клиент: <b>{order_data.get('name')}</b>
🏨 Комната: <b>{order_data.get('room')}</b>
📱 Telegram: {telegram_contact}

🍽 <b>Заказ:</b>
{items_text}

💰 <b>Итого: {order_data.get('total')} ₸</b>
🕐 {order_data.get('timestamp')}

<i>Для изменения статуса: /update {order_id} &lt;статус&gt;</i>
""".strip()

    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, admin_message)
        except Exception as e:
            logger.error(f"Ошибка отправки админу {admin_id}: {e}")

async def notify_client_order_received(order_id: str, order_data: dict):
    telegram_username = order_data.get("telegram_username")
    if not telegram_username:
        return

    try:
        message = f"""
✅ <b>Ваш заказ #{order_id} принят!</b>

Итого: <b>{order_data.get('total')} ₸</b>
Оплата при получении в баре.

Проверить статус: /status {order_id}
""".strip()
        await bot.send_message(f"@{telegram_username}", message)
    except Exception as e:
        logger.warning(f"Не удалось отправить клиенту @{telegram_username}: {e}")


# ==================== HTTP API (/api/order) ====================

def cors_headers(origin: str | None) -> dict:
    origin = origin or ALLOWED_ORIGIN
    return {
        "Access-Control-Allow-Origin": origin,
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
    }


async def handle_new_order(request: web.Request) -> web.Response:
    origin = request.headers.get("Origin")
    headers = cors_headers(origin)

    if request.method == "OPTIONS":
        return web.Response(status=204, headers=headers)

    try:
        order_data = await request.json()
        result = await save_order(order_data)
        status = 200 if result["status"] == "ok" else 500
        return web.json_response(result, status=status, headers=headers)
    except Exception as e:
        logger.error(f"Ошибка webhook: {e}")
        return web.json_response(
            {"status": "error", "message": str(e)},
            status=500,
            headers=headers,
        )


async def start_webhook_server():
    app = web.Application()
    app.router.add_route("POST", "/api/order", handle_new_order)
    app.router.add_route("OPTIONS", "/api/order", handle_new_order)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", WEBHOOK_PORT)
    await site.start()
    logger.info(f"HTTP API запущен на порту {WEBHOOK_PORT} (/api/order)")


# ==================== MAIN ====================

async def main():
    await init_db()

    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, "🤖 Бот запущен!")
        except Exception:
            pass

    asyncio.create_task(start_webhook_server())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
