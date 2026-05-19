import json

import duckdb
import pandas as pd

from backend.app.domain.models import PoolType, StockPool


class QuantRepository:
    def __init__(self, connection: duckdb.DuckDBPyConnection):
        self.connection = connection

    def upsert_daily_bars(self, bars: pd.DataFrame) -> None:
        self.connection.register("incoming_daily_bars", bars)
        try:
            self.connection.execute(
                """
                INSERT OR REPLACE INTO daily_bars
                SELECT
                  symbol,
                  CAST(trade_date AS DATE),
                  open,
                  high,
                  low,
                  close,
                  volume,
                  amount,
                  frequency,
                  source
                FROM incoming_daily_bars
                """
            )
        finally:
            self.connection.unregister("incoming_daily_bars")

    def load_daily_bars(self, symbols: list[str], start_date: str, end_date: str) -> pd.DataFrame:
        if not symbols:
            return pd.DataFrame()
        return self.connection.execute(
            """
            SELECT symbol, CAST(trade_date AS VARCHAR) AS trade_date, open, high, low, close,
                   volume, amount, frequency, source
            FROM daily_bars
            WHERE symbol IN (SELECT * FROM UNNEST(?))
              AND trade_date BETWEEN CAST(? AS DATE) AND CAST(? AS DATE)
              AND frequency = '1d'
            ORDER BY trade_date, symbol
            """,
            [symbols, start_date, end_date],
        ).fetch_df()

    def save_stock_pool(self, pool: StockPool, source: str = "local") -> None:
        self.connection.execute(
            """
            INSERT OR REPLACE INTO stock_pools (pool_id, name, pool_type, symbols, source)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                pool.pool_id,
                pool.name,
                pool.pool_type.value,
                json.dumps(list(pool.symbols)),
                source,
            ],
        )

    def list_stock_pools(self) -> list[StockPool]:
        rows = self.connection.execute(
            "SELECT pool_id, name, pool_type, symbols FROM stock_pools ORDER BY pool_id"
        ).fetchall()
        return [
            StockPool(
                pool_id=row[0],
                name=row[1],
                pool_type=PoolType(row[2]),
                symbols=json.loads(row[3]),
            )
            for row in rows
        ]
