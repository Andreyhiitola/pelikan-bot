# ==============================================================================
# analytics_commands.py - Команды для работы с аналитикой отзывов
# ==============================================================================

import os
from aiogram import Router, F
from aiogram.types import BufferedInputFile
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from analytics_handler import (
    get_reviews_analytics,
    send_telegram_report,
    send_email_report,
    generate_text_report,
    generate_trend_chart,
    generate_category_chart,
    generate_distribution_chart
)

ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(","))) if os.getenv("ADMIN_IDS") else []

analytics_router = Router()

# ==============================================================================
# КОМАНДА /analytics - Главное меню аналитики
# ==============================================================================

@analytics_router.message(Command("analytics"))
async def analytics_menu(message: Message):
    """Главное меню аналитики"""
    user_id = message.from_user.id
    
    if user_id not in ADMIN_IDS:
        await message.answer("❌ Недостаточно прав")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Отчет за 7 дней", callback_data='analytics_7')],
        [InlineKeyboardButton(text="📊 Отчет за 30 дней", callback_data='analytics_30')],
        [InlineKeyboardButton(text="📊 Отчет за 90 дней", callback_data='analytics_90')],
        [InlineKeyboardButton(text="📧 Отправить на email", callback_data='analytics_email')],
        [InlineKeyboardButton(text="📈 Только графики", callback_data='analytics_charts')]
    ])
    
    await message.answer(
        "📊 <b>Аналитика отзывов</b>\n\n"
        "Выберите период для анализа:",
        reply_markup=keyboard
    )

# ==============================================================================
# ОБРАБОТЧИКИ КНОПОК
# ==============================================================================

@analytics_router.callback_query(F.data.startswith('analytics_'))
async def analytics_handler(callback: CallbackQuery):
    """Обработка выбора периода аналитики"""
    await callback.answer()
    
    action = callback.data.split('_')[1]
    
    if action == 'email':
        await callback.message.answer("📧 Отправляю отчет на email...")
        
        try:
            analytics = await get_reviews_analytics(days=30)
            await send_email_report(analytics)
            await callback.message.answer("✅ Отчет отправлен на regsk@mail.ru")
        except Exception as e:
            await callback.message.answer("❌ Ошибка отправки отчета на email", parse_mode=None)
        
        return
    
    if action == 'charts':
        await callback.message.answer("📈 Генерирую графики...")
        
        try:
            analytics = await get_reviews_analytics(days=30)
            
            trend_chart = generate_trend_chart(analytics['daily_stats'])
            category_chart = generate_category_chart(analytics['category_averages'])
            distribution_chart = generate_distribution_chart(analytics['rating_distribution'])
            
            await callback.message.answer_photo(
                photo=BufferedInputFile(trend_chart.getvalue(), filename="trend.png"),
                caption="📈 Динамика средних оценок (30 дней)"
            )
            
            await callback.message.answer_photo(
                photo=BufferedInputFile(category_chart.getvalue(), filename="categories.png"),
                caption="🎯 Средние оценки по категориям"
            )
            
            await callback.message.answer_photo(
                photo=BufferedInputFile(distribution_chart.getvalue(), filename="distribution.png"),
                caption="📊 Распределение отзывов по оценкам"
            )
            
        except Exception as e:
            await callback.message.answer("❌ Ошибка генерации графиков", parse_mode=None)
        
        return
    
    # Обработка периодов (7, 30, 90 дней)
    try:
        days = int(action)
    except ValueError:
        await callback.message.answer("❌ Неверный период")
        return
    
    await callback.message.answer(f"📊 Генерирую отчет за {days} дней...")
    
    try:
        # Собираем аналитику
        analytics = await get_reviews_analytics(days=days)
        
        # Отправляем текстовый отчет
        text_report = generate_text_report(analytics)
        await callback.message.answer(text_report, parse_mode='HTML')
        
        # Отправляем графики
        trend_chart = generate_trend_chart(analytics['daily_stats'])
        category_chart = generate_category_chart(analytics['category_averages'])
        distribution_chart = generate_distribution_chart(analytics['rating_distribution'])
        
        await callback.message.answer_photo(
            photo=BufferedInputFile(trend_chart.getvalue(), filename="trend.png"),
            caption=f"📈 Динамика средних оценок ({days} дней)"
        )
        
        await callback.message.answer_photo(
            photo=BufferedInputFile(category_chart.getvalue(), filename="categories.png"),
            caption="🎯 Средние оценки по категориям"
        )
        
        await callback.message.answer_photo(
            photo=BufferedInputFile(distribution_chart.getvalue(), filename="distribution.png"),
            caption="📊 Распределение отзывов по оценкам"
        )
        
    except Exception as e:
        await callback.message.answer("❌ Ошибка генерации отчета", parse_mode=None)
        import traceback
        traceback.print_exc()

# ==============================================================================
# КОМАНДА /test_report - Тестовая отправка отчета
# ==============================================================================

@analytics_router.message(Command("test_report"))
async def test_report(message: Message):
    """Тестовая отправка ежедневного отчета"""
    user_id = message.from_user.id
    
    if user_id not in ADMIN_IDS:
        await message.answer("❌ Недостаточно прав")
        return
    
    await message.answer("🔄 Генерирую тестовый отчет...")
    
    try:
        analytics = await get_reviews_analytics(days=30)
        
        # Отправляем отчет в Telegram
        await send_telegram_report(message.bot, analytics)
        
        # Отправляем на email
        await send_email_report(analytics)
        
        await message.answer("✅ Тестовый отчет отправлен!")
        
    except Exception as e:
        await message.answer("❌ Произошла ошибка при генерации отчета", parse_mode=None)
        import traceback
        traceback.print_exc()
