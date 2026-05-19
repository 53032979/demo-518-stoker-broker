import pandas as pd

from backend.app.backtest.metrics import calculate_metrics


def test_calculate_metrics_returns_core_values():
    equity = pd.DataFrame(
        {
            "trade_date": ["2024-01-01", "2024-01-02", "2024-01-03"],
            "equity": [100000.0, 105000.0, 102000.0],
        }
    )
    trades = pd.DataFrame({"pnl": [1000.0, -500.0, 800.0]})

    metrics = calculate_metrics(equity, trades)

    assert round(metrics.total_return, 4) == 0.02
    assert round(metrics.max_drawdown, 4) == -0.0286
    assert round(metrics.win_rate, 4) == 0.6667


def test_calculate_metrics_can_use_initial_capital_denominator():
    equity = pd.DataFrame(
        {
            "trade_date": ["2024-01-01"],
            "equity": [99920.8],
        }
    )
    trades = pd.DataFrame()

    metrics = calculate_metrics(equity, trades, initial_capital=100000.0)

    assert round(metrics.total_return, 6) == -0.000792


def test_calculate_metrics_annualizes_using_return_intervals():
    equity = pd.DataFrame(
        {
            "trade_date": ["2024-01-01", "2024-01-02"],
            "equity": [100.0, 101.0],
        }
    )
    trades = pd.DataFrame()

    metrics = calculate_metrics(equity, trades)

    assert round(metrics.annual_return, 6) == round((1.01**252) - 1.0, 6)
