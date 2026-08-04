import json
from pathlib import Path
import polars as pl

from analyze import (
    total_menciones,
    menciones_por_cliente,
    menciones_por_medio,
    menciones_por_dia,
    medio_mayor_alcance,
)


def construir_informe(df: pl.DataFrame) -> dict:
    ranking_alcance = medio_mayor_alcance(df)
    medio_top = ranking_alcance.row(0, named=True) if ranking_alcance.height > 0 else None

    return {
        "total_menciones": total_menciones(df),
        "por_cliente": menciones_por_cliente(df).to_dicts(),
        "por_medio": menciones_por_medio(df).to_dicts(),
        "por_dia": [
            {"fecha": str(fila["fecha"]), "menciones": fila["menciones"]}
            for fila in menciones_por_dia(df).to_dicts()
        ],
        "medio_mayor_alcance": medio_top,
    }


def imprimir_informe(informe: dict) -> None:
    print(f"\nTotal de menciones: {informe['total_menciones']}")

    print("\nMenciones por cliente:")
    for fila in informe["por_cliente"]:
        print(f"  {fila['cliente']}: {fila['menciones']}")

    print("\nMenciones por medio:")
    for fila in informe["por_medio"]:
        print(f"  {fila['medio']}: {fila['menciones']}")

    print(f"\nMedio con mayor alcance acumulado: "
          f"{informe['medio_mayor_alcance']['medio']} "
          f"({informe['medio_mayor_alcance']['alcance_total']:,})")


def guardar_informe(informe: dict, output_path: str) -> None:
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(informe, f, ensure_ascii=False, indent=2, default=str)
    print(f"\nInforme guardado en: {output_path}")