from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from backend.app.api.routes import backtests, data, pools, strategies
from backend.app.config import settings
from backend.app.domain.errors import QuantLabError
from backend.app.storage.database import create_connection, initialize_schema
from backend.app.storage.repository import QuantRepository


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
