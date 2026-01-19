# 📊 SQLite - Шпаргалка по работе с отзывами

## 📂 Расположение базы данных

| Место | Путь |
|-------|------|
| **На VPS (хост)** | `/root/pelikan-bot/data/orders.db` |
| В Docker контейнере | `/app/data/orders.db` |
| Volume | `./data:/app/data` |

**Важно:** Файл один и тот же благодаря volume! Изменения на хосте сразу видны в контейнере.

---

## 🚀 Быстрый старт

### Установка sqlite3 (один раз)
```bash
ssh root@85.192.40.138
apt update && apt install -y sqlite3
```

### Вход в базу данных
```bash
# Способ 1: из директории data
cd ~/pelikan-bot/data
sqlite3 orders.db

# Способ 2: полный путь
sqlite3 ~/pelikan-bot/data/orders.db

# Способ 3: через Docker (не рекомендуется)
docker exec -it bot sqlite3 /app/data/orders.db
```

### Выход из SQLite
```sql
.exit
```
или `Ctrl+D`

---

## 📋 Структура таблицы reviews

```sql
CREATE TABLE reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_user_id INTEGER NOT NULL,
    telegram_username TEXT,
    guest_name TEXT NOT NULL,          -- Имя гостя
    room_number TEXT,                   -- Номер комнаты
    
    -- Оценки 1-10
    cleanliness INTEGER,                -- Чистота
    comfort INTEGER,                    -- Комфорт
    location INTEGER,                   -- Расположение
    facilities INTEGER,                 -- Удобства
    staff INTEGER,                      -- Персонал
    value_for_money INTEGER,            -- Цена/качество
    
    -- Текстовые поля
    pros TEXT,                          -- Плюсы
    cons TEXT,                          -- Минусы
    comment TEXT,                       -- Комментарий
    
    -- Модерация
    status TEXT DEFAULT 'pending',      -- pending, approved, rejected
    is_published INTEGER DEFAULT 0,     -- 0 = не опубликован, 1 = опубликован
    
    -- Мета-данные
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    moderated_at TIMESTAMP,
    moderated_by INTEGER,
    display_name TEXT
);
```

---

## 👀 Просмотр данных

### Базовые команды SQLite
```sql
-- Показать все таблицы
.tables

-- Показать структуру таблицы
.schema reviews

-- Включить красивый вывод
.mode column
.headers on
.width auto
```

### Просмотр отзывов

```sql
-- Все отзывы (кратко)
SELECT id, guest_name, room_number, status, is_published, created_at
FROM reviews 
ORDER BY created_at DESC;

-- Полная информация об отзыве
SELECT * FROM reviews WHERE id = 1;

-- Только опубликованные отзывы
SELECT id, guest_name, 
       ROUND((cleanliness + comfort + location + facilities + staff + value_for_money) / 6.0, 1) as avg_score
FROM reviews 
WHERE status = 'approved' AND is_published = 1;

-- Отзывы на модерации
SELECT id, guest_name, room_number, created_at
FROM reviews 
WHERE status = 'pending'
ORDER BY created_at DESC;

-- Последние 10 отзывов
SELECT id, guest_name, status, is_published, created_at 
FROM reviews 
ORDER BY created_at DESC 
LIMIT 10;
```

---

## ✅ Модерация отзывов

### Одобрение и публикация

```sql
-- Одобрить И опубликовать отзыв #3
UPDATE reviews 
SET status = 'approved', 
    is_published = 1, 
    moderated_at = datetime('now')
WHERE id = 3;

-- Одобрить БЕЗ публикации (отложенная публикация)
UPDATE reviews 
SET status = 'approved', 
    is_published = 0, 
    moderated_at = datetime('now')
WHERE id = 4;

-- Опубликовать уже одобренный отзыв
UPDATE reviews 
SET is_published = 1 
WHERE id = 5;

-- Снять с публикации (скрыть)
UPDATE reviews 
SET is_published = 0 
WHERE id = 6;

-- Отклонить отзыв
UPDATE reviews 
SET status = 'rejected', 
    is_published = 0,
    moderated_at = datetime('now')
WHERE id = 7;
```

---

## ✏️ Редактирование контента

### Изменение текстовых полей

