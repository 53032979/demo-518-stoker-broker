from dataclasses import asdict
from uuid import uuid4

import pandas as pd

from backend.app.api.schemas import BacktestRequest
from backend.app.backtest.engine import BacktestResult, run_equal_weight_backtest
from backend.app.data.providers.free_provider import DEFAULT_POOLS, FreeMarketDataProvider
from backend.app.domain.errors import BacktestRuntimeError, StrategyValidationError
from backend.app.domain.models import CostConfigModel, PoolType, StockPool, StrategyTemplate
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
    template = templates[request.strategy_id]
    top_n = _validated_top_n(request.parameters, template)

    symbols = list(pools[request.pool_id].symbols)
    if top_n > len(symbols):
        raise StrategyValidationError(
            "top_n 大于股票池数量",
            {"top_n": top_n, "pool_size": len(symbols), "pool_id": request.pool_id},
        )

    start_date = request.start_date.isoformat()
    end_date = request.end_date.isoformat()
    bars = FreeMarketDataProvider().load_daily_bars(symbols, start_date, end_date)
    if bars.empty:
        raise BacktestRuntimeError(
            "没有可用行情数据",
            {
                "pool_id": request.pool_id,
                "start_date": start_date,
                "end_date": end_date,
            },
        )
    first_date = bars["trade_date"].min()

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


def _validated_top_n(parameters: dict, template: StrategyTemplate) -> int:
    top_n_schema = template.parameter_schema.get("properties", {}).get("top_n", {})
    default_top_n = template.default_parameters.get("top_n", top_n_schema.get("default", 2))
    value = parameters.get("top_n", default_top_n)

    if isinstance(value, bool) or not isinstance(value, int):
        raise StrategyValidationError(
            "top_n 必须是整数",
            {"top_n": value},
        )

    minimum = top_n_schema.get("minimum")
    maximum = top_n_schema.get("maximum")
    if minimum is not None and value < minimum:
        raise StrategyValidationError(
            "top_n 小于策略模板最小值",
            {"top_n": value, "minimum": minimum},
        )
    if maximum is not None and value > maximum:
        raise StrategyValidationError(
            "top_n 大于策略模板最大值",
            {"top_n": value, "maximum": maximum},
        )
    return value
