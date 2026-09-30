import time

positions = {}
event_log = []


def log_event(event_type, symbol, details=""):
    event_log.append({
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "type": event_type,
        "symbol": symbol,
        "details": details,
    })
    if len(event_log) > 200:
        event_log.pop(0)


def open_new_position(symbol, side, entry_price, quantity, leverage):
    positions[symbol] = {
        "side": side,
        "entry_price": entry_price,
        "original_qty": quantity,
        "remaining_qty": quantity,
        "leverage": leverage,
        "stop_loss": None,
        "tp1_hit": False,
    }
    log_event("open", symbol, f"{side} entry {entry_price}, qty {quantity:.4f}")


def mark_tp_hit(symbol, level, qty_closed):
    pos = positions[symbol]
    pos["remaining_qty"] -= qty_closed
    log_event("tp_close", symbol, f"TP{level}, closed {qty_closed:.4f}")
    if level == 1 and not pos["tp1_hit"]:
        pos["tp1_hit"] = True
        pos["stop_loss"] = pos["entry_price"]
        log_event("breakeven", symbol, f"stop moved to {pos['entry_price']}")
    if pos["remaining_qty"] <= 0:
        del positions[symbol]