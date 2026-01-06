#!/bin/bash
# =============================================================================
# Скрипт тестирования системы заказов "Пеликан Алаколь"
# =============================================================================

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=========================================="
echo "  Тестирование системы заказов"
echo "=========================================="
echo ""

# Проверка сервисов
echo "1. Проверка статуса сервиса..."
echo ""

if systemctl is-active --quiet pelikan-bot; then
    echo -e "${GREEN}✓${NC} pelikan-bot.service работает (polling + webhook)"
else
    echo -e "${RED}✗${NC} pelikan-bot.service не запущен"
fi

echo ""

# Проверка health endpoint
echo "2. Проверка webhook endpoint..."
HEALTH_RESPONSE=$(curl -s http://localhost:8080/health)

if echo "$HEALTH_RESPONSE" | grep -q "ok"; then
    echo -e "${GREEN}✓${NC} Webhook сервер отвечает"
    echo "   $HEALTH_RESPONSE"
else
    echo -e "${RED}✗${NC} Webhook сервер не отвечает"
fi

echo ""

# Проверка БД
echo "3. Проверка базы данных..."
DB_FILE="orders.db"

if [ -f "$DB_FILE" ]; then
    echo -e "${GREEN}✓${NC} База данных существует"
    
    # Проверяем количество заказов
    ORDER_COUNT=$(sqlite3 "$DB_FILE" "SELECT COUNT(*) FROM orders;" 2>/dev/null)
    if [ $? -eq 0 ]; then
        echo "   Всего заказов: $ORDER_COUNT"
    else
        echo -e "${YELLOW}⚠${NC} Не удалось прочитать БД"
    fi
else
    echo -e "${YELLOW}⚠${NC} База данных не найдена (создастся автоматически)"
fi

echo ""

# Тест отправки заказа
echo "4. Тест отправки заказа..."
read -p "Отправить тестовый заказ? (y/n): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    TEST_ORDER_ID="test_$(date +%s)"
    
    RESPONSE=$(curl -s -X POST http://localhost:8080/api/order \
        -H "Content-Type: application/json" \
        -d "{
            \"orderId\": \"$TEST_ORDER_ID\",
            \"name\": \"Тестовый клиент\",
            \"room\": \"999\",
            \"telegram\": \"testuser\",
            \"items\": [
                {\"name\": \"Тестовое блюдо\", \"price\": 1000, \"quantity\": 1}
            ],
            \"total\": 1000,
            \"timestamp\": \"$(date '+%Y-%m-%d %H:%M')\"
        }")
    
    if echo "$RESPONSE" | grep -q "ok"; then
        echo -e "${GREEN}✓${NC} Тестовый заказ отправлен успешно"
        echo "   Order ID: $TEST_ORDER_ID"
        echo "   Response: $RESPONSE"
        
        # Проверяем, что заказ добавился в БД
        sleep 2
        if sqlite3 "$DB_FILE" "SELECT * FROM orders WHERE order_id='$TEST_ORDER_ID';" 2>/dev/null | grep -q "$TEST_ORDER_ID"; then
            echo -e "${GREEN}✓${NC} Заказ найден в базе данных"
        else
            echo -e "${RED}✗${NC} Заказ не найден в базе данных"
        fi
    else
        echo -e "${RED}✗${NC} Ошибка отправки тестового заказа"
        echo "   Response: $RESPONSE"
    fi
fi

echo ""

# Проверка логов
echo "5. Последние логи (10 строк)..."
echo ""
sudo journalctl -u pelikan-bot -n 10 --no-pager

echo ""
echo "=========================================="
echo "  Тестирование завершено"
echo "=========================================="
echo ""

echo "Полезные команды для дальнейшей диагностики:"
echo ""
echo "  Просмотр всех заказов в БД:"
echo "    sqlite3 orders.db 'SELECT * FROM orders;'"
echo ""
echo "  Очистка тестовых заказов:"
echo "    sqlite3 orders.db \"DELETE FROM orders WHERE order_id LIKE 'test_%';\""
echo ""
echo "  Живые логи:"
echo "    sudo journalctl -u pelikan-bot -f"
echo ""
