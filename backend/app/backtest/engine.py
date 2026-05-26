from dataclasses import dataclass

import pandas as pd

from backend.app.backtest.broker import calculate_costs, can_trade_at_limit, round_to_lot
from backend.app.backtest.metrics import calculate_metrics
from backend.app.domain.models import BacktestMetrics, CostConfigModel

TRADE_COLUMNS = [
    "trade_date",
    "symbol",
    "side",
    "price",
    "quantity",
    "gross_amount",
    "costs",
    "net_amount",
    "pnl",
    "reason",
]


@dataclass(frozen=True)
class BacktestResult:
    equity_curve: pd.DataFrame
    positions: pd.DataFrame
    trades: pd.DataFrame
    logs: list[str]
    metrics: BacktestMetrics


def _buy_quantity_for_budget(
    price: float,
    budget: float,
    cash: float,
    costs: CostConfigModel,
) -> int:
    budget = min(budget, cash)
    quantity = round_to_lot(budget / price, costs.min_lot_size)
    while quantity > 0:
        gross = price * quantity
        fee = calculate_costs("buy", price, quantity, costs)
        if gross + fee <= budget and gross + fee <= cash:
            return quantity
        quantity -= costs.min_lot_size
    return 0


def _target_weights(targets: pd.DataFrame) -> dict[str, float]:
    return {
        str(target["symbol"]): float(target["target_weight"])
        for _, target in targets.iterrows()
    }


