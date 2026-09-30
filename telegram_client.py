from dotenv import load_dotenv
load_dotenv()

import os
from telethon.sync import TelegramClient

api_id = int(os.environ["TELEGRAM_API_ID"])
api_hash = os.environ["TELEGRAM_API_HASH"]

MONITORED_CHAT = -1004294961849  # CAV-Scalps

client = TelegramClient("signal_reader", api_id, api_hash)