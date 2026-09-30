RISK_PCT_PER_TRADE = 2.0  # % of balance used as margin per trade


def calculate_quantity(balance: float, entry_price: float, leverage: float, risk_pct: float = RISK_PCT_PER_TRADE) -> float:
    margin_to_use = balance * (risk_pct / 100)
    position_value = margin_to_use * leverage
    quantity = position_value / entry_price
    return quantity