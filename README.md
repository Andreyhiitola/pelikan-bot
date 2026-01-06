# Pelikan Alakol Hotel Bot

Bot: [@Pelican_alacol_hotel_bot](https://t.me/Pelican_alacol_hotel_bot)

## Installation
```bash
git clone https://github.com/Andreyhiitola/pelikan-bot.git
cd pelikan-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create `.env`:
```env
BOT_TOKEN=your_token_here
ADMIN_IDS=your_id_here
DB_FILE=orders.db
```

Run: `python3 bot.py`

## Commands
- `/bar` - Bar menu
- `/stolovaya` - Dining room
- `/booking` - Room booking
- `/info` - Hotel info

## Stack
Python 3.11, aiogram 3.7, aiosqlite
