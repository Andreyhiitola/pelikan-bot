import asyncio
import logging
import os
import json
from datetime import datetime
import aiosqlite
from aiohttp import web
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F, types
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import black
from PIL import Image, ImageDraw, ImageFont
import tempfile
import shutil
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command, CommandObject
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    BotCommand,
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
    WebAppInfo,
    FSInputFile)

from reviews_handler import reviews_router
from navigation_handler import router as navigation_router
from analytics_handler import setup_scheduler
from analytics_commands import analytics_router
from qr_generator import qr_router
# ==================== НАСТРОЙКИ ====================

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "123456789").split(",")))
MANAGER_IDS = list(map(int, os.getenv("MANAGER_IDS", "").split(","))) if os.getenv("MANAGER_IDS") else []
WAITER_IDS = list(map(int, os.getenv("WAITER_IDS", "").split(","))) if os.getenv("WAITER_IDS") else []

def get_user_role(user_id: int) -> str:
    if user_id in ADMIN_IDS:
        return "admin"
    elif user_id in MANAGER_IDS:
        return "manager"
    elif user_id in WAITER_IDS:
        return "waiter"
    return None

def has_permission(user_id: int, permission: str) -> bool:
    role = get_user_role(user_id)
    permissions = {
        "admin": ["view_orders", "change_status", "export", "stats", "cleanup", "admin_panel"],
        "manager": ["view_orders", "export", "stats", "admin_panel"],
        "waiter": ["view_orders", "change_status", "admin_panel"]
    }
    return role and permission in permissions.get(role, [])

DB_FILE = os.getenv("DB_FILE", "orders.db")
WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT", "8080"))
ALLOWED_ORIGIN = os.getenv("ALLOWED_ORIGIN", "https://pelikan-alakol-site-v2.pages.dev")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher(storage=MemoryStorage())

