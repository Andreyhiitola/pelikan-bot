-- ============================================================================
-- Миграция БД: добавление полей для контактов клиентов
-- ============================================================================

-- 1. Добавляем поля контактов в таблицу orders
ALTER TABLE orders ADD COLUMN user_phone TEXT;
ALTER TABLE orders ADD COLUMN user_contact_shared INTEGER DEFAULT 0;

-- 2. Добавляем поля контактов в таблицу reviews  
ALTER TABLE reviews ADD COLUMN user_phone TEXT;
ALTER TABLE reviews ADD COLUMN user_contact_shared INTEGER DEFAULT 0;

-- 3. Проверяем что поля scanned_room_number уже есть (добавлены ранее)
-- Если нет - раскомментируйте эти строки:
-- ALTER TABLE orders ADD COLUMN scanned_room_number TEXT;
-- ALTER TABLE reviews ADD COLUMN scanned_room_number TEXT;

-- ============================================================================
-- Создание индексов для быстрого поиска по номерам комнат
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_orders_scanned_room ON orders(scanned_room_number);
CREATE INDEX IF NOT EXISTS idx_reviews_scanned_room ON reviews(scanned_room_number);
CREATE INDEX IF NOT EXISTS idx_reviews_status ON reviews(status);
CREATE INDEX IF NOT EXISTS idx_reviews_created_at ON reviews(created_at);

-- ============================================================================
-- Проверка уникальности QR кодов по номерам
-- ============================================================================

-- Эта таблица хранит информацию о QR кодах для каждого номера
CREATE TABLE IF NOT EXISTS qr_codes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_number TEXT UNIQUE NOT NULL,
    qr_code_url TEXT NOT NULL,
    deep_link TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    scans_count INTEGER DEFAULT 0,
    last_scanned_at TIMESTAMP
);

-- Индекс для быстрого поиска QR по номеру комнаты
CREATE INDEX IF NOT EXISTS idx_qr_room_number ON qr_codes(room_number);

-- ============================================================================
-- Статистика сканирований QR кодов
-- ============================================================================

CREATE TABLE IF NOT EXISTS qr_scans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_number TEXT NOT NULL,
    telegram_user_id INTEGER NOT NULL,
    telegram_username TEXT,
    action_type TEXT,  -- 'order' или 'review'
    scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_qr_scans_room ON qr_scans(room_number);
CREATE INDEX IF NOT EXISTS idx_qr_scans_user ON qr_scans(telegram_user_id);
CREATE INDEX IF NOT EXISTS idx_qr_scans_date ON qr_scans(scanned_at);
