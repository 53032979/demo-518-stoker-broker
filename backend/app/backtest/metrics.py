import math

import pandas as pd

from backend.app.domain.models import BacktestMetrics


def calculate_metrics(equity_curve: pd.DataFrame, trades: pd.DataFrame) -> BacktestMetrics:
    if equity_curve.empty:
        return BacktestMetrics(0.0, 0.0, 0.0, 0.0, 0.0)

    equity = equity_curve["equity"].astype(float)
    total_return = equity.iloc[-1] / equity.iloc[0] - 1.0
    daily_returns = equity.pct_change().dropna()
    annual_return = (1.0 + total_return) ** (252 / max(len(equity), 1)) - 1.0
    rolling_peak = equity.cummax()
    drawdown = equity / rolling_peak - 1.0
    max_drawdown = float(drawdown.min())
    sharpe = 0.0
    if len(daily_returns) > 1 and daily_returns.std() > 0:
        sharpe = float(daily_returns.mean() / daily_returns.std() * math.sqrt(252))
    win_rate = 0.0
    if not trades.empty and "pnl" in trades.columns and len(trades) > 0:
        win_rate = float((trades["pnl"] > 0).sum() / len(trades))
    return BacktestMetrics(
        total_return=float(total_return),
        annual_return=float(annual_return),
        max_drawdown=max_drawdown,
        sharpe=sharpe,
        win_rate=win_rate,
    )
