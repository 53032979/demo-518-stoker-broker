from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from types import MappingProxyType
from typing import Any


def _freeze_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze_value(item) for key, item in value.items()})
    if isinstance(value, list | tuple):
        return tuple(_freeze_value(item) for item in value)
    if isinstance(value, set | frozenset):
        return frozenset(_freeze_value(item) for item in value)
    return value


def _freeze_mapping(value: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType({key: _freeze_value(item) for key, item in value.items()})


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
    symbols: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "symbols", tuple(self.symbols))


@dataclass(frozen=True)
class StrategyTemplate:
    strategy_id: str
    name: str
    category: str
    description: str
    parameter_schema: Mapping[str, Any]
    default_parameters: Mapping[str, Any]
    required_fields: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "parameter_schema", _freeze_mapping(self.parameter_schema))
        object.__setattr__(self, "default_parameters", _freeze_mapping(self.default_parameters))
        object.__setattr__(self, "required_fields", tuple(self.required_fields))


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
