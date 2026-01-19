# ==============================================================================
# reviews_handler.py - Модуль для работы с отзывами (aiogram 3.x)
# Версия 2.0 - с улучшенной админ-панелью
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
    
    text = f"""
🆕 <b>Новый отзыв #{review_id}</b>

👤 От: {data['guest_name']} (@{username or 'без username'})
🚪 Номер: {data['room']}
⭐ Средняя оценка: <b>{avg_score:.1f}/10</b>

Используйте /admin_reviews для модерации
"""
    
    for manager_id in  ADMIN_IDS:
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
    await state.update_data(guest_name=message.text)
    
    await message.answer(
        "🚪 <b>Шаг 2/12</b>\n\n"
        "В каком номере вы останавливались?",
        reply_markup=get_skip_keyboard()
    )
    await state.set_state(ReviewStates.waiting_for_room)

@reviews_router.message(ReviewStates.waiting_for_room)
async def process_room(message: Message, state: FSMContext):
    await state.update_data(room=message.text)
    
    await message.answer(
        "🧹 <b>Шаг 3/12 - Чистота</b>\n\n"
        "Оцените <b>чистоту</b> номера и территории\n\n"
        "1 = ужасно 😞 | 10 = превосходно 🌟",
        reply_markup=get_score_keyboard('cleanliness')
    )
    await state.set_state(ReviewStates.waiting_for_cleanliness)

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

async def show_confirmation(message: Message, state: FSMContext):
    """Показать подтверждение"""
    data = await state.get_data()
    
    avg_score = (
        data['cleanliness'] + data['comfort'] + data['location'] +
        data['facilities'] + data['staff'] + data['value']
    ) / 6
    
    text = f"""
📝 <b>Шаг 12/12 - Проверьте ваш отзыв</b>

👤 <b>Имя:</b> {data['guest_name']}
🚪 <b>Номер:</b> {data['room']}

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

# ===================== СОХРАНЕНИЕ ОТЗЫВА =====================

@reviews_router.callback_query(F.data == "review_submit")
async def submit_review(callback: CallbackQuery, state: FSMContext):
    """Сохранение отзыва"""
    await callback.answer()
    
    data = await state.get_data()
    user = callback.from_user
    
    try:
        async with aiosqlite.connect(DB_FILE) as db:
            cursor = await db.execute("""
                INSERT INTO reviews (
                    telegram_user_id, telegram_username, guest_name, room_number,
                    cleanliness, comfort, location, facilities, staff, value_for_money,
                    pros, cons, comment, display_name
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user.id, user.username, data['guest_name'], data['room'],
                data['cleanliness'], data['comfort'], data['location'],
                data['facilities'], data['staff'], data['value'],
                data.get('pros'), data.get('cons'), data.get('comment'),
                data['guest_name']
            ))
            
            review_id = cursor.lastrowid
            await db.commit()
        
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

# ===================== АДМИН-ПАНЕЛЬ: МОДЕРАЦИЯ =====================

@reviews_router.message(Command("admin_reviews"))
async def admin_reviews(message: Message):
    """Список отзывов на модерации"""
    user_id = message.from_user.id
    
    if user_id not in  ADMIN_IDS:
        await message.answer("❌ Недостаточно прав")
        return
    
    async with aiosqlite.connect(DB_FILE) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT id, guest_name, room_number, created_at,
                   ROUND((cleanliness + comfort + location + facilities + staff + value_for_money) / 6.0, 1) as avg_score
            FROM reviews
            WHERE status = 'pending'
            ORDER BY created_at DESC
            LIMIT 20
        """)
        
        pending = await cursor.fetchall()
    
    if not pending:
        await message.answer("✅ Нет отзывов на модерации")
        return
    
    keyboard = []
    for review in pending:
        date = datetime.fromisoformat(review['created_at']).strftime('%d.%m.%Y')
        keyboard.append([
            InlineKeyboardButton(
                text=f"⭐{review['avg_score']} - {review['guest_name']} ({date})",
                callback_data=f'mod_review_{review["id"]}'
            )
        ])
    
    await message.answer(
        f"📝 <b>Отзывы на модерации ({len(pending)}):</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )

@reviews_router.callback_query(F.data.startswith('mod_review_'))
async def moderate_review(callback: CallbackQuery):
    """Показать полный отзыв для модерации"""
    await callback.answer()
    
    review_id = int(callback.data.split('_')[2])
    
    async with aiosqlite.connect(DB_FILE) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM reviews WHERE id = ?", (review_id,))
        review = await cursor.fetchone()
    
    if not review:
        await callback.message.answer("❌ Отзыв не найден")
        return
    
    avg_score = (
        review['cleanliness'] + review['comfort'] + review['location'] +
        review['facilities'] + review['staff'] + review['value_for_money']
    ) / 6
    
    text = f"""
