from dotenv import load_dotenv
load_dotenv()

import asyncio
import threading
from telethon import events

from telegram_client import client, MONITORED_CHAT
from extractor import extract_signal
from trading_engine import (
    open_position, close_position_partial,
    handle_stoploss_instruction, close_position_full, check_stops
)
from dashboard import run_dashboard
import bot_state


@client.on(events.NewMessage(chats=MONITORED_CHAT))
async def handler(event):
    if not bot_state.bot_enabled:
        return

    text = event.raw_text or ""
    image_bytes = None

    if event.photo:
        image_bytes = await event.download_media(bytes)

    if not text and not image_bytes:
        return

    try:
        signal = extract_signal(text, image_bytes)
    except Exception as e:
        print(f"Error extracting signal: {e}")
        return

    print("Extracted signal:", signal)

    message_type = signal.get("message_type")
    try:
        if message_type == "new_trade":
            open_position(signal)
        elif message_type == "tp_instruction":
            close_position_partial(signal)
        elif message_type == "stoploss_instruction":
            handle_stoploss_instruction(signal)
        elif message_type == "close":
            close_position_full(signal)
    except Exception as e:
        print(f"Error handling {message_type} for {signal.get('symbol')}: {e}")

    print("---")


async def monitor_loop():
    while True:
        if bot_state.bot_enabled:
            check_stops()
        await asyncio.sleep(10)


print(f"Listening to chat {MONITORED_CHAT}... (leave this running)")
threading.Thread(target=run_dashboard, daemon=True).start()

while True:
    try:
        client.start()
        client.loop.create_task(monitor_loop())
        client.run_until_disconnected()
    except Exception as e:
        print(f"Connection lost: {e}. Reconnecting in 10 seconds...")
        time.sleep(10)