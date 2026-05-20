import math
from collections.abc import Mapping
from dataclasses import asdict
from uuid import uuid4

import pandas as pd

from backend.app.api.schemas import BacktestRequest
from backend.app.backtest.engine import BacktestResult, run_equal_weight_backtest
from backend.app.data.providers.free_provider import DEFAULT_POOLS, FreeMarketDataProvider
from backend.app.domain.errors import BacktestRuntimeError, StrategyValidationError
from backend.app.domain.models import CostConfigModel, PoolType, StockPool, StrategyTemplate
from backend.app.storage.repository import QuantRepository
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


def list_pools(repository: QuantRepository | None = None) -> list[StockPool]:
    pools = {pool.pool_id: pool for pool in list_default_pools()}
    if repository is not None:
        pools.update({pool.pool_id: pool for pool in repository.list_stock_pools()})
    return sorted(pools.values(), key=lambda pool: pool.pool_id)


def run_backtest(request: BacktestRequest, repository: QuantRepository | None = None) -> dict:
    pools = {pool.pool_id: pool for pool in list_pools(repository)}
    if request.pool_id not in pools:
        raise StrategyValidationError("未知股票池", {"pool_id": request.pool_id})

    templates = {template.strategy_id: template for template in get_strategy_templates()}
    if request.strategy_id not in templates:
        raise StrategyValidationError("未知策略模板", {"strategy_id": request.strategy_id})
    template = templates[request.strategy_id]
    parameters = _validated_parameters(request.parameters, template)
    top_n = parameters["top_n"]

    symbols = list(pools[request.pool_id].symbols)
    if top_n > len(symbols):
        raise StrategyValidationError(
            "top_n 大于股票池数量",
            {"top_n": top_n, "pool_size": len(symbols), "pool_id": request.pool_id},
        )

    start_date = request.start_date.isoformat()
    end_date = request.end_date.isoformat()
    bars = _load_bars(repository, symbols, start_date, end_date)
    if bars.empty:
        raise BacktestRuntimeError(
            "没有可用行情数据",
            {
                "pool_id": request.pool_id,
                "start_date": start_date,
                "end_date": end_date,
            },
        )

    targets_by_date, strategy_logs = _build_targets_by_date(
        bars=bars,
        strategy_id=request.strategy_id,
        parameters=parameters,
    )
    if not targets_by_date:
        raise BacktestRuntimeError(
            "策略未产生可交易目标",
            {"strategy_id": request.strategy_id, "pool_id": request.pool_id},
        )

    costs = CostConfigModel(**request.costs.model_dump())
    result = run_equal_weight_backtest(bars, targets_by_date, 100000.0, costs)
    result.logs.extend(strategy_logs)
    run_id = str(uuid4())
    response = serialize_result(run_id, result)
    if repository is not None:
        repository.save_backtest_run(
            run_id=run_id,
            status=response["status"],
            request_payload=request.model_dump(mode="json"),
            response_payload=response,
        )
    return response


def get_backtest_run(run_id: str, repository: QuantRepository) -> dict:
    stored = repository.load_backtest_run(run_id)
    if stored is None:
        raise BacktestRuntimeError("回测记录不存在", {"run_id": run_id})
    return stored["response"]


def get_backtest_status(run_id: str, repository: QuantRepository) -> dict:
    response = get_backtest_run(run_id, repository)
    return {"run_id": run_id, "status": response["status"], "message": ""}


def get_backtest_results(run_id: str, repository: QuantRepository) -> dict:
    return get_backtest_run(run_id, repository)["result"]


def get_backtest_logs(run_id: str, repository: QuantRepository) -> dict:
    response = get_backtest_run(run_id, repository)
    return {"run_id": run_id, "logs": response["result"].get("logs", [])}


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