📝 <b>Отзыв #{review['id']}</b>
👤 {review['guest_name']} (комната {review['room_number']})
📅 {datetime.fromisoformat(review['created_at']).strftime('%d.%m.%Y %H:%M')}

⭐ <b>Оценки:</b>
🧹 Чистота: {review['cleanliness']}/10
🛏️ Комфорт: {review['comfort']}/10
📍 Расположение: {review['location']}/10
🏊 Удобства: {review['facilities']}/10
👥 Персонал: {review['staff']}/10
💰 Цена/качество: {review['value_for_money']}/10

📊 <b>Средняя: {avg_score:.1f}/10</b>

✅ <b>Понравилось:</b>
{review['pros'] or 'не указано'}

❌ <b>Улучшить:</b>
{review['cons'] or 'не указано'}

💬 <b>Комментарий:</b>
{review['comment'] or 'не указано'}
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Одобрить и опубликовать", callback_data=f'approve_pub_{review_id}')],
        [InlineKeyboardButton(text="📝 Одобрить без публикации", callback_data=f'approve_nopub_{review_id}')],
        [InlineKeyboardButton(text="❌ Отклонить", callback_data=f'reject_{review_id}')],
        [InlineKeyboardButton(text="🗑️ Удалить", callback_data=f'delete_{review_id}')],
        [InlineKeyboardButton(text="🔙 Назад", callback_data='back_to_moderation')]
    ])
    
    await callback.message.answer(text, reply_markup=keyboard)

@reviews_router.callback_query(F.data.startswith('approve_pub_'))
async def approve_and_publish(callback: CallbackQuery):
    """Одобрить и опубликовать отзыв"""
    await callback.answer("✅ Одобрен и опубликован")
    
    review_id = int(callback.data.split('_')[2])
    moderator_id = callback.from_user.id
    
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("""
            UPDATE reviews
            SET status = 'approved',
                is_published = 1,
                moderated_at = datetime('now'),
                moderated_by = ?
            WHERE id = ?
        """, (moderator_id, review_id))
        
        await db.commit()
    
    await callback.message.answer(f"✅ Отзыв #{review_id} одобрен и опубликован на сайте!")

@reviews_router.callback_query(F.data.startswith('approve_nopub_'))
async def approve_without_publish(callback: CallbackQuery):
    """Одобрить без публикации"""
    await callback.answer("📝 Одобрен, не опубликован")
    
    review_id = int(callback.data.split('_')[2])
    moderator_id = callback.from_user.id
    
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("""
            UPDATE reviews
            SET status = 'approved',
                is_published = 0,
                moderated_at = datetime('now'),
                moderated_by = ?
            WHERE id = ?
        """, (moderator_id, review_id))
        
        await db.commit()
    
    await callback.message.answer(
        f"📝 Отзыв #{review_id} одобрен, но не опубликован.\n"
        "Используйте /all_reviews для публикации позже."
    )

@reviews_router.callback_query(F.data.startswith('reject_'))
async def reject_review(callback: CallbackQuery):
    """Отклонить отзыв"""
    await callback.answer("❌ Отклонён")
    
    review_id = int(callback.data.split('_')[1])
    moderator_id = callback.from_user.id
    
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("""
            UPDATE reviews
            SET status = 'rejected',
                is_published = 0,
                moderated_at = datetime('now'),
                moderated_by = ?
            WHERE id = ?
        """, (moderator_id, review_id))
        
        await db.commit()
    
    await callback.message.answer(f"❌ Отзыв #{review_id} отклонен")

@reviews_router.callback_query(F.data.startswith('delete_'))
async def delete_review(callback: CallbackQuery):
    """Удалить отзыв из БД"""
    review_id = int(callback.data.split('_')[1])
    user_id = callback.from_user.id
    
    # Только админы могут удалять
    if user_id not in ADMIN_IDS:
        await callback.answer("❌ Недостаточно прав", show_alert=True)
        return
    
    await callback.answer("🗑️ Удалён")
    
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("DELETE FROM reviews WHERE id = ?", (review_id,))
        await db.commit()
    
    await callback.message.answer(f"🗑️ Отзыв #{review_id} удален из базы данных")

