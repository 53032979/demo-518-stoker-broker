from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class CostConfig(BaseModel):
    commission_rate: float = Field(default=0.0003, ge=0, le=0.01)
    stamp_tax_rate: float = Field(default=0.001, ge=0, le=0.02)
    slippage_bps: float = Field(default=5.0, ge=0, le=500)
    min_lot_size: int = Field(default=100, ge=1)


class PoolCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    symbols: list[str] = Field(min_length=1)

    @field_validator("symbols")
    @classmethod
    def normalize_symbols(cls, symbols: list[str]) -> list[str]:
        normalized = [symbol.strip().upper() for symbol in symbols if symbol.strip()]
        if not normalized:
            raise ValueError("symbols must contain at least one non-empty code")
        return normalized


class StockPoolResponse(BaseModel):
    pool_id: str
    name: str
    pool_type: Literal["index", "custom"]
    symbols: list[str]


class BacktestRequest(BaseModel):
    strategy_id: str = Field(min_length=1)
    pool_id: str = Field(min_length=1)
    start_date: str
    end_date: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    costs: CostConfig = Field(default_factory=CostConfig)


class BacktestStatusResponse(BaseModel):
    run_id: str
    status: Literal["queued", "running", "completed", "failed"]
    message: str = ""


class ErrorResponse(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
