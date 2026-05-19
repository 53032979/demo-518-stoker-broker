import numpy as np
import pandas as pd

from backend.app.domain.errors import DataValidationError


REQUIRED_DAILY_COLUMNS = [
    "symbol",
    "trade_date",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "amount",
]


def normalize_daily_bars(raw: pd.DataFrame, source: str) -> pd.DataFrame:
    missing = [column for column in REQUIRED_DAILY_COLUMNS if column not in raw.columns]
    if missing:
        raise DataValidationError("缺少日线行情字段", {"missing": missing})

    frame = raw[REQUIRED_DAILY_COLUMNS].copy()
    if frame["symbol"].isna().any():
        raise DataValidationError("证券代码为空", {"column": "symbol"})

    frame["symbol"] = frame["symbol"].astype(str).str.strip().str.upper()
    trade_date_text = frame["trade_date"].astype("string").str.strip()
    compact_trade_dates = trade_date_text.str.fullmatch(r"\d{8}", na=False)
    parsed_trade_dates = pd.Series(pd.NaT, index=frame.index, dtype="datetime64[ns]")
    parsed_trade_dates.loc[compact_trade_dates] = pd.to_datetime(
        trade_date_text.loc[compact_trade_dates],
        format="%Y%m%d",
        errors="coerce",
    )
    parsed_trade_dates.loc[~compact_trade_dates] = pd.to_datetime(
        trade_date_text.loc[~compact_trade_dates],
        errors="coerce",
    )
    frame["trade_date"] = parsed_trade_dates.dt.strftime("%Y-%m-%d")

    numeric_columns = ["open", "high", "low", "close", "volume", "amount"]
    for column in numeric_columns:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    if frame["trade_date"].isna().any():
        raise DataValidationError("日期格式错误", {"column": "trade_date"})
    if frame["symbol"].eq("").any():
        raise DataValidationError("证券代码为空", {"column": "symbol"})
    if frame[numeric_columns].isna().any().any() or not np.isfinite(
        frame[numeric_columns].to_numpy()
    ).all():
        raise DataValidationError("数值字段包含空值或非法值", {"columns": numeric_columns})
    if (frame[["volume", "amount"]] < 0).any().any():
        raise DataValidationError("成交量和成交额不能为负", {"columns": ["volume", "amount"]})
    if (frame[["open", "high", "low", "close"]] <= 0).any().any():
        raise DataValidationError("价格必须大于 0", {})
    if (frame["high"] < frame[["open", "low", "close"]].max(axis=1)).any():
        raise DataValidationError("最高价小于开盘价、最低价或收盘价", {})
    if (frame["low"] > frame[["open", "high", "close"]].min(axis=1)).any():
        raise DataValidationError("最低价大于开盘价、最高价或收盘价", {})
    if frame.duplicated(["symbol", "trade_date"]).any():
        raise DataValidationError("存在重复的 symbol + trade_date 行", {})

    frame["frequency"] = "1d"
    frame["source"] = source
    return frame.sort_values(["symbol", "trade_date"]).reset_index(drop=True)
