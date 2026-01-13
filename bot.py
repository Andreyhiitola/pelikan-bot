import asyncio
import logging
import os
import json
from datetime import datetime
import aiosqlite
from aiohttp import web
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F, types
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import black
import tempfile
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import black
import tempfile
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import black
import tempfile
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command, CommandObject
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
    WebAppInfo,
    FSInputFile)

# ==================== НАСТРОЙКИ ====================

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "123456789").split(",")))
DB_FILE = os.getenv("DB_FILE", "orders.db")
WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT", "8080"))
ALLOWED_ORIGIN = os.getenv(
    "ALLOWED_ORIGIN",
    "https://pelikan-alakol-site-v2.pages.dev")

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
                pdf_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()
        
        # Миграция: добавляем pdf_path если его нет
        try:
            await db.execute("ALTER TABLE orders ADD COLUMN pdf_path TEXT")
            await db.commit()
            logger.info("Миграция: добавлена колонка pdf_path")
        except:
            pass  # Колонка уже существует
            
    logger.info("База данных готова")


# ==================== TELEGRAM ХЕНДЛЕРЫ ====================

@dp.message(Command("start"))
async def cmd_start(message: Message):
    caption = "🌊 <b>Пеликан Алаколь</b>\n\nВыберите услугу ↓"

    # Базовые кнопки для всех
    buttons = [
        [
            InlineKeyboardButton(
                text="🍸 Бар (еда на заказ)",
                web_app=WebAppInfo(
                    url="https://pelikan-alakol-site-v2.pages.dev/bar.html"
                )),
            InlineKeyboardButton(
                text="🍴 Столовая",
                web_app=WebAppInfo(
                    url="https://pelikan-alakol-site-v2.pages.dev/index_menu.html"
                )),
        ],
        [
            InlineKeyboardButton(
                text="🏠 Бронирование номера",
                url="https://pelikan-alakol-site-v2.pages.dev/maxibooking.html"),
            InlineKeyboardButton(
                text="🚗 Трансфер",
                callback_data="transfer"),
        ],
        [
            InlineKeyboardButton(
                text="🎯 Экскурсии",
                callback_data="activities"),
            InlineKeyboardButton(
                text="Задать вопрос",
                url="https://t.me/pelikan_alakol_support"),
        ],
    ]
    
    # Добавляем админскую кнопку для админов
    if message.from_user.id in ADMIN_IDS:
        buttons.append([
            InlineKeyboardButton(
                text="👨‍💼 Админ-панель",
                callback_data="admin_panel"
            )
        ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    photo_url = "https://pelikan-alakol-site-v2.pages.dev/img/welcome-beach.jpg"

    try:
        await message.answer_photo(
            photo=photo_url,
            caption=caption,
            reply_markup=keyboard)
    except Exception as e:
        logger.warning(f"Фото не загрузилось: {e}")
        await message.answer(caption, reply_markup=keyboard)


# ==================== АДМИН-ПАНЕЛЬ ====================

@dp.callback_query(F.data == "admin_panel")
async def show_admin_panel(callback: CallbackQuery):
    """Показать админ-панель"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ У вас нет прав", show_alert=True)
        return
    
    text = "👨‍💼 <b>АДМИН-ПАНЕЛЬ</b>\n\nУправление заказами и статистика"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📋 Активные заказы", callback_data="admin_orders")
        ],
        [
            InlineKeyboardButton(text="📊 Статистика за день", callback_data="admin_stats")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu")
        ]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@dp.callback_query(F.data == "admin_orders")
async def show_admin_orders(callback: CallbackQuery):
    """Показать активные заказы с кнопками"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ У вас нет прав", show_alert=True)
        return
    
    await callback.answer()
    
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute(
            "SELECT order_id, client_name, room, status, total, items, pdf_path FROM orders WHERE status != 'выдан' ORDER BY created_at DESC LIMIT 10"
        )
        rows = await cursor.fetchall()
    
    if not rows:
        await callback.message.answer("📋 Активных заказов нет")
        return
    
    for order_id, name, room, status, total, items_json, pdf_path in rows:
        emoji = {"принят": "🟡", "готовится": "🟠", "готов": "🟢"}.get(status, "⚪")
        
        # Парсим список блюд
        try:
            items = json.loads(items_json)
            items_text = "\n".join([
                f"• {item['name']} x{item.get('quantity', 1)} - {item['price']}₸"
                for item in items
            ])
        except:
            items_text = "Состав заказа недоступен"
        
        text = f"{emoji} <b>#{order_id}</b>\n👤 {name} | 🏨 {room}\n\n🍽️ Заказ:\n{items_text}\n\n💰 Итого: {total}₸\n📊 Статус: {status}"
        
        # Создаём кнопки с PDF
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="⏳ Готовится", callback_data=f"status:{order_id}:готовится"),
                InlineKeyboardButton(text="✅ Готов", callback_data=f"status:{order_id}:готов"),
            ],
            [
                InlineKeyboardButton(text="🎉 Выдан", callback_data=f"status:{order_id}:выдан"),
                InlineKeyboardButton(text="📄 PDF", callback_data=f"pdf:{order_id}"),
            ]
        ])
        
        await callback.message.answer(text, reply_markup=keyboard)


