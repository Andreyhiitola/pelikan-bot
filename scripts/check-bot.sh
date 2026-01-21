#!/bin/bash
if ! docker ps | grep -q pelikan-bot; then
    echo "$(date): Bot is down! Restarting..."
    cd ~/pelikan-bot/pelikan-bot
    docker compose up -d bot
fi