def _load_bars(
    repository: QuantRepository | None,
    symbols: list[str],
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    if repository is not None:
        stored = repository.load_daily_bars(symbols, start_date, end_date)
        if not stored.empty:
            return stored
    return FreeMarketDataProvider().load_daily_bars(symbols, start_date, end_date)


def _build_targets_by_date(
    bars: pd.DataFrame,
    strategy_id: str,
    parameters: dict,
) -> tuple[dict[str, pd.DataFrame], list[str]]:
    targets_by_date: dict[str, pd.DataFrame] = {}
    logs: list[str] = []
    for rebalance_date in _rebalance_dates(bars, parameters["rebalance"]):
        targets, target_logs = _select_targets(bars, rebalance_date, strategy_id, parameters)
        logs.extend(target_logs)
        if not targets.empty:
            targets_by_date[rebalance_date] = targets
            logs.append(
                f"{rebalance_date} selected: {','.join(targets['symbol'].astype(str).tolist())}"
            )
    return targets_by_date, logs


def _rebalance_dates(bars: pd.DataFrame, rebalance: str) -> list[str]:
    dates = pd.Series(pd.to_datetime(sorted(bars["trade_date"].unique())))
    if dates.empty:
        return []

    period_alias = {
        "weekly": "W",
        "monthly": "M",
        "quarterly": "Q",
    }[rebalance]
    period_end_dates = (
        dates.groupby(dates.dt.to_period(period_alias)).max().dt.strftime("%Y-%m-%d").tolist()
    )
    return sorted(set(period_end_dates))


def _select_targets(
    bars: pd.DataFrame,
    trade_date: str,
    strategy_id: str,
    parameters: dict,
) -> tuple[pd.DataFrame, list[str]]:
    logs: list[str] = []
    factor_frame = _factor_frame(
        bars,
        trade_date,
        lookback=parameters.get("lookback", max(parameters.get("ma_slow", 1), 1)),
        ma_fast=parameters.get("ma_fast"),
        ma_slow=parameters.get("ma_slow"),
    )
    if factor_frame.empty:
        return _empty_targets(), [f"{trade_date} skipped: no factor data"]

    factor_frame = _add_factor_scores(factor_frame)
    top_n = parameters["top_n"]
    if strategy_id == "momentum_top_n":
        selected = factor_frame.sort_values(
            ["momentum", "symbol"], ascending=[False, True]
        ).head(top_n)
        selected = selected.assign(score=selected["momentum_score"])
    elif strategy_id == "low_volatility":
        selected = factor_frame.sort_values(
            ["volatility", "symbol"], ascending=[True, True]
        ).head(top_n)
        selected = selected.assign(score=selected["low_volatility_score"])
    elif strategy_id == "value_quality":
        selected = factor_frame.assign(
            score=(
                factor_frame["value_score"] * 0.55
                + factor_frame["liquidity_score"] * 0.35
                + factor_frame["low_volatility_score"] * 0.10
            )
        ).sort_values(["score", "symbol"], ascending=[False, True]).head(top_n)
    elif strategy_id == "multi_factor_score":
        weights = parameters["weights"]
        selected = factor_frame.assign(
            score=(
                factor_frame["value_score"] * weights["value"]
                + factor_frame["quality_score"] * weights["quality"]
                + factor_frame["momentum_score"] * weights["momentum"]
                + factor_frame["low_volatility_score"] * weights["low_volatility"]
                + factor_frame["liquidity_score"] * weights["liquidity"]
            )
        ).sort_values(["score", "symbol"], ascending=[False, True]).head(top_n)
    elif strategy_id == "ma_trend_filter":
        filtered = factor_frame[factor_frame["ma_fast_value"] > factor_frame["ma_slow_value"]]
        if filtered.empty:
            logs.append(f"{trade_date} MA trend filter left no candidates; using full pool")
            filtered = factor_frame
        selected = filtered.sort_values(["momentum", "symbol"], ascending=[False, True]).head(top_n)
        selected = selected.assign(score=selected["momentum_score"])
    else:
        raise StrategyValidationError("未知策略模板", {"strategy_id": strategy_id})

    return _weighted_targets(selected, parameters["weighting"]), logs


def _factor_frame(
    bars: pd.DataFrame,
    trade_date: str,
    lookback: int,
    ma_fast: int | None = None,
    ma_slow: int | None = None,
) -> pd.DataFrame:
    as_of = pd.Timestamp(trade_date)
    frame = bars.copy()
    frame["trade_date"] = pd.to_datetime(frame["trade_date"])
    frame = frame[frame["trade_date"] <= as_of].sort_values(["symbol", "trade_date"])
    rows: list[dict] = []
    window_size = max(lookback + 1, ma_fast or 1, ma_slow or 1)
    for symbol, history in frame.groupby("symbol"):
        window = history.tail(window_size)
        if window.empty:
            continue
        close = window["close"].astype(float)
        returns = close.pct_change().dropna().tail(lookback)
        momentum = 0.0
        if len(close) >= 2:
            first_close = float(close.iloc[max(0, len(close) - lookback - 1)])
            momentum = float(close.iloc[-1] / first_close - 1.0)
        volatility = float(returns.std(ddof=0)) if not returns.empty else 0.0
        amount = window["amount"].astype(float).tail(lookback)
        rows.append(
            {
                "symbol": symbol,
                "close": float(close.iloc[-1]),
                "momentum": momentum,
                "volatility": volatility,
                "liquidity": float(amount.mean()) if not amount.empty else 0.0,
                "ma_fast_value": float(close.tail(ma_fast or 1).mean()),
                "ma_slow_value": float(close.tail(ma_slow or ma_fast or 1).mean()),
            }
        )
    return pd.DataFrame(rows).sort_values("symbol").reset_index(drop=True)


def _add_factor_scores(frame: pd.DataFrame) -> pd.DataFrame:
    scored = frame.copy()
    scored["value_score"] = _rank_score(scored["close"], higher_is_better=False)
    scored["momentum_score"] = _rank_score(scored["momentum"], higher_is_better=True)
    scored["low_volatility_score"] = _rank_score(
        scored["volatility"], higher_is_better=False
    )
    scored["liquidity_score"] = _rank_score(scored["liquidity"], higher_is_better=True)
    scored["quality_score"] = (
        scored["liquidity_score"] * 0.6 + scored["low_volatility_score"] * 0.4
    )
    return scored


def _rank_score(series: pd.Series, higher_is_better: bool) -> pd.Series:
    return series.rank(method="first", ascending=higher_is_better, pct=True)


def _weighted_targets(selection: pd.DataFrame, weighting: str) -> pd.DataFrame:
    if selection.empty:
        return _empty_targets()
    selected = selection[["symbol", "score"]].copy()
    if weighting == "factor_score":
        positive_scores = selected["score"].clip(lower=0)
        total = float(positive_scores.sum())
        if total > 0:
            selected["target_weight"] = positive_scores / total
        else:
            selected["target_weight"] = 1.0 / len(selected)
    else:
        selected["target_weight"] = 1.0 / len(selected)
    return selected[["symbol", "target_weight"]].reset_index(drop=True)


def _empty_targets() -> pd.DataFrame:
    return pd.DataFrame(columns=["symbol", "target_weight"])


def _records(frame: pd.DataFrame) -> list[dict]:
    return frame.astype(object).where(pd.notnull(frame), None).to_dict(orient="records")


def _validated_parameters(parameters: dict, template: StrategyTemplate) -> dict:
    schema_properties = template.parameter_schema.get("properties", {})
    validated = {
        key: property_schema["default"]
        for key, property_schema in schema_properties.items()
        if "default" in property_schema
    }
    validated.update(dict(template.default_parameters))
    validated.update(parameters)
    validated["top_n"] = _validated_top_n(validated, template)
    validated["rebalance"] = _validated_enum(
        validated.get("rebalance"),
        schema_properties["rebalance"]["enum"],
        "rebalance",
    )
    validated["weighting"] = _validated_enum(
        validated.get("weighting"),
        schema_properties["weighting"]["enum"],
        "weighting",
    )

    for key in ("lookback", "ma_fast", "ma_slow"):
        if key in schema_properties:
            validated[key] = _validated_int(validated.get(key), schema_properties[key], key)

    if "ma_fast" in validated and "ma_slow" in validated and validated["ma_fast"] >= validated["ma_slow"]:
        raise StrategyValidationError(
            "ma_fast 必须小于 ma_slow",
            {"ma_fast": validated["ma_fast"], "ma_slow": validated["ma_slow"]},
        )

    for key in ("stop_loss", "take_profit"):
        if key in schema_properties:
            validated[key] = _validated_number(validated.get(key), schema_properties[key], key)

    if "weights" in schema_properties:
        validated["weights"] = _validated_weights(
            validated.get("weights"),
            schema_properties["weights"],
        )

    return validated


def _validated_top_n(parameters: dict, template: StrategyTemplate) -> int:
    top_n_schema = template.parameter_schema.get("properties", {}).get("top_n", {})
    default_top_n = template.default_parameters.get("top_n", top_n_schema.get("default", 2))
    value = parameters.get("top_n", default_top_n)
    return _validated_int(value, top_n_schema, "top_n")


def _validated_int(value: object, schema: dict, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise StrategyValidationError(f"{name} 必须是整数", {name: value})

    minimum = schema.get("minimum")
    maximum = schema.get("maximum")
    if minimum is not None and value < minimum:
        raise StrategyValidationError(
            f"{name} 小于策略模板最小值",
            {name: value, "minimum": minimum},
        )
    if maximum is not None and value > maximum:
        raise StrategyValidationError(
            f"{name} 大于策略模板最大值",
            {name: value, "maximum": maximum},
        )
    return value


def _validated_number(value: object, schema: dict, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
        raise StrategyValidationError(f"{name} 必须是有限数字", {name: value})
    number = float(value)
    minimum = schema.get("minimum")
    maximum = schema.get("maximum")
    if minimum is not None and number < minimum:
        raise StrategyValidationError(f"{name} 小于最小值", {name: number, "minimum": minimum})
    if maximum is not None and number > maximum:
        raise StrategyValidationError(f"{name} 大于最大值", {name: number, "maximum": maximum})
    return number


def _validated_enum(value: object, allowed: list[str], name: str) -> str:
    if not isinstance(value, str) or value not in allowed:
        raise StrategyValidationError(f"{name} 不在允许范围内", {name: value, "allowed": allowed})
    return value


def _validated_weights(value: object, schema: dict) -> dict[str, float]:
    if not isinstance(value, Mapping):
        raise StrategyValidationError("weights 必须是对象", {"weights": value})
    properties = schema["properties"]
    weights: dict[str, float] = {}
    for key, weight_schema in properties.items():
        raw_value = value.get(key, weight_schema.get("default"))
        weights[key] = _validated_number(raw_value, weight_schema, f"weights.{key}")
    if sum(weights.values()) <= 0:
        raise StrategyValidationError("weights 权重总和必须大于 0", {"weights": weights})
    return weights
