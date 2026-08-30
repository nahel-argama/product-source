import duckdb as db

def up(conn: db.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE UNIQUE INDEX idx_unique_price_entry
        ON product_prices(product_id, date, coalesce(municipality, ''), coalesce(state, ''), coalesce(source, ''));
    """)
