from io import BytesIO

import pandas as pd
from fastapi import APIRouter, Request
from starlette.datastructures import UploadFile

from backend.app.data.validators import normalize_daily_bars
from backend.app.domain.errors import DataValidationError

router = APIRouter(prefix="/data", tags=["data"])


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

    payload = await file.read()
    try:
        if file.filename and file.filename.endswith(".parquet"):
            raw = pd.read_parquet(BytesIO(payload))
        else:
            raw = pd.read_csv(BytesIO(payload))
    except Exception as exc:
        raise DataValidationError(
            "无法读取上传文件",
            {"filename": file.filename or "upload"},
        ) from exc

    normalized = normalize_daily_bars(raw, source=file.filename or "upload")
    request.app.state.repository.upsert_daily_bars(normalized)
    return {
        "status": "validated",
        "rows": int(len(normalized)),
        "symbols": int(normalized["symbol"].nunique()),
        "start_date": str(normalized["trade_date"].min()),
        "end_date": str(normalized["trade_date"].max()),
    }
