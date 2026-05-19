from dataclasses import asdict
from uuid import uuid4

import pandas as pd

from backend.app.api.schemas import BacktestRequest
from backend.app.backtest.engine import BacktestResult, run_equal_weight_backtest
from backend.app.data.providers.free_provider import DEFAULT_POOLS, FreeMarketDataProvider
from backend.app.domain.errors import StrategyValidationError
from backend.app.domain.models import CostConfigModel, PoolType, StockPool
from backend.app.strategies.builtins import get_strategy_templates


def list_default_pools() -> list[StockPool]:
    return [
        StockPool(
            pool_id="csi300",
            name="沪深300",
            pool_type=PoolType.INDEX,
            symbols=DEFAULT_POOLS["csi300"],
        ),
        StockPool(
            pool_id="csi500",
            name="中证500",
            pool_type=PoolType.INDEX,
            symbols=DEFAULT_POOLS["csi500"],
        ),
        StockPool(
            pool_id="csi1000",
            name="中证1000",
            pool_type=PoolType.INDEX,
            symbols=DEFAULT_POOLS["csi1000"],
        ),
    ]


def run_backtest(request: BacktestRequest) -> dict:
    pools = {pool.pool_id: pool for pool in list_default_pools()}
    if request.pool_id not in pools:
        raise StrategyValidationError("未知股票池", {"pool_id": request.pool_id})

    templates = {template.strategy_id: template for template in get_strategy_templates()}
    if request.strategy_id not in templates:
        raise StrategyValidationError("未知策略模板", {"strategy_id": request.strategy_id})

    symbols = list(pools[request.pool_id].symbols)
    start_date = request.start_date.isoformat()
    end_date = request.end_date.isoformat()
    bars = FreeMarketDataProvider().load_daily_bars(symbols, start_date, end_date)
    first_date = bars["trade_date"].min()
    top_n = int(request.parameters.get("top_n", 2))
    if top_n < 1:
        raise StrategyValidationError("top_n 必须大于等于 1", {"top_n": top_n})

    selected = symbols[:top_n]
    target_weight = 1.0 / len(selected)
    targets = pd.DataFrame(
        {"symbol": selected, "target_weight": [target_weight] * len(selected)}
    )
    costs = CostConfigModel(**request.costs.model_dump())
    result = run_equal_weight_backtest(bars, {first_date: targets}, 100000.0, costs)
    return serialize_result(str(uuid4()), result)


def serialize_result(run_id: str, result: BacktestResult) -> dict:
    return {
        "run_id": run_id,
        "status": "completed",
        "result": {
            "metrics": asdict(result.metrics),
            "equity_curve": _records(result.equity_curve),
            "positions": _records(result.positions),
            "trades": _records(result.trades),
            "logs": result.logs,
        },
    }


def _records(frame: pd.DataFrame) -> list[dict]:
    return frame.astype(object).where(pd.notnull(frame), None).to_dict(orient="records")