# Временное хранилище для отслеживания откуда пришел пользователь
user_room_tracking = {}

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
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_user_id INTEGER NOT NULL,
                telegram_username TEXT,
                guest_name TEXT NOT NULL,
                room_number TEXT,
                cleanliness INTEGER CHECK(cleanliness BETWEEN 1 AND 10),
                comfort INTEGER CHECK(comfort BETWEEN 1 AND 10),
                location INTEGER CHECK(location BETWEEN 1 AND 10),
                facilities INTEGER CHECK(facilities BETWEEN 1 AND 10),
                staff INTEGER CHECK(staff BETWEEN 1 AND 10),
                value_for_money INTEGER CHECK(value_for_money BETWEEN 1 AND 10),
                pros TEXT,
                cons TEXT,
                comment TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                moderated_at TIMESTAMP,
                moderated_by INTEGER,
                display_name TEXT,
                is_published INTEGER DEFAULT 0
            )
        """)
        
        await db.commit()
        
        try:
            await db.execute("ALTER TABLE orders ADD COLUMN pdf_path TEXT")
        
            await db.commit()
            logger.info("Миграция: добавлена колонка pdf_path")
        except:
            pass
        try:
            await db.execute("ALTER TABLE orders ADD COLUMN scanned_room_number TEXT")
            await db.commit()
            logger.info("Миграция: добавлена колонка scanned_room_number в orders")
        except:
            pass
        
        try:
            await db.execute("ALTER TABLE reviews ADD COLUMN scanned_room_number TEXT")
            await db.commit()
            logger.info("Миграция: добавлена колонка scanned_room_number в reviews")
        except:
            pass
            await db.commit()
            logger.info("Миграция: добавлена колонка pdf_path")
        except:
            pass
            
    logger.info("База данных готова")

# ==================== TELEGRAM ХЕНДЛЕРЫ ====================

@dp.message(Command("start"))
async def cmd_start(message: Message, command: CommandObject = None):
    user_id = message.from_user.id
    
    # Обрабатываем deep link с номером комнаты из QR-кода
    scanned_room = None
    if command and command.args:
        args = command.args
        if args.startswith("review_"):
            scanned_room = args.replace("review_", "")
            # Сохраняем в памяти откуда пришел пользователь
            user_room_tracking[user_id] = scanned_room
            logger.info(f"Пользователь {user_id} отсканировал QR из номера {scanned_room}")
    
    # Формируем сообщение
    if scanned_room:
        caption = f"🌊 <b>Пеликан Алаколь</b>\n\n📍 <b>Номер {scanned_room}</b>\n\nВыберите услугу ↓"
    else:
        caption = "🌊 <b>Пеликан Алаколь</b>\n\nВыберите услугу ↓"

    buttons = [
        [
            InlineKeyboardButton(
                text="🍸 Бар (еда на заказ)",
                web_app=WebAppInfo(url="https://pelikan-alakol-site-v2.pages.dev/bar.html")),
            InlineKeyboardButton(
                text="🍴 Столовая",
                web_app=WebAppInfo(url="https://pelikan-alakol-site-v2.pages.dev/index_menu.html")),
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
                text="💬 WhatsApp",
                url="https://wa.me/77767275841"),
        ],
        [
            InlineKeyboardButton(
                text="✈️ Telegram",
                url="https://t.me/+77767275841"),
        ],
    ]
    
    buttons.append([
        InlineKeyboardButton(
            text="⭐ Оставить отзыв",
            callback_data="review_start")
    ])
    
    buttons.append([
        InlineKeyboardButton(
            text="🗺️ Как добраться",
            callback_data="navigation")
    ])
    
    if has_permission(message.from_user.id, "admin_panel"):
        buttons.append([
            InlineKeyboardButton(
                text="👨‍💼 Админ-панель",
                callback_data="admin_panel")
        ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    photo_url = "https://pelikan-alakol-site-v2.pages.dev/img/welcome-beach.jpg"

    try:
        await message.answer_photo(photo=photo_url, caption=caption, reply_markup=keyboard)
    except Exception as e:
        logger.warning(f"Фото не загрузилось: {e}")
        await message.answer(caption, reply_markup=keyboard)

# ==================== АДМИН-ПАНЕЛЬ ====================

@dp.callback_query(F.data == "admin_panel")
async def show_admin_panel(callback: CallbackQuery):
    if not has_permission(callback.from_user.id, "admin_panel"):
        await callback.answer("❌ У вас нет прав", show_alert=True)
        return
    
    text = "👨‍💼 <b>АДМИН-ПАНЕЛЬ</b>\n\nУправление заказами и статистика"
    user_id = callback.from_user.id
    buttons = []
    
    if has_permission(user_id, "view_orders"):
        buttons.append([InlineKeyboardButton(text="📋 Активные заказы", callback_data="admin_orders")])
    
    if has_permission(user_id, "stats"):
        buttons.append([InlineKeyboardButton(text="📊 Статистика за день", callback_data="admin_stats")])
    
    if has_permission(user_id, "export"):
        buttons.append([InlineKeyboardButton(text="📥 Экспорт заказов", callback_data="admin_export")])
    
    if has_permission(user_id, "cleanup"):
        buttons.append([InlineKeyboardButton(text="🗑️ Очистка (>30 дней)", callback_data="admin_cleanup")])
    
    buttons.append([InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


# ==================== КОМАНДЫ АДМИН-ПАНЕЛИ ====================

@dp.message(Command("admin_panel"))
async def cmd_admin_panel(message: Message):
    if not has_permission(message.from_user.id, "admin_panel"):
        await message.answer("❌ У вас нет прав")
        return
    
    text = "👨‍💼 <b>АДМИН-ПАНЕЛЬ</b>\n\nУправление заказами и статистика"
    user_id = message.from_user.id
    buttons = []
    
    if has_permission(user_id, "view_orders"):
        buttons.append([InlineKeyboardButton(text="📋 Активные заказы", callback_data="admin_orders")])
    
    if has_permission(user_id, "stats"):
        buttons.append([InlineKeyboardButton(text="📊 Статистика за день", callback_data="admin_stats")])
    
    if has_permission(user_id, "export"):
        buttons.append([InlineKeyboardButton(text="📥 Экспорт заказов", callback_data="admin_export")])
    
    if has_permission(user_id, "cleanup"):
        buttons.append([InlineKeyboardButton(text="🗑️ Очистка (>30 дней)", callback_data="admin_cleanup")])
    
    buttons.append([InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(text, reply_markup=keyboard)


@dp.message(Command("stats"))
async def cmd_stats(message: Message):
    if not has_permission(message.from_user.id, "stats"):
        await message.answer("❌ У вас нет прав")
        return
    
    from datetime import date
    today = date.today().isoformat()
    
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute(
            "SELECT COUNT(*), SUM(total) FROM orders WHERE DATE(created_at) = ?", 
            (today,)
        )
        count, total_sum = await cursor.fetchone()
        
        cursor = await db.execute(
            "SELECT status, COUNT(*) FROM orders WHERE DATE(created_at) = ? GROUP BY status",
            (today,)
        )
        statuses = await cursor.fetchall()
    
    status_text = "\n".join([f"  • {status}: {cnt}" for status, cnt in statuses]) if statuses else "  Нет заказов"
    
    text = f"""📊 <b>Статистика за сегодня</b>

