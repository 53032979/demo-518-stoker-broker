import pandas as pd

from backend.app.backtest.engine import run_equal_weight_backtest
from backend.app.domain.models import CostConfigModel


def test_equal_weight_backtest_produces_equity_and_trades():
    bars = pd.DataFrame(
        [
            {
                "symbol": "A",
                "trade_date": "2024-01-01",
                "open": 10,
                "high": 10,
                "low": 10,
                "close": 10,
                "volume": 10000,
                "amount": 100000,
                "frequency": "1d",
                "source": "unit",
            },
            {
                "symbol": "B",
                "trade_date": "2024-01-01",
                "open": 20,
                "high": 20,
                "low": 20,
                "close": 20,
                "volume": 10000,
                "amount": 200000,
                "frequency": "1d",
                "source": "unit",
            },
            {
                "symbol": "A",
                "trade_date": "2024-01-02",
                "open": 11,
                "high": 11,
                "low": 11,
                "close": 11,
                "volume": 10000,
                "amount": 110000,
                "frequency": "1d",
                "source": "unit",
            },
            {
                "symbol": "B",
                "trade_date": "2024-01-02",
                "open": 19,
                "high": 19,
                "low": 19,
                "close": 19,
                "volume": 10000,
                "amount": 190000,
                "frequency": "1d",
                "source": "unit",
            },
        ]
    )
    targets = pd.DataFrame({"symbol": ["A", "B"], "target_weight": [0.5, 0.5]})

    result = run_equal_weight_backtest(
        bars=bars,
        targets_by_date={"2024-01-01": targets},
        initial_cash=100000.0,
        costs=CostConfigModel(commission_rate=0, stamp_tax_rate=0, slippage_bps=0),
    )

    assert not result.equity_curve.empty
    assert len(result.trades) == 2
    assert result.metrics.total_return != 0
