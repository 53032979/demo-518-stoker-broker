# A Share Quant Lab MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local Web strategy lab for A 股日线策略回测 with form-based strategy templates, uploadable local data, default index pools, and trading-view results.

**Architecture:** FastAPI exposes data, pool, strategy, and backtest APIs. Python domain modules own validation, strategy scoring, storage, metrics, and a deterministic daily backtest engine. React renders one workbench with left-side controls and right-side charts/tables.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic, Pandas, Polars, DuckDB, Pytest, React, TypeScript, Vite, ECharts, Vitest.

---

## Scope Check

The design spec describes one integrated MVP. Backend, strategy registry, storage, backtest engine, and frontend are coupled by the workbench flow, so the plan keeps them in one implementation sequence. The plan does not include real trading, minute-level matching, T+1, ST filtering, IC analysis, or arbitrary Python strategy editing.

## File Structure

Create these files and keep responsibilities narrow:

- `pyproject.toml`: Python package metadata, runtime dependencies, test config.
- `backend/app/main.py`: FastAPI app factory and router wiring.
- `backend/app/config.py`: local paths and settings.
- `backend/app/domain/models.py`: domain dataclasses/enums for bars, pools, strategies, orders, trades, metrics.
- `backend/app/domain/errors.py`: typed application errors converted to API responses.
- `backend/app/api/schemas.py`: Pydantic request/response schemas.
- `backend/app/api/routes/data.py`: upload, import, and coverage endpoints.
- `backend/app/api/routes/pools.py`: default and custom pool endpoints.
- `backend/app/api/routes/strategies.py`: strategy catalog endpoints.
- `backend/app/api/routes/backtests.py`: run, status, result, and log endpoints.
- `backend/app/storage/database.py`: DuckDB connection and schema creation.
- `backend/app/storage/repository.py`: storage read/write boundary.
- `backend/app/data/validators.py`: CSV/Parquet validation and normalization.
- `backend/app/data/providers/base.py`: provider interface.
- `backend/app/data/providers/free_provider.py`: free-data provider boundary with deterministic fallback seed data.
- `backend/app/strategies/base.py`: strategy template protocol and parameter schema definitions.
- `backend/app/strategies/builtins.py`: five built-in strategy templates.
- `backend/app/strategies/scoring.py`: factor ranking and score composition.
- `backend/app/backtest/broker.py`: trade sizing, cost, lot-size, and limit-up/down rules.
- `backend/app/backtest/metrics.py`: equity, drawdown, return, Sharpe, and win-rate metrics.
- `backend/app/backtest/engine.py`: daily backtest loop.
- `backend/app/services/backtest_service.py`: orchestration layer used by API routes.
- `tests/backend/`: backend unit and API tests.
- `frontend/package.json`: frontend scripts and dependencies.
- `frontend/index.html`: Vite entry HTML.
- `frontend/src/main.tsx`: React bootstrap.
- `frontend/src/App.tsx`: page shell.
- `frontend/src/api/client.ts`: typed API client.
- `frontend/src/types.ts`: frontend DTO types matching backend schemas.
- `frontend/src/components/Workbench.tsx`: left-control and right-results composition.
- `frontend/src/components/StrategyPanel.tsx`: strategy, pool, data, and parameter controls.
- `frontend/src/components/ResultSummary.tsx`: metric cards.
- `frontend/src/components/Charts.tsx`: equity, drawdown, and K-line buy/sell chart containers.
- `frontend/src/components/Tables.tsx`: positions, trades, and logs.
- `frontend/src/styles.css`: restrained dashboard styling.
- `frontend/src/__tests__/`: frontend unit tests.
- `README.md`: setup, run, and verification commands.

---

### Task 1: Scaffold Project and Tooling

**Files:**
- Create: `pyproject.toml`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/app/config.py`
- Create: `frontend/package.json`
- Create: `frontend/index.html`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/styles.css`
- Create: `README.md`
- Test: `tests/backend/test_health.py`

- [ ] **Step 1: Write failing backend health test**

Create `tests/backend/test_health.py`:

```python
from fastapi.testclient import TestClient

from backend.app.main import create_app


def test_health_endpoint_returns_ok():
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/backend/test_health.py -q
```

Expected: FAIL because `backend.app.main` does not exist.

- [ ] **Step 3: Create Python project config**

Create `pyproject.toml`:

```toml
[project]
name = "a-share-quant-lab"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
  "akshare>=1.14.0",
  "duckdb>=1.0.0",
  "fastapi>=0.115.0",
  "httpx>=0.27.0",
  "pandas>=2.2.0",
  "polars>=1.0.0",
  "pyarrow>=16.0.0",
  "pydantic>=2.8.0",
  "python-multipart>=0.0.9",
  "uvicorn>=0.30.0"
]

[project.optional-dependencies]
dev = [
  "pytest>=8.2.0",
  "pytest-cov>=5.0.0",
  "ruff>=0.5.0"
]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]

[tool.ruff]
line-length = 100
target-version = "py311"
```

- [ ] **Step 4: Create backend app factory**

Create `backend/app/__init__.py` as an empty package marker.

Create `backend/app/config.py`:

```python
from pathlib import Path
from pydantic import BaseModel


class Settings(BaseModel):
    project_root: Path = Path(__file__).resolve().parents[2]
    data_dir: Path = project_root / ".local-data"
    duckdb_path: Path = data_dir / "quant_lab.duckdb"


settings = Settings()
```

Create `backend/app/main.py`:

```python
from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(title="A Share Quant Lab", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
```

- [ ] **Step 5: Create frontend scaffold**

Create `frontend/package.json`:

```json
{
  "name": "a-share-quant-lab-frontend",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite --host 127.0.0.1",
    "build": "tsc && vite build",
    "test": "vitest run"
  },
  "dependencies": {
    "@vitejs/plugin-react": "^4.3.0",
    "echarts": "^5.5.0",
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "vite": "^5.4.0"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "^6.4.0",
    "@testing-library/react": "^15.0.0",
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "typescript": "^5.5.0",
    "vitest": "^2.0.0"
  }
}
```

Create `frontend/index.html`:

```html
<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>A股量化策略实验室</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

Create `frontend/src/main.tsx`:

```tsx
import React from "react";
import ReactDOM from "react-dom/client";
import { App } from "./App";
import "./styles.css";

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
```

Create `frontend/src/App.tsx`:

```tsx
export function App() {
  return (
    <main className="app-shell">
      <h1>A股量化策略实验室</h1>
      <p>策略配置、日线回测和交易视角结果将在这里整合。</p>
    </main>
  );
}
```

Create `frontend/src/styles.css`:

```css
:root {
  font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  color: #1f2937;
  background: #f4f6f8;
}

body {
  margin: 0;
}

.app-shell {
  min-height: 100vh;
  padding: 24px;
}
```

- [ ] **Step 6: Create README**

Create `README.md`:

```markdown
# A股量化策略实验室

本项目是一个本地 Web 策略实验室，用于 A 股日线级策略回测和结果展示。

## 后端

```bash
python -m pip install -e ".[dev]"
python -m uvicorn backend.app.main:app --reload --port 8000
```

## 前端

```bash
cd frontend
npm install
npm run dev
```

## 验证

