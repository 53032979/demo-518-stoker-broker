import math
from collections.abc import AsyncIterator, Mapping
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.api.routes import backtests, data, pools, strategies
from backend.app.config import settings
from backend.app.domain.errors import QuantLabError
from backend.app.storage.database import create_connection, initialize_schema
from backend.app.storage.repository import QuantRepository


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, str | int | bool):
        return value
    if isinstance(value, float) and not math.isfinite(value):
        return str(value)
    if isinstance(value, float):
        return value
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, set | frozenset):
        return [_json_safe(item) for item in sorted(value, key=str)]
    return str(value)


def create_app(duckdb_path: str | Path | None = None) -> FastAPI:
    database_path = duckdb_path or settings.duckdb_path

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        connection = create_connection(database_path)
        try:
            initialize_schema(connection)
            app.state.repository = QuantRepository(connection)
            yield
        finally:
            connection.close()

    app = FastAPI(title="A Share Quant Lab", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(QuantLabError)
    def handle_quant_lab_error(_, exc: QuantLabError) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={
                "code": exc.code,
                "message": str(exc),
                "details": _json_safe(exc.details),
            },
        )

    @app.exception_handler(RequestValidationError)
    def handle_request_validation_error(_, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={
                "code": "request_validation_error",
                "message": "请求参数校验失败",
                "details": _json_safe(exc.errors()),
            },
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
