import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message
import aiosqlite
import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()
from datetime import datetime
import json
from typing import Optional
from aiohttp import web

# ==================== НАСТРОЙКИ ====================
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "123456789,987654321").split(",")))
DB_FILE = os.getenv("DB_FILE", "orders.db")
WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT", "8080"))
# ==================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


# FSM States
class OrderStates(StatesGroup):
    waiting_room = State()


# Инициализация базы данных
async def init_db():
    """Создание таблицы заказов, если её нет"""
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY,
                client_name TEXT,
                room TEXT,
                telegram TEXT,
                items TEXT,
                total INTEGER,
                status TEXT DEFAULT 'принят',
                timestamp TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()
    logger.info("База данных инициализирована")


# Функция для сохранения заказа (вызывается из webhook)
async def save_order(order_data: dict) -> dict:
    """
    Сохраняет заказ в БД и отправляет уведомления
    
    Args:
        order_data: Данные заказа из webhook
    
    Returns:
        dict: Результат операции с order_id
    """
    order_id = order_data.get("orderId") or str(int(datetime.now().timestamp()))
    
    try:
        async with aiosqlite.connect(DB_FILE) as db:
            await db.execute("""
                INSERT INTO orders 
                (order_id, client_name, room, telegram, items, total, timestamp, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'принят')
            """, (
                order_id,
                order_data.get("name"),
                order_data.get("room"),
                order_data.get("telegram"),
                json.dumps(order_data.get("items", []), ensure_ascii=False),
                order_data.get("total"),
                order_data.get("timestamp")
            ))
            await db.commit()
        
        logger.info(f"Заказ #{order_id} сохранён в БД")
        
        # Уведомление администраторам
        await notify_admins_new_order(order_id, order_data)
        
        # Уведомление клиенту
        await notify_client_order_received(order_id, order_data)
        
        return {"status": "ok", "order_id": order_id}
    
    except Exception as e:
        logger.error(f"Ошибка при сохранении заказа: {e}")
        return {"status": "error", "message": str(e)}


async def notify_admins_new_order(order_id: str, order_data: dict):
    """Отправляет уведомление администраторам о новом заказе"""
    items_text = "\n".join([
        f"• {item['name']} x{item.get('quantity', 1)} — {item['price']} ₸" 
        for item in order_data.get("items", [])
    ])
    
    admin_message = f"""
<b>🆕 Новый заказ #{order_id}</b>

👤 Клиент: <b>{order_data.get('name')}</b>
🏨 Комната: <b>{order_data.get('room')}</b>
📱 Telegram: {order_data.get('telegram') or 'не указан'}

🍽 <b>Заказ:</b>
{items_text}

💰 <b>Итого: {order_data.get('total')} ₸</b>
🕐 {order_data.get('timestamp')}

<i>Для изменения статуса используйте:</i>
/update {order_id} &lt;статус&gt;
    """
    
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, admin_message)
            logger.info(f"Уведомление отправлено админу {admin_id}")
        except Exception as e:
            logger.error(f"Не удалось отправить админу {admin_id}: {e}")


async def notify_client_order_received(order_id: str, order_data: dict):
    """Отправляет клиенту подтверждение о принятии заказа"""
    telegram_username = order_data.get("telegram")
    if not telegram_username:
        return
    
    try:
        # Пробуем отправить по username
        message = f"""
✅ <b>Ваш заказ #{order_id} принят!</b>

Итого: <b>{order_data.get('total')} ₸</b>
Оплата при получении в баре.

Чтобы проверить статус заказа, используйте команду:
/status {order_id}

Приятного аппетита! 😊
        """
        await bot.send_message(f"@{telegram_username}", message)
        logger.info(f"Подтверждение отправлено клиенту @{telegram_username}")
    except Exception as e:
        logger.warning(f"Не удалось отправить клиенту @{telegram_username}: {e}")