```bash
python -m pytest -q
cd frontend && npm test
```
```

- [ ] **Step 7: Run backend test**

Run:

```bash
python -m pytest tests/backend/test_health.py -q
```

Expected: PASS.

- [ ] **Step 8: Commit scaffold**

```bash
git add pyproject.toml backend frontend tests/backend/test_health.py README.md
git commit -m "chore: scaffold quant lab app"
```

---

### Task 2: Add Domain Models and API Schemas

**Files:**
- Create: `backend/app/domain/models.py`
- Create: `backend/app/domain/errors.py`
- Create: `backend/app/api/__init__.py`
- Create: `backend/app/api/schemas.py`
- Test: `tests/backend/test_schemas.py`

- [ ] **Step 1: Write failing schema tests**

Create `tests/backend/test_schemas.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/backend/test_schemas.py -q
```

Expected: FAIL because `backend.app.api.schemas` does not exist.

- [ ] **Step 3: Add typed domain errors**

Create `backend/app/domain/errors.py`:

```python
class QuantLabError(Exception):
    code = "quant_lab_error"
    message = "系统错误"

    def __init__(self, message: str | None = None, details: dict | None = None):
        super().__init__(message or self.message)
        self.details = details or {}


class DataValidationError(QuantLabError):
    code = "data_validation_error"
    message = "数据校验失败"


class StrategyValidationError(QuantLabError):
    code = "strategy_validation_error"
    message = "策略参数校验失败"


class BacktestRuntimeError(QuantLabError):
    code = "backtest_runtime_error"
    message = "回测运行失败"
```

- [ ] **Step 4: Add domain models**

Create `backend/app/domain/models.py`:

```python
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
```

- [ ] **Step 5: Add Pydantic schemas**

Create `backend/app/api/__init__.py` as an empty package marker.

Create `backend/app/api/schemas.py`:

```python
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
```

- [ ] **Step 6: Run schema tests**

Run:

```bash
python -m pytest tests/backend/test_schemas.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit domain schemas**

```bash
git add backend/app/domain backend/app/api tests/backend/test_schemas.py
git commit -m "feat: add quant lab domain schemas"
```

---

### Task 3: Implement Data Validation and DuckDB Storage

**Files:**
- Create: `backend/app/storage/__init__.py`
- Create: `backend/app/storage/database.py`
- Create: `backend/app/storage/repository.py`
- Create: `backend/app/data/__init__.py`
- Create: `backend/app/data/validators.py`
- Test: `tests/backend/test_data_validation.py`
- Test: `tests/backend/test_storage.py`

- [ ] **Step 1: Write failing data validation test**

Create `tests/backend/test_data_validation.py`:

```python
import pandas as pd
import pytest

from backend.app.data.validators import normalize_daily_bars
from backend.app.domain.errors import DataValidationError


def test_normalize_daily_bars_accepts_required_columns():
    raw = pd.DataFrame(
        [
            {
                "symbol": "000001.SZ",
                "trade_date": "2024-01-02",
                "open": 10.0,
                "high": 11.0,
                "low": 9.5,
                "close": 10.5,
                "volume": 100000,
                "amount": 1050000,
            }
        ]
    )

    result = normalize_daily_bars(raw, source="unit")

    assert list(result.columns) == [
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
    assert result.loc[0, "frequency"] == "1d"


def test_normalize_daily_bars_rejects_invalid_prices():
    raw = pd.DataFrame(
        [
            {
                "symbol": "000001.SZ",
                "trade_date": "2024-01-02",
                "open": 10.0,
                "high": 9.0,
                "low": 9.5,
                "close": 10.5,
                "volume": 100000,
                "amount": 1050000,
            }
        ]
    )

    with pytest.raises(DataValidationError):
        normalize_daily_bars(raw, source="unit")
```

- [ ] **Step 2: Write failing storage test**

Create `tests/backend/test_storage.py`:

```python
import pandas as pd

from backend.app.storage.database import create_connection, initialize_schema
from backend.app.storage.repository import QuantRepository


def test_repository_round_trips_daily_bars(tmp_path):
    connection = create_connection(tmp_path / "test.duckdb")
    initialize_schema(connection)
    repo = QuantRepository(connection)
    bars = pd.DataFrame(
        [
            {
                "symbol": "000001.SZ",
                "trade_date": "2024-01-02",
                "open": 10.0,
                "high": 11.0,
                "low": 9.5,
                "close": 10.5,
                "volume": 100000,
                "amount": 1050000,
                "frequency": "1d",
                "source": "unit",
            }
        ]
    )

    repo.upsert_daily_bars(bars)
    result = repo.load_daily_bars(["000001.SZ"], "2024-01-01", "2024-01-31")

    assert len(result) == 1
    assert result.loc[0, "symbol"] == "000001.SZ"
```

- [ ] **Step 3: Run tests to verify failure**

Run:

```bash
python -m pytest tests/backend/test_data_validation.py tests/backend/test_storage.py -q
```

Expected: FAIL because validation and storage modules do not exist.

- [ ] **Step 4: Implement daily bar validation**

Create `backend/app/data/__init__.py` as an empty package marker.

Create `backend/app/data/validators.py`:

```python
import pandas as pd

from backend.app.domain.errors import DataValidationError


REQUIRED_DAILY_COLUMNS = ["symbol", "trade_date", "open", "high", "low", "close", "volume", "amount"]


def normalize_daily_bars(raw: pd.DataFrame, source: str) -> pd.DataFrame:
    missing = [column for column in REQUIRED_DAILY_COLUMNS if column not in raw.columns]
    if missing:
        raise DataValidationError("缺少日线行情字段", {"missing": missing})

    frame = raw[REQUIRED_DAILY_COLUMNS].copy()
    frame["symbol"] = frame["symbol"].astype(str).str.strip().str.upper()
    frame["trade_date"] = pd.to_datetime(frame["trade_date"], errors="coerce").dt.strftime("%Y-%m-%d")

    numeric_columns = ["open", "high", "low", "close", "volume", "amount"]
    for column in numeric_columns:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    if frame["trade_date"].isna().any():
        raise DataValidationError("日期格式错误", {"column": "trade_date"})
    if frame["symbol"].eq("").any():
        raise DataValidationError("证券代码为空", {"column": "symbol"})
    if frame[numeric_columns].isna().any().any():
        raise DataValidationError("数值字段包含空值或非法值", {"columns": numeric_columns})
    if (frame[["open", "high", "low", "close"]] <= 0).any().any():
        raise DataValidationError("价格必须大于 0", {})
    if ((frame["high"] < frame[["open", "low", "close"]].max(axis=1))).any():
        raise DataValidationError("最高价小于开盘价、最低价或收盘价", {})
    if ((frame["low"] > frame[["open", "high", "close"]].min(axis=1))).any():
        raise DataValidationError("最低价大于开盘价、最高价或收盘价", {})
    if frame.duplicated(["symbol", "trade_date"]).any():
        raise DataValidationError("存在重复的 symbol + trade_date 行", {})

    frame["frequency"] = "1d"
    frame["source"] = source
    return frame.sort_values(["symbol", "trade_date"]).reset_index(drop=True)
```

- [ ] **Step 5: Implement DuckDB schema**

Create `backend/app/storage/__init__.py` as an empty package marker.

Create `backend/app/storage/database.py`:

```python
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
            frequency VARCHAR NOT NULL,
            source VARCHAR NOT NULL,
            PRIMARY KEY(symbol, trade_date, frequency, source)
        )
        """
    )
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
```

- [ ] **Step 6: Implement repository**

Create `backend/app/storage/repository.py`:

