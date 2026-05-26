from collections.abc import Mapping

import pandas as pd


def rank_factor(frame: pd.DataFrame, column: str, ascending: bool) -> pd.DataFrame:
    cleaned = frame[["symbol", column]].dropna().copy()
    cleaned[f"{column}_rank"] = cleaned[column].rank(method="first", ascending=ascending)
    return cleaned.sort_values(f"{column}_rank").reset_index(drop=True)


def select_top_n(frame: pd.DataFrame, weights: Mapping[str, float], top_n: int) -> pd.DataFrame:
    if top_n <= 0:
        return frame.iloc[0:0].copy()
    scored = frame[["symbol", *weights.keys()]].dropna().copy()
    scored["score"] = 0.0
    for column, weight in weights.items():
        scored["score"] += scored[column] * weight
    return (
        scored.sort_values(["score", "symbol"], ascending=[False, True])
        .head(top_n)
        .reset_index(drop=True)
    )
