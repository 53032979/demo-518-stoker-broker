# A股量化策略实验室

本项目是一个本地 Web 策略实验室，用于 A 股日线级策略回测和结果展示。

## MVP Workflow

1. Start the backend on `http://127.0.0.1:8000`.
2. Start the frontend from `frontend/`.
3. Open the Vite URL.
4. Select a strategy template and default index pool.
5. Run a daily backtest.
6. Review metrics, equity curve area, positions, trades, and logs.

The first version uses deterministic seed data for the default pools and supports CSV/Parquet upload through the workbench. Uploaded daily bars are validated and persisted through the DuckDB repository.

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
