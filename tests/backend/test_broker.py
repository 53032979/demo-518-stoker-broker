from backend.app.backtest.broker import calculate_costs, can_trade_at_limit, round_to_lot
from backend.app.domain.models import CostConfigModel


def test_round_to_lot_uses_100_shares():
    assert round_to_lot(248, lot_size=100) == 200


def test_calculate_costs_applies_commission_stamp_tax_and_slippage():
    costs = calculate_costs(
        side="sell",
        price=10.0,
        quantity=1000,
        config=CostConfigModel(commission_rate=0.0003, stamp_tax_rate=0.001, slippage_bps=5),
    )

    assert round(costs, 2) == 18.0


def test_limit_up_blocks_buy_and_limit_down_blocks_sell():
    assert can_trade_at_limit(side="buy", close=11.0, previous_close=10.0) is False
    assert can_trade_at_limit(side="sell", close=9.0, previous_close=10.0) is False
    assert can_trade_at_limit(side="buy", close=10.5, previous_close=10.0) is True
