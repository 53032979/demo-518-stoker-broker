import pandas as pd

from backend.app.backtest.engine import run_equal_weight_backtest
from backend.app.domain.models import CostConfigModel


def _bar(symbol: str, trade_date: str, close: float) -> dict:
    return {
        "symbol": symbol,
        "trade_date": trade_date,
        "open": close,
        "high": close,
        "low": close,
        "close": close,
        "volume": 10000,
        "amount": close * 10000,
        "frequency": "1d",
        "source": "unit",
    }


def test_equal_weight_backtest_produces_equity_and_trades():
    bars = pd.DataFrame(
        [
            _bar("A", "2024-01-01", 10),
            _bar("B", "2024-01-01", 20),
            _bar("A", "2024-01-02", 11),
            _bar("B", "2024-01-02", 19),
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
    assert result.trades["quantity"].tolist() == [5000, 2500]
    assert result.equity_curve["cash"].tolist() == [0.0, 0.0]
    assert result.equity_curve["market_value"].tolist() == [100000.0, 102500.0]
    assert round(result.metrics.total_return, 4) == 0.025


def test_one_day_buy_with_costs_reports_negative_return():
    bars = pd.DataFrame([_bar("A", "2024-01-01", 10)])
    targets = pd.DataFrame({"symbol": ["A"], "target_weight": [1.0]})

    result = run_equal_weight_backtest(
        bars=bars,
        targets_by_date={"2024-01-01": targets},
        initial_cash=100000.0,
        costs=CostConfigModel(),
    )

    assert len(result.trades) == 1
    assert result.trades.iloc[0]["quantity"] == 9900
    assert round(result.trades.iloc[0]["costs"], 2) == 79.20
    assert round(result.equity_curve.iloc[-1]["equity"], 2) == 99920.80
    assert result.metrics.total_return < 0


def test_fee_aware_buy_sizing_allows_two_default_cost_targets():
    bars = pd.DataFrame(
        [
            _bar("A", "2024-01-01", 10),
            _bar("B", "2024-01-01", 20),
        ]
    )
    targets = pd.DataFrame({"symbol": ["A", "B"], "target_weight": [0.5, 0.5]})

    result = run_equal_weight_backtest(
        bars=bars,
        targets_by_date={"2024-01-01": targets},
        initial_cash=100000.0,
        costs=CostConfigModel(),
    )

    assert result.trades["symbol"].tolist() == ["A", "B"]
    assert result.trades["quantity"].tolist() == [4900, 2400]
    assert round(result.trades["costs"].sum(), 2) == 77.60
    assert round(result.equity_curve.iloc[-1]["cash"], 2) == 2922.40
    assert round(result.metrics.total_return, 6) == -0.000776


def test_rebalance_liquidates_omitted_symbols_and_removes_zero_holding():
    bars = pd.DataFrame(
        [
            _bar("A", "2024-01-01", 10),
            _bar("B", "2024-01-01", 20),
            _bar("A", "2024-01-02", 10.5),
            _bar("B", "2024-01-02", 19),
        ]
    )
    day_one = pd.DataFrame({"symbol": ["A", "B"], "target_weight": [0.5, 0.5]})
    day_two = pd.DataFrame({"symbol": ["A"], "target_weight": [1.0]})

    result = run_equal_weight_backtest(
        bars=bars,
        targets_by_date={"2024-01-01": day_one, "2024-01-02": day_two},
        initial_cash=100000.0,
        costs=CostConfigModel(commission_rate=0, stamp_tax_rate=0, slippage_bps=0),
    )

    day_two_trades = result.trades[result.trades["trade_date"] == "2024-01-02"]
    day_two_positions = result.positions[result.positions["trade_date"] == "2024-01-02"]

    assert day_two_trades["side"].tolist() == ["sell", "buy"]
    assert day_two_trades["symbol"].tolist() == ["B", "A"]
    assert day_two_trades["quantity"].tolist() == [2500, 4500]
    assert day_two_positions["symbol"].tolist() == ["A"]
    assert day_two_positions.iloc[0]["quantity"] == 9500
    assert result.equity_curve.iloc[-1]["cash"] == 250.0
    assert result.equity_curve.iloc[-1]["market_value"] == 99750.0


def test_missing_target_price_logs_and_skips_symbol():
    bars = pd.DataFrame([_bar("A", "2024-01-01", 10)])
    targets = pd.DataFrame({"symbol": ["A", "MISSING"], "target_weight": [0.5, 0.5]})

    result = run_equal_weight_backtest(
        bars=bars,
        targets_by_date={"2024-01-01": targets},
        initial_cash=100000.0,
        costs=CostConfigModel(commission_rate=0, stamp_tax_rate=0, slippage_bps=0),
    )

    assert result.trades["symbol"].tolist() == ["A"]
    assert result.logs == ["2024-01-01 MISSING skipped: missing price"]


def test_sell_trade_records_realized_pnl_and_win_rate():
    bars = pd.DataFrame(
        [
            _bar("A", "2024-01-01", 10),
            _bar("A", "2024-01-02", 12),
        ]
    )
    entry = pd.DataFrame({"symbol": ["A"], "target_weight": [1.0]})
    exit_all = pd.DataFrame({"symbol": [], "target_weight": []})

    result = run_equal_weight_backtest(
        bars=bars,
        targets_by_date={"2024-01-01": entry, "2024-01-02": exit_all},
        initial_cash=100000.0,
        costs=CostConfigModel(commission_rate=0, stamp_tax_rate=0, slippage_bps=0),
    )

    sell = result.trades[result.trades["side"] == "sell"].iloc[0]

    assert sell["quantity"] == 10000
    assert sell["pnl"] == 20000.0
    assert result.metrics.win_rate == 1.0


def test_limit_up_buy_is_blocked_after_previous_close():
    bars = pd.DataFrame(
        [
            _bar("A", "2024-01-01", 10),
            _bar("A", "2024-01-02", 11),
        ]
    )
    entry = pd.DataFrame({"symbol": ["A"], "target_weight": [1.0]})

    result = run_equal_weight_backtest(
        bars=bars,
        targets_by_date={"2024-01-02": entry},
        initial_cash=100000.0,
        costs=CostConfigModel(commission_rate=0, stamp_tax_rate=0, slippage_bps=0),
    )

    assert result.trades.empty
    assert result.equity_curve["cash"].tolist() == [100000.0, 100000.0]
    assert result.logs == ["2024-01-02 A buy skipped: limit up"]


def test_limit_down_sell_is_blocked_after_previous_close():
    bars = pd.DataFrame(
        [
            _bar("A", "2024-01-01", 10),
            _bar("A", "2024-01-02", 9),
        ]
    )
    entry = pd.DataFrame({"symbol": ["A"], "target_weight": [1.0]})
    exit_all = pd.DataFrame({"symbol": [], "target_weight": []})

    result = run_equal_weight_backtest(
        bars=bars,
        targets_by_date={"2024-01-01": entry, "2024-01-02": exit_all},
        initial_cash=100000.0,
        costs=CostConfigModel(commission_rate=0, stamp_tax_rate=0, slippage_bps=0),
    )

    assert result.trades["side"].tolist() == ["buy"]
    assert result.positions[result.positions["trade_date"] == "2024-01-02"].iloc[0][
        "quantity"
    ] == 10000
    assert result.equity_curve.iloc[-1]["cash"] == 0.0
    assert result.equity_curve.iloc[-1]["market_value"] == 90000.0
    assert result.logs == ["2024-01-02 A sell skipped: limit down"]