```sql
-- Изменить имя гостя
UPDATE reviews 
SET guest_name = 'Андрей Петров' 
WHERE id = 1;

-- Изменить номер комнаты
UPDATE reviews 
SET room_number = 'Люкс 205' 
WHERE id = 1;

-- Изменить плюсы
UPDATE reviews 
SET pros = 'Отличный сервис, чистота, вид на озеро' 
WHERE id = 1;

-- Изменить минусы
UPDATE reviews 
SET cons = 'Далеко от аэропорта' 
WHERE id = 1;

-- Изменить комментарий
UPDATE reviews 
SET comment = 'Прекрасный отдых! Обязательно вернёмся!' 
WHERE id = 1;
```

### Изменение оценок

```sql
-- Изменить одну оценку
UPDATE reviews 
SET staff = 10 
WHERE id = 1;

-- Изменить несколько оценок
UPDATE reviews 
SET cleanliness = 10,
    comfort = 9,
    staff = 10
WHERE id = 1;

-- Установить все оценки в 10
UPDATE reviews 
SET cleanliness = 10,
    comfort = 10,
    location = 10,
    facilities = 10,
    staff = 10,
    value_for_money = 10
WHERE id = 1;
```

### Комплексное редактирование

```sql
-- Изменить несколько полей одновременно
UPDATE reviews 
SET guest_name = 'Мария Иванова', 
    room_number = 'Стандарт',
    pros = 'Чистота, персонал, завтраки', 
    staff = 10,
    value_for_money = 9
WHERE id = 1;
```

---

## 🗑️ Удаление

```sql
-- Удалить конкретный отзыв
DELETE FROM reviews WHERE id = 8;

-- Удалить все отклонённые отзывы
DELETE FROM reviews WHERE status = 'rejected';

-- Удалить отзывы старше 1 года
DELETE FROM reviews 
WHERE created_at < datetime('now', '-1 year');

-- Удалить неопубликованные отзывы старше 30 дней
DELETE FROM reviews 
WHERE is_published = 0 
AND created_at < datetime('now', '-30 days');
```

⚠️ **Внимание:** Удаление необратимо! Сделайте бэкап перед массовым удалением.

---

## 📊 Массовые операции

```sql
-- Опубликовать ВСЕ одобренные отзывы
UPDATE reviews 
SET is_published = 1 
WHERE status = 'approved';

-- Снять ВСЕ отзывы с публикации
UPDATE reviews 
SET is_published = 0;

-- Одобрить все отзывы с рейтингом >= 8
UPDATE reviews 
SET status = 'approved'
WHERE (cleanliness + comfort + location + facilities + staff + value_for_money) / 6.0 >= 8
AND status = 'pending';

-- Отклонить все отзывы с рейтингом < 5
UPDATE reviews 
SET status = 'rejected', is_published = 0
WHERE (cleanliness + comfort + location + facilities + staff + value_for_money) / 6.0 < 5;
```

---

## 📈 Статистика и аналитика

### Общая статистика

```sql
-- Количество отзывов по статусам
SELECT 
    status,
    is_published,
    COUNT(*) as count
FROM reviews 
GROUP BY status, is_published;

-- Средний рейтинг всех опубликованных отзывов
SELECT 
    ROUND(AVG((cleanliness + comfort + location + facilities + staff + value_for_money) / 6.0), 2) as avg_rating,
    COUNT(*) as total_reviews
FROM reviews 
WHERE status = 'approved' AND is_published = 1;

-- Средние оценки по категориям
SELECT 
    ROUND(AVG(cleanliness), 2) as avg_cleanliness,
    ROUND(AVG(comfort), 2) as avg_comfort,
    ROUND(AVG(location), 2) as avg_location,
    ROUND(AVG(facilities), 2) as avg_facilities,
    ROUND(AVG(staff), 2) as avg_staff,
    ROUND(AVG(value_for_money), 2) as avg_value
FROM reviews 
WHERE status = 'approved' AND is_published = 1;
```

### Рейтинги и фильтрация

```sql
-- ТОП-10 лучших отзывов
SELECT 
    id, 
    guest_name, 
    room_number,
    ROUND((cleanliness + comfort + location + facilities + staff + value_for_money) / 6.0, 1) as avg_score
FROM reviews 
WHERE status = 'approved'
ORDER BY avg_score DESC 
LIMIT 10;

-- Отзывы с низким рейтингом (< 6)
SELECT 
    id, 
    guest_name, 
    room_number,
    ROUND((cleanliness + comfort + location + facilities + staff + value_for_money) / 6.0, 1) as avg_score,
    pros,
    cons
FROM reviews 
WHERE (cleanliness + comfort + location + facilities + staff + value_for_money) / 6.0 < 6
ORDER BY avg_score ASC;

-- Отзывы с высоким рейтингом (>= 9)
SELECT 
    id, 
    guest_name,
    ROUND((cleanliness + comfort + location + facilities + staff + value_for_money) / 6.0, 1) as avg_score
FROM reviews 
WHERE (cleanliness + comfort + location + facilities + staff + value_for_money) / 6.0 >= 9;
```

