from pathlib import Path

from pydantic import BaseModel


class Settings(BaseModel):
    project_root: Path = Path(__file__).resolve().parents[2]
    data_dir: Path = project_root / ".local-data"
    duckdb_path: Path = data_dir / "quant_lab.duckdb"


settings = Settings()