```python
import json

import duckdb
import pandas as pd

from backend.app.domain.models import PoolType, StockPool


class QuantRepository:
    def __init__(self, connection: duckdb.DuckDBPyConnection):
        self.connection = connection

    def upsert_daily_bars(self, bars: pd.DataFrame) -> None:
        self.connection.register("incoming_daily_bars", bars)
        self.connection.execute(
            """
            INSERT OR REPLACE INTO daily_bars
            SELECT
              symbol,
              CAST(trade_date AS DATE),
              open,
              high,
              low,
              close,
              volume,
              amount,
              frequency,
              source
            FROM incoming_daily_bars
            """
        )
        self.connection.unregister("incoming_daily_bars")

    def load_daily_bars(self, symbols: list[str], start_date: str, end_date: str) -> pd.DataFrame:
        if not symbols:
            return pd.DataFrame()
        return self.connection.execute(
            """
            SELECT symbol, CAST(trade_date AS VARCHAR) AS trade_date, open, high, low, close,
                   volume, amount, frequency, source
            FROM daily_bars
            WHERE symbol IN (SELECT * FROM UNNEST(?))
              AND trade_date BETWEEN CAST(? AS DATE) AND CAST(? AS DATE)
              AND frequency = '1d'
            ORDER BY trade_date, symbol
            """,
            [symbols, start_date, end_date],
        ).fetch_df()

    def save_stock_pool(self, pool: StockPool, source: str = "local") -> None:
        self.connection.execute(
            """
            INSERT OR REPLACE INTO stock_pools (pool_id, name, pool_type, symbols, source)
            VALUES (?, ?, ?, ?, ?)
            """,
            [pool.pool_id, pool.name, pool.pool_type.value, json.dumps(pool.symbols), source],
        )

    def list_stock_pools(self) -> list[StockPool]:
        rows = self.connection.execute(
            "SELECT pool_id, name, pool_type, symbols FROM stock_pools ORDER BY pool_id"
        ).fetchall()
        return [
            StockPool(
                pool_id=row[0],
                name=row[1],
                pool_type=PoolType(row[2]),
                symbols=json.loads(row[3]),
            )
            for row in rows
        ]
```

- [ ] **Step 7: Run storage and validation tests**

Run:

```bash
python -m pytest tests/backend/test_data_validation.py tests/backend/test_storage.py -q
```

Expected: PASS.

- [ ] **Step 8: Commit data layer**

```bash
git add backend/app/data backend/app/storage tests/backend/test_data_validation.py tests/backend/test_storage.py
git commit -m "feat: add data validation and storage"
```

---

### Task 4: Add Stock Pools and Strategy Registry

**Files:**
- Create: `backend/app/strategies/__init__.py`
- Create: `backend/app/strategies/base.py`
- Create: `backend/app/strategies/scoring.py`
- Create: `backend/app/strategies/builtins.py`
- Test: `tests/backend/test_strategies.py`

- [ ] **Step 1: Write failing strategy tests**

Create `tests/backend/test_strategies.py`:

```python
import pandas as pd

from backend.app.strategies.builtins import get_strategy_templates
from backend.app.strategies.scoring import rank_factor, select_top_n


def test_registry_contains_five_templates():
    templates = get_strategy_templates()

    assert {template.strategy_id for template in templates} == {
        "value_quality",
        "momentum_top_n",
        "low_volatility",
        "multi_factor_score",
        "ma_trend_filter",
    }


def test_rank_factor_supports_descending_and_missing_values():
    frame = pd.DataFrame(
        {"symbol": ["A", "B", "C"], "momentum": [0.2, None, 0.1]}
    )

    ranked = rank_factor(frame, "momentum", ascending=False)

    assert ranked["symbol"].tolist() == ["A", "C"]
    assert ranked["momentum_rank"].tolist() == [1.0, 2.0]


def test_select_top_n_uses_weighted_score():
    frame = pd.DataFrame(
        {
            "symbol": ["A", "B", "C"],
            "value_score": [3.0, 1.0, 2.0],
            "quality_score": [1.0, 3.0, 2.0],
        }
    )

    selected = select_top_n(frame, {"value_score": 0.7, "quality_score": 0.3}, top_n=2)

    assert selected["symbol"].tolist() == ["A", "C"]
```

- [ ] **Step 2: Run strategy tests to verify failure**

Run:

```bash
python -m pytest tests/backend/test_strategies.py -q
```

Expected: FAIL because strategy modules do not exist.

- [ ] **Step 3: Implement scoring helpers**

Create `backend/app/strategies/__init__.py` as an empty package marker.

Create `backend/app/strategies/scoring.py`:

```python
import pandas as pd


def rank_factor(frame: pd.DataFrame, column: str, ascending: bool) -> pd.DataFrame:
    cleaned = frame[["symbol", column]].dropna().copy()
    cleaned[f"{column}_rank"] = cleaned[column].rank(method="first", ascending=ascending)
    return cleaned.sort_values(f"{column}_rank").reset_index(drop=True)


def select_top_n(frame: pd.DataFrame, weights: dict[str, float], top_n: int) -> pd.DataFrame:
    if top_n <= 0:
        return frame.iloc[0:0].copy()
    scored = frame[["symbol", *weights.keys()]].dropna().copy()
    scored["score"] = 0.0
    for column, weight in weights.items():
        scored["score"] += scored[column] * weight
    return scored.sort_values(["score", "symbol"], ascending=[False, True]).head(top_n).reset_index(drop=True)
```

- [ ] **Step 4: Implement strategy template base**

Create `backend/app/strategies/base.py`:

```python
from typing import Any, Protocol

import pandas as pd

from backend.app.domain.models import StrategyTemplate


class StrategyRunner(Protocol):
    template: StrategyTemplate

    def generate_targets(
        self,
        market_data: pd.DataFrame,
        current_date: str,
        parameters: dict[str, Any],
    ) -> pd.DataFrame:
        """Return columns: symbol, target_weight."""
```

- [ ] **Step 5: Implement five strategy templates**

Create `backend/app/strategies/builtins.py`:

```python
from backend.app.domain.models import StrategyTemplate


def _schema(title: str) -> dict:
    return {
        "type": "object",
        "title": title,
        "properties": {
            "top_n": {"type": "integer", "minimum": 1, "maximum": 500, "default": 20},
            "rebalance": {"type": "string", "enum": ["weekly", "monthly", "quarterly"], "default": "monthly"},
            "weighting": {"type": "string", "enum": ["equal", "factor_score"], "default": "equal"},
            "stop_loss": {"type": "number", "minimum": 0, "maximum": 0.8, "default": 0.0},
            "take_profit": {"type": "number", "minimum": 0, "maximum": 5.0, "default": 0.0},
        },
        "required": ["top_n", "rebalance", "weighting"],
    }


def get_strategy_templates() -> list[StrategyTemplate]:
    return [
        StrategyTemplate(
            strategy_id="value_quality",
            name="低估值质量组合",
            category="multi_factor",
            description="低 PE/PB 与质量因子过滤的 Top N 组合。",
            parameter_schema=_schema("低估值质量组合参数"),
            default_parameters={"top_n": 20, "rebalance": "monthly", "weighting": "equal"},
            required_fields=["pe", "pb", "roe"],
        ),
        StrategyTemplate(
            strategy_id="momentum_top_n",
            name="动量 Top N",
            category="momentum",
            description="按近 N 日收益排名选择 Top N。",
            parameter_schema=_schema("动量 Top N 参数"),
            default_parameters={"top_n": 20, "rebalance": "monthly", "weighting": "equal", "lookback": 60},
            required_fields=["close"],
        ),
        StrategyTemplate(
            strategy_id="low_volatility",
            name="低波动组合",
            category="defensive",
            description="选择历史收益波动率较低的标的。",
            parameter_schema=_schema("低波动组合参数"),
            default_parameters={"top_n": 20, "rebalance": "monthly", "weighting": "equal", "lookback": 60},
            required_fields=["close"],
        ),
        StrategyTemplate(
            strategy_id="multi_factor_score",
            name="多因子综合打分",
            category="multi_factor",
            description="价值、质量、动量、低波动、流动性加权评分。",
            parameter_schema=_schema("多因子综合打分参数"),
            default_parameters={
                "top_n": 20,
                "rebalance": "monthly",
                "weighting": "factor_score",
                "weights": {"value": 0.25, "quality": 0.25, "momentum": 0.25, "low_volatility": 0.15, "liquidity": 0.10},
            },
            required_fields=["pe", "pb", "roe", "close", "amount"],
        ),
        StrategyTemplate(
            strategy_id="ma_trend_filter",
            name="均线趋势过滤组合",
            category="timing",
            description="在选股结果上叠加 MA20/MA60 趋势过滤。",
            parameter_schema=_schema("均线趋势过滤组合参数"),
            default_parameters={"top_n": 20, "rebalance": "monthly", "weighting": "equal", "ma_fast": 20, "ma_slow": 60},
            required_fields=["close"],
        ),
    ]
```

