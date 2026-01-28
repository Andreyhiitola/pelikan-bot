# ==============================================================================
# qr_generator.py - Генератор QR-кодов для номеров с логотипом
# ==============================================================================

import os
import qrcode
from io import BytesIO
from PIL import Image, ImageDraw
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(","))) if os.getenv("ADMIN_IDS") else []
BOT_USERNAME = "Pelican_alacol_hotel_bot"

qr_router = Router()

# РЕАЛЬНЫЕ номера из вашей таблицы
ROOM_NUMBERS = [
    # Бунгало 1 (1+1+1) местный: 401-409
    '401', '402', '403', '404', '405', '406', '407', '408', '409',
    # Бунгало-2 (2+1) местный: 401-407, 501-503
    '2-401', '2-402', '2-403', '2-404', '2-405', '2-406', '2-407',
    '2-501', '2-502', '2-503',
    # Бунгало-семейный 6 местный: 1-4
    'Сем-1', 'Сем-2', 'Сем-3', 'Сем-4',
    # Бунгало-люкс семейный 2 местный: 1-4
    'Люкс-Сем-1', 'Люкс-Сем-2', 'Люкс-Сем-3', 'Люкс-Сем-4',
    # Бунгало-стандарт 4 (2+2) местный: 101-711
    '101', '102', '103', '104', '105', '106', '201', '202', '203', '204',
    '205', '206', '301', '302', '303', '304', '305', '306', '307', '308',
    '309', '310', '601', '602', '603', '604', '605', '606', '607', '608',
    '609', '610', '711',
    # Коттедж Люкс: 1
    'Кот-Люкс-1',
    # Коттедж 4 местный: 1-4
    'Кот-4М-1', 'Кот-4М-2', 'Кот-4М-3', 'Кот-4М-4',
    # Коттедж-стандарт 2 местный: 11-16
    'Кот-2М-11', 'Кот-2М-12', 'Кот-2М-13', 'Кот-2М-14', 'Кот-2М-15', 'Кот-2М-16',
    # Стандарт-новый 2+2+1: 1-6
    'Стд-Нов-1', 'Стд-Нов-2', 'Стд-Нов-3', 'Стд-Нов-4', 'Стд-Нов-5', 'Стд-Нов-6',
    # Стандарт 4 местный: 5-8
    'Стд-4М-5', 'Стд-4М-6', 'Стд-4М-7', 'Стд-4М-8',
    # Стандарт-люкс 2 местный: КО41-КО43
    'СтдЛюкс-КО41', 'СтдЛюкс-КО42', 'СтдЛюкс-КО43',
    # Стандарт-люкс 2 местный + завтраки: КО11-КО13
    'СтдЛюксЗав-КО11', 'СтдЛюксЗав-КО12', 'СтдЛюксЗав-КО13',
    # Стандарт-семейный: 1-6
    'СтдСем-1', 'СтдСем-2', 'СтдСем-3', 'СтдСем-4', 'СтдСем-5', 'СтдСем-6',
    # Комнаты в коттедже: 1-8
    'КомКот-1', 'КомКот-2', 'КомКот-3', 'КомКот-4', 'КомКот-5', 'КомКот-6', 'КомКот-7', 'КомКот-8',
    # Комната с завтраком: 1-4
    'КомЗав-1', 'КомЗав-2', 'КомЗав-3', 'КомЗав-4',
    # Жасмин Эконом: 1-5
    'Жасм-Экон-1', 'Жасм-Экон-2', 'Жасм-Экон-3', 'Жасм-Экон-4', 'Жасм-Экон-5',
    # Жасмин Стандарт: 1-6
    'Жасм-Стд-1', 'Жасм-Стд-2', 'Жасм-Стд-3', 'Жасм-Стд-4', 'Жасм-Стд-5', 'Жасм-Стд-6',
]

# Путь к логотипу (должен быть в контейнере)
LOGO_PATH = "/app/logo.png"

