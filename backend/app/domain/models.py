from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class Frequency(StrEnum):
    DAILY = "1d"


class PoolType(StrEnum):
    INDEX = "index"
    CUSTOM = "custom"


class RebalanceFrequency(StrEnum):
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


@dataclass(frozen=True)
class CostConfigModel:
    commission_rate: float = 0.0003
    stamp_tax_rate: float = 0.001
    slippage_bps: float = 5.0
    min_lot_size: int = 100


@dataclass(frozen=True)
class StockPool:
    pool_id: str
    name: str
    pool_type: PoolType
    symbols: list[str]


@dataclass(frozen=True)
class StrategyTemplate:
    strategy_id: str
    name: str
    category: str
    description: str
    parameter_schema: dict[str, Any]
    default_parameters: dict[str, Any]
    required_fields: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Trade:
    trade_date: str
    symbol: str
    side: str
    price: float
    quantity: int
    gross_amount: float
    costs: float
    net_amount: float
    reason: str


@dataclass(frozen=True)
class BacktestMetrics:
    total_return: float
    annual_return: float
    max_drawdown: float
    sharpe: float
    win_rate: float
