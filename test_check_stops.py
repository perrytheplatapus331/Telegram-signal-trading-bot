# test_check_stops.py
from trading_engine import check_stops
from position_tracker import positions
from weex_client import get_current_price

current_price = get_current_price("BTCUSDT")
print("Current BTCUSDT price:", current_price)

# fake a long position with a stop-loss just above current price, so it's already "hit"
positions["BTCUSDT"] = {
    "side": "long",
    "entry_price": current_price + 1000,
    "original_qty": 0.01,
    "remaining_qty": 0.01,
    "leverage": 20,
    "stop_loss": current_price + 500,  # above current price -> should trigger
    "tp1_hit": True,
}

check_stops()
print("Positions after check_stops:", positions)