async def notify_client_status_change(order_id: str, telegram_username: str, new_status: str):
    """Уведомляет клиента об изменении статуса заказа"""
    status_messages = {
        "принят": "принят в обработку",
        "готовится": "готовится 👨‍🍳",
        "готов": "готов к выдаче! Можете забрать в баре 🎉",
        "выдан": "выдан. Приятного аппетита! ✅"
    }
    
    status_text = status_messages.get(new_status, new_status)
    
    try:
        message = f"🔔 Ваш заказ <b>#{order_id}</b> {status_text}"
        await bot.send_message(f"@{telegram_username}", message)
        logger.info(f"Уведомление о статусе отправлено @{telegram_username}")
    except Exception as e:
        logger.warning(f"Не удалось уведомить клиента: {e}")


# ==================== КОМАНДЫ БОТА ====================

@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Приветственное сообщение"""
    await message.answer(
        "🍽 <b>Добро пожаловать в систему заказов бара «Пеликан Алаколь»!</b>\n\n"
        "📋 <b>Доступные команды:</b>\n"
        "/status &lt;номер_заказа&gt; — проверить статус заказа\n"
        "/help — помощь\n\n"
        "Для заказа используйте наш сайт: bar.pelikan-alakol.kz\n\n"
        "Приятного аппетита! 😊"
    )


@dp.message(Command("help"))
async def cmd_help(message: Message):
    """Помощь по использованию бота"""
    help_text = """
<b>📖 Инструкция по использованию бота</b>

<b>Как сделать заказ:</b>
1️⃣ Перейдите на сайт bar.pelikan-alakol.kz
2️⃣ Выберите блюда из меню
3️⃣ Укажите номер комнаты и контакты
4️⃣ Оформите заказ

<b>Проверка статуса:</b>
/status &lt;номер_заказа&gt;

После команды укажите номер вашей комнаты для верификации.

<b>Статусы заказа:</b>
🟡 Принят — заказ получен
🟠 Готовится — готовим ваш заказ
🟢 Готов — можете забрать в баре
✅ Выдан — заказ получен

<b>Оплата:</b>
При получении заказа в баре.

По вопросам: @pelikan_alakol_support
    """
    await message.answer(help_text)


@dp.message(Command("status"))
async def cmd_status(message: Message, state: FSMContext):
    """Запрос статуса заказа"""
    args = message.text.split(maxsplit=1)
    
    if len(args) < 2:
        await message.answer(
            "❌ Укажите номер заказа:\n"
            "/status &lt;номер_заказа&gt;\n\n"
            "Например: /status 1736172000"
        )
        return
    
    order_id = args[1].strip()
    
    # Проверяем существование заказа
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute(
            "SELECT order_id, room FROM orders WHERE order_id = ?", 
            (order_id,)
        ) as cursor:
            row = await cursor.fetchone()
    
    if not row:
        await message.answer("❌ Заказ не найден. Проверьте номер заказа.")
        return
    
    # Сохраняем данные для верификации
    await state.update_data(order_id=order_id, expected_room=row[1])
    await state.set_state(OrderStates.waiting_room)
    
    await message.answer(
        f"🔐 Для просмотра статуса заказа <b>#{order_id}</b>\n"
        f"укажите номер комнаты, в которой вы проживаете:"
    )


@dp.message(OrderStates.waiting_room)
async def verify_room_and_show_status(message: Message, state: FSMContext):
    """Проверка номера комнаты и показ статуса заказа"""
    data = await state.get_data()
    expected_room = data.get("expected_room")
    order_id = data.get("order_id")
    
    user_room = message.text.strip()
    
    if user_room != expected_room:
        await message.answer(
            "❌ Неверный номер комнаты. Доступ запрещён.\n\n"
            "Попробуйте ещё раз: /status " + order_id
        )
        await state.clear()
        return
    
    # Получаем полную информацию о заказе
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute(
            "SELECT * FROM orders WHERE order_id = ?", 
            (order_id,)
        ) as cursor:
            row = await cursor.fetchone()
    
    if not row:
        await message.answer("❌ Ошибка получения данных заказа.")
        await state.clear()
        return
    
    # Парсим items
    items = json.loads(row[4])
    items_text = "\n".join([
        f"• {item['name']} x{item.get('quantity', 1)} — {item['price']} ₸" 
        for item in items
    ])
    
    # Эмодзи статуса
    status_emoji = {
        "принят": "🟡",
        "готовится": "🟠",
        "готов": "🟢",
        "выдан": "✅"
    }.get(row[6], "🟡")
    
    status_message = f"""
{status_emoji} <b>Статус заказа #{order_id}</b>

