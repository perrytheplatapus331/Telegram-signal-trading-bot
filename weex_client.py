from dotenv import load_dotenv
load_dotenv()

import os
import time
import hmac
import hashlib
import base64
import json
import requests
import re
import math

WEEX_API_KEY = os.environ["WEEX_API_KEY"]
WEEX_SECRET_KEY = os.environ["WEEX_SECRET_KEY"]
WEEX_PASSPHRASE = os.environ["WEEX_PASSPHRASE"]
BASE_URL = "https://api-contract.weex.com"


def sign_request(method, request_path, query_string="", body=""):
    timestamp = str(int(time.time() * 1000))
    message = timestamp + method.upper() + request_path + query_string + body
    signature = base64.b64encode(
        hmac.new(WEEX_SECRET_KEY.encode(), message.encode(), hashlib.sha256).digest()
    ).decode()
    return timestamp, signature


def weex_get(request_path, query_string=""):
    timestamp, signature = sign_request("GET", request_path, query_string)
    headers = {
        "ACCESS-KEY": WEEX_API_KEY,
        "ACCESS-SIGN": signature,
        "ACCESS-TIMESTAMP": timestamp,
        "ACCESS-PASSPHRASE": WEEX_PASSPHRASE,
        "Content-Type": "application/json",
    }
    response = requests.get(BASE_URL + request_path + query_string, headers=headers)
    return response.status_code, response.json()


def weex_post(request_path, body_dict):
    body = json.dumps(body_dict)
    timestamp, signature = sign_request("POST", request_path, "", body)
    headers = {
        "ACCESS-KEY": WEEX_API_KEY,
        "ACCESS-SIGN": signature,
        "ACCESS-TIMESTAMP": timestamp,
        "ACCESS-PASSPHRASE": WEEX_PASSPHRASE,
        "Content-Type": "application/json",
    }
    response = requests.post(BASE_URL + request_path, headers=headers, data=body)
    return response.status_code, response.json()


def get_current_price(symbol: str) -> float:
    status, data = weex_get(f"/capi/v3/market/symbolPrice?symbol={symbol}")
    return float(data["price"])


def to_demo_symbol(real_symbol: str) -> str:
    """BTCUSDT -> BTCSUSDT, for /sim/ trading endpoints"""
    if real_symbol.endswith("USDT"):
        return real_symbol[:-4] + "SUSDT"
    return real_symbol


def to_real_symbol(demo_symbol: str) -> str:
    """BTCSUSDT -> BTCUSDT, for market-data endpoints"""
    if demo_symbol.endswith("SUSDT"):
        return demo_symbol[:-5] + "USDT"
    return demo_symbol

def round_to_step(quantity: float, step_size: str) -> str:
    step = float(step_size)
    rounded = math.floor(quantity / step) * step
    decimals = len(step_size.split(".")[1]) if "." in step_size else 0
    return f"{rounded:.{decimals}f}"


def place_order_with_step_retry(request_path: str, order: dict):
    status, response = weex_post(request_path, order)
    if status == 400 and response.get("code") == -1054:
        match = re.search(r"stepSize '([\d.]+)'", response.get("msg", ""))
        if match:
            step_size = match.group(1)
            corrected_qty = round_to_step(float(order["quantity"]), step_size)
            print(f"Retrying with corrected quantity: {corrected_qty} (step {step_size})")
            order["quantity"] = corrected_qty
            status, response = weex_post(request_path, order)
    return status, response