- [ ] **Step 6: Run strategy tests**

Run:

```bash
python -m pytest tests/backend/test_strategies.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit strategy registry**

```bash
git add backend/app/strategies tests/backend/test_strategies.py
git commit -m "feat: add strategy template registry"
```

---

### Task 5: Implement Broker Rules, Metrics, and Backtest Engine

**Files:**
- Create: `backend/app/backtest/__init__.py`
- Create: `backend/app/backtest/broker.py`
- Create: `backend/app/backtest/metrics.py`
- Create: `backend/app/backtest/engine.py`
- Test: `tests/backend/test_broker.py`
- Test: `tests/backend/test_metrics.py`
- Test: `tests/backend/test_engine.py`

- [ ] **Step 1: Write failing broker tests**

Create `tests/backend/test_broker.py`:

```python
from backend.app.backtest.broker import calculate_costs, round_to_lot, can_trade_at_limit
from backend.app.domain.models import CostConfigModel


def test_round_to_lot_uses_100_shares():
    assert round_to_lot(248, lot_size=100) == 200


def test_calculate_costs_applies_commission_stamp_tax_and_slippage():
    costs = calculate_costs(
        side="sell",
        price=10.0,
        quantity=1000,
        config=CostConfigModel(commission_rate=0.0003, stamp_tax_rate=0.001, slippage_bps=5),
    )

    assert round(costs, 2) == 18.0


def test_limit_up_blocks_buy_and_limit_down_blocks_sell():
    assert can_trade_at_limit(side="buy", close=11.0, previous_close=10.0) is False
    assert can_trade_at_limit(side="sell", close=9.0, previous_close=10.0) is False
    assert can_trade_at_limit(side="buy", close=10.5, previous_close=10.0) is True
```

- [ ] **Step 2: Write failing metrics tests**

Create `tests/backend/test_metrics.py`:

```python
import pandas as pd

from backend.app.backtest.metrics import calculate_metrics


def test_calculate_metrics_returns_core_values():
    equity = pd.DataFrame(
        {
            "trade_date": ["2024-01-01", "2024-01-02", "2024-01-03"],
            "equity": [100000.0, 105000.0, 102000.0],
        }
    )
    trades = pd.DataFrame({"pnl": [1000.0, -500.0, 800.0]})

    metrics = calculate_metrics(equity, trades)

    assert round(metrics.total_return, 4) == 0.02
    assert round(metrics.max_drawdown, 4) == -0.0286
    assert round(metrics.win_rate, 4) == 0.6667
```

- [ ] **Step 3: Write failing engine smoke test**

Create `tests/backend/test_engine.py`:

```python
import pandas as pd

from backend.app.backtest.engine import run_equal_weight_backtest
from backend.app.domain.models import CostConfigModel


def test_equal_weight_backtest_produces_equity_and_trades():
    bars = pd.DataFrame(
        [
            {"symbol": "A", "trade_date": "2024-01-01", "open": 10, "high": 10, "low": 10, "close": 10, "volume": 10000, "amount": 100000, "frequency": "1d", "source": "unit"},
            {"symbol": "B", "trade_date": "2024-01-01", "open": 20, "high": 20, "low": 20, "close": 20, "volume": 10000, "amount": 200000, "frequency": "1d", "source": "unit"},
            {"symbol": "A", "trade_date": "2024-01-02", "open": 11, "high": 11, "low": 11, "close": 11, "volume": 10000, "amount": 110000, "frequency": "1d", "source": "unit"},
            {"symbol": "B", "trade_date": "2024-01-02", "open": 19, "high": 19, "low": 19, "close": 19, "volume": 10000, "amount": 190000, "frequency": "1d", "source": "unit"},
        ]
    )
    targets = pd.DataFrame({"symbol": ["A", "B"], "target_weight": [0.5, 0.5]})

    result = run_equal_weight_backtest(
        bars=bars,
        targets_by_date={"2024-01-01": targets},
        initial_cash=100000.0,
        costs=CostConfigModel(commission_rate=0, stamp_tax_rate=0, slippage_bps=0),
    )

    assert not result.equity_curve.empty
    assert len(result.trades) == 2
    assert result.metrics.total_return != 0
```

- [ ] **Step 4: Run tests to verify failure**

Run:

```bash
python -m pytest tests/backend/test_broker.py tests/backend/test_metrics.py tests/backend/test_engine.py -q
```

Expected: FAIL because backtest modules do not exist.

- [ ] **Step 5: Implement broker rules**

Create `backend/app/backtest/__init__.py` as an empty package marker.

Create `backend/app/backtest/broker.py`:

```python
from backend.app.domain.models import CostConfigModel


