import sqlite3
from pathlib import Path
import polars as pl

DB_PATH = Path(__file__).parent.parent / "data" / "processed" / "menciones.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS menciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente TEXT NOT NULL,
    medio TEXT NOT NULL,
    fecha DATE NOT NULL,
    titular TEXT,
    texto TEXT,
    alcance INTEGER,
    UNIQUE(cliente, medio, fecha, titular)
);

CREATE INDEX IF NOT EXISTS idx_cliente_fecha ON menciones(cliente, fecha);
"""


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def crear_esquema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)


def cargar_menciones(conn: sqlite3.Connection, df: pl.DataFrame) -> None:
    filas = df.select(["cliente", "medio", "fecha", "titular", "texto", "alcance"]).rows()
    conn.executemany(
        """
        INSERT OR IGNORE INTO menciones (cliente, medio, fecha, titular, texto, alcance)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        filas,
    )
    conn.commit()


if __name__ == "__main__":
    from extract import extract
    from transform import transform

    raw = extract()
    df = transform(raw)

    conn = get_connection()
    crear_esquema(conn)
    cargar_menciones(conn, df)
    conn.close()

    print(f"Base de datos creada en: {DB_PATH}")


import sqlite3

conn = sqlite3.connect("../data/processed/menciones.db")
cursor = conn.execute("SELECT COUNT(*) FROM menciones")
print("Total filas:", cursor.fetchone()[0])

cursor = conn.execute("SELECT * FROM menciones LIMIT 5")
for fila in cursor.fetchall():
    print(fila)

conn.close()