def run_equal_weight_backtest(
    bars: pd.DataFrame,
    targets_by_date: dict[str, pd.DataFrame],
    initial_cash: float,
    costs: CostConfigModel,
    stop_loss: float = 0.0,
    take_profit: float = 0.0,
) -> BacktestResult:
    cash = initial_cash
    holdings: dict[str, int] = {}
    average_costs: dict[str, float] = {}
    trade_rows: list[dict] = []
    position_rows: list[dict] = []
    equity_rows: list[dict] = []
    logs: list[str] = []
    previous_prices: dict[str, float] = {}

    ordered = bars.sort_values(["trade_date", "symbol"]).copy()
    for trade_date, day_bars in ordered.groupby("trade_date"):
        price_map = dict(zip(day_bars["symbol"], day_bars["close"]))
        risk_exited_symbols: set[str] = set()
        for symbol in sorted(list(holdings)):
            if symbol not in price_map:
                continue
            price = float(price_map[symbol])
            average_cost = average_costs.get(symbol, price)
            exit_reason = None
            if stop_loss > 0 and price <= average_cost * (1 - stop_loss):
                exit_reason = "stop_loss"
            elif take_profit > 0 and price >= average_cost * (1 + take_profit):
                exit_reason = "take_profit"
            if exit_reason is None:
                continue

            risk_exited_symbols.add(symbol)
            previous_close = previous_prices.get(symbol)
            if previous_close is not None and not can_trade_at_limit(
                "sell", price, previous_close
            ):
                logs.append(f"{trade_date} {symbol} {exit_reason} sell skipped: limit down")
                continue

            quantity = holdings.get(symbol, 0)
            if quantity == 0:
                continue
            gross = price * quantity
            fee = calculate_costs("sell", price, quantity, costs)
            net_amount = gross - fee
            pnl = net_amount - average_cost * quantity
            cash += net_amount
            holdings.pop(symbol, None)
            average_costs.pop(symbol, None)
            trade_rows.append(
                {
                    "trade_date": trade_date,
                    "symbol": symbol,
                    "side": "sell",
                    "price": price,
                    "quantity": quantity,
                    "gross_amount": gross,
                    "costs": fee,
                    "net_amount": net_amount,
                    "pnl": pnl,
                    "reason": exit_reason,
                }
            )

        if trade_date in targets_by_date:
            target_weights = {
                symbol: weight
                for symbol, weight in _target_weights(targets_by_date[trade_date]).items()
                if symbol not in risk_exited_symbols
            }
            account_value = cash + sum(
                quantity * price_map.get(symbol, previous_prices.get(symbol, 0.0))
                for symbol, quantity in holdings.items()
            )
            symbols = sorted(set(holdings) | set(target_weights))
            tradable_symbols = []
            for symbol in symbols:
                if symbol not in price_map:
                    logs.append(f"{trade_date} {symbol} skipped: missing price")
                    continue
                tradable_symbols.append(symbol)

            for symbol in tradable_symbols:
                price = float(price_map[symbol])
                current_quantity = holdings.get(symbol, 0)
                target_value = account_value * target_weights.get(symbol, 0.0)
                current_value = current_quantity * price
                delta_value = target_value - current_value
                if delta_value >= 0:
                    continue
                previous_close = previous_prices.get(symbol)
                if previous_close is not None and not can_trade_at_limit(
                    "sell", price, previous_close
                ):
                    logs.append(f"{trade_date} {symbol} sell skipped: limit down")
                    continue
                quantity = min(
                    round_to_lot(abs(delta_value) / price, costs.min_lot_size),
                    current_quantity,
                )
                if quantity == 0:
                    continue
                gross = price * quantity
                fee = calculate_costs("sell", price, quantity, costs)
                net_amount = gross - fee
                pnl = net_amount - average_costs.get(symbol, price) * quantity
                cash += net_amount
                remaining_quantity = current_quantity - quantity
                if remaining_quantity > 0:
                    holdings[symbol] = remaining_quantity
                else:
                    holdings.pop(symbol, None)
                    average_costs.pop(symbol, None)
                trade_rows.append(
                    {
                        "trade_date": trade_date,
                        "symbol": symbol,
                        "side": "sell",
                        "price": price,
                        "quantity": quantity,
                        "gross_amount": gross,
                        "costs": fee,
                        "net_amount": net_amount,
                        "pnl": pnl,
                        "reason": "rebalance",
                    }
                )

            for symbol in tradable_symbols:
                price = float(price_map[symbol])
                current_quantity = holdings.get(symbol, 0)
                target_value = account_value * target_weights.get(symbol, 0.0)
                current_value = current_quantity * price
                delta_value = target_value - current_value
                if delta_value <= 0:
                    continue
                previous_close = previous_prices.get(symbol)
                if previous_close is not None and not can_trade_at_limit(
                    "buy", price, previous_close
                ):
                    logs.append(f"{trade_date} {symbol} buy skipped: limit up")
                    continue
                quantity = _buy_quantity_for_budget(price, delta_value, cash, costs)
                if quantity == 0:
                    logs.append(f"{trade_date} {symbol} buy skipped: insufficient cash")
                    continue
                gross = price * quantity
                fee = calculate_costs("buy", price, quantity, costs)
                net_amount = -(gross + fee)
                previous_quantity = current_quantity
                new_quantity = previous_quantity + quantity
                previous_cost = average_costs.get(symbol, 0.0) * previous_quantity
                average_costs[symbol] = (previous_cost + gross + fee) / new_quantity
                holdings[symbol] = new_quantity
                cash += net_amount
                trade_rows.append(
                    {
                        "trade_date": trade_date,
                        "symbol": symbol,
                        "side": "buy",
                        "price": price,
                        "quantity": quantity,
                        "gross_amount": gross,
                        "costs": fee,
                        "net_amount": net_amount,
                        "pnl": None,
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
        for symbol, price in price_map.items():
            previous_prices[symbol] = float(price)

    equity_curve = pd.DataFrame(equity_rows)
    positions = pd.DataFrame(position_rows)
    trades = pd.DataFrame(trade_rows, columns=TRADE_COLUMNS)
    metrics = calculate_metrics(equity_curve, trades, initial_capital=initial_cash)
    return BacktestResult(
        equity_curve=equity_curve,
        positions=positions,
        trades=trades,
        logs=logs,
        metrics=metrics,
    )