@reviews_router.callback_query(F.data == 'back_to_moderation')
async def back_to_moderation(callback: CallbackQuery):
    """Вернуться к списку отзывов на модерации"""
    await callback.answer()
    
    # Создаём fake Message для повторного вызова admin_reviews
    class FakeMessage:
        def __init__(self, from_user, chat):
            self.from_user = from_user
            self.chat = chat
    
        async def answer(self, text, **kwargs):
            await callback.message.answer(text, **kwargs)
    
    fake = FakeMessage(callback.from_user, callback.message.chat)
    await admin_reviews(fake)

# ===================== АДМИН-ПАНЕЛЬ: УПРАВЛЕНИЕ ВСЕМИ ОТЗЫВАМИ =====================

@reviews_router.message(Command("all_reviews"))
async def all_reviews_menu(message: Message):
    """Главное меню управления отзывами"""
    user_id = message.from_user.id
    
    if user_id not in ADMIN_IDS:
        await message.answer("❌ Недостаточно прав")
        return
    
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute("SELECT COUNT(*) as cnt FROM reviews")
        total = (await cursor.fetchone())[0]
        
        cursor = await db.execute("SELECT COUNT(*) as cnt FROM reviews WHERE status = 'pending'")
        pending = (await cursor.fetchone())[0]
        
        cursor = await db.execute("SELECT COUNT(*) as cnt FROM reviews WHERE status = 'approved' AND is_published = 1")
        published = (await cursor.fetchone())[0]
        
        cursor = await db.execute("SELECT COUNT(*) as cnt FROM reviews WHERE status = 'approved' AND is_published = 0")
        approved_not_published = (await cursor.fetchone())[0]
        
        cursor = await db.execute("SELECT COUNT(*) as cnt FROM reviews WHERE status = 'rejected'")
        rejected = (await cursor.fetchone())[0]
    
    text = f"""
📊 <b>Управление всеми отзывами</b>

📈 Статистика:
📝 Всего отзывов: {total}
⏳ На модерации: {pending}
✅ Опубликовано: {published}
📝 Одобрено (не опубл.): {approved_not_published}
❌ Отклонено: {rejected}
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Все отзывы", callback_data='filter_all')],
        [InlineKeyboardButton(text="✅ Опубликованные", callback_data='filter_published')],
        [InlineKeyboardButton(text="📝 Одобренные (не опубл.)", callback_data='filter_approved_not_pub')],
        [InlineKeyboardButton(text="⏳ На модерации", callback_data='filter_pending')],
        [InlineKeyboardButton(text="❌ Отклонённые", callback_data='filter_rejected')],
        [InlineKeyboardButton(text="⭐ Высокий рейтинг (≥8)", callback_data='filter_high_rating')],
        [InlineKeyboardButton(text="⚠️ Низкий рейтинг (<6)", callback_data='filter_low_rating')],
        [InlineKeyboardButton(text="📥 Скачать все отзывы (CSV)", callback_data='export_all_csv')]
    ])
    
    await message.answer(text, reply_markup=keyboard)

@reviews_router.callback_query(F.data.startswith('filter_'))
async def filter_reviews(callback: CallbackQuery):
    """Показать отфильтрованные отзывы"""
    await callback.answer()
    
    filter_type = callback.data.split('_', 1)[1]
    
    # Формируем SQL запрос в зависимости от фильтра
    if filter_type == 'all':
        where_clause = ""
        title = "Все отзывы"
    elif filter_type == 'published':
        where_clause = "WHERE status = 'approved' AND is_published = 1"
        title = "✅ Опубликованные отзывы"
    elif filter_type == 'approved_not_pub':
        where_clause = "WHERE status = 'approved' AND is_published = 0"
        title = "📝 Одобренные (не опубликованные)"
    elif filter_type == 'pending':
        where_clause = "WHERE status = 'pending'"
        title = "⏳ Отзывы на модерации"
    elif filter_type == 'rejected':
        where_clause = "WHERE status = 'rejected'"
        title = "❌ Отклонённые отзывы"
    elif filter_type == 'high_rating':
        where_clause = "WHERE (cleanliness + comfort + location + facilities + staff + value_for_money) / 6.0 >= 8"
        title = "⭐ Высокий рейтинг (≥8)"
    elif filter_type == 'low_rating':
        where_clause = "WHERE (cleanliness + comfort + location + facilities + staff + value_for_money) / 6.0 < 6"
        title = "⚠️ Низкий рейтинг (<6)"
    else:
        where_clause = ""
        title = "Отзывы"
    
    async with aiosqlite.connect(DB_FILE) as db:
        db.row_factory = aiosqlite.Row
        query = f"""
            SELECT id, guest_name, room_number, status, is_published, created_at,
                   ROUND((cleanliness + comfort + location + facilities + staff + value_for_money) / 6.0, 1) as avg_score
            FROM reviews
            {where_clause}
            ORDER BY created_at DESC
            LIMIT 20
        """
        cursor = await db.execute(query)
        reviews = await cursor.fetchall()
    
    if not reviews:
        await callback.message.answer(f"📭 {title}: нет отзывов")
        return
    
    keyboard = []
    for review in reviews:
        date = datetime.fromisoformat(review['created_at']).strftime('%d.%m')
        
        # Эмодзи статуса
        if review['is_published']:
            status_emoji = "✅"
        elif review['status'] == 'approved':
            status_emoji = "📝"
        elif review['status'] == 'pending':
            status_emoji = "⏳"
        elif review['status'] == 'rejected':
            status_emoji = "❌"
        else:
            status_emoji = "❓"
        
        keyboard.append([
            InlineKeyboardButton(
                text=f"{status_emoji} ⭐{review['avg_score']} - {review['guest_name']} ({date})",
                callback_data=f'view_review_{review["id"]}'
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton(text="🔙 Назад в меню", callback_data='back_to_all_reviews_menu')
    ])
    
    await callback.message.answer(
        f"📋 <b>{title} ({len(reviews)}):</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )

@reviews_router.callback_query(F.data.startswith('view_review_'))
async def view_review_detail(callback: CallbackQuery):
    """Показать детали отзыва с кнопками управления"""
    await callback.answer()
    
    review_id = int(callback.data.split('_')[2])
    
    async with aiosqlite.connect(DB_FILE) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM reviews WHERE id = ?", (review_id,))
        review = await cursor.fetchone()
    
    if not review:
        await callback.message.answer("❌ Отзыв не найден")
        return
    
    avg_score = (
        review['cleanliness'] + review['comfort'] + review['location'] +
        review['facilities'] + review['staff'] + review['value_for_money']
    ) / 6
    
    # Статус
    status_text = {
        'pending': '⏳ На модерации',
        'approved': '✅ Одобрен',
        'rejected': '❌ Отклонён'
    }.get(review['status'], review['status'])
    
    pub_status = "📢 Опубликован" if review['is_published'] else "📥 Не опубликован"
    
    text = f"""
