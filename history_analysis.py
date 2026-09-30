import os
import json
from dotenv import load_dotenv
from telethon import TelegramClient

from extractor import extract_signal

load_dotenv()

api_id = int(os.environ["TELEGRAM_API_ID"])
api_hash = os.environ["TELEGRAM_API_HASH"]
MONITORED_CHAT = -1004294961849  # CAV-Scalps

client = TelegramClient("signal_reader", api_id, api_hash)


async def fetch_history(limit=50):
    rows = []
    async for msg in client.iter_messages(MONITORED_CHAT, limit=limit):
        image_bytes = await msg.download_media(bytes) if msg.photo else None
        rows.append({
            "id": msg.id,
            "date": msg.date.isoformat(),
            "text": msg.text or "",
            "image": image_bytes,
        })
    rows.reverse()  # oldest first
    return rows


async def main():
    rows = await fetch_history(limit=50)
    results = []
    for row in rows:
        if not row["text"] and not row["image"]:
            continue
        parsed = extract_signal(row["text"], row["image"])
        results.append({"id": row["id"], "date": row["date"], "text": row["text"], "parsed": parsed})
        print(row["id"], parsed)

    with open("history_results.json", "w") as f:
        json.dump(results, f, indent=2)


with client:
    client.loop.run_until_complete(main())