from fastapi import APIRouter

from backend.app.api.schemas import BacktestRequest
from backend.app.services.backtest_service import run_backtest

router = APIRouter(prefix="/backtests", tags=["backtests"])


@router.post("")
def create_backtest(request: BacktestRequest) -> dict:
    return run_backtest(request)
