from datetime import date

import pytest
from pydantic import ValidationError

from backend.app.api.schemas import BacktestRequest, CostConfig, PoolCreateRequest
from backend.app.domain.errors import QuantLabError
from backend.app.domain.models import PoolType, StockPool, StrategyTemplate


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
    assert request.start_date == date(2024, 1, 1)
    assert request.costs.slippage_bps == 5


def test_pool_create_rejects_empty_symbols():
    with pytest.raises(ValidationError):
        PoolCreateRequest(name="空股票池", symbols=[])


def test_backtest_request_rejects_invalid_date_format():
    with pytest.raises(ValidationError):
        BacktestRequest(
            strategy_id="multi_factor_score",
            pool_id="csi300",
            start_date="2024/01/01",
            end_date="2024-12-31",
        )


def test_backtest_request_rejects_reversed_date_range():
    with pytest.raises(ValidationError):
        BacktestRequest(
            strategy_id="multi_factor_score",
            pool_id="csi300",
            start_date="2024-12-31",
            end_date="2024-01-01",
        )


def test_cost_config_rejects_out_of_bounds_values():
    with pytest.raises(ValidationError):
        CostConfig(commission_rate=0.02)


def test_pool_create_normalizes_symbols():
    request = PoolCreateRequest(name="核心池", symbols=[" 600519.sh ", "sz000001"])

    assert request.symbols == ["600519.SH", "SZ000001"]


def test_pool_create_rejects_blank_symbol_in_mixed_input():
    with pytest.raises(ValidationError):
        PoolCreateRequest(name="核心池", symbols=["600519.SH", "   "])


def test_stock_pool_symbols_are_immutable_and_isolated_from_constructor_input():
    symbols = ["600519.SH"]

    pool = StockPool(
        pool_id="custom",
        name="自选池",
        pool_type=PoolType.CUSTOM,
        symbols=symbols,
    )
    symbols.append("000001.SZ")

    assert pool.symbols == ("600519.SH",)
    with pytest.raises(AttributeError):
        pool.symbols.append("000002.SZ")


def test_strategy_template_collections_are_immutable_and_isolated_from_constructor_input():
    parameter_schema = {"top_n": {"type": "integer"}}
    default_parameters = {"top_n": 20}
    required_fields = ["close"]

    template = StrategyTemplate(
        strategy_id="multi_factor_score",
        name="多因子",
        category="factor",
        description="score stocks",
        parameter_schema=parameter_schema,
        default_parameters=default_parameters,
        required_fields=required_fields,
    )
    parameter_schema["top_n"] = {"type": "number"}
    default_parameters["top_n"] = 50
    required_fields.append("volume")

    assert template.parameter_schema["top_n"] == {"type": "integer"}
    assert template.default_parameters["top_n"] == 20
    assert template.required_fields == ("close",)
    with pytest.raises(TypeError):
        template.parameter_schema["lookback"] = {"type": "integer"}
    with pytest.raises(TypeError):
        template.default_parameters["lookback"] = 60
    with pytest.raises(AttributeError):
        template.required_fields.append("open")


def test_quant_lab_error_stores_effective_message_on_instance():
    default_error = QuantLabError()
    custom_error = QuantLabError("自定义错误")

    assert default_error.message == str(default_error)
    assert custom_error.message == "自定义错误"
    assert str(custom_error) == "自定义错误"