def round_to_lot(quantity: float, lot_size: int) -> int:
    return int(quantity // lot_size) * lot_size


def calculate_costs(side: str, price: float, quantity: int, config: CostConfigModel) -> float:
    gross = price * quantity
    commission = gross * config.commission_rate
    stamp_tax = gross * config.stamp_tax_rate if side == "sell" else 0.0
    slippage = gross * config.slippage_bps / 10000.0
    return commission + stamp_tax + slippage


def can_trade_at_limit(side: str, close: float, previous_close: float) -> bool:
    upper = round(previous_close * 1.10, 2)
    lower = round(previous_close * 0.90, 2)
    if side == "buy" and close >= upper:
        return False
    if side == "sell" and close <= lower:
        return False
    return True
```

- [ ] **Step 6: Implement metrics**

Create `backend/app/backtest/metrics.py`:

```python
import math

import pandas as pd

from backend.app.domain.models import BacktestMetrics


def calculate_metrics(equity_curve: pd.DataFrame, trades: pd.DataFrame) -> BacktestMetrics:
    if equity_curve.empty:
        return BacktestMetrics(0.0, 0.0, 0.0, 0.0, 0.0)

    equity = equity_curve["equity"].astype(float)
    total_return = equity.iloc[-1] / equity.iloc[0] - 1.0
    daily_returns = equity.pct_change().dropna()
    annual_return = (1.0 + total_return) ** (252 / max(len(equity), 1)) - 1.0
    rolling_peak = equity.cummax()
    drawdown = equity / rolling_peak - 1.0
    max_drawdown = float(drawdown.min())
    sharpe = 0.0
    if len(daily_returns) > 1 and daily_returns.std() > 0:
        sharpe = float(daily_returns.mean() / daily_returns.std() * math.sqrt(252))
    win_rate = 0.0
    if not trades.empty and "pnl" in trades.columns and len(trades) > 0:
        win_rate = float((trades["pnl"] > 0).sum() / len(trades))
    return BacktestMetrics(
        total_return=float(total_return),
        annual_return=float(annual_return),
        max_drawdown=max_drawdown,
        sharpe=sharpe,
        win_rate=win_rate,
    )
```

- [ ] **Step 7: Implement minimal daily engine**

Create `backend/app/backtest/engine.py`:

```python
from dataclasses import dataclass

import pandas as pd

from backend.app.backtest.broker import calculate_costs, round_to_lot
from backend.app.backtest.metrics import calculate_metrics
from backend.app.domain.models import BacktestMetrics, CostConfigModel


@dataclass(frozen=True)
class BacktestResult:
    equity_curve: pd.DataFrame
    positions: pd.DataFrame
    trades: pd.DataFrame
    logs: list[str]
    metrics: BacktestMetrics


def run_equal_weight_backtest(
    bars: pd.DataFrame,
    targets_by_date: dict[str, pd.DataFrame],
    initial_cash: float,
    costs: CostConfigModel,
) -> BacktestResult:
    cash = initial_cash
    holdings: dict[str, int] = {}
    trade_rows: list[dict] = []
    position_rows: list[dict] = []
    equity_rows: list[dict] = []
    logs: list[str] = []
    previous_prices: dict[str, float] = {}

    ordered = bars.sort_values(["trade_date", "symbol"]).copy()
    for trade_date, day_bars in ordered.groupby("trade_date"):
        price_map = dict(zip(day_bars["symbol"], day_bars["close"]))
        if trade_date in targets_by_date:
            targets = targets_by_date[trade_date]
            account_value = cash + sum(quantity * price_map.get(symbol, previous_prices.get(symbol, 0.0)) for symbol, quantity in holdings.items())
            for _, target in targets.iterrows():
                symbol = target["symbol"]
                price = float(price_map[symbol])
                target_value = account_value * float(target["target_weight"])
                current_quantity = holdings.get(symbol, 0)
                current_value = current_quantity * price
                delta_value = target_value - current_value
                side = "buy" if delta_value > 0 else "sell"
                quantity = round_to_lot(abs(delta_value) / price, costs.min_lot_size)
                if quantity == 0:
                    continue
                fee = calculate_costs(side, price, quantity, costs)
                gross = price * quantity
                if side == "buy" and cash < gross + fee:
                    logs.append(f"{trade_date} {symbol} buy skipped: insufficient cash")
                    continue
                if side == "sell":
                    quantity = min(quantity, current_quantity)
                    gross = price * quantity
                    fee = calculate_costs(side, price, quantity, costs)
                if quantity == 0:
                    continue
                if side == "buy":
                    holdings[symbol] = current_quantity + quantity
                    cash -= gross + fee
                    net_amount = -(gross + fee)
                else:
                    holdings[symbol] = current_quantity - quantity
                    cash += gross - fee
                    net_amount = gross - fee
                trade_rows.append(
                    {
                        "trade_date": trade_date,
                        "symbol": symbol,
                        "side": side,
                        "price": price,
                        "quantity": quantity,
                        "gross_amount": gross,
                        "costs": fee,
                        "net_amount": net_amount,
                        "pnl": 0.0,
                        "reason": "rebalance",
                    }
                )

        market_value = 0.0
        for symbol, quantity in holdings.items():
            price = float(price_map.get(symbol, previous_prices.get(symbol, 0.0)))
            previous_prices[symbol] = price
            market_value += quantity * price
            position_rows.append({"trade_date": trade_date, "symbol": symbol, "quantity": quantity, "price": price, "market_value": quantity * price})
        equity_rows.append({"trade_date": trade_date, "equity": cash + market_value, "cash": cash, "market_value": market_value})

    equity_curve = pd.DataFrame(equity_rows)
    positions = pd.DataFrame(position_rows)
    trades = pd.DataFrame(trade_rows)
    metrics = calculate_metrics(equity_curve, trades)
    return BacktestResult(equity_curve=equity_curve, positions=positions, trades=trades, logs=logs, metrics=metrics)
```

- [ ] **Step 8: Run backtest tests**

Run:

```bash
python -m pytest tests/backend/test_broker.py tests/backend/test_metrics.py tests/backend/test_engine.py -q
```

Expected: PASS.

- [ ] **Step 9: Commit backtest engine**

```bash
git add backend/app/backtest tests/backend/test_broker.py tests/backend/test_metrics.py tests/backend/test_engine.py
git commit -m "feat: add daily backtest engine"
```

---

### Task 6: Add API Routes and Backtest Service

**Files:**
- Create: `backend/app/api/routes/__init__.py`
- Create: `backend/app/api/routes/data.py`
- Create: `backend/app/api/routes/pools.py`
- Create: `backend/app/api/routes/strategies.py`
- Create: `backend/app/api/routes/backtests.py`
- Create: `backend/app/data/providers/__init__.py`
- Create: `backend/app/data/providers/base.py`
- Create: `backend/app/data/providers/free_provider.py`
- Create: `backend/app/services/__init__.py`
- Create: `backend/app/services/backtest_service.py`
- Modify: `backend/app/main.py`
- Test: `tests/backend/test_api_routes.py`

- [ ] **Step 1: Write failing API route tests**

Create `tests/backend/test_api_routes.py`:

```python
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
            "costs": {"commission_rate": 0, "stamp_tax_rate": 0, "slippage_bps": 0, "min_lot_size": 100},
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
```

- [ ] **Step 2: Run API tests to verify failure**

Run:

```bash
python -m pytest tests/backend/test_api_routes.py -q
```

Expected: FAIL because routes are not wired.

- [ ] **Step 3: Add free provider seed data**

Create `backend/app/data/providers/__init__.py` as an empty package marker.

Create `backend/app/data/providers/base.py`:

```python
from typing import Protocol

import pandas as pd


class MarketDataProvider(Protocol):
    def load_daily_bars(self, symbols: list[str], start_date: str, end_date: str) -> pd.DataFrame:
        """Return normalized daily bars."""
```

Create `backend/app/data/providers/free_provider.py`:

```python
import pandas as pd


DEFAULT_POOLS = {
    "csi300": ["000001.SZ", "600000.SH", "000002.SZ"],
    "csi500": ["000905.SH", "600519.SH", "000858.SZ"],
    "csi1000": ["000852.SH", "300750.SZ", "002415.SZ"],
}


def load_seed_daily_bars(symbols: list[str], start_date: str, end_date: str) -> pd.DataFrame:
    dates = pd.date_range(start_date, end_date, freq="B")
    rows: list[dict] = []
    for index, symbol in enumerate(symbols):
        base = 10.0 + index * 3
        for offset, trade_date in enumerate(dates):
            close = base * (1 + 0.004 * offset + 0.002 * index)
            rows.append(
                {
                    "symbol": symbol,
                    "trade_date": trade_date.strftime("%Y-%m-%d"),
                    "open": close * 0.995,
                    "high": close * 1.01,
                    "low": close * 0.99,
                    "close": close,
                    "volume": 100000 + offset * 1000,
                    "amount": close * (100000 + offset * 1000),
                    "frequency": "1d",
                    "source": "seed",
                }
            )
    return pd.DataFrame(rows)


class FreeMarketDataProvider:
    def load_daily_bars(self, symbols: list[str], start_date: str, end_date: str) -> pd.DataFrame:
        try:
            import akshare as ak
        except Exception:
            return load_seed_daily_bars(symbols, start_date, end_date)

        rows: list[pd.DataFrame] = []
        for symbol in symbols:
            ak_symbol = symbol.split(".")[0]
            raw = ak.stock_zh_a_hist(
                symbol=ak_symbol,
                period="daily",
                start_date=start_date.replace("-", ""),
                end_date=end_date.replace("-", ""),
                adjust="qfq",
            )
            if raw.empty:
                continue
            frame = raw.rename(
                columns={
                    "日期": "trade_date",
                    "开盘": "open",
                    "最高": "high",
                    "最低": "low",
                    "收盘": "close",
                    "成交量": "volume",
                    "成交额": "amount",
                }
            )
            frame["symbol"] = symbol
            frame["frequency"] = "1d"
            frame["source"] = "akshare"
            rows.append(frame[["symbol", "trade_date", "open", "high", "low", "close", "volume", "amount", "frequency", "source"]])
        if not rows:
            return load_seed_daily_bars(symbols, start_date, end_date)
        return pd.concat(rows, ignore_index=True)
```

- [ ] **Step 4: Add backtest service**

Create `backend/app/services/__init__.py` as an empty package marker.

Create `backend/app/services/backtest_service.py`:

```python
from uuid import uuid4

import pandas as pd

from backend.app.api.schemas import BacktestRequest
from backend.app.backtest.engine import BacktestResult, run_equal_weight_backtest
from backend.app.data.providers.free_provider import DEFAULT_POOLS, FreeMarketDataProvider
from backend.app.domain.errors import StrategyValidationError
from backend.app.domain.models import CostConfigModel, PoolType, StockPool
from backend.app.strategies.builtins import get_strategy_templates


def list_default_pools() -> list[StockPool]:
    return [
        StockPool(pool_id="csi300", name="沪深300", pool_type=PoolType.INDEX, symbols=DEFAULT_POOLS["csi300"]),
        StockPool(pool_id="csi500", name="中证500", pool_type=PoolType.INDEX, symbols=DEFAULT_POOLS["csi500"]),
        StockPool(pool_id="csi1000", name="中证1000", pool_type=PoolType.INDEX, symbols=DEFAULT_POOLS["csi1000"]),
    ]


def run_backtest(request: BacktestRequest) -> dict:
    pools = {pool.pool_id: pool for pool in list_default_pools()}
    if request.pool_id not in pools:
        raise StrategyValidationError("未知股票池", {"pool_id": request.pool_id})
    templates = {template.strategy_id: template for template in get_strategy_templates()}
    if request.strategy_id not in templates:
        raise StrategyValidationError("未知策略模板", {"strategy_id": request.strategy_id})

    symbols = pools[request.pool_id].symbols
    bars = FreeMarketDataProvider().load_daily_bars(symbols, request.start_date, request.end_date)
    first_date = bars["trade_date"].min()
    top_n = int(request.parameters.get("top_n", 2))
    selected = symbols[:top_n]
    targets = pd.DataFrame({"symbol": selected, "target_weight": [1.0 / len(selected)] * len(selected)})
    costs = CostConfigModel(**request.costs.model_dump())
    result = run_equal_weight_backtest(bars, {first_date: targets}, 100000.0, costs)
    return serialize_result(str(uuid4()), result)


def serialize_result(run_id: str, result: BacktestResult) -> dict:
    return {
        "run_id": run_id,
        "status": "completed",
        "result": {
            "metrics": result.metrics.__dict__,
            "equity_curve": result.equity_curve.to_dict(orient="records"),
            "positions": result.positions.to_dict(orient="records"),
            "trades": result.trades.to_dict(orient="records"),
            "logs": result.logs,
        },
    }
```

- [ ] **Step 5: Add routes**

Create `backend/app/api/routes/__init__.py` as an empty package marker.

Create `backend/app/api/routes/strategies.py`:

```python
from fastapi import APIRouter

from backend.app.strategies.builtins import get_strategy_templates

router = APIRouter(prefix="/strategies", tags=["strategies"])


@router.get("")
def list_strategies() -> list[dict]:
    return [template.__dict__ for template in get_strategy_templates()]
```

Create `backend/app/api/routes/pools.py`:

```python
from fastapi import APIRouter

from backend.app.services.backtest_service import list_default_pools

router = APIRouter(prefix="/pools", tags=["pools"])


@router.get("")
def list_pools() -> list[dict]:
    return [
        {
            "pool_id": pool.pool_id,
            "name": pool.name,
            "pool_type": pool.pool_type.value,
            "symbols": pool.symbols,
        }
        for pool in list_default_pools()
    ]
```

Create `backend/app/api/routes/backtests.py`:

```python
from fastapi import APIRouter

from backend.app.api.schemas import BacktestRequest
from backend.app.services.backtest_service import run_backtest

router = APIRouter(prefix="/backtests", tags=["backtests"])


@router.post("")
def create_backtest(request: BacktestRequest) -> dict:
    return run_backtest(request)
```

Create `backend/app/api/routes/data.py`:

```python
from io import BytesIO

import pandas as pd
from fastapi import APIRouter, File, Request, UploadFile

from backend.app.data.validators import normalize_daily_bars

router = APIRouter(prefix="/data", tags=["data"])


@router.get("/coverage")
def coverage() -> dict:
    return {"sources": ["seed"], "frequency": "1d"}


@router.post("/uploads")
async def upload_daily_bars(request: Request, file: UploadFile = File(...)) -> dict:
    payload = await file.read()
    if file.filename and file.filename.endswith(".parquet"):
        raw = pd.read_parquet(BytesIO(payload))
    else:
        raw = pd.read_csv(BytesIO(payload))
    normalized = normalize_daily_bars(raw, source=file.filename or "upload")
    request.app.state.repository.upsert_daily_bars(normalized)
    return {
        "status": "validated",
        "rows": int(len(normalized)),
        "symbols": int(normalized["symbol"].nunique()),
        "start_date": str(normalized["trade_date"].min()),
        "end_date": str(normalized["trade_date"].max()),
    }
```

- [ ] **Step 6: Wire routes and errors in app factory**

Modify `backend/app/main.py`:

```python
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from backend.app.api.routes import backtests, data, pools, strategies
from backend.app.config import settings
from backend.app.domain.errors import QuantLabError
from backend.app.storage.database import create_connection, initialize_schema
from backend.app.storage.repository import QuantRepository


def create_app() -> FastAPI:
    app = FastAPI(title="A Share Quant Lab", version="0.1.0")
    connection = create_connection(settings.duckdb_path)
    initialize_schema(connection)
    app.state.repository = QuantRepository(connection)

    @app.exception_handler(QuantLabError)
    def handle_quant_lab_error(_, exc: QuantLabError) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={"code": exc.code, "message": str(exc), "details": exc.details},
        )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(data.router)
    app.include_router(pools.router)
    app.include_router(strategies.router)
    app.include_router(backtests.router)
    return app


