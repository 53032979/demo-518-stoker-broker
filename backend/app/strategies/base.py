from typing import Any, Protocol

import pandas as pd

from backend.app.domain.models import StrategyTemplate


class StrategyRunner(Protocol):
    template: StrategyTemplate

    def generate_targets(
        self,
        market_data: pd.DataFrame,
        current_date: str,
        parameters: dict[str, Any],
    ) -> pd.DataFrame:
        """Return columns: symbol, target_weight."""

