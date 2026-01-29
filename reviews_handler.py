# ==============================================================================
# reviews_handler.py - Модуль для работы с отзывами (aiogram 3.x)
# Версия 2.1 - с улучшенной обработкой номеров комнат
# ==============================================================================

import os
import csv
import io
import aiosqlite
from datetime import datetime
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile

# Импорт из главного файла
DB_FILE = os.getenv('DB_FILE', 'orders.db')
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(","))) if os.getenv("ADMIN_IDS") else []
MANAGER_IDS = list(map(int, os.getenv("MANAGER_IDS", "").split(","))) if os.getenv("MANAGER_IDS") else []

# Импортируем отслеживание номеров из bot.py
try:
    from bot import user_room_tracking
except ImportError:
    user_room_tracking = {}

# Создаём роутер для отзывов
reviews_router = Router()

# ===================== СОСТОЯНИЯ FSM =====================

class ReviewStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_room = State()
    waiting_for_cleanliness = State()
    waiting_for_comfort = State()
    waiting_for_location = State()
    waiting_for_facilities = State()
    waiting_for_staff = State()
    waiting_for_value = State()
    waiting_for_pros = State()
    waiting_for_cons = State()
    waiting_for_comment = State()
    waiting_for_confirm = State()

# ===================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====================

def get_score_keyboard(criteria: str) -> InlineKeyboardMarkup:
    """Создаёт клавиатуру с оценками 1-10"""
    keyboard = []
    # По 5 кнопок в ряд
    for i in range(0, 10, 5):
        row = [
            InlineKeyboardButton(
                text=str(j), 
                callback_data=f'score_{criteria}_{j}'
            ) for j in range(i+1, min(i+6, 11))
        ]
        keyboard.append(row)
    
    keyboard.append([
        InlineKeyboardButton(text="❌ Отменить опрос", callback_data='review_cancel')
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_skip_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой пропуска"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭️ Пропустить", callback_data='review_skip')],
        [InlineKeyboardButton(text="❌ Отменить опрос", callback_data='review_cancel')]
    ])

async def notify_managers_new_review(bot, review_id: int, user_id: int, username: str, data: dict):
    """Уведомить менеджеров о новом отзыве"""
    avg_score = (
        data['cleanliness'] + data['comfort'] + data['location'] +
        data['facilities'] + data['staff'] + data['value']
    ) / 6
    
    room_info = data.get('room', 'не указан')
    scanned_info = f"\n📱 QR из номера: <b>{data.get('scanned_room')}</b>" if data.get('scanned_room') else ""
    
    text = f"""
🆕 <b>Новый отзыв #{review_id}</b>

👤 От: {data['guest_name']} (@{username or 'без username'})
🚪 Номер: {room_info}{scanned_info}
⭐ Средняя оценка: <b>{avg_score:.1f}/10</b>

Используйте /admin_reviews для модерации
"""
    
    for manager_id in ADMIN_IDS:
        try:
            await bot.send_message(chat_id=manager_id, text=text)
        except:
            pass

# ===================== КОМАНДА /review =====================

