from pathlib import Path

import duckdb


def create_connection(path: str | Path) -> duckdb.DuckDBPyConnection:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(path))


def initialize_schema(connection: duckdb.DuckDBPyConnection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS daily_bars (
            symbol VARCHAR NOT NULL,
            trade_date DATE NOT NULL,
            open DOUBLE NOT NULL,
            high DOUBLE NOT NULL,
            low DOUBLE NOT NULL,
            close DOUBLE NOT NULL,
            volume DOUBLE NOT NULL,
            amount DOUBLE NOT NULL,
            frequency VARCHAR NOT NULL,
            source VARCHAR NOT NULL,
            PRIMARY KEY(symbol, trade_date, frequency, source)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS stock_pools (
            pool_id VARCHAR PRIMARY KEY,
            name VARCHAR NOT NULL,
            pool_type VARCHAR NOT NULL,
            symbols VARCHAR NOT NULL,
            source VARCHAR NOT NULL
        )
        """
    )
