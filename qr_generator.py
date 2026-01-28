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
    # Бунгало (1+1+1): 501-510
    'Бунгало (1+1+1) 501', 'Бунгало (1+1+1) 502', 'Бунгало (1+1+1) 503',
    'Бунгало (1+1+1) 504', 'Бунгало (1+1+1) 505', 'Бунгало (1+1+1) 506',
    'Бунгало (1+1+1) 507', 'Бунгало (1+1+1) 508', 'Бунгало (1+1+1) 509', 'Бунгало (1+1+1) 510',
    
    # Бунгало (2+1): 401-804
    'Бунгало (2+1) 401', 'Бунгало (2+1) 402', 'Бунгало (2+1) 403', 'Бунгало (2+1) 404',
    'Бунгало (2+1) 405', 'Бунгало (2+1) 406', 'Бунгало (2+1) 407', 'Бунгало (2+1) 408',
    'Бунгало (2+1) 601', 'Бунгало (2+1) 602', 'Бунгало (2+1) 603', 'Бунгало (2+1) 604',
    'Бунгало (2+1) 605', 'Бунгало (2+1) 606', 'Бунгало (2+1) 607', 'Бунгало (2+1) 608',
    'Бунгало (2+1) 701', 'Бунгало (2+1) 702', 'Бунгало (2+1) 703', 'Бунгало (2+1) 704',
    'Бунгало (2+1) 705', 'Бунгало (2+1) 706', 'Бунгало (2+1) 707',
    'Бунгало (2+1) 801', 'Бунгало (2+1) 802', 'Бунгало (2+1) 803', 'Бунгало (2+1) 804',
    
    # Бунгало-сем 6в.: 1-4
    'Бунгало-сем 6в. 1', 'Бунгало-сем 6в. 2', 'Бунгало-сем 6в. 3', 'Бунгало-сем 6в. 4',
    
    # Бунгало-улуч 3в.: 1-6
    'Бунгало-улуч 3в. 1', 'Бунгало-улуч 3в. 2', 'Бунгало-улуч 3в. 3',
    'Бунгало-улуч 3в. 4', 'Бунгало-улуч 3в. 5', 'Бунгало-улуч 3в. 6',
    
    # Бунгало (2+2): 101-912
    'Бунгало (2+2) 101', 'Бунгало (2+2) 102', 'Бунгало (2+2) 103',
    'Бунгало (2+2) 104', 'Бунгало (2+2) 105', 'Бунгало (2+2) 106',
    'Бунгало (2+2) 201', 'Бунгало (2+2) 203', 'Бунгало (2+2) 204',
    'Бунгало (2+2) 205', 'Бунгало (2+2) 206', 'Бунгало (2+2) 207',
    'Бунгало (2+2) 301', 'Бунгало (2+2) 302', 'Бунгало (2+2) 303',
    'Бунгало (2+2) 304', 'Бунгало (2+2) 305', 'Бунгало (2+2) 306',
    'Бунгало (2+2) 901', 'Бунгало (2+2) 902', 'Бунгало (2+2) 903',
    'Бунгало (2+2) 904', 'Бунгало (2+2) 905', 'Бунгало (2+2) 906',
    'Бунгало (2+2) 907', 'Бунгало (2+2) 908', 'Бунгало (2+2) 909',
    'Бунгало (2+2) 910', 'Бунгало (2+2) 911', 'Бунгало (2+2) 912',
    
    # Коттедж-Роза 7в.: 1
    'Коттедж-Роза 7в. 1',
    
    # Коттедж 6в.: 1, 3, 4
    'Коттедж 6в. 1', 'Коттедж 6в. 3', 'Коттедж 6в. 4',
    
    # Люкс 2в.: 3, 4
    'Люкс 2в. 3', 'Люкс 2в. 4',
    
    # Люкс-бунгало 2в.: 1
    'Люкс-бунгало 2в. 1',
    
    # Люкс-Роза 2в.: 1, 2
    'Люкс-Роза 2в. 1', 'Люкс-Роза 2в. 2',
    
    # Стандарт 2в.: 11-16
    'Стандарт 2в. 11', 'Стандарт 2в. 12', 'Стандарт 2в. 13',
    'Стандарт 2в. 14', 'Стандарт 2в. 15', 'Стандарт 2в. 16',
    
    # Стандарт (2+1): 1, 3, 4, 9, 10
    'Стандарт (2+1) 1', 'Стандарт (2+1) 3', 'Стандарт (2+1) 4',
    'Стандарт (2+1) 9', 'Стандарт (2+1) 10',
    
    # Стандарт 4в.: 5-8
    'Стандарт 4в. 5', 'Стандарт 4в. 6', 'Стандарт 4в. 7', 'Стандарт 4в. 8',
    
    # Стандарт Junior 4в.: Юн1-Юн7
    'Стандарт Junior 4в. Юн1', 'Стандарт Junior 4в. Юн2', 'Стандарт Junior 4в. Юн3',
    'Стандарт Junior 4в. Юн4', 'Стандарт Junior 4в. Юн5', 'Стандарт Junior 4в. Юн6',
    'Стандарт Junior 4в. Юн7',
    
    # Ст.Jun 4в.+веранда: Юн8-Юн14
    'Ст.Jun 4в.+веранда Юн8', 'Ст.Jun 4в.+веранда Юн9', 'Ст.Jun 4в.+веранда Юн10',
    'Ст.Jun 4в.+веранда Юн11', 'Ст.Jun 4в.+веранда Юн12', 'Ст.Jun 4в.+веранда Юн13',
    'Ст.Jun 4в.+веранда Юн14',
    
    # Стандарт-сем 5в.: 1-6
    'Стандарт-сем 5в. 1', 'Стандарт-сем 5в. 2', 'Стандарт-сем 5в. 3',
    'Стандарт-сем 5в. 4', 'Стандарт-сем 5в. 5', 'Стандарт-сем 5в. 6',
    
    # Стандарт-сем 5в. 2санузла: 1, 2
    'Ст-сем 5в. 2с/у 1', 'Ст-сем 5в. 2с/у 2',
    
    # Стандарт-улуч 4в.: 1-4
    'Стандарт-улуч 4в. 1', 'Стандарт-улуч 4в. 2', 'Стандарт-улуч 4в. 3', 'Стандарт-улуч 4в. 4',
    
    # Эконом-коннект 5в.: 1-7
    'Эконом-коннект 5в. 1', 'Эконом-коннект 5в. 2', 'Эконом-коннект 5в. 3',
    'Эконом-коннект 5в. 4', 'Эконом-коннект 5в. 5', 'Эконом-коннект 5в. 6', 'Эконом-коннект 5в. 7',
    
    # Эконом-сем 6в.: 1-4
    'Эконом-сем 6в. 1', 'Эконом-сем 6в. 2', 'Эконом-сем 6в. 3', 'Эконом-сем 6в. 4',
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
            c.drawCentredString(text_x, text_y - 5 * mm, "")
        else:
            c.drawCentredString(text_x, text_y - 5 * mm, "")
        
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
