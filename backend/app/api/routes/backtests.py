from fastapi import APIRouter, Request

from backend.app.api.schemas import BacktestRequest
from backend.app.services.backtest_service import (
    get_backtest_logs,
    get_backtest_results,
    get_backtest_run,
    get_backtest_status,
    run_backtest,
)

router = APIRouter(prefix="/backtests", tags=["backtests"])


@router.post("")
def create_backtest(payload: BacktestRequest, request: Request) -> dict:
    return run_backtest(payload, request.app.state.repository)


@router.get("/{run_id}")
def read_backtest(run_id: str, request: Request) -> dict:
    return get_backtest_run(run_id, request.app.state.repository)


@router.get("/{run_id}/status")
def read_backtest_status(run_id: str, request: Request) -> dict:
    return get_backtest_status(run_id, request.app.state.repository)


@router.get("/{run_id}/results")
def read_backtest_results(run_id: str, request: Request) -> dict:
    return get_backtest_results(run_id, request.app.state.repository)


@router.get("/{run_id}/logs")
def read_backtest_logs(run_id: str, request: Request) -> dict:
    return get_backtest_logs(run_id, request.app.state.repository)
