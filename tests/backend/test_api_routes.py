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


def test_custom_pool_create_validate_and_list(tmp_path):
    with TestClient(create_app(tmp_path / "test.duckdb")) as client:
        validate_response = client.post(
            "/pools/validate",
            json={"symbols": [" 000001.sz ", "600519.SH"]},
        )
        assert validate_response.status_code == 200
        assert validate_response.json()["symbols"] == ["000001.SZ", "600519.SH"]

        create_response = client.post(
            "/pools",
            json={"name": "核心池", "symbols": [" 000001.sz ", "600519.SH"]},
        )

        assert create_response.status_code == 200
        pool = create_response.json()
        assert pool["pool_type"] == "custom"
        assert pool["symbols"] == ["000001.SZ", "600519.SH"]

        list_response = client.get("/pools")
        listed = {item["pool_id"]: item for item in list_response.json()}
        assert listed[pool["pool_id"]] == pool


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
        assert payload["result"]["price_bars"]


def test_strategy_ids_select_different_symbols_on_uploaded_data(tmp_path):
    rows = [
        "symbol,trade_date,open,high,low,close,volume,amount",
        "AAA.SZ,2024-01-02,10,10.2,9.8,10,100000,1000000",
        "AAA.SZ,2024-01-03,10.8,11.0,10.6,10.8,100000,1080000",
        "AAA.SZ,2024-01-04,11.6,11.8,11.4,11.6,100000,1160000",
        "BBB.SZ,2024-01-02,20,20.2,19.8,20,100000,2000000",
        "BBB.SZ,2024-01-03,20.1,20.3,19.9,20.1,100000,2010000",
        "BBB.SZ,2024-01-04,20.2,20.4,20.0,20.2,100000,2020000",
    ]
    csv_bytes = ("\n".join(rows) + "\n").encode("utf-8")

    with TestClient(create_app(tmp_path / "test.duckdb")) as client:
        upload = client.post(
            "/data/uploads",
            files={"file": ("strategy.csv", csv_bytes, "text/csv")},
        )
        pool_id = upload.json()["pool"]["pool_id"]
        base_payload = _backtest_payload(
            {"top_n": 1, "rebalance": "monthly", "weighting": "equal", "lookback": 2},
            pool_id=pool_id,
        )
        base_payload["start_date"] = "2024-01-02"
        base_payload["end_date"] = "2024-01-04"

        momentum = client.post("/backtests", json=base_payload).json()
        low_vol_payload = dict(base_payload, strategy_id="low_volatility")
        low_vol = client.post("/backtests", json=low_vol_payload).json()

        momentum_symbols = {trade["symbol"] for trade in momentum["result"]["trades"]}
        low_vol_symbols = {trade["symbol"] for trade in low_vol["result"]["trades"]}
        assert momentum_symbols == {"AAA.SZ"}
        assert low_vol_symbols == {"BBB.SZ"}


def test_uploaded_csv_pool_can_be_backtested_and_affects_run(tmp_path):
    csv_bytes = (
        "symbol,trade_date,open,high,low,close,volume,amount\n"
        "ZZZ.SZ,2024-01-02,50,51,49,50,100000,5000000\n"
        "ZZZ.SZ,2024-01-03,54.5,55,54,54.5,100000,5450000\n"
        "YYY.SZ,2024-01-02,10,10.2,9.8,10,100000,1000000\n"
        "YYY.SZ,2024-01-03,10.1,10.3,9.9,10.1,100000,1010000\n"
    ).encode("utf-8")

    with TestClient(create_app(tmp_path / "test.duckdb")) as client:
        upload = client.post(
            "/data/uploads",
            files={"file": ("custom.csv", csv_bytes, "text/csv")},
        )

        assert upload.status_code == 200
        pool = upload.json()["pool"]
        payload = _backtest_payload(
            {"top_n": 1, "rebalance": "monthly", "weighting": "equal", "lookback": 1},
            pool_id=pool["pool_id"],
        )
        payload["start_date"] = "2024-01-02"
        payload["end_date"] = "2024-01-03"

        response = client.post("/backtests", json=payload)

        assert response.status_code == 200
        traded_symbols = {trade["symbol"] for trade in response.json()["result"]["trades"]}
        assert traded_symbols == {"ZZZ.SZ"}


