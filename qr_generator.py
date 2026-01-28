# ==============================================================================
# qr_generator.py - Генератор QR-кодов для номеров
# ==============================================================================

import os
import qrcode
from io import BytesIO
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm

ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(","))) if os.getenv("ADMIN_IDS") else []
BOT_USERNAME = "Pelican_alacol_hotel_bot"  # Имя бота

qr_router = Router()

# Список номеров отеля (можно расширить)
ROOM_NUMBERS = [
    '101', '102', '103', '104', '105', '106', '107', '108', '109', '110',
    '201', '202', '203', '204', '205', '206', '207', '208', '209', '210',
    '301', '302', '303', '304', '305', '306', '307', '308', '309', '310',
    '401', '402', '403', '404', '405', '406', '407', '408', '409', '410',
    '501', '502', '503', '504', '505', '506', '507', '508', '509', '510'
]

def generate_qr_code(room_number: str) -> BytesIO:
    """Генерирует QR-код для конкретного номера"""
    # Deep link для бота
    deep_link = f"https://t.me/{BOT_USERNAME}?start=review_{room_number}"
    
    # Создаём QR-код
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(deep_link)
    qr.make(fit=True)
    
    # Генерируем изображение
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Сохраняем в BytesIO
    buf = BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    
    return buf

def generate_qr_pdf_all_rooms() -> BytesIO:
    """Генерирует PDF с QR-кодами для всех номеров (4 на страницу)"""
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Параметры размещения (2x2 на страницу)
    qr_size = 70 * mm
    margin = 20 * mm
    spacing_x = (width - 2 * margin - 2 * qr_size) / 1
    spacing_y = (height - 2 * margin - 2 * qr_size) / 1
    
    positions = [
        (margin, height - margin - qr_size),  # Верхний левый
        (margin + qr_size + spacing_x, height - margin - qr_size),  # Верхний правый
        (margin, height - margin - 2 * qr_size - spacing_y),  # Нижний левый
        (margin + qr_size + spacing_x, height - margin - 2 * qr_size - spacing_y)  # Нижний правый
    ]
    
    for i, room in enumerate(ROOM_NUMBERS):
        pos_index = i % 4
        
        # Новая страница каждые 4 номера
        if i > 0 and pos_index == 0:
            c.showPage()
        
        x, y = positions[pos_index]
        
        # Генерируем QR-код
        qr_img = generate_qr_code(room)
        
        # Сохраняем временно для добавления в PDF
        temp_file = f"/tmp/qr_{room}.png"
        with open(temp_file, 'wb') as f:
            f.write(qr_img.read())
        
        # Добавляем QR-код в PDF
        c.drawImage(temp_file, x, y, width=qr_size, height=qr_size)
        
        # Добавляем текст с номером комнаты
        c.setFont("Helvetica-Bold", 16)
        text_x = x + qr_size / 2
        text_y = y - 15 * mm
        c.drawCentredString(text_x, text_y, f"Номер {room}")
        
        # Добавляем инструкцию
        c.setFont("Helvetica", 10)
        c.drawCentredString(text_x, text_y - 8 * mm, "Отсканируйте для отзыва")
        
        # Удаляем временный файл
        os.remove(temp_file)
    
    c.save()
    buffer.seek(0)
    return buffer

@qr_router.message(Command("generate_qr"))
async def generate_qr_command(message: Message):
    """Команда для генерации QR-кодов"""
    user_id = message.from_user.id
    
    if user_id not in ADMIN_IDS:
        await message.answer("❌ Недостаточно прав")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📄 Все номера (PDF)", callback_data='qr_all_pdf')],
        [InlineKeyboardButton(text="🖼️ Один номер (PNG)", callback_data='qr_single')]
    ])
    
    await message.answer(
        "📱 <b>Генератор QR-кодов</b>\n\n"
        "Выберите вариант:",
        reply_markup=keyboard
    )

@qr_router.callback_query(F.data == 'qr_all_pdf')
async def generate_all_qr_pdf(callback: CallbackQuery):
    """Генерирует PDF со всеми QR-кодами"""
    await callback.answer()
    await callback.message.answer("🔄 Генерирую PDF с QR-кодами для всех номеров...")
    
    try:
        pdf_buffer = generate_qr_pdf_all_rooms()
        
        await callback.message.answer_document(
            document=BufferedInputFile(pdf_buffer.read(), filename="qr_codes_all_rooms.pdf"),
            caption=f"📄 QR-коды для всех номеров ({len(ROOM_NUMBERS)} шт.)\n\n"
                    "Распечатайте и разместите в номерах!"
        )
    except Exception as e:
        await callback.message.answer(f"❌ Ошибка генерации: {e}")
        import traceback
        traceback.print_exc()

@qr_router.callback_query(F.data == 'qr_single')
async def request_room_number(callback: CallbackQuery):
    """Запрашивает номер комнаты для генерации одного QR"""
    await callback.answer()
    await callback.message.answer(
        "🏨 Введите номер комнаты (например: 205):"
    )

@qr_router.message(F.text.regexp(r'^\d{3}$'))
async def generate_single_qr(message: Message):
    """Генерирует QR-код для одного номера"""
    user_id = message.from_user.id
    
    if user_id not in ADMIN_IDS:
        return
    
    room_number = message.text
    
    if room_number not in ROOM_NUMBERS:
        await message.answer(f"⚠️ Номер {room_number} не найден в списке")
        return
    
    try:
        qr_img = generate_qr_code(room_number)
        
        await message.answer_photo(
            photo=BufferedInputFile(qr_img.read(), filename=f"qr_{room_number}.png"),
            caption=f"📱 QR-код для номера {room_number}\n\n"
                    f"Ссылка: https://t.me/{BOT_USERNAME}?start=review_{room_number}"
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

# ==============================================================================
# ОБРАБОТКА DEEP LINK (start=review_205)
# ==============================================================================

@qr_router.message(Command("start"))
async def handle_start_with_room(message: Message):
    """Обрабатывает команду /start с параметром review_XXX"""
    args = message.text.split()
    
    if len(args) > 1 and args[1].startswith('review_'):
        room_number = args[1].replace('review_', '')
        
        # Начинаем процесс отзыва для этого номера
        # TODO: Интегрировать с reviews_handler.py
        await message.answer(
            f"🏨 Добро пожаловать в Pelican Alakol Hotel!\n\n"
            f"Вы отдыхали в номере {room_number}?\n\n"
            f"Пожалуйста, используйте команду /review чтобы оставить отзыв."
        )
    else:
        # Обычная команда /start
        await message.answer(
            "🏨 Добро пожаловать в Pelican Alakol Hotel!\n\n"
            "Доступные команды:\n"
            "/review - Оставить отзыв\n"
            "/help - Помощь"
        )
