from trading_engine import open_position, close_position_partial
from position_tracker import positions

fake_open_signal = {
    "symbol": "BTCUSDT",
    "side": "long",
    "leverage": 20,
    "entry_price": 65000,
}

print("--- Opening ---")
open_position(fake_open_signal)
print("Tracked position:", positions.get("BTCUSDT"))

fake_tp1_signal = {
    "symbol": "BTCUSDT",
    "tp_level_mentioned": 1,
    "explicit_close_percentage": None,
}

print("\n--- Closing TP1 ---")
close_position_partial(fake_tp1_signal)
print("Tracked position after TP1:", positions.get("BTCUSDT"))