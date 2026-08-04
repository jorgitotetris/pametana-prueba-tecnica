import polars as pl

def total_menciones(df: pl.DataFrame) -> int:
    return df.height

def menciones_por_cliente(df: pl.DataFrame) -> pl.DataFrame:
    return (
        df.group_by("cliente")
        .agg(pl.len().alias("menciones"))
        .sort("menciones", descending=True)
    )


def menciones_por_medio(df: pl.DataFrame) -> pl.DataFrame:
    return (
        df.group_by("medio")
        .agg(pl.len().alias("menciones"))
        .sort("menciones", descending=True)
    )


def menciones_por_dia(df: pl.DataFrame) -> pl.DataFrame:
    return (
        df.group_by("fecha")
        .agg(pl.len().alias("menciones"))
        .sort("fecha")
    )


def medio_mayor_alcance(df: pl.DataFrame) -> pl.DataFrame:
    return (
        df.filter(pl.col("alcance").is_not_null())   # excluye los no parseables, criterio ya acordado
        .group_by("medio")
        .agg(pl.col("alcance").sum().alias("alcance_total"))
        .sort("alcance_total", descending=True)
    )

def filtrar_por_keyword(df: pl.DataFrame, keyword: str) -> pl.DataFrame:
    keyword = keyword.lower()
    return df.filter(
        pl.col("titular").str.to_lowercase().str.contains(keyword)
        | pl.col("texto").str.to_lowercase().str.contains(keyword)
    )