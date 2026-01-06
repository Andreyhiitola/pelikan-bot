# Полезные SQL команды для управления базой данных заказов

## Просмотр данных

### Все заказы
```sql
SELECT * FROM orders;
```

### Последние 10 заказов
```sql
SELECT * FROM orders ORDER BY created_at DESC LIMIT 10;
```

### Активные заказы (не выданные)
```sql
SELECT * FROM orders WHERE status != 'выдан' ORDER BY created_at DESC;
```

### Заказы по статусу
```sql
SELECT * FROM orders WHERE status = 'готов';
```

### Заказы конкретного клиента
```sql
SELECT * FROM orders WHERE client_name LIKE '%Иван%';
```

### Заказы из конкретной комнаты
```sql
SELECT * FROM orders WHERE room = '205';
```

## Статистика

### Количество заказов по статусам
```sql
SELECT status, COUNT(*) as count 
FROM orders 
GROUP BY status;
```

### Общая сумма всех заказов
```sql
SELECT SUM(total) as total_sum FROM orders;
```

### Сумма заказов за сегодня
```sql
SELECT SUM(total) as today_sum 
FROM orders 
WHERE DATE(created_at) = DATE('now');
```

### Средний чек
```sql
SELECT AVG(total) as average_order FROM orders;
```

### Самые популярные блюда (требует парсинга JSON)
```sql
SELECT items, COUNT(*) as frequency 
FROM orders 
GROUP BY items 
ORDER BY frequency DESC 
LIMIT 10;
```

### Заказы за последние 7 дней
```sql
SELECT DATE(created_at) as date, COUNT(*) as orders, SUM(total) as revenue
FROM orders 
WHERE created_at >= DATE('now', '-7 days')
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

## Обновление данных

### Изменить статус заказа
```sql
UPDATE orders 
SET status = 'готов' 
WHERE order_id = '1736172000';
```

### Массовое обновление старых заказов
```sql
UPDATE orders 
SET status = 'выдан' 
WHERE status = 'готов' 
AND created_at < DATETIME('now', '-2 hours');
```

## Удаление данных

### Удалить конкретный заказ
```sql
DELETE FROM orders WHERE order_id = '1736172000';
```

### Удалить тестовые заказы
```sql
DELETE FROM orders WHERE order_id LIKE 'test_%';
```

### Удалить старые выданные заказы (старше 30 дней)
```sql
DELETE FROM orders 
WHERE status = 'выдан' 
AND created_at < DATETIME('now', '-30 days');
```

### Очистить всю таблицу (осторожно!)
```sql
DELETE FROM orders;
```

## Резервное копирование

### Создать резервную копию
```bash
sqlite3 orders.db .dump > backup_$(date +%Y%m%d).sql
```

### Восстановить из резервной копии
```bash
sqlite3 orders_new.db < backup_20260106.sql
```

### Экспорт в CSV
```bash
sqlite3 -header -csv orders.db "SELECT * FROM orders;" > orders.csv
```

## Оптимизация

### Пересоздать индексы
```sql
REINDEX;
```

### Очистить неиспользуемое пространство
```sql
VACUUM;
```

### Анализ для оптимизации запросов
```sql
ANALYZE;
```

## Примеры использования в терминале

### Быстрый просмотр
```bash
sqlite3 orders.db "SELECT order_id, client_name, room, status, total FROM orders ORDER BY created_at DESC LIMIT 10;"
```

### Интерактивный режим
```bash
sqlite3 orders.db
sqlite> .headers on
sqlite> .mode column
sqlite> SELECT * FROM orders LIMIT 5;
sqlite> .quit
```

### Поиск заказа
```bash
sqlite3 orders.db "SELECT * FROM orders WHERE order_id = '1736172000';"
```

### Статистика за сегодня
```bash
sqlite3 orders.db "SELECT COUNT(*) as orders, SUM(total) as revenue FROM orders WHERE DATE(created_at) = DATE('now');"
```

## Полезные настройки для интерактивного режима

```sql
.headers on          -- Показывать названия колонок
.mode column         -- Колоночный вывод
.width 15 20 10 10   -- Ширина колонок
.timer on            -- Показывать время выполнения
```

## Создание отчётов

### Ежедневный отчёт
```bash
sqlite3 -header -column orders.db "
SELECT 
    DATE(created_at) as date,
    COUNT(*) as total_orders,
    SUM(total) as revenue,
    AVG(total) as avg_check,
    MIN(total) as min_check,
    MAX(total) as max_check
FROM orders 
WHERE created_at >= DATE('now', '-7 days')
GROUP BY DATE(created_at)
ORDER BY date DESC;
" > daily_report.txt
```

### Отчёт по комнатам
```bash
sqlite3 -header -column orders.db "
SELECT 
    room,
    COUNT(*) as orders_count,
    SUM(total) as total_spent
FROM orders 
GROUP BY room 
ORDER BY orders_count DESC 
LIMIT 20;
" > rooms_report.txt
```
