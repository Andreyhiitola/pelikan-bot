import logging
logger = logging.getLogger(__name__)

# ==============================================================================
# analytics_handler.py - Модуль аналитики отзывов
# ==============================================================================

import os
import io
import aiosqlite
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from typing import Dict, List, Tuple
import matplotlib
matplotlib.use('Agg')  # Для работы без GUI
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram.types import BufferedInputFile
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# Настройки
DB_FILE = os.getenv('DB_FILE', 'orders.db')
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(","))) if os.getenv("ADMIN_IDS") else []

# Email настройки
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.mail.ru')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER = os.getenv('SMTP_USER', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
REPORT_EMAIL = os.getenv('REPORT_EMAIL', 'regsk@mail.ru')

# Настройка русского языка для графиков
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

# ==============================================================================
# СБОР ДАННЫХ ИЗ БД
# ==============================================================================

async def get_reviews_analytics(days: int = 30) -> Dict:
    """
    Собирает аналитику по отзывам за последние N дней
    
    Returns:
        Dict с аналитикой:
        - daily_stats: статистика по дням
        - category_averages: средние оценки по категориям
        - rating_distribution: распределение по рейтингам
        - trends: тренды изменений
        - problem_areas: проблемные зоны
        - best_reviews: лучшие отзывы
        - worst_reviews: худшие отзывы
    """
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    async with aiosqlite.connect(DB_FILE) as db:
        db.row_factory = aiosqlite.Row
        
        # 1. Статистика по дням
        cursor = await db.execute("""
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as count,
                ROUND(AVG((cleanliness + comfort + location + facilities + staff + value_for_money) / 6.0), 2) as avg_rating,
                ROUND(AVG(cleanliness), 2) as avg_cleanliness,
                ROUND(AVG(comfort), 2) as avg_comfort,
                ROUND(AVG(location), 2) as avg_location,
                ROUND(AVG(facilities), 2) as avg_facilities,
                ROUND(AVG(staff), 2) as avg_staff,
                ROUND(AVG(value_for_money), 2) as avg_value
            FROM reviews
            WHERE created_at >= ? AND status IN ('approved', 'pending')
            GROUP BY DATE(created_at)
            ORDER BY date
        """, (start_date,))
        daily_stats = await cursor.fetchall()
        
        # 2. Общие средние по категориям (за весь период)
        cursor = await db.execute("""
            SELECT 
                ROUND(AVG(cleanliness), 2) as avg_cleanliness,
                ROUND(AVG(comfort), 2) as avg_comfort,
                ROUND(AVG(location), 2) as avg_location,
                ROUND(AVG(facilities), 2) as avg_facilities,
                ROUND(AVG(staff), 2) as avg_staff,
                ROUND(AVG(value_for_money), 2) as avg_value
            FROM reviews
            WHERE created_at >= ? AND status IN ('approved', 'pending')
        """, (start_date,))
        category_averages = await cursor.fetchone()
        
        # 3. Распределение по рейтингам (очень плохо - отлично)
        cursor = await db.execute("""
            SELECT 
                CASE 
                    WHEN (cleanliness + comfort + location + facilities + staff + value_for_money) / 6.0 < 2 THEN 'Очень плохо'
                    WHEN (cleanliness + comfort + location + facilities + staff + value_for_money) / 6.0 < 4 THEN 'Плохо'
                    WHEN (cleanliness + comfort + location + facilities + staff + value_for_money) / 6.0 < 6 THEN 'Удовлетворительно'
                    WHEN (cleanliness + comfort + location + facilities + staff + value_for_money) / 6.0 < 8 THEN 'Хорошо'
                    ELSE 'Отлично'
                END as rating_category,
                COUNT(*) as count
            FROM reviews
            WHERE created_at >= ? AND status IN ('approved', 'pending')
            GROUP BY rating_category
        """, (start_date,))
        rating_distribution = await cursor.fetchall()
        
        # 4. Топ-3 лучших отзыва
        cursor = await db.execute("""
            SELECT 
                id, guest_name, room_number,
                ROUND((cleanliness + comfort + location + facilities + staff + value_for_money) / 6.0, 1) as avg_rating,
                pros, comment, created_at
            FROM reviews
            WHERE created_at >= ? AND status IN ('approved', 'pending')
            ORDER BY avg_rating DESC, created_at DESC
            LIMIT 3
        """, (start_date,))
        best_reviews = await cursor.fetchall()
        
        # 5. Топ-3 худших отзыва
        cursor = await db.execute("""
            SELECT 
                id, guest_name, room_number,
                ROUND((cleanliness + comfort + location + facilities + staff + value_for_money) / 6.0, 1) as avg_rating,
                cons, comment, created_at
            FROM reviews
            WHERE created_at >= ? AND status IN ('approved', 'pending')
            ORDER BY avg_rating ASC, created_at DESC
            LIMIT 3
        """, (start_date,))
        worst_reviews = await cursor.fetchall()
        
        # 6. Сравнение с предыдущим периодом
        prev_start_date = (datetime.now() - timedelta(days=days*2)).strftime('%Y-%m-%d')
        prev_end_date = start_date
        
        cursor = await db.execute("""
            SELECT 
                ROUND(AVG((cleanliness + comfort + location + facilities + staff + value_for_money) / 6.0), 2) as avg_rating
            FROM reviews
            WHERE created_at >= ? AND created_at < ? AND status IN ('approved', 'pending')
        """, (prev_start_date, prev_end_date))
        prev_period = await cursor.fetchone()
        
        cursor = await db.execute("""
            SELECT 
                ROUND(AVG((cleanliness + comfort + location + facilities + staff + value_for_money) / 6.0), 2) as avg_rating
            FROM reviews
            WHERE created_at >= ? AND status IN ('approved', 'pending')
        """, (start_date,))
        current_period = await cursor.fetchone()
    
    return {
        'daily_stats': [dict(row) for row in daily_stats],
        'category_averages': dict(category_averages) if category_averages else {},
        'rating_distribution': [dict(row) for row in rating_distribution],
        'best_reviews': [dict(row) for row in best_reviews],
        'worst_reviews': [dict(row) for row in worst_reviews],
        'prev_period_avg': prev_period['avg_rating'] if prev_period and prev_period['avg_rating'] else None,
        'current_period_avg': current_period['avg_rating'] if current_period and current_period['avg_rating'] else None,
        'days': days,
        'start_date': start_date
    }

