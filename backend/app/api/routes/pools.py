from uuid import uuid4

from fastapi import APIRouter, Request

from backend.app.api.schemas import PoolCreateRequest, PoolValidateRequest
from backend.app.domain.models import PoolType, StockPool
from backend.app.services.backtest_service import list_pools

router = APIRouter(prefix="/pools", tags=["pools"])


@router.get("")
def get_pools(request: Request) -> list[dict]:
    return [
        {
            "pool_id": pool.pool_id,
            "name": pool.name,
            "pool_type": pool.pool_type.value,
            "symbols": list(pool.symbols),
        }
        for pool in list_pools(request.app.state.repository)
    ]


@router.post("")
def create_pool(payload: PoolCreateRequest, request: Request) -> dict:
    pool = StockPool(
        pool_id=f"custom_{uuid4().hex[:12]}",
        name=payload.name,
        pool_type=PoolType.CUSTOM,
        symbols=tuple(payload.symbols),
    )
    request.app.state.repository.save_stock_pool(pool, source="custom")
    return _pool_response(pool)


@router.post("/validate")
def validate_pool(payload: PoolValidateRequest) -> dict:
    return {"symbols": payload.symbols, "valid": True, "invalid": []}


def _pool_response(pool: StockPool) -> dict:
    return {
        "pool_id": pool.pool_id,
        "name": pool.name,
        "pool_type": pool.pool_type.value,
        "symbols": list(pool.symbols),
    }