### Статистика по периодам

```sql
-- Отзывы за последние 7 дней
SELECT COUNT(*) as total, 
       AVG((cleanliness + comfort + location + facilities + staff + value_for_money) / 6.0) as avg_rating
FROM reviews 
WHERE created_at >= datetime('now', '-7 days');

-- Отзывы за текущий месяц
SELECT COUNT(*) as total
FROM reviews 
WHERE strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now');

-- Статистика по месяцам
SELECT 
    strftime('%Y-%m', created_at) as month,
    COUNT(*) as total,
    ROUND(AVG((cleanliness + comfort + location + facilities + staff + value_for_money) / 6.0), 2) as avg_rating
FROM reviews 
GROUP BY month
ORDER BY month DESC;
```

---

## 🔍 Поиск и фильтрация

```sql
-- Найти отзывы по имени гостя
SELECT * FROM reviews 
WHERE guest_name LIKE '%Андрей%';

-- Найти отзывы по номеру комнаты
SELECT * FROM reviews 
WHERE room_number = 'Люкс';

-- Найти отзывы по ключевому слову в комментарии
SELECT id, guest_name, comment 
FROM reviews 
WHERE comment LIKE '%пляж%';

-- Найти отзывы с упоминанием в плюсах
SELECT id, guest_name, pros 
FROM reviews 
WHERE pros LIKE '%персонал%';

-- Найти отзывы от конкретного Telegram пользователя
SELECT * FROM reviews 
WHERE telegram_user_id = 31310268;
```

---

## 📤 Экспорт данных

### Экспорт в CSV

```sql
.mode csv
.headers on
.output /root/pelikan-bot/data/reviews_export.csv
SELECT * FROM reviews;
.output stdout
```

### Экспорт в JSON

```sql
.mode json
.output /root/pelikan-bot/data/reviews_export.json
SELECT * FROM reviews WHERE is_published = 1;
.output stdout
```

### Экспорт опубликованных отзывов для сайта

```sql
.mode json
.output /root/pelikan-bot/data/published_reviews.json
SELECT 
    guest_name as name,
    room_number,
    cleanliness,
    comfort,
    location,
    facilities,
    staff,
    value_for_money,
    ROUND((cleanliness + comfort + location + facilities + staff + value_for_money) / 6.0, 1) as avg_score,
    pros,
    cons,
    comment,
    created_at as date
FROM reviews 
WHERE status = 'approved' AND is_published = 1
ORDER BY created_at DESC;
.output stdout
```

---

## 🔧 Служебные команды

### Настройки отображения

```sql
-- Режим колонок (красиво)
.mode column
.headers on
.width auto

-- Режим списка
.mode list

-- Режим табуляции
.mode tabs

-- Режим HTML
.mode html

-- Показать текущие настройки
.show
```

### Информация о базе

```sql
-- Размер базы данных
.dbinfo

-- Показать индексы
.indexes

-- Показать SQL создания таблицы
.schema reviews

-- Вывести время выполнения запросов
.timer on
```

---

## 💾 Бэкап и восстановление

### Создание бэкапа

```bash
# Способ 1: Простое копирование файла
cp ~/pelikan-bot/data/orders.db ~/pelikan-bot/data/orders_backup_$(date +%Y%m%d_%H%M%S).db

# Способ 2: Через SQLite
sqlite3 ~/pelikan-bot/data/orders.db ".backup ~/pelikan-bot/data/orders_backup.db"

# Способ 3: Dump в SQL
sqlite3 ~/pelikan-bot/data/orders.db ".dump" > ~/pelikan-bot/data/orders_dump.sql
```

### Восстановление из бэкапа

```bash
# Способ 1: Заменить файл
cp ~/pelikan-bot/data/orders_backup.db ~/pelikan-bot/data/orders.db

# Способ 2: Восстановить из dump
sqlite3 ~/pelikan-bot/data/orders.db < ~/pelikan-bot/data/orders_dump.sql

# Перезапустить бота
docker-compose restart bot
```

---

## 🔐 Безопасность

### ВАЖНО: Всегда делайте бэкап перед изменениями!

```bash
# Быстрый бэкап перед изменениями
cp ~/pelikan-bot/data/orders.db ~/pelikan-bot/data/orders.db.backup
```

### После прямого редактирования БД

