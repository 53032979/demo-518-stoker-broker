from backend.app.domain.models import CostConfigModel


def round_to_lot(quantity: float, lot_size: int) -> int:
    return int(quantity // lot_size) * lot_size


def calculate_costs(side: str, price: float, quantity: int, config: CostConfigModel) -> float:
    gross = price * quantity
    commission = gross * config.commission_rate
    stamp_tax = gross * config.stamp_tax_rate if side == "sell" else 0.0
    slippage = gross * config.slippage_bps / 10000.0
    return commission + stamp_tax + slippage


def can_trade_at_limit(side: str, close: float, previous_close: float) -> bool:
    upper = round(previous_close * 1.10, 2)
    lower = round(previous_close * 0.90, 2)
    if side == "buy" and close >= upper:
        return False
    if side == "sell" and close <= lower:
        return False
    return True
