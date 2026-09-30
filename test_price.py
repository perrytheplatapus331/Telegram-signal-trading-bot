from weex_client import get_current_price

price = get_current_price("BTCUSDT")  # real symbol, not BTCSUSDT
print("BTCUSDT price:", price)