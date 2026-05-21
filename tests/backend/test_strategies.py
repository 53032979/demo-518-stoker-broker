from collections.abc import Mapping

import pandas as pd

from backend.app.api.schemas import BacktestRequest
from backend.app.data.providers.free_provider import DEFAULT_POOLS
from backend.app.services.backtest_service import run_backtest
from backend.app.strategies.builtins import get_strategy_templates
from backend.app.strategies.scoring import rank_factor, select_top_n


def _plain(value):
    if isinstance(value, Mapping):
        return {key: _plain(item) for key, item in value.items()}
    return value


def test_registry_contains_five_templates():
    templates = get_strategy_templates()
    strategy_ids = [template.strategy_id for template in templates]

    assert len(templates) == 5
    assert len(strategy_ids) == len(set(strategy_ids))
    assert set(strategy_ids) == {
        "value_quality",
        "momentum_top_n",
        "low_volatility",
        "multi_factor_score",
        "ma_trend_filter",
    }


def test_default_parameters_are_declared_in_schema_properties():
    for template in get_strategy_templates():
        properties = template.parameter_schema["properties"]

        assert set(template.default_parameters) <= set(properties), template.strategy_id


def test_schema_defaults_match_default_parameters():
    for template in get_strategy_templates():
        properties = template.parameter_schema["properties"]
        for key, expected_default in template.default_parameters.items():
            if "default" not in properties[key]:
                continue

            assert _plain(properties[key]["default"]) == _plain(
                expected_default
            ), f"{template.strategy_id}.{key}"


def test_strategy_defaults_do_not_select_entire_seed_pool():
    smallest_seed_pool = min(len(symbols) for symbols in DEFAULT_POOLS.values())

    for template in get_strategy_templates():
        assert template.default_parameters["top_n"] < smallest_seed_pool, template.strategy_id


def test_default_seed_runs_show_different_strategy_curves():
    final_returns = set()
    for template in get_strategy_templates():
        request = BacktestRequest(
            strategy_id=template.strategy_id,
            pool_id="csi300",
            start_date="2024-01-01",
            end_date="2024-12-31",
            parameters=_plain(template.default_parameters),
            costs={
                "commission_rate": 0.0003,
                "stamp_tax_rate": 0.001,
                "slippage_bps": 5,
                "min_lot_size": 100,
            },
        )
        result = run_backtest(request)
        final_returns.add(round(result["result"]["metrics"]["total_return"], 6))

    assert len(final_returns) > 1


def test_rank_factor_supports_descending_and_missing_values():
    frame = pd.DataFrame(
        {"symbol": ["A", "B", "C"], "momentum": [0.2, None, 0.1]}
    )

    ranked = rank_factor(frame, "momentum", ascending=False)

    assert ranked["symbol"].tolist() == ["A", "C"]
    assert ranked["momentum_rank"].tolist() == [1.0, 2.0]


def test_select_top_n_uses_weighted_score():
    frame = pd.DataFrame(
        {
            "symbol": ["A", "B", "C"],
            "value_score": [3.0, 1.0, 2.0],
            "quality_score": [1.0, 3.0, 2.0],
        }
    )

    selected = select_top_n(frame, {"value_score": 0.7, "quality_score": 0.3}, top_n=2)

    assert selected["symbol"].tolist() == ["A", "C"]