# ==============================================================================
# ГЕНЕРАЦИЯ ГРАФИКОВ
# ==============================================================================

def generate_trend_chart(daily_stats: List[Dict]) -> io.BytesIO:
    """Генерирует график тренда средних оценок по дням"""
    if not daily_stats:
        # Пустой график
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.text(0.5, 0.5, 'Нет данных за период', 
                ha='center', va='center', fontsize=16)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
    else:
        dates = [datetime.strptime(row['date'], '%Y-%m-%d') for row in daily_stats]
        ratings = [row['avg_rating'] if row['avg_rating'] is not None else 0 for row in daily_stats]        
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(dates, ratings, marker='o', linewidth=2, markersize=8, color='#2E86AB')
        
        # Линия тренда
        if len(dates) > 1:
            z = np.polyfit(range(len(dates)), ratings, 1)
            p = np.poly1d(z)
            ax.plot(dates, p(range(len(dates))), "--", color='red', alpha=0.5, label='Тренд')
        
        ax.set_xlabel('Дата', fontsize=12)
        ax.set_ylabel('Средняя оценка', fontsize=12)
        ax.set_title('Динамика средних оценок', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0, 10)
        
        # Форматирование дат на оси X
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(dates)//10)))
        plt.xticks(rotation=45)
        
        if len(dates) > 1:
            ax.legend()
    
    plt.tight_layout()
    
    # Сохраняем в буфер
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0)
    plt.close()
    
    return buf

def generate_category_chart(category_averages: Dict) -> io.BytesIO:
    """Генерирует диаграмму средних оценок по категориям"""
    if not category_averages:
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, 'Нет данных', ha='center', va='center', fontsize=16)
        ax.axis('off')
    else:
        # Безопасная функция для получения значений
        def safe_value(val):
            return val if val is not None else 0
        
        categories = {
            'Чистота': safe_value(category_averages.get('avg_cleanliness')),
            'Комфорт': safe_value(category_averages.get('avg_comfort')),
            'Расположение': safe_value(category_averages.get('avg_location')),
            'Удобства': safe_value(category_averages.get('avg_facilities')),
            'Персонал': safe_value(category_averages.get('avg_staff')),
            'Цена/качество': safe_value(category_averages.get('avg_value'))
        }
        
        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.barh(list(categories.keys()), list(categories.values()), color='#2E86AB')
        
        # Подписи значений на столбцах
        for i, (bar, value) in enumerate(zip(bars, categories.values())):
            ax.text(value + 0.1, i, f'{value:.1f}', va='center', fontsize=11)
        
        ax.set_xlabel('Средняя оценка', fontsize=12)
        ax.set_title('Средние оценки по категориям', fontsize=14, fontweight='bold')
        ax.set_xlim(0, 10)
        ax.grid(True, alpha=0.3, axis='x')
    
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0)
    plt.close()
    
    return buf

