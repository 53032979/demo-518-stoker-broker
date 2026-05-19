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
    "frequency",
    "source",
]

DEFAULT_POOLS = {
    "csi300": ["000001.SZ", "600000.SH", "000002.SZ"],
    "csi500": ["000905.SH", "600519.SH", "000858.SZ"],
    "csi1000": ["000852.SH", "300750.SZ", "002415.SZ"],
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
            frame["frequency"] = "1d"
            frame["source"] = "akshare"
            rows.append(frame[DAILY_BAR_COLUMNS])
        if not rows:
            return load_seed_daily_bars(symbols, start_date, end_date)
        return pd.concat(rows, ignore_index=True)
