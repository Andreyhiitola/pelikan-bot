#!/bin/bash
# ==============================================================================
# setup_analytics_branch.sh - Создание ветки для модуля аналитики
# ==============================================================================

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🌿 Настройка ветки для модуля аналитики${NC}"
echo "=============================================="

# Проверка, что мы в Git-репозитории
if [ ! -d ".git" ]; then
    echo -e "${RED}❌ Ошибка: не в Git-репозитории. Запустите из директории pelikan-hotel-bot/${NC}"
    exit 1
fi

# Проверка текущего статуса
echo -e "${YELLOW}📋 Проверка текущего состояния...${NC}"
if ! git diff-index --quiet HEAD --; then
    echo -e "${YELLOW}⚠️  Есть незакоммиченные изменения${NC}"
    echo -e "${YELLOW}Хотите закоммитить их перед созданием новой ветки? (y/n)${NC}"
    read -r response
    if [[ "$response" == "y" ]]; then
        git add .
        echo -e "${YELLOW}Введите сообщение коммита:${NC}"
        read -r commit_msg
        git commit -m "$commit_msg"
        echo -e "${GREEN}✅ Изменения закоммичены${NC}"
    fi
fi

# Получаем текущую ветку
current_branch=$(git branch --show-current)
echo -e "${BLUE}📍 Текущая ветка: ${current_branch}${NC}"

# Создаем новую ветку
branch_name="feature/analytics"
echo -e "${YELLOW}🌿 Создание новой ветки: ${branch_name}${NC}"

if git show-ref --verify --quiet refs/heads/$branch_name; then
    echo -e "${YELLOW}⚠️  Ветка ${branch_name} уже существует${NC}"
    echo -e "${YELLOW}Переключиться на неё? (y/n)${NC}"
    read -r response
    if [[ "$response" == "y" ]]; then
        git checkout $branch_name
        echo -e "${GREEN}✅ Переключено на ${branch_name}${NC}"
    fi
else
    git checkout -b $branch_name
    echo -e "${GREEN}✅ Создана и активирована ветка ${branch_name}${NC}"
fi

# Проверяем наличие новых файлов
echo ""
echo -e "${YELLOW}📦 Проверка файлов модуля аналитики...${NC}"

required_files=(
    "analytics_handler.py"
    "analytics_commands.py"
)

missing_files=()
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -gt 0 ]; then
    echo -e "${RED}❌ Не найдены файлы:${NC}"
    for file in "${missing_files[@]}"; do
        echo "   - $file"
    done
    echo ""
    echo -e "${YELLOW}Скопируйте следующие файлы в текущую директорию:${NC}"
    echo "   - analytics_handler.py"
    echo "   - analytics_commands.py"
    echo "   - requirements.txt (обновленный)"
    echo "   - Dockerfile (обновленный)"
    echo ""
    echo -e "${YELLOW}После копирования запустите скрипт снова${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Все необходимые файлы найдены${NC}"

# Проверяем, обновлен ли bot.py
echo ""
echo -e "${YELLOW}🔍 Проверка интеграции в bot.py...${NC}"

if grep -q "from analytics_handler import setup_scheduler" bot.py && \
   grep -q "from analytics_commands import analytics_router" bot.py && \
   grep -q "dp.include_router(analytics_router)" bot.py; then
    echo -e "${GREEN}✅ bot.py уже обновлен${NC}"
else
    echo -e "${YELLOW}⚠️  bot.py требует обновления${NC}"
    echo ""
    echo -e "${YELLOW}Добавьте следующие строки в bot.py:${NC}"
    echo ""
    echo "# В импорты (начало файла):"
    echo "from analytics_handler import setup_scheduler"
    echo "from analytics_commands import analytics_router"
    echo ""
    echo "# После других роутеров:"
    echo "dp.include_router(analytics_router)"
    echo ""
    echo "# В функцию main() после await init_db():"
    echo "scheduler = setup_scheduler(bot)"
    echo "scheduler.start()"
    echo ""
    echo -e "${YELLOW}Откройте bot.py для редактирования? (y/n)${NC}"
    read -r response
    if [[ "$response" == "y" ]]; then
        ${EDITOR:-nano} bot.py
    fi
fi

# Проверяем .env
echo ""
echo -e "${YELLOW}🔍 Проверка .env...${NC}"

if [ ! -f ".env" ]; then
    echo -e "${RED}❌ Файл .env не найден${NC}"
    exit 1
fi

if grep -q "SMTP_USER" .env && grep -q "SMTP_PASSWORD" .env; then
    echo -e "${GREEN}✅ SMTP настройки найдены в .env${NC}"
else
    echo -e "${YELLOW}⚠️  SMTP настройки не найдены в .env${NC}"
    echo ""
    echo -e "${YELLOW}Добавьте в .env:${NC}"
    echo "SMTP_SERVER=smtp.mail.ru"
    echo "SMTP_PORT=587"
    echo "SMTP_USER=your_email@mail.ru"
    echo "SMTP_PASSWORD=пароль_приложения"
    echo "REPORT_EMAIL=regsk@mail.ru"
    echo ""
    echo -e "${YELLOW}Открыть .env для редактирования? (y/n)${NC}"
    read -r response
    if [[ "$response" == "y" ]]; then
        ${EDITOR:-nano} .env
    fi
fi

# Добавляем файлы в Git
echo ""
echo -e "${YELLOW}📝 Добавление файлов в Git...${NC}"

files_to_add=(
    "analytics_handler.py"
    "analytics_commands.py"
    "requirements.txt"
    "Dockerfile"
    "bot.py"
)

for file in "${files_to_add[@]}"; do
    if [ -f "$file" ]; then
        git add "$file"
        echo -e "${GREEN}✅ Добавлен: $file${NC}"
    fi
done

# Показываем статус
echo ""
echo -e "${YELLOW}📊 Статус Git:${NC}"
git status --short

# Предлагаем закоммитить
echo ""
echo -e "${YELLOW}💾 Закоммитить изменения? (y/n)${NC}"
read -r response
if [[ "$response" == "y" ]]; then
    git commit -m "feat: добавлен модуль аналитики отзывов

- Добавлен analytics_handler.py: сбор статистики, генерация графиков
- Добавлен analytics_commands.py: команды /analytics и /test_report
- Обновлен requirements.txt: matplotlib, numpy, apscheduler
- Обновлен Dockerfile: копирование новых модулов
- Обновлен bot.py: интеграция роутера и планировщика
- Ежедневные отчеты в 8:00 в Telegram и на email"
    
    echo -e "${GREEN}✅ Изменения закоммичены${NC}"
fi

# Финальная информация
echo ""
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Ветка ${branch_name} готова!${NC}"
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}📋 Следующие шаги:${NC}"
echo ""
echo "1️⃣  Протестируйте изменения:"
echo "   docker-compose down"
echo "   docker-compose build --no-cache"
echo "   docker-compose up -d"
echo "   docker logs -f pelikan-bot"
echo ""
echo "2️⃣  Проверьте в Telegram:"
echo "   /test_report"
echo ""
echo "3️⃣  Если всё работает - мердж в main:"
echo "   git checkout main"
echo "   git merge ${branch_name}"
echo "   git push origin main"
echo ""
echo "4️⃣  Если не работает - продолжайте исправления:"
echo "   git add ."
echo "   git commit -m \"fix: описание исправления\""
echo ""
echo -e "${YELLOW}📚 Документация: GIT_WORKFLOW.md${NC}"
echo ""