# ==================== ОБРАБОТЧИК КНОПОК СТАТУСА ====================

@dp.callback_query(F.data.startswith("status:"))
async def handle_status_button(callback: CallbackQuery):
    """Обработка нажатия кнопки изменения статуса"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ У вас нет прав", show_alert=True)
        return
    
    # Парсим данные: status:ORD123456:готовится
    parts = callback.data.split(":")
    order_id = parts[1]
    new_status = parts[2]
    
    # Обновляем статус в базе
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute(
            "UPDATE orders SET status = ? WHERE order_id = ?",
            (new_status, order_id)
        )
        await db.commit()
        
        if cursor.rowcount == 0:
            await callback.answer("❌ Заказ не найден", show_alert=True)
            return
    
    # Уведомляем клиента
    await notify_client_status_update(order_id, new_status)
    
    # Обновляем сообщение
    emoji = {"готовится": "🟠", "готов": "🟢", "выдан": "🎉"}.get(new_status, "⚪")
    
    try:
        # Убираем кнопки если статус "выдан"
        new_markup = None if new_status == "выдан" else callback.message.reply_markup
        
        # Обновляем текст
        old_text = callback.message.text or callback.message.caption
        new_text = old_text.split('\n')
        
        # Меняем эмодзи и статус
        if new_text:
            new_text[0] = f"{emoji} <b>#{order_id}</b>"
            for i, line in enumerate(new_text):
                if "📊 Статус:" in line:
                    new_text[i] = f"📊 Статус: {new_status}"
                    break
        
        await callback.message.edit_text(
            "\n".join(new_text),
            reply_markup=new_markup,
            parse_mode="HTML"
        )
    except:
        pass
    
    await callback.answer(f"✅ Статус изменён на '{new_status}'")



@dp.callback_query(F.data.startswith("pdf:"))
async def handle_pdf_button(callback: CallbackQuery):
    """Отправка PDF накладной"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ У вас нет прав", show_alert=True)
        return
    
    # Парсим order_id из callback_data
    order_id = callback.data.split(":")[1]
    
    # Получаем путь к PDF из базы
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute(
            "SELECT pdf_path FROM orders WHERE order_id = ?",
            (order_id,)
        )
        row = await cursor.fetchone()
    
    if not row or not row[0]:
        await callback.answer("❌ PDF не найден", show_alert=True)
        return
    
    pdf_path = row[0]
    
    # Проверяем существование файла
    import os
    if not os.path.exists(pdf_path):
        await callback.answer("❌ Файл не найден на диске", show_alert=True)
        return
    
    try:
        # Отправляем PDF
        await bot.send_document(
            callback.from_user.id,
            document=FSInputFile(pdf_path),
            caption=f"📄 Накладная {order_id}"
        )
        await callback.answer("✅ PDF отправлен!")
    except Exception as e:
        logger.error(f"Ошибка отправки PDF: {e}")
        await callback.answer("❌ Ошибка отправки", show_alert=True)






@dp.callback_query(F.data == "admin_stats")
async def show_admin_stats(callback: CallbackQuery):
    """Показать статистику за день"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ У вас нет прав", show_alert=True)
        return
    
    await callback.answer()
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    async with aiosqlite.connect(DB_FILE) as db:
        # Всего заказов
        cursor = await db.execute(
            "SELECT COUNT(*), SUM(total) FROM orders WHERE DATE(created_at) = ?", (today)
        )
        total_orders, total_sum = await cursor.fetchone()
        
        # По статусам
        cursor = await db.execute(
            "SELECT status, COUNT(*) FROM orders WHERE DATE(created_at) = ? GROUP BY status", (today)
        )
        statuses = await cursor.fetchall()
    
    status_text = "\n".join([f"• {s[0]}: {s[1]}" for s in statuses])
    
    text = f"""
📊 <b>Статистика за {today}</b>

📦 Всего заказов: {total_orders or 0}
💰 Сумма: {total_sum or 0}₸