def generate_distribution_chart(rating_distribution: List[Dict]) -> io.BytesIO:
    """Генерирует круговую диаграмму распределения оценок"""
    if not rating_distribution:
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.text(0.5, 0.5, 'Нет данных', ha='center', va='center', fontsize=16)
        ax.axis('off')
    else:
        # Упорядочиваем категории
        order = ['Очень плохо', 'Плохо', 'Удовлетворительно', 'Хорошо', 'Отлично']
        labels = []
        sizes = []
        
        for category in order:
            found = next((item for item in rating_distribution if item['rating_category'] == category), None)
            if found:
                labels.append(category)
                sizes.append(found['count'])
        
        colors = ['#D32F2F', '#F57C00', '#FBC02D', '#7CB342', '#388E3C']
        
        fig, ax = plt.subplots(figsize=(8, 8))
        wedges, texts, autotexts = ax.pie(
            sizes, 
            labels=labels, 
            colors=colors[:len(labels)],
            autopct='%1.1f%%',
            startangle=90,
            textprops={'fontsize': 11}
        )
        
        # Жирный текст для процентов
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        ax.set_title('Распределение отзывов по оценкам', fontsize=14, fontweight='bold', pad=20)
    
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0)
    plt.close()
    
    return buf

# Импортируем numpy для линии тренда
import numpy as np

# ==============================================================================
# ГЕНЕРАЦИЯ ТЕКСТОВОГО ОТЧЕТА
# ==============================================================================

