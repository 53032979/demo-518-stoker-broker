from io import BytesIO
from pathlib import Path
from hashlib import sha1

import pandas as pd
from fastapi import APIRouter, Request
from starlette.datastructures import UploadFile

from backend.app.data.validators import normalize_daily_bars
from backend.app.domain.errors import DataValidationError
from backend.app.domain.models import PoolType, StockPool

router = APIRouter(prefix="/data", tags=["data"])

MAX_UPLOAD_BYTES = 20 * 1024 * 1024
ALLOWED_EXTENSIONS = {".csv", ".parquet"}


@router.get("/coverage")
def coverage() -> dict:
    return {"sources": ["seed"], "frequency": "1d"}


@router.post("/uploads")
async def upload_daily_bars(request: Request) -> dict:
    try:
        form = await request.form()
    except Exception as exc:
        raise DataValidationError("无法读取上传表单", {}) from exc

    file = form.get("file")
    if not isinstance(file, UploadFile):
        raise DataValidationError("缺少上传文件", {"field": "file"})

    filename = Path(file.filename or "upload").name
    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise DataValidationError(
            "上传文件类型不支持",
            {"filename": filename, "allowed_extensions": sorted(ALLOWED_EXTENSIONS)},
        )

    payload = await file.read()
    if len(payload) > MAX_UPLOAD_BYTES:
        raise DataValidationError(
            "上传文件超过大小限制",
            {"filename": filename, "max_bytes": MAX_UPLOAD_BYTES},
        )

    try:
        if extension == ".parquet":
            raw = pd.read_parquet(BytesIO(payload))
        else:
            raw = pd.read_csv(BytesIO(payload))
    except Exception as exc:
        raise DataValidationError(
            "无法读取上传文件",
            {"filename": filename},
        ) from exc

    normalized = normalize_daily_bars(raw, source=filename)
    request.app.state.repository.upsert_daily_bars(normalized)
    symbols = sorted(normalized["symbol"].unique().tolist())
    pool = StockPool(
        pool_id=f"upload_{sha1(','.join(symbols).encode('utf-8')).hexdigest()[:12]}",
        name=f"Uploaded {Path(filename).stem}",
        pool_type=PoolType.CUSTOM,
        symbols=tuple(symbols),
    )
    request.app.state.repository.save_stock_pool(pool, source=filename)
    return {
        "status": "validated",
        "rows": int(len(normalized)),
        "symbols": int(normalized["symbol"].nunique()),
        "start_date": str(normalized["trade_date"].min()),
        "end_date": str(normalized["trade_date"].max()),
        "pool": {
            "pool_id": pool.pool_id,
            "name": pool.name,
            "pool_type": pool.pool_type.value,
            "symbols": list(pool.symbols),
        },
    }