Статусы:
{status_text or 'нет данных'}
"""
    
    await callback.message.answer(text)


@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    """Вернуться в главное меню"""
    await callback.answer()
    await cmd_start(callback.message)


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
            # Генерируем PDF
            pdf_path = generate_receipt_pdf(order_id, order_data)
            
            await db.execute(
                """
                INSERT INTO orders 
                (order_id, client_name, room, telegram_user_id, telegram_username, items, total, timestamp, pdf_path, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'принят')
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
                    pdf_path,
                ))
            await db.commit()

        logger.info(f"Заказ #{order_id} сохранён")

        # Добавляем pdf_path в order_data
        order_data['pdf_path'] = pdf_path
        
        await notify_admins_new_order(order_id, order_data)
        await notify_client_order_received(order_id, order_data)

        return {"status": "ok", "order_id": order_id}

    except Exception as e:
        logger.error(f"Ошибка сохранения заказа: {e}")
        return {"status": "error", "message": str(e)}




def generate_receipt_pdf(order_id: str, order_data: dict) -> str:
    """Генерирует PDF накладную и возвращает путь к файлу"""
    # Создаём директорию для PDF
    pdf_dir = '/app/data/receipts'
    import os
    os.makedirs(pdf_dir, exist_ok=True)
    
    # Путь к файлу
    pdf_path = f"{pdf_dir}/{order_id}.pdf"
    
    # Создаём PDF
    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4
    
    # Пытаемся загрузить русский шрифт
    try:
        pdfmetrics.registerFont(TTFont('DejaVu', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
        font_name = 'DejaVu'
    except:
        font_name = 'Helvetica'
    
    # Заголовок
    c.setFont(font_name, 16)
    c.drawCentredString(width/2, height - 50*mm, "ПЕЛИКАН АЛАКОЛЬ")
    c.setFont(font_name, 12)
    c.drawCentredString(width/2, height - 60*mm, "Заказ из бара")
    
    # Линия
    c.line(40*mm, height - 65*mm, width - 40*mm, height - 65*mm)
    
    y = height - 75*mm
    c.setFont(font_name, 10)
    
    # Информация о заказе
    c.drawString(40*mm, y, f"Заказ №: {order_id}")
    y -= 6*mm
    
    from datetime import datetime
    try:
        dt = datetime.fromisoformat(order_data.get('timestamp', '').replace('Z', '+00:00'))
        date_str = dt.strftime('%d.%m.%Y %H:%M')
    except:
        date_str = order_data.get('timestamp', 'н/д')
    
    c.drawString(40*mm, y, f"Дата: {date_str}")
    y -= 10*mm
    
    # Клиент
    c.setFont(font_name, 11)
    c.drawString(40*mm, y, "КЛИЕНТ")
    c.setFont(font_name, 10)
    y -= 6*mm
    c.drawString(40*mm, y, f"Имя: {order_data.get('name', 'н/д')}")
    y -= 5*mm
    c.drawString(40*mm, y, f"Комната: {order_data.get('room', 'н/д')}")
    y -= 10*mm
    
    # Состав заказа
    c.setFont(font_name, 11)
    c.drawString(40*mm, y, "СОСТАВ ЗАКАЗА:")
    c.setFont(font_name, 9)
    y -= 6*mm
    
    items = order_data.get('items', [])
    for item in items:
        name = item['name']
        qty = item.get('quantity', 1)
        price = item['price']
        c.drawString(40*mm, y, f"• {name} x{qty}")
        c.drawRightString(width - 40*mm, y, f"{price} ₸")
        y -= 5*mm
    
    # Линия
    y -= 3*mm
    c.line(40*mm, y, width - 40*mm, y)
    y -= 7*mm
    
    # Итого
    c.setFont(font_name, 12)
    c.drawString(40*mm, y, "ИТОГО К ОПЛАТЕ:")
    c.drawRightString(width - 40*mm, y, f"{order_data.get('total', 0)} ₸")
    y -= 15*mm
    
    # Подписи
    c.setFont(font_name, 10)
    c.line(40*mm, y, width - 40*mm, y)
    y -= 10*mm
    
    c.drawString(40*mm, y, "Подпись клиента: ___________________")
    y -= 8*mm
    c.drawString(40*mm, y, "Подпись официанта: ___________________")
    y -= 8*mm
    c.drawString(40*mm, y, "Дата выдачи: ___________________")
    
    c.save()
    return pdf_path


async def notify_admins_new_order(order_id: str, order_data: dict):
    """Уведомление админов о новом заказе с PDF накладной"""
    items_text = "\n".join(
        f"• {item['name']} x{item.get('quantity', 1)} — {item['price']} ₸"
        for item in order_data.get("items", [])
    )

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
""".strip()

    # Получаем путь к PDF из order_data
    pdf_path = order_data.get('pdf_path')
    
    for admin_id in ADMIN_IDS:
        try:
            # Отправляем сообщение
            await bot.send_message(admin_id, admin_message)
            
            # Отправляем PDF если он есть
            if pdf_path:
                await bot.send_document(
                    admin_id,
                    document=FSInputFile(pdf_path),
                    caption=f"📄 Накладная {order_id}"
                )
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
            headers=headers)




async def get_order_by_id(request: web.Request) -> web.Response:
    """API для получения заказа по ID (для страницы печати)"""
    origin = request.headers.get("Origin")
    headers = cors_headers(origin)
    
    if request.method == "OPTIONS":
        return web.Response(status=204, headers=headers)
    
    try:
        order_id = request.match_info.get('order_id')
        
        async with aiosqlite.connect(DB_FILE) as db:
            cursor = await db.execute(
                "SELECT order_id, client_name, room, items, total, timestamp FROM orders WHERE order_id = ?",
                (order_id)
            )
            row = await cursor.fetchone()
        
        if not row:
            return web.json_response(
                {"error": "Заказ не найден"},
                status=404,
                headers=headers
            )
        
        order_id, client_name, room, items_json, total, timestamp = row
        
        order_data = {
            "order_id": order_id,
            "client_name": client_name,
            "room": room,
            "items": json.loads(items_json),
            "total": total,
            "timestamp": timestamp
        }
        
        return web.json_response(order_data, headers=headers)
        
    except Exception as e:
        logger.error(f"Ошибка получения заказа: {e}")
        return web.json_response(
            {"error": str(e)},
            status=500,
            headers=headers
        )


async def start_webhook_server():
    app = web.Application()
    app.router.add_route("POST", "/api/order", handle_new_order)
    app.router.add_route("OPTIONS", "/api/order", handle_new_order)
    app.router.add_route("GET", "/api/order/{order_id}", get_order_by_id)
    app.router.add_route("OPTIONS", "/api/order/{order_id}", get_order_by_id)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", WEBHOOK_PORT)
    await site.start()
    logger.info(f"HTTP API запущен на порту {WEBHOOK_PORT} (/api/order)")



# ==================== WEBAPP ОБРАБОТЧИК ====================

@dp.message(F.web_app_data)
async def handle_webapp_order(message: Message):
    """Обработка заказа из Mini App"""
    try:
        order_data = json.loads(message.web_app_data.data)
        
        # Добавляем telegram данные
        order_data["telegram_user_id"] = message.from_user.id
        order_data["telegram_username"] = message.from_user.username
        order_data["timestamp"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Сохраняем
        result = await save_order(order_data)
        
        if result["status"] == "ok":
            await message.answer(
                f"✅ <b>Заказ #{result['order_id']} принят!</b>\n\n"
                f"💰 Итого: {order_data['total']}₸\n"
                f"⏱️ Примерное время: ~20 минут\n\n"
                f"Проверить статус: /status {result['order_id']}"
            )
        else:
            await message.answer("❌ Ошибка при создании заказа")
            
    except Exception as e:
        logger.error(f"Ошибка обработки WebApp: {e}")
        await message.answer("❌ Ошибка при обработке заказа")


# ==================== КОМАНДЫ ДЛЯ АДМИНОВ ====================

@dp.message(Command("orders"))
async def cmd_orders(message: Message):
    """Список активных заказов"""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ У вас нет прав.")
        return
    
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute(
            "SELECT order_id, client_name, room, status, total FROM orders WHERE status != 'выдан' ORDER BY created_at DESC LIMIT 10"
        )
        rows = await cursor.fetchall()
    
    if not rows:
        await message.answer("📋 Активных заказов нет")
        return
    
    text = "<b>📋 Активные заказы:</b>\n\n"
    for order_id, name, room, status, total in rows:
        emoji = {"принят": "🟡", "готовится": "🟠", "готов": "🟢"}.get(status, "⚪")
        text += f"{emoji} #{order_id}\n👤 {name} | 🏨 {room}\n💰 {total}₸ | {status}\n\n"
    
    await message.answer(text)


@dp.message(Command("stats"))
async def cmd_stats(message: Message):
    """Статистика за сегодня"""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ У вас нет прав.")
        return
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    async with aiosqlite.connect(DB_FILE) as db:
        # Всего заказов
        cursor = await db.execute(
            "SELECT COUNT(*), SUM(total) FROM orders WHERE DATE(created_at) = ?", (today)
        )
        total_orders, total_sum = await cursor.fetchone()
        
        # По статусам
        cursor = await db.execute(
            "SELECT status, COUNT(*) FROM orders WHERE DATE(created_at) = ? GROUP BY status", (today)
        )
        statuses = await cursor.fetchall()
    
    status_text = "\n".join([f"• {s[0]}: {s[1]}" for s in statuses])
    
    text = f"""
📊 <b>Статистика за {today}</b>

📦 Всего заказов: {total_orders or 0}
💰 Сумма: {total_sum or 0}₸

Статусы:
{status_text or 'нет данных'}
"""
    
    await message.answer(text)


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

# ==================== ОБРАБОТЧИКИ КОМАНД ====================

@dp.message(Command("update"))
async def cmd_update_status(message: types.Message, command: CommandObject):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ У вас нет прав.")
        return

    args = command.args
    if not args or len(args.split()) < 2:
        await message.answer("❌ Формат: /update ORD123456 статус")
        return

    order_id, new_status = args.split(maxsplit=1)
    new_status = new_status.lower()

    valid_statuses = ["принят", "готовится", "готов", "выдан", "отменен"]
    if new_status not in valid_statuses:
        await message.answer(f"❌ Неверный статус. Доступны: {', '.join(valid_statuses)}")
        return

    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute(
            "UPDATE orders SET status = ? WHERE order_id = ?",
            (new_status, order_id)
        )
        await db.commit()

        if cursor.rowcount == 0:
            await message.answer(f"❌ Заказ {order_id} не найден")
            return

    await notify_client_status_update(order_id, new_status)
    await message.answer(f"✅ Статус {order_id} изменён на '{new_status}'")


@dp.message(Command("status"))
async def cmd_status(message: types.Message, command: CommandObject):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ У вас нет прав.")
        return

    order_id = command.args
    if not order_id:
        await message.answer("❌ Формат: /status ORD123456")
        return

    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute(
            "SELECT * FROM orders WHERE order_id = ?", (order_id)
        )
        row = await cursor.fetchone()

    if not row:
        await message.answer(f"❌ Заказ {order_id} не найден")
        return

    order_dict = dict(zip([d[0] for d in cursor.description], row))
    items = json.loads(order_dict["items"])

    items_text = "\n".join(
        f"• {item['name']} x{item.get('quantity', 1)} — {item['price']} ₸"
        for item in items
    )

    telegram_user_id = order_dict['telegram_user_id']
    telegram_username = order_dict['telegram_username']
    contact_info = f"@{telegram_username}" if telegram_username else f"ID:{telegram_user_id}"

    status_message = f"""
<b>Заказ #{order_id}</b>

👤 Клиент: {order_dict['client_name']}
🏨 Комната: {order_dict['room']}
📱 Telegram: {contact_info}

🍽 Заказ:
{items_text}

💰 Итого: {order_dict['total']} ₸
🕐 {order_dict['timestamp']}
📊 Статус: {order_dict['status']}
""".strip()

    await message.answer(status_message, parse_mode="HTML")


# ==================== УВЕДОМЛЕНИЯ КЛИЕНТУ ====================

async def notify_client_status_update(order_id: str, status: str):
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute(
            "SELECT telegram_user_id, telegram_username FROM orders WHERE order_id = ?",
            (order_id)
        )
        row = await cursor.fetchone()
        
        if not row:
            return
        
        telegram_user_id, telegram_username = row

    messages = {
        "готовится": f"⏳ Ваш заказ #{order_id} готовится!",
        "готов": f"✅ Ваш заказ #{order_id} готов! Можно забирать в баре.",
        "выдан": f"🎉 Ваш заказ #{order_id} выдан! Приятного аппетита!",
        "отменен": f"❌ Заказ #{order_id} отменен. Свяжитесь с администратором.",
    }
    
    message = messages.get(status, f"Статус заказа #{order_id} обновлён.")

    if telegram_user_id:
        try:
            await bot.send_message(telegram_user_id, message)
        except Exception as e:
            logger.warning(f"Не удалось отправить клиенту {telegram_user_id}: {e}")


# ==================== ОСТАЛЬНЫЕ ХЕНДЛЕРЫ ====================

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
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


@dp.callback_query(F.data.in_(["transfer", "activities"]))
async def handle_simple(callback: types.CallbackQuery):
    if callback.data == "transfer":
        await callback.message.answer(
            "🚗 Для заказа трансфера пиши @pelikan_alakol_support"
        )
    elif callback.data == "activities":
        await callback.message.answer(
            "🎯 Экскурсии — уточняй у @pelikan_alakol_support"
        )
    await callback.answer()


# ==================== MAIN ====================

if __name__ == "__main__":
    asyncio.run(main())

