import sqlite3


def evolucion_mensual_cliente(conn: sqlite3.Connection, cliente: str) -> list[dict]:
    """Devuelve el número de menciones y alcance total por mes para un cliente dado."""
    cursor = conn.execute(
        """
        SELECT
            strftime('%Y-%m', fecha) AS mes,
            COUNT(*) AS menciones,
            SUM(alcance) AS alcance_total
        FROM menciones
        WHERE cliente = ?
        GROUP BY mes
        ORDER BY mes
        """,
        (cliente,),
    )
    columnas = [desc[0] for desc in cursor.description]
    return [dict(zip(columnas, fila)) for fila in cursor.fetchall()]


if __name__ == "__main__":
    from load_db import get_connection

    conn = get_connection()
    resultados = evolucion_mensual_cliente(conn, "Velfy")
    for fila in resultados:
        print(fila)
    conn.close()