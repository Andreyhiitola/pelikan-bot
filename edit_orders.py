#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
================================================================================
  РЕДАКТОР ЗАКАЗОВ - Пеликан Алаколь Hotel
================================================================================

ЧТО ЭТО:
    Интерактивный редактор для управления заказами из бара и столовой.
    Позволяет просматривать, редактировать, удалять и анализировать заказы.

ДЛЯ ЧЕГО:
    - Просмотр всех заказов в удобном формате
    - Редактирование имён, комнат, статусов, сумм
    - Удаление ошибочных заказов
    - Анализ продаж (статистика, топ клиентов, средний чек)
    - Очистка старых заказов

КАК ПОЛЬЗОВАТЬСЯ:
    1. Подключитесь к VPS:
       ssh root@85.192.40.138
    
    2. Запустите скрипт:
       python3 ~/pelikan-bot/edit_orders.py
    
    3. Выберите действие из меню:
       1 - Показать все заказы
       2 - Посмотреть конкретный заказ
       3 - Редактировать заказ
       4 - Удалить заказ
       5 - Статистика и аналитика
       6 - Очистка старых заказов (>30 дней)
       0 - Выход

СТАТУСЫ ЗАКАЗОВ:
    - принят: Заказ принят, ожидает приготовления
    - готовится: Заказ в процессе приготовления
    - готов: Заказ готов к выдаче
    - выдан: Заказ выдан клиенту (завершён)

ВАЖНО:
    - База данных: /root/pelikan-bot/data/orders.db
    - Таблица заказов: orders
    - Изменения сохраняются автоматически
    - Удаление заказов необратимо!

ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ:
    # Просмотр активных заказов
    Выберите: 1
    Фильтр: активные
    
    # Изменить статус заказа
    Выберите: 3
    ID заказа: 1234567890
    Что редактируем: 3
    Новый статус: готов
    
    # Статистика за сегодня
    Выберите: 5
    Выберите: 1
    
    # Удалить старые заказы
    Выберите: 6

АВТОР: Создано для Pelikan Alakol Hotel Bot
ДАТА: Январь 2026
================================================================================
"""

import sqlite3
import sys
import json
from datetime import datetime, timedelta

DB_PATH = '/root/pelikan-bot/data/orders.db'

def show_orders(filter_type='all'):
    """Показать заказы с фильтром"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if filter_type == 'active':
        query = """
            SELECT order_id, client_name, room, status, total, created_at 
            FROM orders 
            WHERE status != 'выдан'
            ORDER BY created_at DESC
        """
    elif filter_type == 'today':
        today = datetime.now().date().isoformat()
        query = f"""
            SELECT order_id, client_name, room, status, total, created_at 
            FROM orders 
            WHERE DATE(created_at) = '{today}'
            ORDER BY created_at DESC
        """
    else:  # all
        query = """
            SELECT order_id, client_name, room, status, total, created_at 
            FROM orders 
            ORDER BY created_at DESC 
            LIMIT 50
        """
    
    cursor.execute(query)
    orders = cursor.fetchall()
    
    if not orders:
        print("\n📭 Заказов не найдено")
        conn.close()
        return
    
    print("\n" + "="*100)
    print("ID Заказа   | Клиент         | Комната | Статус     | Сумма  | Дата и время")
    print("="*100)
    
    for row in orders:
        order_id = row[0][:10] + "..." if len(row[0]) > 10 else row[0]
        print(f"{order_id:<12} | {row[1]:<14} | {row[2]:<7} | {row[3]:<10} | {row[4]:<6}₸ | {row[5][:16]}")
    
    print("="*100)
    print(f"Всего заказов: {len(orders)}\n")
    conn.close()

def view_order(order_id):
    """Показать полный заказ"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,))
    row = cursor.fetchone()
    
    if not row:
        print(f"❌ Заказ #{order_id} не найден")
        conn.close()
        return
    
    # Парсим items JSON
    try:
        items = json.loads(row[5])
        items_text = "\n".join([f"      • {item['name']} x{item.get('quantity', 1)} - {item['price']}₸" for item in items])
    except:
        items_text = "      Ошибка чтения состава заказа"
    
    print(f"""
