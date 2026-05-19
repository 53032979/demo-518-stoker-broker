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
            "symbols": list(pool.symbols),
        }
        for pool in list_default_pools()
    ]
