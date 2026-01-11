import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery,
    MenuButtonWebApp, WebAppInfo
)

import aiosqlite
import os
from dotenv import load_dotenv
from datetime import datetime
import json
from aiohttp import web

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "123456789").split(",")))
DB_FILE = os.getenv("DB_FILE", "orders.db")
WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT", "8080"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher(storage=MemoryStorage())

class OrderStates(StatesGroup):
    waiting_room = State()

# ==================== ИНИЦИАЛИЗАЦИЯ ====================
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

async def setup_main_menu_button():
    """Постоянная кнопка «Бар» внизу слева"""
    await bot.set_chat_menu_button(
        scope=types.BotCommandScopeDefault(),
        menu_button=MenuButtonWebApp(
            text="🍸 Бар",
            web_app=WebAppInfo(url="https://pelikan-alakol-site-v2.pages.dev/bar.html")
        )
    )

# ==================== ПРИВЕТСТВИЕ ====================
@dp.message(Command("start"))
async def cmd_start(message: Message):
    caption = "🌊 <b>Пеликан Алаколь</b>\n\nВыберите услугу ↓"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton("🍸 Бар (еда на заказ)", web_app=WebAppInfo(url="https://pelikan-alakol-site-v2.pages.dev/bar.html")),
            InlineKeyboardButton("🍴 Столовая", web_app=WebAppInfo(url="https://pelikan-alakol-site-v2.pages.dev/index_menu.html")),
        ],
        [
            InlineKeyboardButton("🏠 Бронирование номера", url="https://pelikan-alakol-site-v2.pages.dev/maxibooking.html"),
            InlineKeyboardButton("🚗 Трансфер", callback_data="transfer"),
        ],
        [
            InlineKeyboardButton("🎯 Экскурсии", callback_data="activities"),
            InlineKeyboardButton("Задать вопрос", url="https://t.me/pelikan_alakol_support"),
        ]
    ])

    photo_url = "https://pelikan-alakol-site-v2.pages.dev/img/welcome-beach.jpg"  # ← замени на реальную

    try:
        await message.answer_photo(
            photo=photo_url,
            caption=caption,
            reply_markup=keyboard
        )
    except Exception as e:
        logger.warning(f"Фото не загрузилось: {e}")
        await message.answer(caption, reply_markup=keyboard)

# ==================== ПРОСТЫЕ CALLBACK ====================
@dp.callback_query(F.data.in_(["transfer", "activities"]))
async def handle_simple(callback: CallbackQuery):
    if callback.data == "transfer":
        await callback.message.answer("🚗 Для заказа трансфера пиши @pelikan_alakol_support")
    elif callback.data == "activities":
        await callback.message.answer("🎯 Экскурсии — уточняй у @pelikan_alakol_support")
    await callback.answer()

# ==================== КОРОТКИЙ /help ====================
@dp.message(Command("help"))
async def cmd_help(message: Message):
    text = (
        "📖 <b>Помощь</b>\n\n"
        "🍸 Бар — еда и напитки в номер\n"
        "• Нажми кнопку «Бар» внизу слева\n\n"
        "🏠 Бронирование — онлайн на сайте\n"
        "🚗 Трансфер / 🎯 Экскурсии — пиши @pelikan_alakol_support\n\n"
        "Проверка статуса:\n"
        "/status <номер_заказа>\n"
        "Укажи номер комнаты\n\n"
        "Статусы:\n"
        "🟡 Принят\n🟠 Готовится\n🟢 Готов\n✅ Выдан\n\n"
        "Оплата — в баре при получении"
    )
    await message.answer(text)

# ==================== ОСТАЛЬНОЙ КОД (ЗАКАЗЫ, СТАТУСЫ, АДМИН, WEBHOOK) ====================
async def save_order(order_data: dict) -> dict:
    order_id = order_data.get("orderId") or str(int(datetime.now().timestamp()))
    
    try:
        async with aiosqlite.connect(DB_FILE) as db:
            await db.execute("""
                INSERT INTO orders 
                (order_id, client_name, room, telegram_user_id, telegram_username, items, total, timestamp, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'принят')
            """, (
                order_id,
                order_data.get("name"),
                order_data.get("room"),
                order_data.get("telegram_user_id"),
                order_data.get("telegram_username"),
                json.dumps(order_data.get("items", []), ensure_ascii=False),
                order_data.get("total"),
                order_data.get("timestamp")
            ))
            await db.commit()
        
        logger.info(f"Заказ #{order_id} сохранён")
        
        await notify_admins_new_order(order_id, order_data)
        await notify_client_order_received(order_id, order_data)
        
        return {"status": "ok", "order_id": order_id}
    
    except Exception as e:
        logger.error(f"Ошибка сохранения заказа: {e}")
        return {"status": "error", "message": str(e)}

async def notify_admins_new_order(order_id: str, order_data: dict):
    items_text = "\n".join([
        f"• {item['name']} x{item.get('quantity', 1)} — {item['price']} ₸"
        for item in order_data.get("items", [])
    ])
    
    admin_message = f"""
<b>🆕 Новый заказ #{order_id}</b>

👤 Клиент: <b>{order_data.get('name')}</b>
🏨 Комната: <b>{order_data.get('room')}</b>
📱 Telegram: {order_data.get('telegram_username') or 'не указан'}

🍽 <b>Заказ:</b>
{items_text}

💰 <b>Итого: {order_data.get('total')} ₸</b>
🕐 {order_data.get('timestamp')}

<i>Для изменения статуса: /update {order_id} <статус></i>
    """
    
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
        """
        await bot.send_message(f"@{telegram_username}", message)
    except Exception as e:
        logger.warning(f"Не удалось отправить клиенту @{telegram_username}: {e}")

# ... (остальные функции: notify_client_status_change, cmd_bar, cmd_stolovaya, cmd_booking и т.д. — оставляем как есть или обновляем по необходимости)

# ==================== WEBHOOK ====================
async def handle_new_order(request):
    try:
        order_data = await request.json()
        result = await save_order(order_data)
        if result["status"] == "ok":
            return web.json_response(result, status=200)
        else:
            return web.json_response(result, status=500)
    except Exception as e:
        logger.error(f"Ошибка webhook: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)

async def start_webhook_server():
    app = web.Application()
    app.router.add_post("/api/order", handle_new_order)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", WEBHOOK_PORT)
    await site.start()
    logger.info(f"Webhook запущен на порту {WEBHOOK_PORT}")

async def main():
    await init_db()
    await setup_main_menu_button()
    
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, "🤖 Бот запущен!")
        except:
            pass
    
    asyncio.create_task(start_webhook_server())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
