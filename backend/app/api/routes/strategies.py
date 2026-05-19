from fastapi import APIRouter
from fastapi.encoders import jsonable_encoder

from backend.app.strategies.builtins import get_strategy_templates

router = APIRouter(prefix="/strategies", tags=["strategies"])


@router.get("")
def list_strategies() -> list[dict]:
    return jsonable_encoder([template.__dict__ for template in get_strategy_templates()])
