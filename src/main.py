import argparse
from pathlib import Path

from extract import extract
from transform import transform
from analyze import filtrar_por_keyword
from report import construir_informe, imprimir_informe, guardar_informe

PROJECT_ROOT = Path(__file__).parent.parent
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "processed" / "informe.json"


def main():
    parser = argparse.ArgumentParser(description="Análisis de menciones - Pametana")
    parser.add_argument("--keyword", type=str, default=None,
                         help="Filtra las menciones que contengan esta palabra clave")
    parser.add_argument("--output", type=str, default=str(DEFAULT_OUTPUT),
                         help="Ruta del fichero de informe de salida")
    args = parser.parse_args()

    raw = extract()
    df = transform(raw)

    if args.keyword:
        df = filtrar_por_keyword(df, args.keyword)
        print(f"Filtrando por keyword: '{args.keyword}' ({df.height} menciones encontradas)")

    informe = construir_informe(df)
    imprimir_informe(informe)
    guardar_informe(informe, args.output)


if __name__ == "__main__":
    main()