```bash
# Перезапуск НЕ обязателен (volume синхронизирован)
# Но для надёжности можно перезапустить
docker-compose restart bot

# Проверить логи
docker logs -f bot
```

---

## 🚀 Однострочные команды (без входа в SQLite)

```bash
# Посмотреть все отзывы
sqlite3 ~/pelikan-bot/data/orders.db "SELECT id, guest_name, status, is_published FROM reviews;"

# Опубликовать отзыв #5
sqlite3 ~/pelikan-bot/data/orders.db "UPDATE reviews SET is_published=1, status='approved' WHERE id=5;"

# Снять с публикации отзыв #3
sqlite3 ~/pelikan-bot/data/orders.db "UPDATE reviews SET is_published=0 WHERE id=3;"

# Удалить отзыв #7
sqlite3 ~/pelikan-bot/data/orders.db "DELETE FROM reviews WHERE id=7;"

# Посмотреть статистику
sqlite3 ~/pelikan-bot/data/orders.db "SELECT status, COUNT(*) FROM reviews GROUP BY status;"

# Экспорт в CSV
sqlite3 -header -csv ~/pelikan-bot/data/orders.db "SELECT * FROM reviews;" > ~/reviews.csv
```

---

## 📋 Быстрая справка по командам

| Задача | Команда |
|--------|---------|
| Вход в БД | `sqlite3 ~/pelikan-bot/data/orders.db` |
| Выход | `.exit` или `Ctrl+D` |
| Показать таблицы | `.tables` |
| Структура таблицы | `.schema reviews` |
| Все отзывы | `SELECT * FROM reviews;` |
| Опубликовать | `UPDATE reviews SET is_published=1 WHERE id=5;` |
| Удалить | `DELETE FROM reviews WHERE id=7;` |
| Бэкап | `cp orders.db orders_backup.db` |
| Экспорт CSV | `.mode csv` → `.output file.csv` |

---

## 🎯 Типичные сценарии

### Сценарий 1: Массовая модерация

```sql
-- 1. Посмотреть отзывы на модерации
SELECT id, guest_name, 
    ROUND((cleanliness + comfort + location + facilities + staff + value_for_money) / 6.0, 1) as avg
FROM reviews 
WHERE status = 'pending';

-- 2. Одобрить все с рейтингом >= 7
UPDATE reviews 
SET status = 'approved', is_published = 1
WHERE status = 'pending' 
AND (cleanliness + comfort + location + facilities + staff + value_for_money) / 6.0 >= 7;

-- 3. Отклонить все с рейтингом < 5
UPDATE reviews 
SET status = 'rejected'
WHERE status = 'pending' 
AND (cleanliness + comfort + location + facilities + staff + value_for_money) / 6.0 < 5;
```

### Сценарий 2: Исправление ошибок

```sql
-- 1. Найти отзыв с ошибкой
SELECT id, guest_name, comment FROM reviews WHERE id = 5;

-- 2. Исправить
UPDATE reviews 
SET guest_name = 'Правильное Имя',
    comment = 'Исправленный комментарий'
WHERE id = 5;

-- 3. Проверить
SELECT * FROM reviews WHERE id = 5;
```

### Сценарий 3: Подготовка к публикации

```sql
-- 1. Посмотреть одобренные, но не опубликованные
SELECT id, guest_name, room_number,
    ROUND((cleanliness + comfort + location + facilities + staff + value_for_money) / 6.0, 1) as avg
FROM reviews 
WHERE status = 'approved' AND is_published = 0;

-- 2. Опубликовать выбранные
UPDATE reviews SET is_published = 1 WHERE id IN (3, 5, 7, 9);

-- 3. Проверить результат
SELECT COUNT(*) FROM reviews WHERE is_published = 1;
```

---

## 🆘 Решение проблем

### База заблокирована
```bash
# Проверить процессы
ps aux | grep sqlite

# Перезапустить бота
docker-compose restart bot
```

### Ошибка "database is locked"
```bash
# Подождать или перезапустить
docker-compose restart bot
```

### База повреждена
```bash
# Восстановить из бэкапа
cp ~/pelikan-bot/data/orders_backup.db ~/pelikan-bot/data/orders.db
docker-compose restart bot
```

---

## 📚 Полезные ссылки

- [SQLite Official Documentation](https://www.sqlite.org/docs.html)
- [SQLite Commands](https://www.sqlite.org/cli.html)
- [SQL Tutorial](https://www.w3schools.com/sql/)

---

**Последнее обновление:** 19 января 2026  
**Версия:** 1.0  
**Проект:** Pelikan Alakol Hotel Bot