@reviews_router.message(Command("review"))
async def cmd_review(message: Message):
    """Команда /review - начать опрос"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ Начать опрос", callback_data='review_start')]
    ])
    
    await message.answer(
        "🏨 <b>Спасибо, что выбрали Пеликан Алаколь!</b>\n\n"
        "Мы будем очень благодарны за ваш отзыв.\n"
        "Опрос займет всего 2-3 минуты.\n\n"
        "✅ <i>Ваш отзыв поможет другим гостям и улучшит наш сервис</i>",
        reply_markup=keyboard
    )

@reviews_router.callback_query(F.data == "review_start")
async def start_review(callback: CallbackQuery, state: FSMContext):
    """Начало опроса"""
    await callback.answer()
    
    await callback.message.answer(
        "👤 <b>Шаг 1/12</b>\n\n"
        "Как вас зовут?\n"
        "<i>(это имя будет показано в отзыве)</i>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отменить", callback_data='review_cancel')]
        ])
    )
    
    await state.set_state(ReviewStates.waiting_for_name)

# ===================== СБОР ДАННЫХ =====================

@reviews_router.message(ReviewStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    """Обработка имени - ИСПРАВЛЕНО: проверяем scanned_room"""
    user_id = message.from_user.id
    await state.update_data(guest_name=message.text)
    
    # ✅ НОВАЯ ЛОГИКА: Проверяем есть ли scanned_room из QR-кода
    scanned_room = user_room_tracking.get(user_id)
    
    if scanned_room:
        # Если есть scanned_room - автоматически используем его и пропускаем вопрос
        await state.update_data(room=scanned_room)
        
        await message.answer(
            f"🚪 <b>Номер комнаты:</b> {scanned_room}\n"
            f"<i>(определён автоматически из QR-кода)</i>\n\n"
            "🧹 <b>Шаг 2/11 - Чистота</b>\n\n"
            "Оцените <b>чистоту</b> номера и территории\n\n"
            "1 = ужасно 😞 | 10 = превосходно 🌟",
            reply_markup=get_score_keyboard('cleanliness')
        )
        await state.set_state(ReviewStates.waiting_for_cleanliness)
    else:
        # Если нет scanned_room - спрашиваем (с возможностью пропустить)
        await message.answer(
            "🚪 <b>Шаг 2/12</b>\n\n"
            "В каком номере вы останавливались?\n\n"
            "<i>Вы можете указать номер или пропустить этот вопрос</i>",
            reply_markup=get_skip_keyboard()
        )
        await state.set_state(ReviewStates.waiting_for_room)

@reviews_router.message(ReviewStates.waiting_for_room)
async def process_room(message: Message, state: FSMContext):
    """Обработка номера комнаты (если пользователь ввёл вручную)"""
    await state.update_data(room=message.text)
    
    await message.answer(
        "🧹 <b>Шаг 3/12 - Чистота</b>\n\n"
        "Оцените <b>чистоту</b> номера и территории\n\n"
        "1 = ужасно 😞 | 10 = превосходно 🌟",
        reply_markup=get_score_keyboard('cleanliness')
    )
    await state.set_state(ReviewStates.waiting_for_cleanliness)

@reviews_router.callback_query(F.data == "review_skip", ReviewStates.waiting_for_room)
async def skip_room(callback: CallbackQuery, state: FSMContext):
    """Пропуск вопроса о номере комнаты"""
    await callback.answer()
    await state.update_data(room=None)  # Сохраняем NULL
    
    await callback.message.answer(
        "🧹 <b>Шаг 3/12 - Чистота</b>\n\n"
        "Оцените <b>чистоту</b> номера и территории\n\n"
        "1 = ужасно 😞 | 10 = превосходно 🌟",
        reply_markup=get_score_keyboard('cleanliness')
    )
    await state.set_state(ReviewStates.waiting_for_cleanliness)

# ===================== ОЦЕНКИ (без изменений) =====================

@reviews_router.callback_query(F.data.startswith('score_cleanliness_'))
async def process_cleanliness(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    score = int(callback.data.split('_')[2])
    await state.update_data(cleanliness=score)
    
    await callback.message.answer(
        "🛏️ <b>Шаг 4/12 - Комфорт</b>\n\n"
        "Оцените <b>комфорт</b> номера\n\n"
        "1 = ужасно 😞 | 10 = превосходно 🌟",
        reply_markup=get_score_keyboard('comfort')
    )
    await state.set_state(ReviewStates.waiting_for_comfort)

@reviews_router.callback_query(F.data.startswith('score_comfort_'))
async def process_comfort(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    score = int(callback.data.split('_')[2])
    await state.update_data(comfort=score)
    
    await callback.message.answer(
        "📍 <b>Шаг 5/12 - Расположение</b>\n\n"
        "Оцените <b>расположение</b> отеля\n\n"
        "1 = ужасно 😞 | 10 = превосходно 🌟",
        reply_markup=get_score_keyboard('location')
    )
    await state.set_state(ReviewStates.waiting_for_location)

@reviews_router.callback_query(F.data.startswith('score_location_'))
async def process_location(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    score = int(callback.data.split('_')[2])
    await state.update_data(location=score)
    
    await callback.message.answer(
        "🏊 <b>Шаг 6/12 - Удобства</b>\n\n"
        "Оцените <b>удобства</b> отеля\n\n"
        "1 = ужасно 😞 | 10 = превосходно 🌟",
        reply_markup=get_score_keyboard('facilities')
    )
    await state.set_state(ReviewStates.waiting_for_facilities)

@reviews_router.callback_query(F.data.startswith('score_facilities_'))
async def process_facilities(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    score = int(callback.data.split('_')[2])
    await state.update_data(facilities=score)
    
    await callback.message.answer(
        "👥 <b>Шаг 7/12 - Персонал</b>\n\n"
        "Оцените <b>персонал</b> отеля\n\n"
        "1 = ужасно 😞 | 10 = превосходно 🌟",
        reply_markup=get_score_keyboard('staff')
    )
    await state.set_state(ReviewStates.waiting_for_staff)

@reviews_router.callback_query(F.data.startswith('score_staff_'))
async def process_staff(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    score = int(callback.data.split('_')[2])
    await state.update_data(staff=score)
    
    await callback.message.answer(
        "💰 <b>Шаг 8/12 - Цена/Качество</b>\n\n"
        "Оцените <b>соотношение цены и качества</b>\n\n"
        "1 = ужасно 😞 | 10 = превосходно 🌟",
        reply_markup=get_score_keyboard('value')
    )
    await state.set_state(ReviewStates.waiting_for_value)

@reviews_router.callback_query(F.data.startswith('score_value_'))
async def process_value(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    score = int(callback.data.split('_')[2])
    await state.update_data(value=score)
    
    await callback.message.answer(
        "✅ <b>Шаг 9/12 - Что понравилось</b>\n\n"
        "Напишите, что вам <b>понравилось больше всего</b>?\n\n"
        "<i>Или нажмите 'Пропустить'</i>",
        reply_markup=get_skip_keyboard()
    )
    await state.set_state(ReviewStates.waiting_for_pros)

# ===================== ТЕКСТОВЫЕ ОТЗЫВЫ =====================

@reviews_router.message(ReviewStates.waiting_for_pros)
async def process_pros(message: Message, state: FSMContext):
    await state.update_data(pros=message.text)
    
    await message.answer(
        "❌ <b>Шаг 10/12 - Что улучшить</b>\n\n"
        "Что мы можем <b>улучшить</b>?\n\n"
        "<i>Или нажмите 'Пропустить'</i>",
        reply_markup=get_skip_keyboard()
    )
    await state.set_state(ReviewStates.waiting_for_cons)

@reviews_router.callback_query(F.data == "review_skip", ReviewStates.waiting_for_pros)
async def skip_pros(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(pros=None)
    
    await callback.message.answer(
        "❌ <b>Шаг 10/12 - Что улучшить</b>\n\n"
        "Что мы можем <b>улучшить</b>?\n\n"
        "<i>Или нажмите 'Пропустить'</i>",
        reply_markup=get_skip_keyboard()
    )
    await state.set_state(ReviewStates.waiting_for_cons)

@reviews_router.message(ReviewStates.waiting_for_cons)
async def process_cons(message: Message, state: FSMContext):
    await state.update_data(cons=message.text)
    
    await message.answer(
        "💬 <b>Шаг 11/12 - Общий комментарий</b>\n\n"
        "Расскажите об общих впечатлениях от отдыха\n\n"
        "<i>Или нажмите 'Пропустить'</i>",
        reply_markup=get_skip_keyboard()
    )
    await state.set_state(ReviewStates.waiting_for_comment)

@reviews_router.callback_query(F.data == "review_skip", ReviewStates.waiting_for_cons)
async def skip_cons(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(cons=None)
    
    await callback.message.answer(
        "💬 <b>Шаг 11/12 - Общий комментарий</b>\n\n"
        "Расскажите об общих впечатлениях\n\n"
        "<i>Или нажмите 'Пропустить'</i>",
        reply_markup=get_skip_keyboard()
    )
    await state.set_state(ReviewStates.waiting_for_comment)

@reviews_router.message(ReviewStates.waiting_for_comment)
async def process_comment(message: Message, state: FSMContext):
    await state.update_data(comment=message.text)
    await show_confirmation(message, state)

@reviews_router.callback_query(F.data == "review_skip", ReviewStates.waiting_for_comment)
async def skip_comment(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(comment=None)
    await show_confirmation(callback.message, state)

# ===================== ПОДТВЕРЖДЕНИЕ И СОХРАНЕНИЕ =====================

async def show_confirmation(message: Message, state: FSMContext):
    """Показать подтверждение - ИСПРАВЛЕНО: обработка NULL номера"""
    data = await state.get_data()
    
    avg_score = (
        data['cleanliness'] + data['comfort'] + data['location'] +
        data['facilities'] + data['staff'] + data['value']
    ) / 6
    
    # ✅ Обработка номера комнаты (может быть None)
    room_display = data.get('room') or '<i>не указан</i>'
    
    text = f"""