╔════════════════════════════════════════════════════════════════╗
║  ЗАКАЗ #{row[0]}
╠════════════════════════════════════════════════════════════════╣
║  Клиент: {row[1]}
║  Комната: {row[2]}
║  Telegram: @{row[4] or 'не указан'} (ID: {row[3] or 'н/д'})
╠════════════════════════════════════════════════════════════════╣
║  СОСТАВ ЗАКАЗА:
{items_text}
╠════════════════════════════════════════════════════════════════╣
║  Итого: {row[6]}₸
║  Статус: {row[7]}
║  Дата заказа: {row[8]}
║  Создан: {row[10]}
╠════════════════════════════════════════════════════════════════╣
║  PDF накладная: {row[9] or 'не создана'}
╚════════════════════════════════════════════════════════════════╝
    """)
    conn.close()

def edit_order(order_id):
    """Редактировать заказ"""
    view_order(order_id)
    
    print("\nЧто редактируем?")
    print("1. Имя клиента")
    print("2. Номер комнаты")
    print("3. Статус заказа")
    print("4. Сумму заказа")
    print("0. Назад")
    
    choice = input("\nВыберите (0-4): ").strip()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if choice == '1':
        new_value = input("Новое имя клиента: ").strip()
        cursor.execute("UPDATE orders SET client_name = ? WHERE order_id = ?", (new_value, order_id))
        print(f"✅ Имя клиента изменено на '{new_value}'")
    
    elif choice == '2':
        new_value = input("Новый номер комнаты: ").strip()
        cursor.execute("UPDATE orders SET room = ? WHERE order_id = ?", (new_value, order_id))
        print(f"✅ Номер комнаты изменён на '{new_value}'")
    
    elif choice == '3':
        print("\n1. принят")
        print("2. готовится")
        print("3. готов")
        print("4. выдан")
        status_choice = input("Выберите статус (1-4): ").strip()
        statuses = {'1': 'принят', '2': 'готовится', '3': 'готов', '4': 'выдан'}
        if status_choice in statuses:
            cursor.execute("UPDATE orders SET status = ? WHERE order_id = ?", (statuses[status_choice], order_id))
            print(f"✅ Статус изменён на '{statuses[status_choice]}'")
    
    elif choice == '4':
        new_value = input("Новая сумма (₸): ").strip()
        if new_value.isdigit():
            cursor.execute("UPDATE orders SET total = ? WHERE order_id = ?", (int(new_value), order_id))
            print(f"✅ Сумма изменена на {new_value}₸")
        else:
            print("❌ Введите число")
    
    conn.commit()
    conn.close()

def delete_order(order_id):
    """Удалить заказ"""
    view_order(order_id)
    confirm = input("\n⚠️  Удалить этот заказ НАВСЕГДА? (yes/no): ").strip().lower()
    
    if confirm == 'yes':
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM orders WHERE order_id = ?", (order_id,))
        conn.commit()
        conn.close()
        print(f"✅ Заказ #{order_id} удалён")
    else:
        print("❌ Отмена")

def show_statistics():
    """Показать статистику и аналитику"""
    while True:
        print("\n" + "="*50)
        print("  📊 СТАТИСТИКА И АНАЛИТИКА")
        print("="*50)
        print("1. Статистика за сегодня")
        print("2. Статистика за последние 7 дней")
        print("3. Статистика за месяц")
        print("4. Топ-10 клиентов")
        print("5. Средний чек")
        print("6. Статистика по статусам")
        print("0. Назад")
        print("="*50)
        
        choice = input("\nВыберите (0-6): ").strip()
        
        if choice == '1':
            stats_for_period(1)
        elif choice == '2':
            stats_for_period(7)
        elif choice == '3':
            stats_for_period(30)
        elif choice == '4':
            top_clients()
        elif choice == '5':
            average_check()
        elif choice == '6':
            status_statistics()
        elif choice == '0':
            break

def stats_for_period(days):
    """Статистика за период"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    date_from = (datetime.now() - timedelta(days=days-1)).date().isoformat()
    
    cursor.execute("""
        SELECT 
            COUNT(*) as total_orders,
            SUM(total) as total_sum,
            AVG(total) as avg_check,
            MIN(total) as min_check,
            MAX(total) as max_check
        FROM orders 
        WHERE DATE(created_at) >= ?
    """, (date_from,))
    
    stats = cursor.fetchone()
    
    period_name = {1: "сегодня", 7: "последние 7 дней", 30: "последние 30 дней"}
    
    print(f"\n📊 Статистика за {period_name.get(days, f'{days} дней')}:")
    print("="*50)
    print(f"Всего заказов: {stats[0] or 0}")
    print(f"Общая сумма: {stats[1] or 0}₸")
    print(f"Средний чек: {int(stats[2]) if stats[2] else 0}₸")
    print(f"Минимальный чек: {stats[3] or 0}₸")
    print(f"Максимальный чек: {stats[4] or 0}₸")
    print("="*50)
    
    conn.close()