def test_value_quality_uses_uploaded_factor_columns(tmp_path):
    csv_bytes = (
        "symbol,trade_date,open,high,low,close,volume,amount,pe,pb,roe\n"
        "AAA.SZ,2024-01-02,10,10.2,9.8,10,100000,1000000,30,4,0.05\n"
        "BBB.SZ,2024-01-02,10,10.2,9.8,10,100000,1000000,8,1,0.20\n"
    ).encode("utf-8")

    with TestClient(create_app(tmp_path / "test.duckdb")) as client:
        upload = client.post(
            "/data/uploads",
            files={"file": ("factors.csv", csv_bytes, "text/csv")},
        )
        payload = _backtest_payload(
            {"top_n": 1, "rebalance": "monthly", "weighting": "equal"},
            pool_id=upload.json()["pool"]["pool_id"],
        )
        payload["strategy_id"] = "value_quality"
        payload["start_date"] = "2024-01-02"
        payload["end_date"] = "2024-01-02"

        response = client.post("/backtests", json=payload)

        assert response.status_code == 200
        traded_symbols = {trade["symbol"] for trade in response.json()["result"]["trades"]}
        assert traded_symbols == {"BBB.SZ"}


def test_ma_trend_filter_does_not_trade_when_all_symbols_are_downtrend(tmp_path):
    csv_bytes = (
        "symbol,trade_date,open,high,low,close,volume,amount\n"
        "AAA.SZ,2024-01-01,10,10.2,9.8,10,100000,1000000\n"
        "AAA.SZ,2024-01-02,9,9.2,8.8,9,100000,900000\n"
        "AAA.SZ,2024-01-03,8,8.2,7.8,8,100000,800000\n"
    ).encode("utf-8")

    with TestClient(create_app(tmp_path / "test.duckdb")) as client:
        upload = client.post(
            "/data/uploads",
            files={"file": ("downtrend.csv", csv_bytes, "text/csv")},
        )
        payload = _backtest_payload(
            {
                "top_n": 1,
                "rebalance": "monthly",
                "weighting": "equal",
                "ma_fast": 1,
                "ma_slow": 3,
            },
            pool_id=upload.json()["pool"]["pool_id"],
        )
        payload["strategy_id"] = "ma_trend_filter"
        payload["start_date"] = "2024-01-01"
        payload["end_date"] = "2024-01-03"

        response = client.post("/backtests", json=payload)

        assert response.status_code == 400
        assert response.json()["code"] == "backtest_runtime_error"


def test_uploaded_pool_uses_latest_bound_source_for_same_symbols(tmp_path):
    old_csv = (
        "symbol,trade_date,open,high,low,close,volume,amount\n"
        "AAA.SZ,2024-01-02,10,10.2,9.8,10,100000,1000000\n"
    ).encode("utf-8")
    new_csv = (
        "symbol,trade_date,open,high,low,close,volume,amount\n"
        "AAA.SZ,2024-01-02,20,20.2,19.8,20,100000,2000000\n"
    ).encode("utf-8")

    with TestClient(create_app(tmp_path / "test.duckdb")) as client:
        client.post("/data/uploads", files={"file": ("zzz_old.csv", old_csv, "text/csv")})
        upload = client.post(
            "/data/uploads",
            files={"file": ("aaa_new.csv", new_csv, "text/csv")},
        )
        pool_id = upload.json()["pool"]["pool_id"]
        payload = _backtest_payload(
            {"top_n": 1, "rebalance": "monthly", "weighting": "equal", "lookback": 1},
            pool_id=pool_id,
        )
        payload["start_date"] = "2024-01-02"
        payload["end_date"] = "2024-01-02"

        response = client.post("/backtests", json=payload)

        assert response.status_code == 200
        buy = response.json()["result"]["trades"][0]
        assert buy["symbol"] == "AAA.SZ"
        assert buy["price"] == 20.0


def test_uploaded_pool_id_keeps_older_same_symbol_upload_bound_to_its_source(tmp_path):
    old_csv = (
        "symbol,trade_date,open,high,low,close,volume,amount\n"
        "AAA.SZ,2024-01-02,10,10.2,9.8,10,100000,1000000\n"
    ).encode("utf-8")
    new_csv = (
        "symbol,trade_date,open,high,low,close,volume,amount\n"
        "AAA.SZ,2024-01-02,20,20.2,19.8,20,100000,2000000\n"
    ).encode("utf-8")

    with TestClient(create_app(tmp_path / "test.duckdb")) as client:
        old_upload = client.post(
            "/data/uploads",
            files={"file": ("zzz_old.csv", old_csv, "text/csv")},
        )
        new_upload = client.post(
            "/data/uploads",
            files={"file": ("aaa_new.csv", new_csv, "text/csv")},
        )
        assert old_upload.json()["pool"]["pool_id"] != new_upload.json()["pool"]["pool_id"]
        payload = _backtest_payload(
            {"top_n": 1, "rebalance": "monthly", "weighting": "equal", "lookback": 1},
            pool_id=old_upload.json()["pool"]["pool_id"],
        )
        payload["start_date"] = "2024-01-02"
        payload["end_date"] = "2024-01-02"

        response = client.post("/backtests", json=payload)

        assert response.status_code == 200
        buy = response.json()["result"]["trades"][0]
        assert buy["symbol"] == "AAA.SZ"
        assert buy["price"] == 10.0


