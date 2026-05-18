import pytest
from pydantic import ValidationError

from backend.app.api.schemas import BacktestRequest, CostConfig, PoolCreateRequest


def test_backtest_request_accepts_valid_payload():
    request = BacktestRequest(
        strategy_id="multi_factor_score",
        pool_id="csi300",
        start_date="2024-01-01",
        end_date="2024-12-31",
        parameters={"top_n": 20, "rebalance": "monthly"},
        costs=CostConfig(commission_rate=0.0003, stamp_tax_rate=0.001, slippage_bps=5),
    )

    assert request.strategy_id == "multi_factor_score"
    assert request.costs.slippage_bps == 5


def test_pool_create_rejects_empty_symbols():
    with pytest.raises(ValidationError):
        PoolCreateRequest(name="空股票池", symbols=[])
