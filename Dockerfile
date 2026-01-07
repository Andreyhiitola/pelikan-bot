FROM python:3.11-slim

LABEL maintainer="Pelikan Alakol <info@pelikan-alakol.kz>"
LABEL description="Telegram bot for Pelikan Alakol Hotel"

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY bot.py .

RUN mkdir -p /app/data

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sqlite3; sqlite3.connect('/app/data/orders.db').close()" || exit 1

CMD ["python", "-u", "bot.py"]
