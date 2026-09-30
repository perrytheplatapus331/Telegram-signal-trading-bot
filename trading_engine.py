import time
from weex_client import weex_get, get_current_price, to_demo_symbol, place_order_with_step_retry
from position_sizing import calculate_quantity
from position_tracker import positions, open_new_position, mark_tp_hit, log_event
from telegram_client import client


def notify(message: str):
    client.loop.create_task(client.send_message("me", message))


def open_position(parsed_signal: dict):
    status, balance_data = weex_get("/capi/v3/sim/balance")
    current_balance = float(balance_data[0]["availableBalance"])

    quantity = calculate_quantity(
        balance=current_balance,
        entry_price=parsed_signal["entry_price"],
        leverage=parsed_signal["leverage"],
    )

    order = {
        "symbol": to_demo_symbol(parsed_signal["symbol"]),
        "side": "BUY" if parsed_signal["side"] == "long" else "SELL",
        "positionSide": parsed_signal["side"].upper(),
        "type": "MARKET",
        "quantity": str(round(quantity, 4)),
        "newClientOrderId": f"open-{parsed_signal['symbol']}-{int(time.time())}",
    }

    status, response = place_order_with_step_retry("/capi/v3/sim/order", order)
    print("Open order result:", status, response)

    if response.get("success"):
        open_new_position(
            symbol=parsed_signal["symbol"],
            side=parsed_signal["side"],
            entry_price=parsed_signal["entry_price"],
            quantity=quantity,
            leverage=parsed_signal["leverage"],
        )
        notify(f"🟢 Opened {parsed_signal['side'].upper()} {parsed_signal['symbol']} @ {parsed_signal['entry_price']} (qty {quantity:.4f})")
    return response


def close_position_partial(parsed_signal: dict):
    symbol = parsed_signal["symbol"]
    pos = positions.get(symbol)
    if pos is None:
        print(f"{symbol}: TP instruction received but no tracked position")
        return

    if parsed_signal.get("explicit_close_percentage") is not None:
        fraction = parsed_signal["explicit_close_percentage"] / 100
        qty_to_close = pos["remaining_qty"] * fraction
    else:
        defaults = {1: 1/3, 2: 2/3, 3: 1.0}
        level = parsed_signal["tp_level_mentioned"]
        target_cumulative_qty = pos["original_qty"] * defaults[level]
        already_closed_qty = pos["original_qty"] - pos["remaining_qty"]
        qty_to_close = target_cumulative_qty - already_closed_qty

    close_order = {
        "symbol": to_demo_symbol(symbol),
        "side": "SELL" if pos["side"] == "long" else "BUY",
        "positionSide": pos["side"].upper(),
        "type": "MARKET",
        "quantity": str(round(qty_to_close, 4)),
        "newClientOrderId": f"tp-{symbol}-{int(time.time())}",
    }

    status, response = place_order_with_step_retry("/capi/v3/sim/order", close_order)
    print("TP close result:", status, response)

    if response.get("success"):
        level = parsed_signal["tp_level_mentioned"]
        mark_tp_hit(symbol, level, qty_to_close)
        notify(f"💰 TP{level} hit on {symbol}, closed {qty_to_close:.4f}")
        if level == 1:
            notify(f"🛡️ {symbol} stop-loss moved to breakeven")
    return response


def handle_stoploss_instruction(parsed_signal: dict):
    symbol = parsed_signal["symbol"]
    pos = positions.get(symbol)
    if pos is None:
        print(f"{symbol}: stop-loss instruction received but no tracked position")
        return
    pos["stop_loss"] = pos["entry_price"]
    log_event("stoploss_set", symbol, f"stop set to {pos['entry_price']} via caption")
    notify(f"🛡️ {symbol} stop-loss manually set to {pos['entry_price']}")


def close_position_full(parsed_signal: dict):
    symbol = parsed_signal["symbol"]
    pos = positions.get(symbol)
    if pos is None:
        print(f"{symbol}: close instruction received but no tracked position")
        return

    close_order = {
        "symbol": to_demo_symbol(symbol),
        "side": "SELL" if pos["side"] == "long" else "BUY",
        "positionSide": pos["side"].upper(),
        "type": "MARKET",
        "quantity": str(round(pos["remaining_qty"], 4)),
        "newClientOrderId": f"close-{symbol}-{int(time.time())}",
    }
    status, response = place_order_with_step_retry("/capi/v3/sim/order", close_order)
    print("Full close result:", status, response)
    if response.get("success"):
        log_event("close", symbol, f"closed remaining {pos['remaining_qty']:.4f}")
        notify(f"🔴 Closed {symbol} fully")
        del positions[symbol]


def check_stops():
    for symbol, pos in list(positions.items()):
        if pos["stop_loss"] is None:
            continue
        price = get_current_price(symbol)
        hit = (price <= pos["stop_loss"]) if pos["side"] == "long" else (price >= pos["stop_loss"])
        if hit:
            print(f"{symbol}: stop-loss hit at {price}, closing remaining {pos['remaining_qty']}")
            close_order = {
                "symbol": to_demo_symbol(symbol),
                "side": "SELL" if pos["side"] == "long" else "BUY",
                "positionSide": pos["side"].upper(),
                "type": "MARKET",
                "quantity": str(round(pos["remaining_qty"], 4)),
                "newClientOrderId": f"stoploss-{symbol}-{int(time.time())}",
            }
            place_order_with_step_retry("/capi/v3/sim/order", close_order)
            log_event("stop_hit", symbol, f"closed at {price}")
            notify(f"🛑 Stop-loss hit on {symbol} at {price}")
            del positions[symbol]