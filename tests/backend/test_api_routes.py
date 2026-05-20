import pytest
from fastapi.testclient import TestClient

from backend.app.main import create_app


def _backtest_payload(parameters: dict | None = None, pool_id: str = "csi300") -> dict:
    return {
        "strategy_id": "momentum_top_n",
        "pool_id": pool_id,
        "start_date": "2024-01-01",
        "end_date": "2024-01-10",
        "parameters": parameters
        if parameters is not None
        else {"top_n": 2, "rebalance": "monthly", "weighting": "equal"},
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


@pytest.mark.parametrize("origin", ["http://localhost:5173", "http://127.0.0.1:5173"])
def test_local_browser_origin_receives_cors_header(tmp_path, origin):
    with TestClient(create_app(tmp_path / "test.duckdb")) as client:
        response = client.get("/strategies", headers={"origin": origin})
        remote_response = client.get("/strategies", headers={"origin": "https://example.com"})

        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == origin
        assert "access-control-allow-origin" not in remote_response.headers


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


@pytest.mark.parametrize("pool_id", ["csi300", "csi500", "csi1000"])
def test_default_pool_supports_default_top_n_backtest(tmp_path, pool_id):
    with TestClient(create_app(tmp_path / "test.duckdb")) as client:
        pools_response = client.get("/pools")
        pool = next(pool for pool in pools_response.json() if pool["pool_id"] == pool_id)

        assert len(pool["symbols"]) >= 20

        response = client.post("/backtests", json=_backtest_payload({}, pool_id=pool_id))

        assert response.status_code == 200
        assert response.json()["status"] == "completed"


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


def test_backtest_endpoint_rejects_top_n_larger_than_pool_size(tmp_path):
    with TestClient(create_app(tmp_path / "test.duckdb")) as client:
        response = client.post(
            "/backtests",
            json=_backtest_payload({"top_n": 21, "rebalance": "monthly", "weighting": "equal"}),
        )

        assert response.status_code == 400
        assert response.json()["code"] == "strategy_validation_error"


def test_backtest_endpoint_rejects_non_finite_raw_top_n(tmp_path):
    raw_payload = """
    {
      "strategy_id": "momentum_top_n",
      "pool_id": "csi300",
      "start_date": "2024-01-01",
      "end_date": "2024-01-10",
      "parameters": {"top_n": 1e999, "rebalance": "monthly", "weighting": "equal"},
      "costs": {
        "commission_rate": 0,
        "stamp_tax_rate": 0,
        "slippage_bps": 0,
        "min_lot_size": 100
      }
    }
    """
    with TestClient(
        create_app(tmp_path / "test.duckdb"),
        raise_server_exceptions=False,
    ) as client:
        response = client.post(
            "/backtests",
            content=raw_payload,
            headers={"content-type": "application/json"},
        )

        assert response.status_code == 400
        payload = response.json()
        assert payload["code"] == "strategy_validation_error"
        assert payload["details"]["top_n"] == "inf"


def test_backtest_endpoint_returns_structured_error_for_non_finite_request_validation(
    tmp_path,
):
    raw_payload = """
    {
      "strategy_id": "momentum_top_n",
      "pool_id": "csi300",
      "start_date": "2024-01-01",
      "end_date": "2024-01-10",
      "parameters": {"top_n": 2, "rebalance": "monthly", "weighting": "equal"},
      "costs": {
        "commission_rate": 1e999,
        "stamp_tax_rate": 0,
        "slippage_bps": 0,
        "min_lot_size": 100
      }
    }
    """
    with TestClient(
        create_app(tmp_path / "test.duckdb"),
        raise_server_exceptions=False,
    ) as client:
        response = client.post(
            "/backtests",
            content=raw_payload,
            headers={"content-type": "application/json"},
        )

        assert response.status_code == 400
        payload = response.json()
        assert payload["code"] == "request_validation_error"
        assert payload["details"]


def test_backtest_endpoint_returns_structured_error_for_reversed_dates(tmp_path):
    with TestClient(
        create_app(tmp_path / "test.duckdb"),
        raise_server_exceptions=False,
    ) as client:
        payload = _backtest_payload()
        payload["start_date"] = "2024-01-10"
        payload["end_date"] = "2024-01-01"

        response = client.post("/backtests", json=payload)

        assert response.status_code == 400
        body = response.json()
        assert body["code"] == "request_validation_error"
        assert body["details"]


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


def test_data_upload_endpoint_rejects_header_only_csv(tmp_path):
    csv_bytes = "symbol,trade_date,open,high,low,close,volume,amount\n".encode("utf-8")

    with TestClient(create_app(tmp_path / "test.duckdb")) as client:
        response = client.post(
            "/data/uploads",
            files={"file": ("daily.csv", csv_bytes, "text/csv")},
        )

        assert response.status_code == 400
        assert response.json()["code"] == "data_validation_error"


def test_data_upload_endpoint_rejects_missing_file(tmp_path):
    with TestClient(create_app(tmp_path / "test.duckdb")) as client:
        response = client.post("/data/uploads")

        assert response.status_code == 400
        assert response.json()["code"] == "data_validation_error"


def test_data_upload_endpoint_rejects_wrong_file_field(tmp_path):
    csv_bytes = (
        "symbol,trade_date,open,high,low,close,volume,amount\n"
        "000001.SZ,2024-01-02,10,11,9.5,10.5,100000,1050000\n"
    ).encode("utf-8")

    with TestClient(create_app(tmp_path / "test.duckdb")) as client:
        response = client.post(
            "/data/uploads",
            files={"wrong": ("daily.csv", csv_bytes, "text/csv")},
        )

        assert response.status_code == 400
        assert response.json()["code"] == "data_validation_error"


def test_data_upload_endpoint_rejects_non_file_upload_field(tmp_path):
    with TestClient(create_app(tmp_path / "test.duckdb")) as client:
        response = client.post(
            "/data/uploads",
            files={"file": (None, "abc")},
        )

        assert response.status_code == 400
        assert response.json()["code"] == "data_validation_error"
