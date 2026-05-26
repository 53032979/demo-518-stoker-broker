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
            pe DOUBLE,
            pb DOUBLE,
            roe DOUBLE,
            dividend_yield DOUBLE,
            gross_margin DOUBLE,
            debt_ratio DOUBLE,
            turnover DOUBLE,
            frequency VARCHAR NOT NULL,
            source VARCHAR NOT NULL,
            PRIMARY KEY(symbol, trade_date, frequency, source)
        )
        """
    )
    for column in (
        "pe",
        "pb",
        "roe",
        "dividend_yield",
        "gross_margin",
        "debt_ratio",
        "turnover",
    ):
        connection.execute(f"ALTER TABLE daily_bars ADD COLUMN IF NOT EXISTS {column} DOUBLE")
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
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS backtest_runs (
            run_id VARCHAR PRIMARY KEY,
            status VARCHAR NOT NULL,
            request_payload VARCHAR NOT NULL,
            response_payload VARCHAR NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
