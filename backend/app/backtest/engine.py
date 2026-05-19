from dataclasses import dataclass

import pandas as pd

from backend.app.backtest.broker import calculate_costs, round_to_lot
from backend.app.backtest.metrics import calculate_metrics
from backend.app.domain.models import BacktestMetrics, CostConfigModel


@dataclass(frozen=True)
class BacktestResult:
    equity_curve: pd.DataFrame
    positions: pd.DataFrame
    trades: pd.DataFrame
    logs: list[str]
    metrics: BacktestMetrics


def run_equal_weight_backtest(
    bars: pd.DataFrame,
    targets_by_date: dict[str, pd.DataFrame],
    initial_cash: float,
    costs: CostConfigModel,
) -> BacktestResult:
    cash = initial_cash
    holdings: dict[str, int] = {}
    trade_rows: list[dict] = []
    position_rows: list[dict] = []
    equity_rows: list[dict] = []
    logs: list[str] = []
    previous_prices: dict[str, float] = {}

    ordered = bars.sort_values(["trade_date", "symbol"]).copy()
    for trade_date, day_bars in ordered.groupby("trade_date"):
        price_map = dict(zip(day_bars["symbol"], day_bars["close"]))
        if trade_date in targets_by_date:
            targets = targets_by_date[trade_date]
            account_value = cash + sum(
                quantity * price_map.get(symbol, previous_prices.get(symbol, 0.0))
                for symbol, quantity in holdings.items()
            )
            for _, target in targets.iterrows():
                symbol = target["symbol"]
                price = float(price_map[symbol])
                target_value = account_value * float(target["target_weight"])
                current_quantity = holdings.get(symbol, 0)
                current_value = current_quantity * price
                delta_value = target_value - current_value
                side = "buy" if delta_value > 0 else "sell"
                quantity = round_to_lot(abs(delta_value) / price, costs.min_lot_size)
                if quantity == 0:
                    continue
                fee = calculate_costs(side, price, quantity, costs)
                gross = price * quantity
                if side == "buy" and cash < gross + fee:
                    logs.append(f"{trade_date} {symbol} buy skipped: insufficient cash")
                    continue
                if side == "sell":
                    quantity = min(quantity, current_quantity)
                    gross = price * quantity
                    fee = calculate_costs(side, price, quantity, costs)
                if quantity == 0:
                    continue
                if side == "buy":
                    holdings[symbol] = current_quantity + quantity
                    cash -= gross + fee
                    net_amount = -(gross + fee)
                else:
                    holdings[symbol] = current_quantity - quantity
                    cash += gross - fee
                    net_amount = gross - fee
                trade_rows.append(
                    {
                        "trade_date": trade_date,
                        "symbol": symbol,
                        "side": side,
                        "price": price,
                        "quantity": quantity,
                        "gross_amount": gross,
                        "costs": fee,
                        "net_amount": net_amount,
                        "pnl": 0.0,
                        "reason": "rebalance",
                    }
                )

        market_value = 0.0
        for symbol, quantity in holdings.items():
            price = float(price_map.get(symbol, previous_prices.get(symbol, 0.0)))
            previous_prices[symbol] = price
            market_value += quantity * price
            position_rows.append(
                {
                    "trade_date": trade_date,
                    "symbol": symbol,
                    "quantity": quantity,
                    "price": price,
                    "market_value": quantity * price,
                }
            )
        equity_rows.append(
            {
                "trade_date": trade_date,
                "equity": cash + market_value,
                "cash": cash,
                "market_value": market_value,
            }
        )

    equity_curve = pd.DataFrame(equity_rows)
    positions = pd.DataFrame(position_rows)
    trades = pd.DataFrame(trade_rows)
    metrics = calculate_metrics(equity_curve, trades)
    return BacktestResult(
        equity_curve=equity_curve,
        positions=positions,
        trades=trades,
        logs=logs,
        metrics=metrics,
    )