📦 Всего заказов: {count or 0}
💰 Сумма: {total_sum or 0}₸

📋 По статусам:
{status_text}
"""
    await message.answer(text)


@dp.message(Command("backup"))
async def cmd_backup(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Недостаточно прав")
        return
    
    try:
        backup_name = f"orders_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        backup_path = f"/tmp/{backup_name}"
        
        await message.answer("⏳ Создаю бэкап...")
        
        shutil.copy(DB_FILE, backup_path)
        
        file = FSInputFile(backup_path)
        await message.answer_document(
            document=file,
            caption=f"📦 <b>Бэкап базы данных</b>\n\n"
                    f"📅 Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
                    f"💾 Размер: {os.path.getsize(backup_path) / 1024:.1f} KB"
        )
        
        os.remove(backup_path)
        
    except Exception as e:
        await message.answer(f"❌ Ошибка создания бэкапа: {e}")
        logger.error(f"Ошибка бэкапа: {e}")


@dp.callback_query(F.data == "admin_stats")
async def show_stats(callback: CallbackQuery):
    if not has_permission(callback.from_user.id, "stats"):
        await callback.answer("❌ У вас нет прав", show_alert=True)
        return
    
    await callback.answer()
    
    from datetime import date
    today = date.today().isoformat()
    
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute(
            "SELECT COUNT(*), SUM(total) FROM orders WHERE DATE(created_at) = ?", 
            (today,)
        )
        count, total_sum = await cursor.fetchone()
        
        cursor = await db.execute(
            "SELECT status, COUNT(*) FROM orders WHERE DATE(created_at) = ? GROUP BY status",
            (today,)
        )
        statuses = await cursor.fetchall()
    
    status_text = "\n".join([f"  • {status}: {cnt}" for status, cnt in statuses]) if statuses else "  Нет заказов"
    
    text = f"""📊 <b>Статистика за сегодня</b>

📦 Всего заказов: {count or 0}
💰 Сумма: {total_sum or 0}₸

📋 По статусам:
{status_text}
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад в админ-панель", callback_data="admin_panel")]
    ])
    
    await callback.message.answer(text, reply_markup=keyboard)


@dp.callback_query(F.data == "admin_export")
async def export_orders(callback: CallbackQuery):
    if not has_permission(callback.from_user.id, "export"):
        await callback.answer("❌ У вас нет прав", show_alert=True)
        return
    
    await callback.answer("📥 Генерирую отчёт...")
    
    import csv
    from io import StringIO
    from datetime import date
    
    today = date.today().isoformat()
    
    async with aiosqlite.connect(DB_FILE) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM orders WHERE DATE(created_at) = ? ORDER BY created_at DESC",
            (today,)
        )
        orders = await cursor.fetchall()
    
    if not orders:
        await callback.message.answer("📭 Нет заказов за сегодня")
        return
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Клиент', 'Комната', 'Сумма', 'Статус', 'Дата'])
    
    for order in orders:
        writer.writerow([
            order['order_id'],
            order['client_name'],
            order['room'],
            order['total'],
            order['status'],
            order['created_at']
        ])
    
    filename = f"orders_{today}.csv"
    csv_path = f"/app/data/exports/{filename}"
    
    os.makedirs("/app/data/exports", exist_ok=True)
    
    with open(csv_path, 'w', encoding='utf-8') as f:
        f.write(output.getvalue())
    
    await bot.send_document(
        callback.from_user.id,
        document=FSInputFile(csv_path),
        caption=f"📊 Отчёт за {today}\nВсего заказов: {len(orders)}"
    )


