import math

import pandas as pd

from backend.app.domain.models import BacktestMetrics


def calculate_metrics(
    equity_curve: pd.DataFrame,
    trades: pd.DataFrame,
    initial_capital: float | None = None,
) -> BacktestMetrics:
    if equity_curve.empty:
        return BacktestMetrics(0.0, 0.0, 0.0, 0.0, 0.0)

    equity = equity_curve["equity"].astype(float)
    starting_equity = float(initial_capital) if initial_capital is not None else float(equity.iloc[0])
    total_return = equity.iloc[-1] / starting_equity - 1.0
    daily_returns = equity.pct_change().dropna()
    if initial_capital is not None:
        initial_return = pd.Series([equity.iloc[0] / starting_equity - 1.0])
        daily_returns = pd.concat([initial_return, daily_returns], ignore_index=True)
    annual_return = (1.0 + total_return) ** (252 / max(len(daily_returns), 1)) - 1.0
    drawdown_equity = equity
    if initial_capital is not None:
        drawdown_equity = pd.concat([pd.Series([starting_equity]), equity], ignore_index=True)
    rolling_peak = drawdown_equity.cummax()
    drawdown = drawdown_equity / rolling_peak - 1.0
    max_drawdown = float(drawdown.min())
    sharpe = 0.0
    if len(daily_returns) > 1 and daily_returns.std() > 0:
        sharpe = float(daily_returns.mean() / daily_returns.std() * math.sqrt(252))
    win_rate = 0.0
    if not trades.empty and "pnl" in trades.columns and len(trades) > 0:
        realized_pnl = pd.to_numeric(trades["pnl"], errors="coerce").dropna()
        if len(realized_pnl) > 0:
            win_rate = float((realized_pnl > 0).sum() / len(realized_pnl))
    return BacktestMetrics(
        total_return=float(total_return),
        annual_return=float(annual_return),
        max_drawdown=max_drawdown,
        sharpe=sharpe,
        win_rate=win_rate,
    )
