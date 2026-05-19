import pytest
from fastapi.testclient import TestClient

from backend.app.main import create_app


def _backtest_payload(parameters: dict | None = None) -> dict:
    return {
        "strategy_id": "momentum_top_n",
        "pool_id": "csi300",
        "start_date": "2024-01-01",
        "end_date": "2024-01-10",
        "parameters": parameters
        or {"top_n": 2, "rebalance": "monthly", "weighting": "equal"},
        "costs": {
            "commission_rate": 0,
            "stamp_tax_rate": 0,
            "slippage_bps": 0,
            "min_lot_size": 100,
        },
    }


def test_strategies_endpoint_returns_templates(tmp_path):
    with TestClient(create_app(tmp_path / "test.duckdb")) as client:
        response = client.get("/strategies")

        assert response.status_code == 200
        assert len(response.json()) == 5


def test_pools_endpoint_returns_default_index_pools(tmp_path):
    with TestClient(create_app(tmp_path / "test.duckdb")) as client:
        response = client.get("/pools")

        assert response.status_code == 200
        pool_ids = {pool["pool_id"] for pool in response.json()}
        assert {"csi300", "csi500", "csi1000"}.issubset(pool_ids)


def test_app_lifespan_releases_duckdb_connection(tmp_path):
    db_path = tmp_path / "test.duckdb"

    with TestClient(create_app(db_path)) as client:
        assert client.get("/health").json() == {"status": "ok"}

    with TestClient(create_app(db_path)) as client:
        assert client.get("/health").json() == {"status": "ok"}


def test_backtest_endpoint_returns_completed_result_for_seed_data(tmp_path):
    with TestClient(create_app(tmp_path / "test.duckdb")) as client:
        response = client.post("/backtests", json=_backtest_payload())

        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "completed"
        assert payload["result"]["metrics"]["total_return"] is not None
        assert payload["result"]["equity_curve"]


def test_data_upload_endpoint_validates_and_persists_csv(tmp_path):
    csv_bytes = (
        "symbol,trade_date,open,high,low,close,volume,amount\n"
        "000001.SZ,2024-01-02,10,11,9.5,10.5,100000,1050000\n"
    ).encode("utf-8")
    with TestClient(create_app(tmp_path / "test.duckdb")) as client:
        response = client.post(
            "/data/uploads",
            files={"file": ("daily.csv", csv_bytes, "text/csv")},
        )

        assert response.status_code == 200
        assert response.json()["rows"] == 1
        assert response.json()["status"] == "validated"
        persisted = client.app.state.repository.load_daily_bars(
            ["000001.SZ"],
            "2024-01-01",
            "2024-01-31",
        )
        assert persisted.to_dict(orient="records") == [
            {
                "symbol": "000001.SZ",
                "trade_date": "2024-01-02",
                "open": 10.0,
                "high": 11.0,
                "low": 9.5,
                "close": 10.5,
                "volume": 100000.0,
                "amount": 1050000.0,
                "frequency": "1d",
                "source": "daily.csv",
            }
        ]


@pytest.mark.parametrize("top_n", ["abc", 1.9, True, 0, 501])
def test_backtest_endpoint_rejects_invalid_top_n(tmp_path, top_n):
    with TestClient(create_app(tmp_path / "test.duckdb")) as client:
        response = client.post(
            "/backtests",
            json=_backtest_payload({"top_n": top_n, "rebalance": "monthly", "weighting": "equal"}),
        )

        assert response.status_code == 400
        assert response.json()["code"] == "strategy_validation_error"


def test_backtest_endpoint_rejects_weekend_only_seed_range(tmp_path):
    payload = _backtest_payload()
    payload["start_date"] = "2024-01-06"
    payload["end_date"] = "2024-01-07"
    with TestClient(create_app(tmp_path / "test.duckdb")) as client:
        response = client.post("/backtests", json=payload)

        assert response.status_code == 400
        assert response.json()["code"] == "backtest_runtime_error"


def test_data_upload_endpoint_rejects_invalid_csv(tmp_path):
    with TestClient(create_app(tmp_path / "test.duckdb")) as client:
        response = client.post(
            "/data/uploads",
            files={"file": ("daily.csv", b'not,"valid\ncsv', "text/csv")},
        )

        assert response.status_code == 400
        assert response.json()["code"] == "data_validation_error"