def generate_text_report(analytics: Dict) -> str:
    """Генерирует текстовый отчет для Telegram"""
    
    # Заголовок
    report_date = datetime.now().strftime('%d.%m.%Y')
    text = f"📊 <b>Ежедневный отчет по отзывам</b>\n"
    text += f"📅 Дата: {report_date}\n"
    text += f"📈 Период анализа: последние {analytics['days']} дней\n\n"
    
    # Общая статистика
    total_reviews = len(analytics['daily_stats'])
    if analytics['current_period_avg']:
        text += f"⭐ <b>Средняя оценка:</b> {analytics['current_period_avg']:.1f}/10\n"
        
        # Сравнение с предыдущим периодом
        if analytics['prev_period_avg']:
            diff = analytics['current_period_avg'] - analytics['prev_period_avg']
            if diff > 0:
                emoji = "📈"
                trend = f"+{diff:.1f}"
            elif diff < 0:
                emoji = "📉"
                trend = f"{diff:.1f}"
            else:
                emoji = "➡️"
                trend = "0.0"
            
            text += f"{emoji} <b>Изменение:</b> {trend} (по сравнению с предыдущими {analytics['days']} днями)\n\n"
        else:
            text += "\n"
    else:
        text += "⚠️ <i>Нет отзывов за период</i>\n\n"
    
    # Распределение по категориям
    if analytics['rating_distribution']:
        text += "📊 <b>Распределение отзывов:</b>\n"
        for item in analytics['rating_distribution']:
            text += f"  • {item['rating_category']}: {item['count']} отзывов\n"
        text += "\n"
    
    # Средние оценки по категориям
    if analytics['category_averages']:
        text += "🎯 <b>Оценки по категориям:</b>\n"
        cat = analytics['category_averages']
        
        categories_emoji = {
            'avg_cleanliness': ('🧹', 'Чистота'),
            'avg_comfort': ('🛏️', 'Комфорт'),
            'avg_location': ('📍', 'Расположение'),
            'avg_facilities': ('🏊', 'Удобства'),
            'avg_staff': ('👥', 'Персонал'),
            'avg_value': ('💰', 'Цена/качество')
        }
        
        for key, (emoji, name) in categories_emoji.items():
            if key in cat and cat[key]:
                text += f"  {emoji} {name}: <b>{cat[key]:.1f}</b>/10\n"
        text += "\n"
    
    # Проблемные зоны (оценка < 7)
    if analytics['category_averages']:
        problems = []
        cat = analytics['category_averages']
        threshold = 7.0
        
        if (cat.get('avg_cleanliness') or 10) < threshold:
            problems.append(f"🧹 Чистота ({cat.get('avg_cleanliness', 0):.1f})")
        if (cat.get('avg_comfort') or 10) < threshold:
            problems.append(f"🛏️ Комфорт ({cat.get('avg_comfort', 0):.1f})")
        if (cat.get('avg_location') or 10) < threshold:
            problems.append(f"📍 Расположение ({cat.get('avg_location', 0):.1f})")
        if (cat.get('avg_facilities') or 10) < threshold:
            problems.append(f"🏊 Удобства ({cat.get('avg_facilities', 0):.1f})")
        if (cat.get('avg_staff') or 10) < threshold:
            problems.append(f"👥 Персонал ({cat.get('avg_staff', 0):.1f})")
        if (cat.get('avg_value') or 10) < threshold:
            problems.append(f"💰 Цена/качество ({cat.get('avg_value', 0):.1f})")
        
        if problems:
            text += "⚠️ <b>Требуют внимания:</b>\n"
            for problem in problems:
                text += f"  • {problem}\n"
            text += "\n"
    
    # Лучшие отзывы
    if analytics['best_reviews']:
        text += "⭐ <b>Лучшие отзывы:</b>\n"
        for review in analytics['best_reviews']:
            date = datetime.fromisoformat(review['created_at']).strftime('%d.%m')
            text += f"  • {review['guest_name']} ({date}): {review['avg_rating']:.1f}/10\n"
            if review['pros']:
                text += f"    <i>\"{review['pros'][:100]}...\"</i>\n" if len(review['pros']) > 100 else f"    <i>\"{review['pros']}\"</i>\n"
        text += "\n"
    
    # Худшие отзывы (для внутреннего анализа)
    if analytics['worst_reviews']:
        text += "⚠️ <b>Отзывы, требующие внимания:</b>\n"
        for review in analytics['worst_reviews']:
            date = datetime.fromisoformat(review['created_at']).strftime('%d.%m')
            text += f"  • {review['guest_name']} ({date}): {review['avg_rating']:.1f}/10\n"
            if review['cons']:
                text += f"    <i>\"{review['cons'][:100]}...\"</i>\n" if len(review['cons']) > 100 else f"    <i>\"{review['cons']}\"</i>\n"
        text += "\n"
    
    text += "━━━━━━━━━━━━━━━━━\n"
    text += "Подробные графики прикреплены к сообщению."
    
    return text

# ОТПРАВКА ОТЧЕТА В TELEGRAM
# ==============================================================================

async def send_telegram_report(bot: Bot, analytics: Dict):
    """Отправляет отчет в Telegram админам"""
    
    # Генерируем текстовый отчет
    text_report = generate_text_report(analytics)
    
    # Генерируем графики
    trend_chart = generate_trend_chart(analytics['daily_stats'])
    category_chart = generate_category_chart(analytics['category_averages'])
    distribution_chart = generate_distribution_chart(analytics['rating_distribution'])
    
    # Отправляем каждому админу
    for admin_id in ADMIN_IDS:
        try:
            # Отправляем текстовый отчет
            await bot.send_message(
                chat_id=admin_id,
                text=text_report,
                parse_mode='HTML'
            )
            
            # Отправляем графики
            trend_chart.seek(0)
            await bot.send_photo(
                chat_id=admin_id,
                photo=BufferedInputFile(trend_chart.read(), filename="trend.png"),
                caption="📈 Динамика средних оценок"
            )
            
            
            category_chart.seek(0)
            await bot.send_photo(
                chat_id=admin_id,
                photo=BufferedInputFile(category_chart.read(), filename="category.png"),
                caption="📊 Средние оценки по категориям"
            )
            
            distribution_chart.seek(0)
            await bot.send_photo(
                chat_id=admin_id,
                photo=BufferedInputFile(distribution_chart.read(), filename="distribution.png"),
                caption="📉 Распределение оценок"
            )
            
        except Exception as e:
            print(f"Ошибка отправки отчета админу {admin_id}: {e}")
            continue


# ПЛАНИРОВЩИК
# ==============================================================================

