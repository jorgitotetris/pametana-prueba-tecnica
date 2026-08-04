import polars as pl
from pathlib import Path

RAW_DATA_PATH = Path(__file__).parent.parent / "data" / "raw"
CSV_FILENAME = "menciones.csv"

def extract() -> pl.DataFrame:
    csv_path = RAW_DATA_PATH / CSV_FILENAME
    if not csv_path.exists():
        raise FileNotFoundError(f"No se encontró el path")

    return pl.read_csv(
        csv_path,
        infer_schema_length=0,
        encoding="utf8-lossy"
    )