@dp.callback_query(F.data == "admin_cleanup")
async def cleanup_old_orders(callback: CallbackQuery):
    if not has_permission(callback.from_user.id, "cleanup"):
        await callback.answer("❌ У вас нет прав", show_alert=True)
        return
    
    await callback.answer()
    
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute(
            "DELETE FROM orders WHERE created_at < datetime('now', '-30 days')"
        )
        await db.commit()
        deleted = cursor.rowcount
    
    await callback.message.answer(
        f"🗑️ Очистка завершена\n\n"
        f"Удалено заказов: {deleted}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
        ])
    )


@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    await callback.answer()
    await cmd_start(callback.message)


@dp.callback_query(F.data.in_(["transfer", "activities"]))
async def handle_simple(callback: CallbackQuery):
    if callback.data == "transfer":
        text = """🚗 <b>Трансфер</b>

Мы организуем трансфер от/до ЖД вокзала Акши.

Для заказа свяжитесь с нами:
💬 WhatsApp: +7 (776) 727 58 41
✈️ Telegram: https://t.me/+77767275841
📞 Телефон: +7 (776) 727 58 41"""
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="💬 WhatsApp", url="https://wa.me/77767275841"),
                InlineKeyboardButton(text="✈️ Telegram", url="https://t.me/+77767275841")
            ],
            [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu")]
        ])
        await callback.message.answer(text, reply_markup=keyboard)
        
    elif callback.data == "activities":
        text = """🎯 <b>Экскурсии и достопримечательности</b>

Мы не занимаемся организацией экскурсий, но с радостью подскажем интересные места в районе озера Алаколь!

📍 <b>Что посмотреть:</b>
Свяжитесь с нами - мы порекомендуем локации исходя из ваших интересов.

Вы также можете найти местных экскурсионных операторов через интернет."""
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="💬 WhatsApp", url="https://wa.me/77767275841"),
                InlineKeyboardButton(text="✈️ Telegram", url="https://t.me/+77767275841")
            ],
            [InlineKeyboardButton(text="🗺️ Как добраться", callback_data="navigation")],
            [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu")]
        ])
        await callback.message.answer(text, reply_markup=keyboard)
        
    await callback.answer()


@dp.message(Command("help"))
async def cmd_help(message: Message):
    text = (
        "📖 <b>Помощь</b>\n\n"
        "🍸 Бар — еда и напитки в номер\n"
        "🏠 Бронирование — онлайн на сайте\n"
        "🚗 Трансфер / 🎯 Экскурсии — свяжитесь с нами:\n"
        "💬 WhatsApp: +7 (776) 727 58 41\n"
        "✈️ Telegram: https://t.me/+77767275841\n\n"
        "Статусы:\n🟡 Принят\n🟠 Готовится\n🟢 Готов\n✅ Выдан"
    )
    await message.answer(text)


# ==================== ОБРАБОТЧИКИ ЗАКАЗОВ ====================

@dp.callback_query(F.data == "admin_orders")
async def show_admin_orders(callback: CallbackQuery):
    if not has_permission(callback.from_user.id, "view_orders"):
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
        
        try:
            items = json.loads(items_json)
            items_text = "\n".join([f"• {item['name']} x{item.get('quantity', 1)} - {item['price']}₸" for item in items])
        except:
            items_text = "Состав заказа недоступен"
        
        text = f"{emoji} <b>#{order_id}</b>\n👤 {name} | 🏨 {room}\n\n🍽️ Заказ:\n{items_text}\n\n💰 Итого: {total}₸\n📊 Статус: {status}"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="⏳ Готовится", callback_data=f"status:{order_id}:готовится"),
                InlineKeyboardButton(text="✅ Готов", callback_data=f"status:{order_id}:готов"),
            ],
            [InlineKeyboardButton(text="🎉 Выдан", callback_data=f"status:{order_id}:выдан")],
            [
                InlineKeyboardButton(text="📸 Фото", callback_data=f"photo:{order_id}"),
                InlineKeyboardButton(text="📄 PDF", callback_data=f"pdf:{order_id}"),
            ]
        ])
        
        await callback.message.answer(text, reply_markup=keyboard)