def generate_qr_code(room_number: str) -> BytesIO:
    """Генерирует QR-код для конкретного номера с логотипом в центре"""
    deep_link = f"https://t.me/{BOT_USERNAME}?start=review_{room_number}"
    
    # Создаем QR-код
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(deep_link)
    qr.make(fit=True)
    
    qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
    
    # Размеры QR-кода
    qr_width, qr_height = qr_img.size
    
    # Вставляем логотип если он есть
    if os.path.exists(LOGO_PATH):
        try:
            logo = Image.open(LOGO_PATH)
            
            # Создаем круглый белый фон для логотипа
            logo_size = qr_width // 4
            background = Image.new('RGB', (logo_size, logo_size), 'white')
            draw = ImageDraw.Draw(background)
            
            # Рисуем белый круг
            draw.ellipse([0, 0, logo_size, logo_size], fill='white', outline='#CC7722', width=4)
            
            # Изменяем размер логотипа (чуть меньше круга)
            logo_resized = logo.resize((int(logo_size * 0.65), int(logo_size * 0.65)), Image.Resampling.LANCZOS)
            
            # Центрируем логотип на белом круге
            logo_x = (logo_size - logo_resized.width) // 2
            logo_y = (logo_size - logo_resized.height) // 2
            
            # Если у логотипа есть прозрачность, используем её как маску
            if logo_resized.mode == 'RGBA':
                background.paste(logo_resized, (logo_x, logo_y), logo_resized)
            else:
                background.paste(logo_resized, (logo_x, logo_y))
            
            # Вставляем логотип в центр QR-кода
            logo_pos = ((qr_width - logo_size) // 2, (qr_height - logo_size) // 2)
            qr_img.paste(background, logo_pos)
        except Exception as e:
            print(f"Ошибка при добавлении логотипа: {e}")
    
    # Сохраняем в BytesIO
    buf = BytesIO()
    qr_img.save(buf, format='PNG')
    buf.seek(0)
    
    return buf

def generate_qr_pdf_all_rooms() -> BytesIO:
    """Генерирует PDF с QR-кодами для всех номеров (4 на страницу)"""
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Регистрируем шрифт для кириллицы
    font_registered = False
    try:
        pdfmetrics.registerFont(TTFont('DejaVuSans', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
        pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
        font_name = 'DejaVuSans-Bold'
        font_regular = 'DejaVuSans'
        font_registered = True
    except Exception as e:
        print(f"Ошибка загрузки шрифта DejaVu: {e}")
        font_name = 'Helvetica-Bold'
        font_regular = 'Helvetica'
    
    qr_size = 65 * mm
    margin = 15 * mm
    spacing_x = (width - 2 * margin - 2 * qr_size) / 1
    spacing_y = (height - 2 * margin - 2 * qr_size) / 1
    
    positions = [
        (margin, height - margin - qr_size),
        (margin + qr_size + spacing_x, height - margin - qr_size),
        (margin, height - margin - 2 * qr_size - spacing_y),
        (margin + qr_size + spacing_x, height - margin - 2 * qr_size - spacing_y)
    ]
    
    for i, room in enumerate(ROOM_NUMBERS):
        pos_index = i % 4
        
        if i > 0 and pos_index == 0:
            c.showPage()
        
        x, y = positions[pos_index]
        
        # Рисуем фоновую рамку с фирменным цветом
        c.setStrokeColorRGB(0.8, 0.47, 0.13)  # Оранжевый #CC7722
        c.setLineWidth(2)
        c.rect(x - 3, y - 3, qr_size + 6, qr_size + 6, stroke=1, fill=0)
        
        # Добавляем QR-код
        qr_img = generate_qr_code(room)
        temp_file = f"/tmp/qr_{room.replace('/', '_')}.png"
        with open(temp_file, 'wb') as f:
            f.write(qr_img.read())
        
        c.drawImage(temp_file, x, y, width=qr_size, height=qr_size)
        
        # Заголовок номера
        c.setFont(font_name, 16)
        c.setFillColorRGB(0.8, 0.47, 0.13)
        text_x = x + qr_size / 2
        text_y = y - 10 * mm
        
        if font_registered:
            c.drawCentredString(text_x, text_y, f"Номер {room}")
        else:
            c.drawCentredString(text_x, text_y, f"Room {room}")
        
        # Подзаголовок
        c.setFont(font_regular, 10)
        c.setFillColorRGB(0.3, 0.3, 0.3)
        if font_registered:
            c.drawCentredString(text_x, text_y - 5 * mm, "Сканируйте для отзыва")
        else:
            c.drawCentredString(text_x, text_y - 5 * mm, "Scan for review")
        
        # Название отеля внизу
        c.setFont(font_name, 8)
        c.setFillColorRGB(0.8, 0.47, 0.13)
        if font_registered:
            c.drawCentredString(text_x, text_y - 10 * mm, "ПАРК ОТЕЛЬ ПЕЛИКАН")
        else:
            c.drawCentredString(text_x, text_y - 10 * mm, "PARK HOTEL PELICAN")
        
        try:
            os.remove(temp_file)
        except:
            pass
    
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
        f"✨ Всего номеров: {len(ROOM_NUMBERS)}\n"
        "🎨 С фирменным логотипом PELICAN\n\n"
        "Выберите вариант:",
        reply_markup=keyboard
    )

@qr_router.callback_query(F.data == 'qr_all_pdf')
async def generate_all_qr_pdf(callback: CallbackQuery):
    """Генерирует PDF со всеми QR-кодами"""
    await callback.answer()
    await callback.message.answer(f"🔄 Генерирую PDF с QR-кодами для {len(ROOM_NUMBERS)} номеров...")
    
    try:
        pdf_buffer = generate_qr_pdf_all_rooms()
        
        await callback.message.answer_document(
            document=BufferedInputFile(pdf_buffer.read(), filename="pelican_qr_all_rooms.pdf"),
            caption=f"📄 <b>QR-коды PELICAN ALAKOL</b>\n\n"
                    f"✅ Готово: {len(ROOM_NUMBERS)} номеров\n"
                    f"🎨 Логотип в центре каждого QR-кода\n"
                    f"📍 Распечатайте и разместите в номерах!"
        )
    except Exception as e:
        await callback.message.answer(f"❌ Ошибка генерации: {e}")
        import traceback
        traceback.print_exc()

@qr_router.callback_query(F.data == 'qr_single')
async def request_room_number(callback: CallbackQuery):
    """Запрашивает номер комнаты"""
    await callback.answer()
    
    # Группируем номера для удобного отображения
    room_info = (
        "🏨 <b>Введите номер комнаты</b>\n\n"
        "<b>Примеры номеров:</b>\n"
        "• Бунгало: 401-409\n"
        "• Бунгало-2: 2-401, 2-501\n"
        "• Стандарт: 101, 201, 301\n"
        "• Коттедж: Кот-4М-1\n"
        "• Жасмин: Жасм-Стд-1\n\n"
        "Или напишите мне любой номер из списка"
    )
    
    await callback.message.answer(room_info)

@qr_router.message(F.text)
async def generate_single_qr(message: Message):
    """Генерирует QR-код для одного номера"""
    user_id = message.from_user.id
    
    # Проверяем админа
    if user_id not in ADMIN_IDS:
        return
    
    room_number = message.text.strip()
    
    # Проверяем наличие номера
    if room_number not in ROOM_NUMBERS:
        # Пробуем найти похожий
        similar = [r for r in ROOM_NUMBERS if room_number.lower() in r.lower()]
        if similar:
            await message.answer(
                f"❌ Номер '{room_number}' не найден\n\n"
                f"Возможно вы имели в виду:\n" + "\n".join(f"• {r}" for r in similar[:5])
            )
        else:
            await message.answer(f"❌ Номер '{room_number}' не найден в базе")
        return
    
    try:
        qr_buffer = generate_qr_code(room_number)
        
        await message.answer_photo(
            photo=BufferedInputFile(qr_buffer.read(), filename=f"qr_{room_number}.png"),
            caption=f"🏨 <b>QR-код для номера {room_number}</b>\n\n"
                    f"✨ С логотипом PELICAN ALAKOL\n"
                    f"📱 Отсканируйте для отзыва"
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
