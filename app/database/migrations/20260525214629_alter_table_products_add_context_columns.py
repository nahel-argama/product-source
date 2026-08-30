import duckdb as db


def up(conn: db.DuckDBPyConnection) -> None:
    conn.execute("""
        ALTER TABLE products ADD COLUMN presentation_name TEXT;
    """)
