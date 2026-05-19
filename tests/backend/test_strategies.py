import pandas as pd

from backend.app.strategies.builtins import get_strategy_templates
from backend.app.strategies.scoring import rank_factor, select_top_n


def test_registry_contains_five_templates():
    templates = get_strategy_templates()

    assert {template.strategy_id for template in templates} == {
        "value_quality",
        "momentum_top_n",
        "low_volatility",
        "multi_factor_score",
        "ma_trend_filter",
    }


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
