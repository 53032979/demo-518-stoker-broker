from collections.abc import Mapping

import pandas as pd

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
