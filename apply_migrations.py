#!/usr/bin/env python3
"""
Скрипт для применения миграций к базе данных
Запуск: python apply_migrations.py
"""

import aiosqlite
import asyncio
import os

DB_FILE = os.getenv("DB_FILE", "orders.db")

async def apply_migrations():
    """Применяет все миграции к базе данных"""
    
    print(f"🔧 Начинаю миграцию базы данных: {DB_FILE}")
    
    async with aiosqlite.connect(DB_FILE) as db:
        
        # 1. Добавляем поля контактов в orders
        print("\n📝 Миграция 1: Добавление полей контактов в таблицу orders...")
        try:
            await db.execute("ALTER TABLE orders ADD COLUMN user_phone TEXT")
            print("  ✅ Добавлено поле user_phone")
        except Exception as e:
            print(f"  ⚠️  user_phone уже существует или ошибка: {e}")
        
        try:
            await db.execute("ALTER TABLE orders ADD COLUMN user_contact_shared INTEGER DEFAULT 0")
            print("  ✅ Добавлено поле user_contact_shared")
        except Exception as e:
            print(f"  ⚠️  user_contact_shared уже существует или ошибка: {e}")
        
        # 2. Добавляем поля контактов в reviews
        print("\n📝 Миграция 2: Добавление полей контактов в таблицу reviews...")
        try:
            await db.execute("ALTER TABLE reviews ADD COLUMN user_phone TEXT")
            print("  ✅ Добавлено поле user_phone")
        except Exception as e:
            print(f"  ⚠️  user_phone уже существует или ошибка: {e}")
        
        try:
            await db.execute("ALTER TABLE reviews ADD COLUMN user_contact_shared INTEGER DEFAULT 0")
            print("  ✅ Добавлено поле user_contact_shared")
        except Exception as e:
            print(f"  ⚠️  user_contact_shared уже существует или ошибка: {e}")
        
        # 3. Проверяем поля scanned_room_number
        print("\n📝 Миграция 3: Проверка полей scanned_room_number...")
        try:
            await db.execute("ALTER TABLE orders ADD COLUMN scanned_room_number TEXT")
            print("  ✅ Добавлено поле scanned_room_number в orders")
        except Exception as e:
            print(f"  ⚠️  scanned_room_number в orders уже существует")
        
        try:
            await db.execute("ALTER TABLE reviews ADD COLUMN scanned_room_number TEXT")
            print("  ✅ Добавлено поле scanned_room_number в reviews")
        except Exception as e:
            print(f"  ⚠️  scanned_room_number в reviews уже существует")
        
        # 4. Создаем таблицу qr_codes
        print("\n📝 Миграция 4: Создание таблицы qr_codes...")
        await db.execute("""
            CREATE TABLE IF NOT EXISTS qr_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_number TEXT UNIQUE NOT NULL,
                qr_code_url TEXT NOT NULL,
                deep_link TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                scans_count INTEGER DEFAULT 0,
                last_scanned_at TIMESTAMP
            )
        """)
        print("  ✅ Таблица qr_codes создана или уже существует")
        
        # 5. Создаем таблицу qr_scans
        print("\n📝 Миграция 5: Создание таблицы qr_scans...")
        await db.execute("""
            CREATE TABLE IF NOT EXISTS qr_scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_number TEXT NOT NULL,
                telegram_user_id INTEGER NOT NULL,
                telegram_username TEXT,
                action_type TEXT,
                scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("  ✅ Таблица qr_scans создана или уже существует")
        
        # 6. Создаем индексы
        print("\n📝 Миграция 6: Создание индексов...")
        indices = [
            ("idx_orders_scanned_room", "orders", "scanned_room_number"),
            ("idx_reviews_scanned_room", "reviews", "scanned_room_number"),
            ("idx_reviews_status", "reviews", "status"),
            ("idx_reviews_created_at", "reviews", "created_at"),
            ("idx_qr_room_number", "qr_codes", "room_number"),
            ("idx_qr_scans_room", "qr_scans", "room_number"),
            ("idx_qr_scans_user", "qr_scans", "telegram_user_id"),
            ("idx_qr_scans_date", "qr_scans", "scanned_at"),
        ]
        
        for idx_name, table, column in indices:
            try:
                await db.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table}({column})")
                print(f"  ✅ Индекс {idx_name} создан")
            except Exception as e:
                print(f"  ⚠️  Ошибка создания индекса {idx_name}: {e}")
        
        await db.commit()
        
        # 7. Проверяем структуру таблиц
        print("\n📊 Проверка структуры таблиц:")
        
        cursor = await db.execute("PRAGMA table_info(orders)")
        orders_columns = await cursor.fetchall()
        print(f"\n  📋 Таблица orders ({len(orders_columns)} колонок):")
        for col in orders_columns:
            print(f"    - {col[1]} ({col[2]})")
        
        cursor = await db.execute("PRAGMA table_info(reviews)")
        reviews_columns = await cursor.fetchall()
        print(f"\n  📋 Таблица reviews ({len(reviews_columns)} колонок):")
        for col in reviews_columns:
            print(f"    - {col[1]} ({col[2]})")
        
        cursor = await db.execute("PRAGMA table_info(qr_codes)")
        qr_columns = await cursor.fetchall()
        print(f"\n  📋 Таблица qr_codes ({len(qr_columns)} колонок):")
        for col in qr_columns:
            print(f"    - {col[1]} ({col[2]})")
        
        # 8. Проверяем количество записей
        cursor = await db.execute("SELECT COUNT(*) FROM orders")
        orders_count = (await cursor.fetchone())[0]
        
        cursor = await db.execute("SELECT COUNT(*) FROM reviews")
        reviews_count = (await cursor.fetchone())[0]
        
        cursor = await db.execute("SELECT COUNT(*) FROM qr_codes")
        qr_count = (await cursor.fetchone())[0]
        
        print(f"\n📈 Статистика:")
        print(f"  🛎️  Заказов: {orders_count}")
        print(f"  ⭐ Отзывов: {reviews_count}")
        print(f"  🔲 QR кодов: {qr_count}")
    
    print("\n✅ Миграция завершена успешно!")

if __name__ == "__main__":
    asyncio.run(apply_migrations())