async def scheduled_report(bot: Bot):
    """Запланированная отправка отчета"""
    try:
        analytics = await generate_analytics()
        await send_telegram_report(bot, analytics)
        logger.info("Scheduled report sent successfully")
    except Exception as e:
        print(f"Error sending scheduled report: {e}")


def setup_scheduler(bot: Bot):
    """Настройка планировщика для автоматической отправки отчетов"""
    scheduler = AsyncIOScheduler(timezone='Asia/Almaty')
    
    # Отправка отчета каждый день в 9:00
    scheduler.add_job(
        scheduled_report,
        trigger='cron',
        hour=9,
        minute=0,
        args=[bot]
    )
    
    scheduler.start()
    logger.info("Analytics scheduler started")
    return scheduler


async def send_email_report(analytics: Dict):
    """Отправка отчета по email с вложениями через Mail.ru SMTP"""
    try:
        # Читаем настройки из .env
        smtp_server = os.getenv("SMTP_SERVER", "smtp.mail.ru")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        from_email = os.getenv("SMTP_USER", "sttek@mail.ru")
        to_emails_str = os.getenv("REPORT_EMAIL", "sttek@mail.ru")
        to_emails = [e.strip() for e in to_emails_str.split(",")]
        smtp_password = os.getenv("SMTP_PASSWORD", "")
        
        if not smtp_password:
            logger.error("❌ SMTP_PASSWORD не установлен в .env файле!")
            return
        
        # Создаём письмо
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = ", ".join(to_emails)
        msg['Subject'] = f"📊 Ежедневный отчёт Pelican Alakol - {datetime.now().strftime('%d.%m.%Y')}"
        
        # Получаем данные из analytics
        daily_stats = analytics.get('daily_stats', [])
        category_avg = analytics.get('category_averages', {})
        rating_dist = analytics.get('rating_distribution', [])
        
        total_reviews = len(daily_stats)
        avg_rating = sum([s.get('avg_rating', 0) for s in daily_stats]) / total_reviews if total_reviews > 0 else 0
        
        # Формируем текст письма
        body = f"""Ежедневный отчёт по отзывам

Дата: {datetime.now().strftime('%d.%m.%Y')}
Всего отзывов: {total_reviews}
Средняя оценка: {avg_rating:.1f}/10

Категории:
"""
        if category_avg:
            for cat, val in category_avg.items():
                emoji = {'cleanliness': '🧹', 'comfort': '🛏️', 'location': '📍', 
                        'facilities': '🏊', 'staff': '👥', 'value_for_money': '💰'}.get(cat, '•')
                body += f"{emoji} {cat}: {val:.1f}\n"
        
        body += "\nРаспределение оценок:\n"
        for item in rating_dist:
            body += f"{item.get('rating_group', 'N/A')}: {item.get('count', 0)} отзывов\n"
        
        body += "\nФайлы с графиками прикреплены к письму.\n\n---\nАвтоматическое письмо от бота Pelican Alakol Hotel"
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # Прикрепляем графики
        chart_files = [
            analytics.get('trend_chart'),
            analytics.get('categories_chart'),
            analytics.get('distribution_chart')
        ]
        
        attached_count = 0
        for chart_path in chart_files:
            if chart_path and os.path.exists(chart_path):
                try:
                    with open(chart_path, 'rb') as f:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(f.read())
                        encoders.encode_base64(part)
                        filename = os.path.basename(chart_path)
                        part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
                        msg.attach(part)
                        attached_count += 1
                        logger.info(f"📎 Прикреплен файл: {filename}")
                except Exception as e:
                    logger.error(f"❌ Ошибка прикрепления {chart_path}: {e}")
            else:
                logger.warning(f"⚠️ Файл не найден: {chart_path}")
        
        if attached_count == 0:
            logger.warning("⚠️ Ни один файл не был прикреплен!")
        
        # Отправка через Mail.ru SMTP
        logger.info(f"📧 Подключение к {smtp_server}:{smtp_port}...")
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        
        logger.info(f"🔐 Авторизация как {from_email}...")
        server.login(from_email, smtp_password)
        
        logger.info(f"📤 Отправка письма на {len(to_emails)} адресов...")
        server.sendmail(from_email, to_emails, msg.as_string())
        server.quit()
        
        logger.info(f"✅ Email отчёт отправлен успешно на: {', '.join(to_emails)}! Прикреплено файлов: {attached_count}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка отправки email: {e}")
        import traceback
        traceback.print_exc()
