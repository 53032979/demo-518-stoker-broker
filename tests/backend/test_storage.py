import pandas as pd

from backend.app.domain.models import PoolType, StockPool
from backend.app.storage.database import create_connection, initialize_schema
from backend.app.storage.repository import QuantRepository


def test_repository_round_trips_daily_bars(tmp_path):
    connection = create_connection(tmp_path / "test.duckdb")
    initialize_schema(connection)
    repo = QuantRepository(connection)
    bars = pd.DataFrame(
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
                "frequency": "1d",
                "source": "unit",
            }
        ]
    )

    repo.upsert_daily_bars(bars)
    result = repo.load_daily_bars(["000001.SZ"], "2024-01-01", "2024-01-31")

    assert len(result) == 1
    assert result.loc[0, "symbol"] == "000001.SZ"


def test_repository_round_trips_stock_pools(tmp_path):
    connection = create_connection(tmp_path / "test.duckdb")
    initialize_schema(connection)
    repo = QuantRepository(connection)
    pool = StockPool(
        pool_id="core",
        name="核心池",
        pool_type=PoolType.CUSTOM,
        symbols=("000001.SZ", "600519.SH"),
    )

    repo.save_stock_pool(pool, source="unit")
    result = repo.list_stock_pools()

    assert result == [pool]
    assert isinstance(result[0].symbols, tuple)
