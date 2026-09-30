from dotenv import load_dotenv
load_dotenv()

import base64
import json
from openai import OpenAI

openai_client = OpenAI()

EXTRACTION_PROMPT = """You are parsing a message from a crypto trading signal group.
Each message may be a branded trade-update card (showing symbol, side, leverage,
entry price, last price, % PnL) with an optional caption underneath.

Extract this JSON:

{
  "message_type": one of "new_trade", "trade_update", "tp_instruction",
                  "stoploss_instruction", "close", "chit_chat",
  "symbol": string like "AEROUSDT" or null,
  "side": "long" or "short" or null,
  "leverage": number or null,
  "entry_price": number or null,
  "last_price": number or null,
  "has_instruction": true or false,
  "instruction_text": string or null,
  "tp_level_mentioned": 1, 2, 3, or null,
  "explicit_close_percentage": number or null
}

Rules:
- "explicit_close_percentage" is set only if the caption states an exact percentage
  to close (e.g. "book 50%" -> 50). Leave null if no explicit percentage is given,
  even if a TP level is mentioned.
- "has_instruction" is true only if the caption gives an actual directive, not for
  plain status updates, memes, or captions with no action implied.
- Extract exactly what the message shows. Do not guess values that are not visible.

Respond with ONLY the JSON object, nothing else.
"""


def extract_signal(text: str, image_bytes: bytes = None) -> dict:
    content = [{"type": "text", "text": f"{EXTRACTION_PROMPT}\n\nMessage text: {text!r}"}]

    if image_bytes:
        b64_image = base64.b64encode(image_bytes).decode("utf-8")
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}
        })

    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": content}],
        response_format={"type": "json_object"},
    )

    return json.loads(response.choices[0].message.content)