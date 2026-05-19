import pandas as pd
import pytest

from backend.app.data.validators import normalize_daily_bars
from backend.app.domain.errors import DataValidationError


def _valid_bar(**overrides):
    bar = {
        "symbol": "000001.SZ",
        "trade_date": "2024-01-02",
        "open": 10.0,
        "high": 11.0,
        "low": 9.5,
        "close": 10.5,
        "volume": 100000,
        "amount": 1050000,
    }
    bar.update(overrides)
    return bar


def test_normalize_daily_bars_accepts_required_columns():
    raw = pd.DataFrame([_valid_bar()])
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


@pytest.mark.parametrize("trade_date", [20240102, "20240102"])
def test_normalize_daily_bars_accepts_compact_yyyymmdd_trade_dates(trade_date):
    raw = pd.DataFrame([_valid_bar(trade_date=trade_date)])

    result = normalize_daily_bars(raw, source="unit")

    assert result.loc[0, "trade_date"] == "2024-01-02"


def test_normalize_daily_bars_rejects_missing_required_columns():
    raw = pd.DataFrame([{key: value for key, value in _valid_bar().items() if key != "amount"}])

    with pytest.raises(DataValidationError) as exc_info:
        normalize_daily_bars(raw, source="unit")

    assert exc_info.value.details == {"missing": ["amount"]}


def test_normalize_daily_bars_rejects_bad_dates():
    raw = pd.DataFrame([_valid_bar(trade_date="not-a-date")])

    with pytest.raises(DataValidationError, match="日期格式错误"):
        normalize_daily_bars(raw, source="unit")


@pytest.mark.parametrize("symbol", ["   ", None, pd.NA, float("nan")])
def test_normalize_daily_bars_rejects_empty_or_null_symbols(symbol):
    raw = pd.DataFrame([_valid_bar(symbol=symbol)])

    with pytest.raises(DataValidationError, match="证券代码为空"):
        normalize_daily_bars(raw, source="unit")


@pytest.mark.parametrize("column", ["open", "high", "low", "close", "volume", "amount"])
def test_normalize_daily_bars_rejects_non_numeric_numeric_fields(column):
    raw = pd.DataFrame([_valid_bar(**{column: "not-a-number"})])

    with pytest.raises(DataValidationError, match="数值字段包含空值或非法值"):
        normalize_daily_bars(raw, source="unit")


@pytest.mark.parametrize("column", ["open", "high", "low", "close"])
def test_normalize_daily_bars_rejects_non_positive_ohlc_prices(column):
    raw = pd.DataFrame([_valid_bar(**{column: 0})])

    with pytest.raises(DataValidationError, match="价格必须大于 0"):
        normalize_daily_bars(raw, source="unit")


@pytest.mark.parametrize(
    "overrides,error_message",
    [
        ({"high": 9.0}, "最高价小于开盘价、最低价或收盘价"),
        ({"low": 10.75}, "最低价大于开盘价、最高价或收盘价"),
    ],
)
def test_normalize_daily_bars_rejects_invalid_high_low_relationships(
    overrides, error_message
):
    raw = pd.DataFrame([_valid_bar(**overrides)])

    with pytest.raises(DataValidationError, match=error_message):
        normalize_daily_bars(raw, source="unit")


def test_normalize_daily_bars_rejects_duplicate_symbol_trade_date():
    raw = pd.DataFrame([_valid_bar(), _valid_bar()])

    with pytest.raises(DataValidationError):
        normalize_daily_bars(raw, source="unit")
