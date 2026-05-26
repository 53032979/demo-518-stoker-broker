from typing import Protocol

import pandas as pd


class MarketDataProvider(Protocol):
    def load_daily_bars(
        self,
        symbols: list[str],
        start_date: str,
        end_date: str,
    ) -> pd.DataFrame:
        """Return normalized daily bars."""