def top_clients():
    """Топ клиентов по количеству заказов"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            client_name,
            room,
            COUNT(*) as order_count,
            SUM(total) as total_spent
        FROM orders
        GROUP BY client_name, room
        ORDER BY order_count DESC, total_spent DESC
        LIMIT 10
    """)
    
    clients = cursor.fetchall()
    
    print("\n🏆 ТОП-10 КЛИЕНТОВ:")
    print("="*70)
    print("Место | Клиент         | Комната | Заказов | Потрачено")
    print("="*70)
    
    for i, row in enumerate(clients, 1):
        print(f"{i:<5} | {row[0]:<14} | {row[1]:<7} | {row[2]:<7} | {row[3]}₸")
    
    print("="*70 + "\n")
    conn.close()

def average_check():
    """Средний чек"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Общий средний чек
    cursor.execute("SELECT AVG(total) FROM orders")
    avg_all = cursor.fetchone()[0]
    
    # Средний чек за последние 7 дней
    date_from = (datetime.now() - timedelta(days=6)).date().isoformat()
    cursor.execute("SELECT AVG(total) FROM orders WHERE DATE(created_at) >= ?", (date_from,))
    avg_week = cursor.fetchone()[0]
    
    # Средний чек за сегодня
    today = datetime.now().date().isoformat()
    cursor.execute("SELECT AVG(total) FROM orders WHERE DATE(created_at) = ?", (today,))
    avg_today = cursor.fetchone()[0]
    
    print("\n💰 СРЕДНИЙ ЧЕК:")
    print("="*50)
    print(f"За все время: {int(avg_all) if avg_all else 0}₸")
    print(f"За последние 7 дней: {int(avg_week) if avg_week else 0}₸")
    print(f"За сегодня: {int(avg_today) if avg_today else 0}₸")
    print("="*50 + "\n")
    
    conn.close()

def status_statistics():
    """Статистика по статусам"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            status,
            COUNT(*) as count,
            SUM(total) as total_sum
        FROM orders
        GROUP BY status
        ORDER BY count DESC
    """)
    
    statuses = cursor.fetchall()
    
    print("\n📋 СТАТИСТИКА ПО СТАТУСАМ:")
    print("="*60)
    print("Статус      | Количество | Сумма")
    print("="*60)
    
    for row in statuses:
        print(f"{row[0]:<11} | {row[1]:<10} | {row[2]}₸")
    
    print("="*60 + "\n")
    conn.close()

def cleanup_old_orders():
    """Очистка старых заказов"""
    print("\n⚠️  ОЧИСТКА СТАРЫХ ЗАКАЗОВ")
    print("="*50)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Показать сколько будет удалено
    cursor.execute("""
        SELECT COUNT(*), SUM(total) 
        FROM orders 
        WHERE created_at < datetime('now', '-30 days')
    """)
    count, total = cursor.fetchone()
    
    if count == 0:
        print("✅ Нет заказов старше 30 дней")
        conn.close()
        return
    
    print(f"Будет удалено заказов: {count}")
    print(f"На общую сумму: {total or 0}₸")
    
    confirm = input("\nПродолжить удаление? (yes/no): ").strip().lower()
    
    if confirm == 'yes':
        cursor.execute("DELETE FROM orders WHERE created_at < datetime('now', '-30 days')")
        conn.commit()
        print(f"✅ Удалено {count} заказов")
    else:
        print("❌ Отмена")
    
    conn.close()

def main():
    while True:
        print("\n" + "="*50)
        print("  РЕДАКТОР ЗАКАЗОВ - Пеликан Алаколь")
        print("="*50)
        print("1. Показать заказы")
        print("2. Посмотреть заказ")
        print("3. Редактировать заказ")
        print("4. Удалить заказ")
        print("5. Статистика и аналитика")
        print("6. Очистка старых заказов (>30 дней)")
        print("0. Выход")
        print("="*50)
        
        choice = input("\nВыберите действие (0-6): ").strip()
        
        if choice == '1':
            print("\nФильтр:")
            print("1. Все заказы (последние 50)")
            print("2. Активные заказы (не выданные)")
            print("3. Заказы за сегодня")
            filter_choice = input("Выберите (1-3): ").strip()
            filters = {'1': 'all', '2': 'active', '3': 'today'}
            show_orders(filters.get(filter_choice, 'all'))
        
        elif choice == '2':
            order_id = input("ID заказа: ").strip()
            view_order(order_id)
        
        elif choice == '3':
            order_id = input("ID заказа для редактирования: ").strip()
            edit_order(order_id)
        
        elif choice == '4':
            order_id = input("ID заказа для удаления: ").strip()
            delete_order(order_id)
        
        elif choice == '5':
            show_statistics()
        
        elif choice == '6':
            cleanup_old_orders()
        
        elif choice == '0':
            print("👋 До свидания!")
            sys.exit(0)
        
        else:
            print("❌ Неверный выбор")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 До свидания!")
        sys.exit(0)
