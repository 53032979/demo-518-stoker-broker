from fastapi.testclient import TestClient

from backend.app.main import create_app


def test_strategies_endpoint_returns_templates():
    client = TestClient(create_app())

    response = client.get("/strategies")

    assert response.status_code == 200
    assert len(response.json()) == 5


def test_pools_endpoint_returns_default_index_pools():
    client = TestClient(create_app())

    response = client.get("/pools")

    assert response.status_code == 200
    pool_ids = {pool["pool_id"] for pool in response.json()}
    assert {"csi300", "csi500", "csi1000"}.issubset(pool_ids)


def test_backtest_endpoint_returns_completed_result_for_seed_data():
    client = TestClient(create_app())

    response = client.post(
        "/backtests",
        json={
            "strategy_id": "momentum_top_n",
            "pool_id": "csi300",
            "start_date": "2024-01-01",
            "end_date": "2024-01-10",
            "parameters": {"top_n": 2, "rebalance": "monthly", "weighting": "equal"},
            "costs": {
                "commission_rate": 0,
                "stamp_tax_rate": 0,
                "slippage_bps": 0,
                "min_lot_size": 100,
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "completed"
    assert payload["result"]["metrics"]["total_return"] is not None
    assert payload["result"]["equity_curve"]


def test_data_upload_endpoint_validates_and_persists_csv():
    client = TestClient(create_app())
    csv_bytes = (
        "symbol,trade_date,open,high,low,close,volume,amount\n"
        "000001.SZ,2024-01-02,10,11,9.5,10.5,100000,1050000\n"
    ).encode("utf-8")

    response = client.post(
        "/data/uploads",
        files={"file": ("daily.csv", csv_bytes, "text/csv")},
    )

    assert response.status_code == 200
    assert response.json()["rows"] == 1
    assert response.json()["status"] == "validated"