@dp.callback_query(F.data.startswith("status:"))
async def handle_status_button(callback: CallbackQuery):
    if not has_permission(callback.from_user.id, "change_status"):
        await callback.answer("❌ У вас нет прав", show_alert=True)
        return
    
    parts = callback.data.split(":")
    order_id = parts[1]
    new_status = parts[2]
    
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute("UPDATE orders SET status = ? WHERE order_id = ?", (new_status, order_id))
        await db.commit()
        
        if cursor.rowcount == 0:
            await callback.answer("❌ Заказ не найден", show_alert=True)
            return
    
    await notify_client_status_update(order_id, new_status)
    
    emoji = {"готовится": "🟠", "готов": "🟢", "выдан": "🎉"}.get(new_status, "⚪")
    
    try:
        new_markup = None if new_status == "выдан" else callback.message.reply_markup
        old_text = callback.message.text or callback.message.caption
        new_text = old_text.split('\n')
        
        if new_text:
            new_text[0] = f"{emoji} <b>#{order_id}</b>"
            for i, line in enumerate(new_text):
                if "📊 Статус:" in line:
                    new_text[i] = f"📊 Статус: {new_status}"
                    break
        
        await callback.message.edit_text("\n".join(new_text), reply_markup=new_markup, parse_mode="HTML")
    except:
        pass
    
    await callback.answer(f"✅ Статус изменён на '{new_status}'")


async def notify_client_status_update(order_id: str, status: str):
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute("SELECT telegram_user_id FROM orders WHERE order_id = ?", (order_id,))
        row = await cursor.fetchone()
        if not row:
            return
        telegram_user_id = row[0]
    
    messages = {
        "готовится": f"⏳ Ваш заказ #{order_id} готовится!",
        "готов": f"✅ Ваш заказ #{order_id} готов! Можно забирать в баре.",
        "выдан": f"🎉 Ваш заказ #{order_id} выдан! Приятного аппетита!",
    }
    
    message = messages.get(status, f"Статус заказа #{order_id} обновлён.")
    
    if telegram_user_id:
        try:
            await bot.send_message(telegram_user_id, message)
        except Exception as e:
            logger.warning(f"Не удалось отправить клиенту {telegram_user_id}: {e}")


# ==================== PDF И ФОТО ====================

