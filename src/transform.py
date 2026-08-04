
import polars as pl

def clean_medio(df: pl.DataFrame) -> pl.DataFrame:
    return df.with_columns(
        pl.col("medio")
        .str.strip_chars()          # quita espacios al principio/final
        .str.replace_all(r"\s+", " ")  # colapsa dobles espacios internos
        .str.to_titlecase()         # unifica mayus/minus: "el mundo" -> "El Mundo"
    )

def parse_fecha(df: pl.DataFrame) -> pl.DataFrame:
    return df.with_columns(
        pl.coalesce([
            pl.col("fecha").str.strptime(pl.Date, "%Y-%m-%d", strict=False),
            pl.col("fecha").str.strptime(pl.Date, "%d/%m/%Y", strict=False),
        ]).alias("fecha")
    )


import re
from typing import Optional

def _parse_alcance_valor(valor: Optional[str]) -> Optional[int]:
    """Convierte un valor de alcance en texto a entero, o None si no es interpretable."""
    if valor is None:
        return None

    valor = valor.strip().lower()
    if valor in {"", "-", "n.d.", "n/d", "sin datos"}:
        return None

    match = re.match(r"^([\d.,]+)\s*(k|m)?$", valor)
    if not match:
        return None

    numero_str, sufijo = match.groups()

    if sufijo:
        numero = float(numero_str.replace(",", "."))
        multiplicador = 1_000 if sufijo == "k" else 1_000_000
        return int(numero * multiplicador)
    else:
        return int(numero_str.replace(".", "").replace(",", ""))


def parse_alcance(df: pl.DataFrame) -> pl.DataFrame:
    return df.with_columns(
        pl.col("alcance")
        .map_elements(_parse_alcance_valor, return_dtype=pl.Int64)
        .alias("alcance")
    )


def transform(df: pl.DataFrame) -> pl.DataFrame:
    df = clean_medio(df)
    df = parse_fecha(df)
    df = parse_alcance(df)
    df = df.drop_nulls(subset=["cliente", "medio"])
    df = df.unique()
    return df