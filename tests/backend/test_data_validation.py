import pandas as pd
import pytest

from backend.app.data.validators import normalize_daily_bars
from backend.app.domain.errors import DataValidationError


def test_normalize_daily_bars_accepts_required_columns():
    raw = pd.DataFrame(
        [
            {
                "symbol": "000001.SZ",
                "trade_date": "2024-01-02",
                "open": 10.0,
                "high": 11.0,
                "low": 9.5,
                "close": 10.5,
                "volume": 100000,
                "amount": 1050000,
            }
        ]
    )

    result = normalize_daily_bars(raw, source="unit")

    assert list(result.columns) == [
        "symbol",
        "trade_date",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "amount",
        "frequency",
        "source",
    ]
    assert result.loc[0, "frequency"] == "1d"


def test_normalize_daily_bars_rejects_invalid_prices():
    raw = pd.DataFrame(
        [
            {
                "symbol": "000001.SZ",
                "trade_date": "2024-01-02",
                "open": 10.0,
                "high": 9.0,
                "low": 9.5,
                "close": 10.5,
                "volume": 100000,
                "amount": 1050000,
            }
        ]
    )

    with pytest.raises(DataValidationError):
        normalize_daily_bars(raw, source="unit")