def generate_receipt_pdf(order_id: str, order_data: dict) -> str:
    pdf_dir = '/app/data/receipts'
    os.makedirs(pdf_dir, exist_ok=True)
    
    pdf_path = f"{pdf_dir}/{order_id}.pdf"
    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4
    
    try:
        pdfmetrics.registerFont(TTFont('DejaVu', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
        font_name = 'DejaVu'
    except:
        font_name = 'Helvetica'
    
    c.setFont(font_name, 16)
    c.drawCentredString(width/2, height - 50*mm, "ПЕЛИКАН АЛАКОЛЬ")
    c.setFont(font_name, 12)
    c.drawCentredString(width/2, height - 60*mm, "Заказ из бара")
    c.line(40*mm, height - 65*mm, width - 40*mm, height - 65*mm)
    
    y = height - 75*mm
    c.setFont(font_name, 10)
    c.drawString(40*mm, y, f"Заказ №: {order_id}")
    y -= 10*mm
    
    c.setFont(font_name, 11)
    c.drawString(40*mm, y, "КЛИЕНТ")
    c.setFont(font_name, 10)
    y -= 6*mm
    c.drawString(40*mm, y, f"Имя: {order_data.get('name', 'н/д')}")
    y -= 5*mm
    c.drawString(40*mm, y, f"Комната: {order_data.get('room', 'н/д')}")
    y -= 10*mm
    
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
    
    y -= 3*mm
    c.line(40*mm, y, width - 40*mm, y)
    y -= 7*mm
    
    c.setFont(font_name, 12)
    c.drawString(40*mm, y, "ИТОГО К ОПЛАТЕ:")
    c.drawRightString(width - 40*mm, y, f"{order_data.get('total', 0)} ₸")
    
    c.save()
    return pdf_path


def generate_receipt_image(order_id: str, order_data: dict) -> str:
    img_dir = '/app/data/receipts'
    os.makedirs(img_dir, exist_ok=True)
    
    img_path = f"{img_dir}/{order_id}.png"
    width = 600
    padding = 30
    line_height = 35
    
    items = order_data.get('items', [])
    height = 400 + (len(items) * line_height) + 150
    
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    try:
        font_title = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 32)
        font_large = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 24)
        font_normal = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 20)
    except:
        font_title = font_large = font_normal = ImageFont.load_default()
    
    y = padding
    draw.text((width//2, y), "ПЕЛИКАН АЛАКОЛЬ", fill='#2C3E50', font=font_title, anchor='mt')
    y += 50
    draw.text((width//2, y), "Заказ из бара", fill='#34495E', font=font_normal, anchor='mt')
    y += 40
    draw.line([(padding, y), (width - padding, y)], fill='#BDC3C7', width=2)
    y += 25
    
    draw.text((padding, y), f"Заказ №: {order_id}", fill='#2C3E50', font=font_large)
    y += 45
    
    draw.text((padding, y), "КЛИЕНТ", fill='#E74C3C', font=font_large)
    y += 35
    draw.text((padding, y), f"Имя: {order_data.get('name', 'н/д')}", fill='#2C3E50', font=font_normal)
    y += 30
    draw.text((padding, y), f"Комната: {order_data.get('room', 'н/д')}", fill='#2C3E50', font=font_normal)
    y += 45
    
    draw.text((padding, y), "СОСТАВ ЗАКАЗА:", fill='#E74C3C', font=font_large)
    y += 35
    
    for item in items:
        item_text = f"• {item['name']} x{item.get('quantity', 1)}"
        price_text = f"{item['price']} ₸"
        draw.text((padding + 10, y), item_text, fill='#2C3E50', font=font_normal)
        draw.text((width - padding, y), price_text, fill='#27AE60', font=font_normal, anchor='rt')
        y += line_height
    
    y += 15
    draw.line([(padding, y), (width - padding, y)], fill='#BDC3C7', width=2)
    y += 25
    
    draw.text((padding, y), "ИТОГО К ОПЛАТЕ:", fill='#2C3E50', font=font_large)
    draw.text((width - padding, y), f"{order_data.get('total', 0)} ₸", fill='#E74C3C', font=font_large, anchor='rt')
    
    img.save(img_path, 'PNG', quality=95)
    return img_path


@dp.callback_query(F.data.startswith("pdf:"))
async def handle_pdf_button(callback: CallbackQuery):
    if not has_permission(callback.from_user.id, "view_orders"):
        await callback.answer("❌ У вас нет прав", show_alert=True)
        return
    
    order_id = callback.data.split(":")[1]
    
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute("SELECT pdf_path FROM orders WHERE order_id = ?", (order_id,))
        row = await cursor.fetchone()
    
    if not row or not row[0]:
        await callback.answer("❌ PDF не найден", show_alert=True)
        return
    
    pdf_path = row[0]
    
    if not os.path.exists(pdf_path):
        await callback.answer("❌ Файл не найден на диске", show_alert=True)
        return
    
    try:
        await bot.send_document(callback.from_user.id, document=FSInputFile(pdf_path), caption=f"📄 Накладная {order_id}")
        await callback.answer("✅ PDF отправлен!")
    except Exception as e:
        logger.error(f"Ошибка отправки PDF: {e}")
        await callback.answer("❌ Ошибка отправки", show_alert=True)


@dp.callback_query(F.data.startswith("photo:"))
async def handle_photo_button(callback: CallbackQuery):
    if not has_permission(callback.from_user.id, "view_orders"):
        await callback.answer("❌ У вас нет прав", show_alert=True)
        return
    
    order_id = callback.data.split(":")[1]
    
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute("SELECT client_name, room, items, total, timestamp FROM orders WHERE order_id = ?", (order_id,))
        row = await cursor.fetchone()
    
    if not row:
        await callback.answer("❌ Заказ не найден", show_alert=True)
        return
    
    name, room, items_json, total, timestamp = row
    order_data = {'name': name, 'room': room, 'items': json.loads(items_json), 'total': total, 'timestamp': timestamp}
    
    try:
        img_path = generate_receipt_image(order_id, order_data)
        await bot.send_photo(callback.from_user.id, photo=FSInputFile(img_path), caption=f"📸 Накладная {order_id}")
        await callback.answer("✅ Фото отправлено!")
    except Exception as e:
        logger.error(f"Ошибка отправки фото: {e}")
        await callback.answer("❌ Ошибка отправки", show_alert=True)


# ==================== ЛОГИКА ЗАКАЗОВ ====================

async def save_order(order_data: dict) -> dict:
    order_id = order_data.get("orderId") or str(int(datetime.now().timestamp()))
    
    # Получаем отслеживаемый номер комнаты из QR-кода
    user_id = order_data.get("telegram_user_id")
    scanned_room = user_room_tracking.get(user_id) if user_id else None
    
    try:
        async with aiosqlite.connect(DB_FILE) as db:
            pdf_path = generate_receipt_pdf(order_id, order_data)
            
            await db.execute("""
                INSERT INTO orders 
                (order_id, client_name, room, telegram_user_id, telegram_username, items, total, timestamp, pdf_path, status, scanned_room_number)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'принят', ?)
            """, (
                order_id,
                order_data.get("name"),
                order_data.get("room"),
                order_data.get("telegram_user_id"),
                order_data.get("telegram_username"),
                json.dumps(order_data.get("items", []), ensure_ascii=False),
                order_data.get("total"),
                order_data.get("timestamp"),
                pdf_path,
                scanned_room
            ))
            await db.commit()
        
        logger.info(f"Заказ #{order_id} сохранён (QR-номер: {scanned_room or 'не указан'})")
        order_data['pdf_path'] = pdf_path
        order_data['scanned_room'] = scanned_room
        
        await notify_admins_new_order(order_id, order_data)
        await notify_client_order_received(order_id, order_data)
        
        return {"status": "ok", "order_id": order_id}
    except Exception as e:
        logger.error(f"Ошибка сохранения заказа: {e}")
        return {"status": "error", "message": str(e)}

async def notify_admins_new_order(order_id: str, order_data: dict):
    items_text = "\n".join(f"• {item['name']} x{item.get('quantity', 1)} — {item['price']} ₸" for item in order_data.get("items", []))
    
    telegram_username = order_data.get("telegram_username")
    telegram_user_id = order_data.get("telegram_user_id")
    telegram_contact = f"@{telegram_username}" if telegram_username else f"ID:{telegram_user_id}" if telegram_user_id else "не указан"
    
    scanned_room = order_data.get('scanned_room')
    room_info = f"\n📱 <b>QR-код из номера: {scanned_room}</b>" if scanned_room else ""
    
    admin_message = f"""<b>🆕 Новый заказ #{order_id}</b>

👤 Клиент: <b>{order_data.get('name')}</b>
🏨 Комната: <b>{order_data.get('room')}</b>{room_info}
📱 Telegram: {telegram_contact}

🍽 <b>Заказ:</b>
{items_text}

💰 <b>Итого: {order_data.get('total')} ₸</b>
🕐 {order_data.get('timestamp')}"""
    
    pdf_path = order_data.get('pdf_path')
    
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, admin_message)
            if pdf_path:
                await bot.send_document(admin_id, document=FSInputFile(pdf_path), caption=f"📄 Накладная {order_id}")
        except Exception as e:
            logger.error(f"Ошибка отправки админу {admin_id}: {e}")

async def notify_client_order_received(order_id: str, order_data: dict):
    telegram_username = order_data.get("telegram_username")
    if not telegram_username:
        return
    
    try:
        message = f"""✅ <b>Ваш заказ #{order_id} принят!</b>

Итого: <b>{order_data.get('total')} ₸</b>
Оплата при получении в баре.

Проверить статус: /status {order_id}"""
        await bot.send_message(f"@{telegram_username}", message)
    except Exception as e:
        logger.warning(f"Не удалось отправить клиенту @{telegram_username}: {e}")


@dp.message(F.web_app_data)
async def handle_webapp_order(message: Message):
    try:
        order_data = json.loads(message.web_app_data.data)
        order_data["telegram_user_id"] = message.from_user.id
        order_data["telegram_username"] = message.from_user.username
        order_data["timestamp"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
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


# ==================== НАВИГАЦИЯ ====================

@dp.callback_query(F.data == "navigation")
async def handle_navigation_callback(callback: CallbackQuery):
    """Обработка кнопки 'Как добраться'"""
    from navigation_handler import cmd_navigation
    await cmd_navigation(callback)


# ==================== HTTP API ====================

def cors_headers(origin: str | None) -> dict:
    origin = origin or ALLOWED_ORIGIN
    return {
        "Access-Control-Allow-Origin": origin,
        "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
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
        return web.json_response({"status": "error", "message": str(e)}, status=500, headers=headers)


async def get_reviews_endpoint(request: web.Request) -> web.Response:
    origin = request.headers.get("Origin")
    headers = cors_headers(origin)
    
    if request.method == "OPTIONS":
        return web.Response(status=204, headers=headers)
    
    try:
        async with aiosqlite.connect(DB_FILE) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT 
                    display_name as name,
                    room_number,
                    cleanliness, comfort, location, facilities, staff, value_for_money,
                    ROUND((cleanliness + comfort + location + facilities + staff + value_for_money) / 6.0, 1) as avg_score,
                    pros, cons, comment,
                    created_at as date
                FROM reviews
                WHERE is_published = 1 AND status = 'approved'
                ORDER BY created_at DESC
                LIMIT 50
            """)
            
            reviews = []
            async for row in cursor:
                reviews.append({
                    'name': row['name'],
                    'room_number': row['room_number'],
                    'cleanliness': row['cleanliness'],
                    'comfort': row['comfort'],
                    'location': row['location'],
                    'facilities': row['facilities'],
                    'staff': row['staff'],
                    'value_for_money': row['value_for_money'],
                    'avg_score': row['avg_score'],
                    'pros': row['pros'],
                    'cons': row['cons'],
                    'comment': row['comment'],
                    'date': row['date']
                })
        
        return web.json_response(reviews, headers=headers)
    except Exception as e:
        logger.error(f"Ошибка API /reviews: {e}")
        return web.json_response({'error': 'Internal server error'}, status=500, headers=headers)


async def start_webhook_server():
    app = web.Application()
    app.router.add_route("POST", "/api/order", handle_new_order)
    app.router.add_route("OPTIONS", "/api/order", handle_new_order)
    app.router.add_route("GET", "/api/reviews", get_reviews_endpoint)
    app.router.add_route("OPTIONS", "/api/reviews", get_reviews_endpoint)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", WEBHOOK_PORT)
    await site.start()
    logger.info(f"HTTP API запущен на порту {WEBHOOK_PORT} (/api/order, /api/reviews)")


# ==================== MAIN ====================

async def main():
    await init_db()
    
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, "🤖 Бот запущен!")
        except Exception:
            pass
    
    dp.include_router(reviews_router)
    dp.include_router(navigation_router)
    dp.include_router(analytics_router)
    dp.include_router(qr_router)
    asyncio.create_task(start_webhook_server())
    scheduler = setup_scheduler(bot)  # Внутри main()!
    # Регистрируем команды бота
    commands = [
        BotCommand(command="start", description="🏠 Главное меню"),
        BotCommand(command="analytics", description="📊 Аналитика и отчеты"),
        BotCommand(command="test_report", description="🧪 Тестовая отправка отчета"),
        BotCommand(command="generate_qr", description="📱 Генерация QR-кодов"), 
        BotCommand(command="help", description="❓ Помощь")
    ]
    await bot.set_my_commands(commands)
    logger.info(f"✅ Зарегистрировано {len(commands)} команд бота")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
