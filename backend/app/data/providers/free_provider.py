import pandas as pd

DAILY_BAR_COLUMNS = [
    "symbol",
    "trade_date",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "amount",
    "pe",
    "pb",
    "roe",
    "dividend_yield",
    "gross_margin",
    "debt_ratio",
    "turnover",
    "frequency",
    "source",
]

DEFAULT_POOLS = {
    "csi300": [
        "000001.SZ",
        "600000.SH",
        "000002.SZ",
        "600519.SH",
        "000858.SZ",
        "300750.SZ",
        "601318.SH",
        "600036.SH",
        "000333.SZ",
        "002415.SZ",
        "600276.SH",
        "601166.SH",
        "600030.SH",
        "000651.SZ",
        "601888.SH",
        "600900.SH",
        "002594.SZ",
        "600887.SH",
        "300059.SZ",
        "601398.SH",
    ],
    "csi500": [
        "000905.SH",
        "600039.SH",
        "600079.SH",
        "600118.SH",
        "600160.SH",
        "600161.SH",
        "600176.SH",
        "600183.SH",
        "600201.SH",
        "600216.SH",
        "600256.SH",
        "600258.SH",
        "600271.SH",
        "600298.SH",
        "600315.SH",
        "600325.SH",
        "600329.SH",
        "600332.SH",
        "600348.SH",
        "600352.SH",
    ],
    "csi1000": [
        "000852.SH",
        "000021.SZ",
        "000027.SZ",
        "000031.SZ",
        "000039.SZ",
        "000050.SZ",
        "000060.SZ",
        "000089.SZ",
        "000156.SZ",
        "000158.SZ",
        "000400.SZ",
        "000401.SZ",
        "000402.SZ",
        "000415.SZ",
        "000423.SZ",
        "000425.SZ",
        "000426.SZ",
        "000513.SZ",
        "000519.SZ",
        "000528.SZ",
    ],
}


def load_seed_daily_bars(symbols: list[str], start_date: str, end_date: str) -> pd.DataFrame:
    dates = pd.date_range(start_date, end_date, freq="B")
    rows: list[dict] = []
    for index, symbol in enumerate(symbols):
        base = 10.0 + index * 3
        for offset, trade_date in enumerate(dates):
            close = base * (1 + 0.004 * offset + 0.002 * index)
            rows.append(
                {
                    "symbol": symbol,
                    "trade_date": trade_date.strftime("%Y-%m-%d"),
                    "open": close * 0.995,
                    "high": close * 1.01,
                    "low": close * 0.99,
                    "close": close,
                    "volume": 100000 + offset * 1000,
                    "amount": close * (100000 + offset * 1000),
                    "pe": 8.0 + index * 1.8,
                    "pb": 0.9 + index * 0.15,
                    "roe": 0.22 - index * 0.004,
                    "dividend_yield": 0.04 - index * 0.0005,
                    "gross_margin": 0.48 - index * 0.003,
                    "debt_ratio": 0.25 + index * 0.004,
                    "turnover": 0.015 + index * 0.0008 + offset * 0.00005,
                    "frequency": "1d",
                    "source": "seed",
                }
            )
    return pd.DataFrame(rows, columns=DAILY_BAR_COLUMNS)


class FreeMarketDataProvider:
    def __init__(self, prefer_live: bool = False) -> None:
        self.prefer_live = prefer_live

    def load_daily_bars(self, symbols: list[str], start_date: str, end_date: str) -> pd.DataFrame:
        if not self.prefer_live:
            return load_seed_daily_bars(symbols, start_date, end_date)

        try:
            import akshare as ak
        except Exception:
            return load_seed_daily_bars(symbols, start_date, end_date)

        rows: list[pd.DataFrame] = []
        for symbol in symbols:
            ak_symbol = symbol.split(".")[0]
            try:
                raw = ak.stock_zh_a_hist(
                    symbol=ak_symbol,
                    period="daily",
                    start_date=start_date.replace("-", ""),
                    end_date=end_date.replace("-", ""),
                    adjust="qfq",
                )
            except Exception:
                return load_seed_daily_bars(symbols, start_date, end_date)
            if raw.empty:
                continue
            frame = raw.rename(
                columns={
                    "日期": "trade_date",
                    "开盘": "open",
                    "最高": "high",
                    "最低": "low",
                    "收盘": "close",
                    "成交量": "volume",
                    "成交额": "amount",
                }
            )
            frame["trade_date"] = pd.to_datetime(frame["trade_date"]).dt.strftime("%Y-%m-%d")
            frame["symbol"] = symbol
            for column in DAILY_BAR_COLUMNS:
                if column not in frame.columns and column not in {"frequency", "source"}:
                    frame[column] = None
            frame["frequency"] = "1d"
            frame["source"] = "akshare"
            rows.append(frame[DAILY_BAR_COLUMNS])
        if not rows:
            return load_seed_daily_bars(symbols, start_date, end_date)
        return pd.concat(rows, ignore_index=True)