📝 <b>Отзыв #{review['id']}</b>
👤 {review['guest_name']} (комната {review['room_number']})
📅 {datetime.fromisoformat(review['created_at']).strftime('%d.%m.%Y %H:%M')}

📊 <b>Статус:</b> {status_text}
📢 <b>Публикация:</b> {pub_status}

⭐ <b>Оценки:</b>
🧹 Чистота: {review['cleanliness']}/10
🛏️ Комфорт: {review['comfort']}/10
📍 Расположение: {review['location']}/10
🏊 Удобства: {review['facilities']}/10
👥 Персонал: {review['staff']}/10
💰 Цена/качество: {review['value_for_money']}/10

📊 <b>Средняя: {avg_score:.1f}/10</b>

✅ <b>Понравилось:</b>
{review['pros'] or 'не указано'}

❌ <b>Улучшить:</b>
{review['cons'] or 'не указано'}

💬 <b>Комментарий:</b>
{review['comment'] or 'не указано'}
"""
    
    # Формируем кнопки в зависимости от статуса
    keyboard = []
    
    # Кнопки публикации/снятия с публикации
    if review['status'] == 'approved':
        if review['is_published']:
            keyboard.append([InlineKeyboardButton(text="📥 Снять с публикации", callback_data=f'unpublish_{review_id}')])
        else:
            keyboard.append([InlineKeyboardButton(text="📢 Опубликовать", callback_data=f'publish_{review_id}')])
    
    # Кнопка удаления (только для админов)
    keyboard.append([InlineKeyboardButton(text="🗑️ Удалить", callback_data=f'delete_{review_id}')])
    
    # Кнопка назад
    keyboard.append([InlineKeyboardButton(text="🔙 Назад к списку", callback_data='back_to_filtered_list')])
    
    await callback.message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

@reviews_router.callback_query(F.data.startswith('publish_'))
async def publish_review(callback: CallbackQuery):
    """Опубликовать одобренный отзыв"""
    await callback.answer("📢 Опубликован")
    
    review_id = int(callback.data.split('_')[1])
    
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("""
            UPDATE reviews
            SET is_published = 1
            WHERE id = ? AND status = 'approved'
        """, (review_id,))
        
        await db.commit()
    
    await callback.message.answer(f"📢 Отзыв #{review_id} опубликован на сайте!")

@reviews_router.callback_query(F.data.startswith('unpublish_'))
async def unpublish_review(callback: CallbackQuery):
    """Снять отзыв с публикации"""
    await callback.answer("📥 Снят с публикации")
    
    review_id = int(callback.data.split('_')[1])
    
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("""
            UPDATE reviews
            SET is_published = 0
            WHERE id = ?
        """, (review_id,))
        
        await db.commit()
    
    await callback.message.answer(f"📥 Отзыв #{review_id} снят с публикации")

@reviews_router.callback_query(F.data == 'back_to_all_reviews_menu')
async def back_to_all_reviews_menu(callback: CallbackQuery):
    """Вернуться в главное меню управления отзывами"""
    await callback.answer()
    
    class FakeMessage:
        def __init__(self, from_user, chat):
            self.from_user = from_user
            self.chat = chat
    
        async def answer(self, text, **kwargs):
            await callback.message.answer(text, **kwargs)
    
    fake = FakeMessage(callback.from_user, callback.message.chat)
    await all_reviews_menu(fake)

@reviews_router.callback_query(F.data == 'back_to_filtered_list')
async def back_to_filtered_list(callback: CallbackQuery):
    """Заглушка для возврата к списку (требует сохранения фильтра)"""
    await callback.answer("Используйте /all_reviews для возврата в меню")

# ===================== ЭКСПОРТ В CSV =====================

@reviews_router.callback_query(F.data == 'export_all_csv')
async def export_reviews_csv(callback: CallbackQuery):
    """Экспортировать все отзывы в CSV"""
    user_id = callback.from_user.id
    
    if user_id not in ADMIN_IDS:
        await callback.answer("❌ Недостаточно прав", show_alert=True)
        return
    
    await callback.answer("📥 Генерирую CSV...")
    
    try:
        async with aiosqlite.connect(DB_FILE) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT 
                    id, guest_name, room_number, telegram_username,
                    cleanliness, comfort, location, facilities, staff, value_for_money,
                    ROUND((cleanliness + comfort + location + facilities + staff + value_for_money) / 6.0, 1) as avg_score,
                    pros, cons, comment, status, is_published, created_at, moderated_at
                FROM reviews
                ORDER BY created_at DESC
            """)
            
            reviews = await cursor.fetchall()
        
        if not reviews:
            await callback.message.answer("📭 Нет отзывов для экспорта")
            return
        
        # Создаём CSV в памяти
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Заголовки
        writer.writerow([
            'ID', 'Имя', 'Номер', 'Telegram', 
            'Чистота', 'Комфорт', 'Расположение', 'Удобства', 'Персонал', 'Цена/качество', 'Средняя оценка',
            'Плюсы', 'Минусы', 'Комментарий', 'Статус', 'Опубликован', 'Дата создания', 'Дата модерации'
        ])
        
        # Данные
        for r in reviews:
            writer.writerow([
                r['id'], r['guest_name'], r['room_number'], r['telegram_username'] or '',
                r['cleanliness'], r['comfort'], r['location'], r['facilities'], r['staff'], r['value_for_money'], r['avg_score'],
                r['pros'] or '', r['cons'] or '', r['comment'] or '',
                r['status'], 'Да' if r['is_published'] else 'Нет',
                r['created_at'], r['moderated_at'] or ''
            ])
        
        # Конвертируем в bytes
        csv_bytes = output.getvalue().encode('utf-8-sig')  # BOM для Excel
        
        # Отправляем файл
        filename = f"reviews_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        file = BufferedInputFile(csv_bytes, filename=filename)
        
        await callback.message.answer_document(
            document=file,
            caption=f"📊 Экспорт отзывов\n📝 Всего: {len(reviews)} отзывов"
        )
        
    except Exception as e:
        await callback.message.answer(f"❌ Ошибка при экспорте: {e}")
        print(f"Ошибка экспорта CSV: {e}")
