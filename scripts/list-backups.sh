#!/bin/bash
echo "💾 Список бэкапов базы данных:"
echo ""
ls -lth ~/backups/*.db
echo ""
echo "📊 Всего бэкапов: $(ls ~/backups/*.db 2>/dev/null | wc -l)"
echo "💿 Занято места: $(du -sh ~/backups 2>/dev/null | cut -f1)"