app = create_app()
```

- [ ] **Step 7: Run API tests**

Run:

```bash
python -m pytest tests/backend/test_api_routes.py -q
```

Expected: PASS.

- [ ] **Step 8: Commit API service**

```bash
git add backend/app/api backend/app/data/providers backend/app/services backend/app/main.py tests/backend/test_api_routes.py
git commit -m "feat: expose quant lab API routes"
```

---

### Task 7: Add Frontend Types, API Client, and Workbench State

**Files:**
- Create: `frontend/src/types.ts`
- Create: `frontend/src/api/client.ts`
- Create: `frontend/src/components/Workbench.tsx`
- Modify: `frontend/src/App.tsx`
- Test: `frontend/src/__tests__/client.test.ts`
- Test: `frontend/src/__tests__/Workbench.test.tsx`

- [ ] **Step 1: Write failing frontend tests**

Create `frontend/src/__tests__/client.test.ts`:

```ts
import { describe, expect, it, vi } from "vitest";
import { fetchStrategies } from "../api/client";

describe("api client", () => {
  it("loads strategies", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => [{ strategy_id: "momentum_top_n", name: "动量 Top N" }],
      }),
    );

    const result = await fetchStrategies();

    expect(result[0].strategy_id).toBe("momentum_top_n");
  });
});
```

Create `frontend/src/__tests__/Workbench.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Workbench } from "../components/Workbench";