📝 <b>Шаг 12/12 - Проверьте ваш отзыв</b>

👤 <b>Имя:</b> {data['guest_name']}
🚪 <b>Номер:</b> {room_display}

⭐ <b>Оценки:</b>
🧹 Чистота: {data['cleanliness']}/10
🛏️ Комфорт: {data['comfort']}/10
📍 Расположение: {data['location']}/10
🏊 Удобства: {data['facilities']}/10
👥 Персонал: {data['staff']}/10
💰 Цена/качество: {data['value']}/10

📊 <b>Средняя оценка: {avg_score:.1f}/10</b>

✅ <b>Понравилось:</b> {data.get('pros') or 'не указано'}
❌ <b>Улучшить:</b> {data.get('cons') or 'не указано'}
💬 <b>Комментарий:</b> {data.get('comment') or 'не указано'}
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Отправить отзыв", callback_data='review_submit')],
        [InlineKeyboardButton(text="❌ Отменить", callback_data='review_cancel')]
    ])
    
    await message.answer(text, reply_markup=keyboard)
    await state.set_state(ReviewStates.waiting_for_confirm)

@reviews_router.callback_query(F.data == "review_submit")
async def submit_review(callback: CallbackQuery, state: FSMContext):
    """Сохранение отзыва - ИСПРАВЛЕНО: добавлено сохранение данных для уведомления"""
    await callback.answer()
    
    data = await state.get_data()
    user = callback.from_user
    
    try:
        async with aiosqlite.connect(DB_FILE) as db:
            # Получаем номер из QR-кода если есть
            scanned_room = user_room_tracking.get(user.id)
            
            cursor = await db.execute("""
                INSERT INTO reviews (
                    telegram_user_id, telegram_username, guest_name, room_number,
                    cleanliness, comfort, location, facilities, staff, value_for_money,
                    pros, cons, comment, display_name, scanned_room_number
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user.id, user.username, data['guest_name'], data.get('room'),
                data['cleanliness'], data['comfort'], data['location'],
                data['facilities'], data['staff'], data['value'],
                data.get('pros'), data.get('cons'), data.get('comment'),
                data['guest_name'], scanned_room
            ))
            
            review_id = cursor.lastrowid
            await db.commit()
        
        # ✅ Добавляем scanned_room в data для уведомления
        data['scanned_room'] = scanned_room
        
        # Уведомляем менеджеров
        await notify_managers_new_review(callback.bot, review_id, user.id, user.username, data)
        
        await callback.message.answer(
            "✅ <b>Спасибо за ваш отзыв!</b>\n\n"
            f"Отзыв #{review_id} принят и будет проверен менеджером.\n"
            "После проверки он появится на нашем сайте.\n\n"
            "🙏 Мы ценим ваше мнение!"
        )
        
        await state.clear()
        
    except Exception as e:
        await callback.message.answer(
            "❌ Произошла ошибка при сохранении отзыва.\n"
            "Пожалуйста, попробуйте позже."
        )
        print(f"Ошибка сохранения отзыва: {e}")

# ===================== ОТМЕНА ОПРОСА =====================

@reviews_router.callback_query(F.data == "review_cancel")
async def cancel_review(callback: CallbackQuery, state: FSMContext):
    """Отмена опроса"""
    await callback.answer()
    await state.clear()
    
    await callback.message.answer(
        "❌ Отзыв отменен.\n\n"
        "Вы можете начать заново командой /review"
    )

# ===================== АДМИН-ПАНЕЛЬ (без изменений - оставляем как есть) =====================
# ... (весь остальной код админки остаётся без изменений)
