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