describe("Workbench", () => {
  it("renders the main regions", () => {
    render(<Workbench />);

    expect(screen.getByText("策略配置")).toBeInTheDocument();
    expect(screen.getByText("回测结果")).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run frontend tests to verify failure**

Run:

```bash
cd frontend
npm test
```

Expected: FAIL because frontend modules do not exist.

- [ ] **Step 3: Add frontend types**

Create `frontend/src/types.ts`:

```ts
export type StrategyTemplate = {
  strategy_id: string;
  name: string;
  category: string;
  description: string;
  parameter_schema: Record<string, unknown>;
  default_parameters: Record<string, unknown>;
  required_fields: string[];
};

export type StockPool = {
  pool_id: string;
  name: string;
  pool_type: "index" | "custom";
  symbols: string[];
};

export type BacktestPayload = {
  strategy_id: string;
  pool_id: string;
  start_date: string;
  end_date: string;
  parameters: Record<string, unknown>;
  costs: {
    commission_rate: number;
    stamp_tax_rate: number;
    slippage_bps: number;
    min_lot_size: number;
  };
};

export type BacktestResult = {
  run_id: string;
  status: "completed" | "failed" | "running" | "queued";
  result?: {
    metrics: Record<string, number>;
    equity_curve: Array<Record<string, number | string>>;
    positions: Array<Record<string, number | string>>;
    trades: Array<Record<string, number | string>>;
    logs: string[];
  };
};
```

- [ ] **Step 4: Add API client**

Create `frontend/src/api/client.ts`:

```ts
import type { BacktestPayload, BacktestResult, StockPool, StrategyTemplate } from "../types";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000";

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    ...init,
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: response.statusText }));
    throw new Error(error.message ?? "API request failed");
  }
  return response.json() as Promise<T>;
}

export function fetchStrategies(): Promise<StrategyTemplate[]> {
  return requestJson<StrategyTemplate[]>("/strategies");
}

export function fetchPools(): Promise<StockPool[]> {
  return requestJson<StockPool[]>("/pools");
}

export function runBacktest(payload: BacktestPayload): Promise<BacktestResult> {
  return requestJson<BacktestResult>("/backtests", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function uploadDailyBars(file: File): Promise<{ status: string; rows: number; symbols: number; start_date: string; end_date: string }> {
  const form = new FormData();
  form.append("file", file);
  const response = await fetch(`${API_BASE}/data/uploads`, {
    method: "POST",
    body: form,
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: response.statusText }));
    throw new Error(error.message ?? "Upload failed");
  }
  return response.json();
}
```

- [ ] **Step 5: Add Workbench shell**

Create `frontend/src/components/Workbench.tsx`:

```tsx
export function Workbench() {
  return (
    <section className="workbench">
      <aside className="control-panel">
        <h2>策略配置</h2>
        <label>
          策略模板
          <select>
            <option>动量 Top N</option>
          </select>
        </label>
        <label>
          股票池
          <select>
            <option>沪深300</option>
          </select>
        </label>
        <button type="button">运行回测</button>
      </aside>
      <section className="result-panel">
        <h2>回测结果</h2>
        <div className="metric-grid">
          <div>总收益</div>
          <div>年化收益</div>
          <div>最大回撤</div>
          <div>夏普</div>
          <div>胜率</div>
        </div>
      </section>
    </section>
  );
}
```

Modify `frontend/src/App.tsx`:

```tsx
import { Workbench } from "./components/Workbench";

export function App() {
  return <Workbench />;
}
```

- [ ] **Step 6: Expand CSS for A layout**

Append to `frontend/src/styles.css`:

```css
.workbench {
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr);
  gap: 16px;
  min-height: 100vh;
  padding: 16px;
}

.control-panel,
.result-panel {
  background: #ffffff;
  border: 1px solid #d9dee7;
  border-radius: 8px;
  padding: 16px;
}

.control-panel {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.control-panel label {
  display: grid;
  gap: 6px;
  font-size: 13px;
}

.control-panel select,
.control-panel button {
  min-height: 36px;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(110px, 1fr));
  gap: 10px;
}

@media (max-width: 900px) {
  .workbench {
    grid-template-columns: 1fr;
  }
}
```

- [ ] **Step 7: Run frontend tests**

Run:

```bash
cd frontend
npm test
```

Expected: PASS.

- [ ] **Step 8: Commit frontend shell**

```bash
git add frontend
git commit -m "feat: add frontend workbench shell"
```

---

### Task 8: Implement Frontend Controls, Results, and Chart Containers

**Files:**
- Create: `frontend/src/components/StrategyPanel.tsx`
- Create: `frontend/src/components/ResultSummary.tsx`
- Create: `frontend/src/components/Charts.tsx`
- Create: `frontend/src/components/Tables.tsx`
- Modify: `frontend/src/components/Workbench.tsx`
- Modify: `frontend/src/styles.css`
- Test: `frontend/src/__tests__/StrategyPanel.test.tsx`
- Test: `frontend/src/__tests__/ResultSummary.test.tsx`

- [ ] **Step 1: Write failing component tests**

Create `frontend/src/__tests__/StrategyPanel.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { StrategyPanel } from "../components/StrategyPanel";

describe("StrategyPanel", () => {
  it("renders strategy and pool options", () => {
    render(
      <StrategyPanel
        strategies={[{ strategy_id: "momentum_top_n", name: "动量 Top N", category: "momentum", description: "", parameter_schema: {}, default_parameters: {}, required_fields: [] }]}
        pools={[{ pool_id: "csi300", name: "沪深300", pool_type: "index", symbols: ["000001.SZ"] }]}
        onRun={vi.fn()}
      />,
    );

    expect(screen.getByText("动量 Top N")).toBeInTheDocument();
    expect(screen.getByText("沪深300")).toBeInTheDocument();
  });
});
```

Create `frontend/src/__tests__/ResultSummary.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ResultSummary } from "../components/ResultSummary";

describe("ResultSummary", () => {
  it("formats core metrics", () => {
    render(
      <ResultSummary
        metrics={{ total_return: 0.12, annual_return: 0.18, max_drawdown: -0.08, sharpe: 1.23, win_rate: 0.55 }}
      />,
    );

    expect(screen.getByText("12.00%")).toBeInTheDocument();
    expect(screen.getByText("-8.00%")).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run frontend tests to verify failure**

Run:

```bash
cd frontend
npm test
```

Expected: FAIL because components do not exist.

- [ ] **Step 3: Implement StrategyPanel**

Create `frontend/src/components/StrategyPanel.tsx`:

```tsx
import type { StockPool, StrategyTemplate } from "../types";

type Props = {
  strategies: StrategyTemplate[];
  pools: StockPool[];
  onRun: () => void;
  onUpload?: (file: File) => void;
};

export function StrategyPanel({ strategies, pools, onRun, onUpload }: Props) {
  return (
    <aside className="control-panel">
      <h2>策略配置</h2>
      <label>
        策略模板
        <select aria-label="策略模板">
          {strategies.map((strategy) => (
            <option key={strategy.strategy_id} value={strategy.strategy_id}>
              {strategy.name}
            </option>
          ))}
        </select>
      </label>
      <label>
        股票池
        <select aria-label="股票池">
          {pools.map((pool) => (
            <option key={pool.pool_id} value={pool.pool_id}>
              {pool.name}
            </option>
          ))}
        </select>
      </label>
      <label>
        回测区间
        <input aria-label="开始日期" type="date" defaultValue="2024-01-01" />
        <input aria-label="结束日期" type="date" defaultValue="2024-12-31" />
      </label>
      <label>
        持仓数量
        <input aria-label="持仓数量" type="number" defaultValue={20} min={1} />
      </label>
      <label>
        本地数据文件
        <input
          aria-label="本地数据文件"
          type="file"
          accept=".csv,.parquet"
          onChange={(event) => {
            const file = event.currentTarget.files?.[0];
            if (file && onUpload) onUpload(file);
          }}
        />
      </label>
      <button type="button" onClick={onRun}>
        运行回测
      </button>
    </aside>
  );
}
```

- [ ] **Step 4: Implement ResultSummary**

Create `frontend/src/components/ResultSummary.tsx`:

```tsx
type Props = {
  metrics?: Record<string, number>;
};

function percent(value?: number) {
  return typeof value === "number" ? `${(value * 100).toFixed(2)}%` : "--";
}

function number(value?: number) {
  return typeof value === "number" ? value.toFixed(2) : "--";
}

export function ResultSummary({ metrics }: Props) {
  return (
    <div className="metric-grid">
      <article><span>总收益</span><strong>{percent(metrics?.total_return)}</strong></article>
      <article><span>年化收益</span><strong>{percent(metrics?.annual_return)}</strong></article>
      <article><span>最大回撤</span><strong>{percent(metrics?.max_drawdown)}</strong></article>
      <article><span>夏普</span><strong>{number(metrics?.sharpe)}</strong></article>
      <article><span>胜率</span><strong>{percent(metrics?.win_rate)}</strong></article>
    </div>
  );
}
```

- [ ] **Step 5: Implement chart and table containers**

Create `frontend/src/components/Charts.tsx`:

```tsx
import type { BacktestResult } from "../types";

type Props = {
  result?: BacktestResult;
};

export function Charts({ result }: Props) {
  const hasResult = result?.result?.equity_curve?.length;
  return (
    <section className="chart-grid">
      <div className="chart-box">{hasResult ? "资金曲线 / 回撤曲线" : "运行回测后显示资金曲线"}</div>
      <div className="chart-box">{hasResult ? "K线 + 买卖点" : "运行回测后显示K线买卖点"}</div>
    </section>
  );
}
```

Create `frontend/src/components/Tables.tsx`:

```tsx
import type { BacktestResult } from "../types";

type Props = {
  result?: BacktestResult;
};

export function Tables({ result }: Props) {
  const positions = result?.result?.positions ?? [];
  const trades = result?.result?.trades ?? [];
  const logs = result?.result?.logs ?? [];
  return (
    <section className="table-grid">
      <div><h3>当前持仓</h3><p>{positions.length} 条</p></div>
      <div><h3>交易流水</h3><p>{trades.length} 条</p></div>
      <div><h3>运行日志</h3><p>{logs.length} 条</p></div>
    </section>
  );
}
```

- [ ] **Step 6: Compose Workbench**

Modify `frontend/src/components/Workbench.tsx`:

```tsx
import { useEffect, useState } from "react";
import { fetchPools, fetchStrategies, runBacktest, uploadDailyBars } from "../api/client";
import type { BacktestResult, StockPool, StrategyTemplate } from "../types";
import { Charts } from "./Charts";
import { ResultSummary } from "./ResultSummary";
import { StrategyPanel } from "./StrategyPanel";
import { Tables } from "./Tables";

export function Workbench() {
  const [strategies, setStrategies] = useState<StrategyTemplate[]>([]);
  const [pools, setPools] = useState<StockPool[]>([]);
  const [result, setResult] = useState<BacktestResult | undefined>();
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([fetchStrategies(), fetchPools()])
      .then(([strategyData, poolData]) => {
        setStrategies(strategyData);
        setPools(poolData);
      })
      .catch((reason) => setError(reason instanceof Error ? reason.message : "加载失败"));
  }, []);

  async function handleRun() {
    setError("");
    try {
      const payload = {
        strategy_id: strategies[0]?.strategy_id ?? "momentum_top_n",
        pool_id: pools[0]?.pool_id ?? "csi300",
        start_date: "2024-01-01",
        end_date: "2024-12-31",
        parameters: { top_n: 2, rebalance: "monthly", weighting: "equal" },
        costs: { commission_rate: 0.0003, stamp_tax_rate: 0.001, slippage_bps: 5, min_lot_size: 100 },
      };
      setResult(await runBacktest(payload));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "回测失败");
    }
  }

  async function handleUpload(file: File) {
    setError("");
    try {
      const summary = await uploadDailyBars(file);
      setError(`数据校验通过：${summary.rows} 行，${summary.symbols} 个标的`);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "上传失败");
    }
  }

  return (
    <section className="workbench">
      <StrategyPanel strategies={strategies} pools={pools} onRun={handleRun} onUpload={handleUpload} />
      <section className="result-panel">
        <h2>回测结果</h2>
        {error && <p className="error-banner">{error}</p>}
        <ResultSummary metrics={result?.result?.metrics} />
        <Charts result={result} />
        <Tables result={result} />
      </section>
    </section>
  );
}
```

- [ ] **Step 7: Add result CSS**

Append to `frontend/src/styles.css`:

```css
.metric-grid article,
.chart-box,
.table-grid > div {
  background: #f8fafc;
  border: 1px solid #e1e7ef;
  border-radius: 8px;
  padding: 12px;
}

