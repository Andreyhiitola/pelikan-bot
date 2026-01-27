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
            await bot.send_photo(
                chat_id=admin_id,
                photo=trend_chart,
                caption="📈 Динамика средних оценок"
            )
            
            trend_chart.seek(0)  # Возвращаем к началу для повторного использования
            
            await bot.send_photo(
                chat_id=admin_id,
                photo=category_chart,
                caption="🎯 Средние оценки по категориям"
            )
            
            category_chart.seek(0)
            
            await bot.send_photo(
                chat_id=admin_id,
                photo=distribution_chart,
                caption="📊 Распределение отзывов по оценкам"
            )
            
            distribution_chart.seek(0)
            
        except Exception as e:
            print(f"Ошибка отправки отчета админу {admin_id}: {e}")

# ==============================================================================
# ОТПРАВКА ОТЧЕТА НА EMAIL
# ==============================================================================

def generate_html_email_report(analytics: Dict) -> str:
    """Генерирует HTML-версию отчета для email"""
    
    report_date = datetime.now().strftime('%d.%m.%Y')
    
    html = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }}
            .header {{
                background-color: #2E86AB;
                color: white;
                padding: 20px;
                border-radius: 10px 10px 0 0;
            }}
            .content {{
                background-color: white;
                padding: 20px;
                border-radius: 0 0 10px 10px;
            }}
            .stat-box {{
                background-color: #f0f8ff;
                padding: 15px;
                margin: 10px 0;
                border-left: 4px solid #2E86AB;
            }}
            .positive {{
                color: #388E3C;
                font-weight: bold;
            }}
            .negative {{
                color: #D32F2F;
                font-weight: bold;
            }}
            .category-row {{
                display: flex;
                justify-content: space-between;
                padding: 8px 0;
                border-bottom: 1px solid #eee;
            }}
            .review-box {{
                background-color: #fafafa;
                padding: 10px;
                margin: 5px 0;
                border-left: 3px solid #ccc;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📊 Ежедневный отчет по отзывам</h1>
            <p>Дата: {report_date} | Период: последние {analytics['days']} дней</p>
        </div>
        
        <div class="content">
    """
    
    # Общая статистика
    if analytics['current_period_avg']:
        html += f"""
        <div class="stat-box">
            <h2>⭐ Средняя оценка: {analytics['current_period_avg']:.1f}/10</h2>
        """
        
        if analytics['prev_period_avg']:
            diff = analytics['current_period_avg'] - analytics['prev_period_avg']
            if diff > 0:
                trend_class = "positive"
                trend_text = f"↑ +{diff:.1f}"
            elif diff < 0:
                trend_class = "negative"
                trend_text = f"↓ {diff:.1f}"
            else:
                trend_class = ""
                trend_text = "→ 0.0"
            
            html += f'<p class="{trend_class}">Изменение: {trend_text} (по сравнению с предыдущим периодом)</p>'
        
        html += "</div>"
    
    # Оценки по категориям
    if analytics['category_averages']:
        html += "<h3>🎯 Оценки по категориям:</h3>"
        cat = analytics['category_averages']
        
        categories = [
            ('🧹 Чистота', cat.get('avg_cleanliness')),
            ('🛏️ Комфорт', cat.get('avg_comfort')),
            ('📍 Расположение', cat.get('avg_location')),
            ('🏊 Удобства', cat.get('avg_facilities')),
            ('👥 Персонал', cat.get('avg_staff')),
            ('💰 Цена/качество', cat.get('avg_value'))
        ]
        
        for name, value in categories:
            if value:
                html += f'<div class="category-row"><span>{name}</span><strong>{value:.1f}/10</strong></div>'
    
    # Распределение
    if analytics['rating_distribution']:
        html += "<h3>📊 Распределение отзывов:</h3><ul>"
        for item in analytics['rating_distribution']:
            html += f"<li>{item['rating_category']}: {item['count']} отзывов</li>"
        html += "</ul>"
    
    # Лучшие отзывы
    if analytics['best_reviews']:
        html += "<h3>⭐ Лучшие отзывы:</h3>"
        for review in analytics['best_reviews']:
            date = datetime.fromisoformat(review['created_at']).strftime('%d.%m')
            html += f"""
            <div class="review-box">
                <strong>{review['guest_name']} ({date}): {review['avg_rating']:.1f}/10</strong><br>
                <em>{review['pros'][:150] if review['pros'] else ''}</em>
            </div>
            """
    
    # Проблемные отзывы
    if analytics['worst_reviews']:
        html += "<h3>⚠️ Отзывы, требующие внимания:</h3>"
        for review in analytics['worst_reviews']:
            date = datetime.fromisoformat(review['created_at']).strftime('%d.%m')
            html += f"""
            <div class="review-box">
                <strong>{review['guest_name']} ({date}): {review['avg_rating']:.1f}/10</strong><br>
                <em>{review['cons'][:150] if review['cons'] else ''}</em>
            </div>
            """
    
    html += """
        <hr>
        <p style="color: #666; font-size: 12px;">
            Это автоматический отчет из системы Pelikan Alakol Hotel Bot.<br>
            Графики прикреплены к письму.
        </p>
        </div>
    </body>
    </html>
    """
    
    return html

async def send_email_report(analytics: Dict):
    """Отправляет отчет на email"""
    
    if not SMTP_USER or not SMTP_PASSWORD:
        print("⚠️ SMTP настройки не заданы, отправка email пропущена")
        return
    
    try:
        # Создаём письмо
        msg = MIMEMultipart('related')
        msg['From'] = SMTP_USER
        msg['To'] = REPORT_EMAIL
        msg['Subject'] = f'Отчет по отзывам - {datetime.now().strftime("%d.%m.%Y")}'
        
        # HTML-версия отчета
        html_report = generate_html_email_report(analytics)
        msg.attach(MIMEText(html_report, 'html', 'utf-8'))
        
        # Прикрепляем графики
        trend_chart = generate_trend_chart(analytics['daily_stats'])
        image1 = MIMEImage(trend_chart.read())
        image1.add_header('Content-Disposition', 'attachment', filename='trend_chart.png')
        msg.attach(image1)
        
        category_chart = generate_category_chart(analytics['category_averages'])
        image2 = MIMEImage(category_chart.read())
        image2.add_header('Content-Disposition', 'attachment', filename='category_chart.png')
        msg.attach(image2)
        
        distribution_chart = generate_distribution_chart(analytics['rating_distribution'])
        image3 = MIMEImage(distribution_chart.read())
        image3.add_header('Content-Disposition', 'attachment', filename='distribution_chart.png')
        msg.attach(image3)
        
        # Отправляем
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        
        print(f"✅ Email-отчет отправлен на {REPORT_EMAIL}")
        
    except Exception as e:
        print(f"❌ Ошибка отправки email: {e}")

# ==============================================================================
# ПЛАНИРОВЩИК ЗАДАЧ
# ==============================================================================

async def daily_report_job(bot: Bot):
    """Задача для ежедневного отчета"""
    print(f"🔄 Запуск ежедневного отчета: {datetime.now()}")
    
    try:
        # Собираем аналитику за последние 30 дней
        analytics = await get_reviews_analytics(days=30)
        
        # Отправляем в Telegram
        await send_telegram_report(bot, analytics)
        
        # Отправляем на email
        await send_email_report(analytics)
        
        print("✅ Ежедневный отчет отправлен успешно")
        
    except Exception as e:
        print(f"❌ Ошибка при генерации отчета: {e}")

def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    """Настраивает планировщик для ежедневных отчетов"""
    scheduler = AsyncIOScheduler()
    
    # Добавляем задачу: каждый день в 8:00
    scheduler.add_job(
        daily_report_job,
        trigger=CronTrigger(hour=8, minute=0),
        args=[bot],
        id='daily_report',
        name='Ежедневный отчет по отзывам',
        replace_existing=True
    )
    
    return scheduler