def test_custom_pool_with_partial_uploaded_coverage_keeps_all_pool_members(tmp_path):
    csv_bytes = (
        "symbol,trade_date,open,high,low,close,volume,amount\n"
        "AAA.SZ,2024-01-02,10,10.2,9.8,10,100000,1000000\n"
    ).encode("utf-8")

    with TestClient(create_app(tmp_path / "test.duckdb")) as client:
        client.post("/data/uploads", files={"file": ("partial.csv", csv_bytes, "text/csv")})
        pool = client.post(
            "/pools",
            json={"name": "混合池", "symbols": ["AAA.SZ", "BBB.SZ"]},
        ).json()
        payload = _backtest_payload(
            {"top_n": 2, "rebalance": "monthly", "weighting": "equal", "lookback": 1},
            pool_id=pool["pool_id"],
        )
        payload["start_date"] = "2024-01-02"
        payload["end_date"] = "2024-01-02"

        response = client.post("/backtests", json=payload)

        assert response.status_code == 200
        traded_symbols = {trade["symbol"] for trade in response.json()["result"]["trades"]}
        assert traded_symbols == {"AAA.SZ", "BBB.SZ"}


def test_stop_loss_parameter_triggers_real_sell_trade(tmp_path):
    csv_bytes = (
        "symbol,trade_date,open,high,low,close,volume,amount\n"
        "AAA.SZ,2024-01-01,10,10.2,9.8,10,100000,1000000\n"
        "AAA.SZ,2024-01-08,9.4,9.5,9.3,9.4,100000,940000\n"
    ).encode("utf-8")

    with TestClient(create_app(tmp_path / "test.duckdb")) as client:
        upload = client.post(
            "/data/uploads",
            files={"file": ("stop_loss.csv", csv_bytes, "text/csv")},
        )
        payload = _backtest_payload(
            {
                "top_n": 1,
                "rebalance": "weekly",
                "weighting": "equal",
                "lookback": 1,
                "stop_loss": 0.05,
            },
            pool_id=upload.json()["pool"]["pool_id"],
        )
        payload["start_date"] = "2024-01-01"
        payload["end_date"] = "2024-01-08"

        response = client.post("/backtests", json=payload)

        assert response.status_code == 200
        trades = response.json()["result"]["trades"]
        assert [trade["side"] for trade in trades] == ["buy", "sell"]
        assert trades[1]["reason"] == "stop_loss"


def test_backtest_run_retrieval_endpoints_return_persisted_data(tmp_path):
    with TestClient(create_app(tmp_path / "test.duckdb")) as client:
        created = client.post("/backtests", json=_backtest_payload()).json()
        run_id = created["run_id"]

        full = client.get(f"/backtests/{run_id}")
        status = client.get(f"/backtests/{run_id}/status")
        results = client.get(f"/backtests/{run_id}/results")
        logs = client.get(f"/backtests/{run_id}/logs")

        assert full.status_code == 200
        assert full.json() == created
        assert status.json() == {"run_id": run_id, "status": "completed", "message": ""}
        assert results.json() == created["result"]
        assert logs.json() == {"run_id": run_id, "logs": created["result"]["logs"]}


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
        assert response.json()["pool"]["symbols"] == ["000001.SZ"]
        persisted = client.app.state.repository.load_daily_bars(
            ["000001.SZ"],
            "2024-01-01",
            "2024-01-31",
        )
        assert persisted[
            [
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
        ].to_dict(orient="records") == [
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
        assert {"pe", "pb", "roe"}.issubset(persisted.columns)


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


def test_data_upload_endpoint_rejects_unknown_extension(tmp_path):
    with TestClient(create_app(tmp_path / "test.duckdb")) as client:
        response = client.post(
            "/data/uploads",
            files={"file": ("daily.txt", b"symbol,trade_date\n", "text/plain")},
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