.metric-grid span {
  display: block;
  color: #667085;
  font-size: 12px;
}

.metric-grid strong {
  display: block;
  margin-top: 4px;
  font-size: 20px;
}

.chart-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-top: 12px;
}

.chart-box {
  min-height: 280px;
  display: grid;
  place-items: center;
}

.table-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-top: 12px;
}

.error-banner {
  color: #b42318;
  background: #fff1f0;
  border: 1px solid #fecdca;
  border-radius: 8px;
  padding: 10px 12px;
}
```

- [ ] **Step 8: Run frontend tests**

Run:

```bash
cd frontend
npm test
```

Expected: PASS.

- [ ] **Step 9: Commit frontend workbench**

```bash
git add frontend
git commit -m "feat: build strategy workbench UI"
```

---

### Task 9: Final Integration, Verification, and Documentation

**Files:**
- Modify: `README.md`
- Test: all backend and frontend tests.

- [ ] **Step 1: Run complete backend test suite**

Run:

```bash
python -m pytest -q
```

Expected: all backend tests PASS.

- [ ] **Step 2: Run complete frontend test suite**

Run:

```bash
cd frontend
npm test
```

Expected: all frontend tests PASS.

- [ ] **Step 3: Build frontend**

Run:

```bash
cd frontend
npm run build
```

Expected: TypeScript and Vite build complete successfully.

- [ ] **Step 4: Start backend and frontend manually**

Run backend:

```bash
python -m uvicorn backend.app.main:app --reload --port 8000
```

Run frontend in a second terminal:

```bash
cd frontend
npm run dev
```

Expected: backend serves `http://127.0.0.1:8000/health`; frontend serves a Vite URL and renders the workbench.

- [ ] **Step 5: Update README with MVP workflow**

Modify `README.md` so it includes:

```markdown
## MVP Workflow

1. Start the backend on `http://127.0.0.1:8000`.
2. Start the frontend from `frontend/`.
3. Open the Vite URL.
4. Select a strategy template and default index pool.
5. Run a daily backtest.
6. Review metrics, equity curve area, positions, trades, and logs.

The first version uses deterministic seed data for the default pools and supports CSV/Parquet upload through the workbench. Uploaded daily bars are validated and persisted through the DuckDB repository.
```

- [ ] **Step 6: Commit final docs**

```bash
git add README.md
git commit -m "docs: document MVP workflow"
```

---

## Self-Review

Spec coverage:

- Web workbench: Tasks 7 and 8.
- FastAPI backend: Tasks 1 and 6.
- Domain schema: Task 2.
- DuckDB and data validation: Task 3.
- Five strategy templates: Task 4.
- Daily backtest and basic trading costs: Task 5.
- API boundaries: Task 6.
- Frontend result display: Tasks 7 and 8.
- Verification and docs: Task 9.

Known implementation gaps that remain outside this MVP plan:

- Tushare provider wiring beyond provider boundary.
- AkShare production hardening: retries, local cache invalidation, provider health diagnostics.
- Research-view analytics.
- A 股 advanced constraints: T+1, ST,停牌,退市,新股过滤.
- Minute-level matching.

These gaps match the approved design scope and should not be added during MVP execution unless the user explicitly changes scope.