<b>Ваш заказ:</b>
{items_text}

💰 <b>Итого: {row[5]} ₸</b>
📅 {row[7]}
🔔 Статус: <b>{row[6].capitalize()}</b>

<i>Оплата при получении в баре.</i>
    """
    
    await message.answer(status_message)
    await state.clear()


# ==================== АДМИН-КОМАНДЫ ====================

@dp.message(Command("update"), F.from_user.id.in_(ADMIN_IDS))
async def cmd_update_status(message: Message):
    """Изменение статуса заказа (только для админов)"""
    parts = message.text.split()
    
    if len(parts) < 3:
        await message.answer(
            "❌ Использование:\n"
            "/update &lt;order_id&gt; &lt;статус&gt;\n\n"
            "<b>Доступные статусы:</b>\n"
            "• принят\n"
            "• готовится\n"
            "• готов\n"
            "• выдан"
        )
        return
    
    order_id = parts[1]
    new_status = parts[2].lower()
    
    valid_statuses = ["принят", "готовится", "готов", "выдан"]
    if new_status not in valid_statuses:
        await message.answer(
            f"❌ Недопустимый статус.\n\n"
            f"Доступные статусы: {', '.join(valid_statuses)}"
        )
        return
    
    # Обновляем статус в БД
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute(
            "UPDATE orders SET status = ? WHERE order_id = ?", 
            (new_status, order_id)
        )
        await db.commit()
        
        # Получаем telegram клиента
        async with db.execute(
            "SELECT telegram, client_name FROM orders WHERE order_id = ?", 
            (order_id,)
        ) as cursor:
            row = await cursor.fetchone()
    
    if row and row[0]:
        await notify_client_status_change(order_id, row[0], new_status)
    
    await message.answer(
        f"✅ Статус заказа <b>#{order_id}</b> изменён на <b>«{new_status}»</b>\n"
        f"Клиент: {row[1] if row else 'неизвестен'}"
    )
    logger.info(f"Статус заказа #{order_id} изменён на '{new_status}' админом {message.from_user.id}")


@dp.message(Command("orders"), F.from_user.id.in_(ADMIN_IDS))
async def cmd_list_orders(message: Message):
    """Список активных заказов (только для админов)"""
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute(
            "SELECT order_id, client_name, room, status, total, timestamp "
            "FROM orders WHERE status != 'выдан' ORDER BY created_at DESC LIMIT 20"
        ) as cursor:
            rows = await cursor.fetchall()
    
    if not rows:
        await message.answer("📋 Нет активных заказов")
        return
    
    orders_text = "<b>📋 Активные заказы:</b>\n\n"
    for row in rows:
        status_emoji = {
            "принят": "🟡",
            "готовится": "🟠",
            "готов": "🟢"
        }.get(row[3], "🟡")
        
        orders_text += (
            f"{status_emoji} <b>#{row[0]}</b>\n"
            f"   👤 {row[1]} | 🏨 {row[2]}\n"
            f"   💰 {row[4]} ₸ | {row[5]}\n"
            f"   Статус: {row[3]}\n\n"
        )
    
    await message.answer(orders_text)


@dp.message(Command("stats"), F.from_user.id.in_(ADMIN_IDS))
async def cmd_stats(message: Message):
    """Статистика заказов (только для админов)"""
    async with aiosqlite.connect(DB_FILE) as db:
        # Общее количество заказов
        async with db.execute("SELECT COUNT(*) FROM orders") as cursor:
            total = (await cursor.fetchone())[0]
        
        # По статусам
        async with db.execute(
            "SELECT status, COUNT(*) FROM orders GROUP BY status"
        ) as cursor:
            by_status = await cursor.fetchall()
        
        # Сумма за сегодня
        async with db.execute(
            "SELECT SUM(total) FROM orders WHERE DATE(created_at) = DATE('now')"
        ) as cursor:
            today_sum = (await cursor.fetchone())[0] or 0
    
    stats_text = "<b>📊 Статистика заказов</b>\n\n"
    stats_text += f"<b>Всего заказов:</b> {total}\n\n"
    stats_text += "<b>По статусам:</b>\n"
    
    for status, count in by_status:
        emoji = {
            "принят": "🟡",
            "готовится": "🟠",
            "готов": "🟢",
            "выдан": "✅"
        }.get(status, "⚪")
        stats_text += f"{emoji} {status.capitalize()}: {count}\n"
    
    stats_text += f"\n<b>Сумма за сегодня:</b> {today_sum} ₸"
    
    await message.answer(stats_text)


# ==================== ОБРАБОТЧИК НЕИЗВЕСТНЫХ КОМАНД ====================

@dp.message()
async def handle_unknown(message: Message):
    """Обработчик неизвестных сообщений"""
    if message.from_user.id in ADMIN_IDS:
        await message.answer(
            "❓ Неизвестная команда.\n\n"
            "<b>Доступные команды для админов:</b>\n"
            "/update &lt;id&gt; &lt;статус&gt; — изменить статус\n"
            "/orders — список активных заказов\n"
            "/stats — статистика\n"
            "/help — помощь"
        )
    else:
        await message.answer(
            "❓ Я не понимаю эту команду.\n\n"
            "Используйте /help для списка доступных команд."
        )


# ==================== WEBHOOK ДЛЯ ПРИЁМА ЗАКАЗОВ ====================

async def handle_new_order(request):
    """Обработчик webhook для новых заказов с сайта"""
    try:
        order_data = await request.json()
        logger.info(f"Получен новый заказ: {order_data.get('orderId')}")
        
        # Валидация
        required_fields = ["name", "room", "items", "total"]
        for field in required_fields:
            if field not in order_data:
                return web.json_response(
                    {"status": "error", "message": f"Отсутствует поле: {field}"},
                    status=400
                )
        
        if not order_data["items"]:
            return web.json_response(
                {"status": "error", "message": "Заказ не может быть пустым"},
                status=400
            )
        
        # Сохраняем заказ
        result = await save_order(order_data)
        
        if result["status"] == "ok":
            return web.json_response(result, status=200)
        else:
            return web.json_response(result, status=500)
    
    except json.JSONDecodeError:
        logger.error("Ошибка парсинга JSON")
        return web.json_response(
            {"status": "error", "message": "Неверный формат JSON"},
            status=400
        )
    except Exception as e:
        logger.error(f"Ошибка обработки заказа: {e}")
        return web.json_response(
            {"status": "error", "message": str(e)},
            status=500
        )


async def handle_health_check(request):
    """Проверка здоровья сервера"""
    return web.json_response({"status": "ok", "service": "pelikan-bar-bot"})


async def start_webhook_server():
    """Запуск встроенного webhook сервера"""
    app = web.Application()
    app.router.add_post("/api/order", handle_new_order)
    app.router.add_get("/health", handle_health_check)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, "0.0.0.0", WEBHOOK_PORT)
    await site.start()
    
    logger.info(f"Webhook сервер запущен на порту {WEBHOOK_PORT}")
    logger.info(f"Эндпоинт для заказов: http://0.0.0.0:{WEBHOOK_PORT}/api/order")


async def main():
    """Основная функция запуска"""
    await init_db()
    
    # Уведомляем админов о запуске
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id, 
                "🤖 Бот «Пеликан Алаколь» запущен и готов к работе!"
            )
        except Exception as e:
            logger.error(f"Не удалось уведомить админа {admin_id}: {e}")
    
    logger.info("Бот запущен и готов к работе")
    
    # Запускаем webhook сервер в фоне
    webhook_task = asyncio.create_task(start_webhook_server())
    
    try:
        # Запуск polling
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
