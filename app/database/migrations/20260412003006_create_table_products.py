import duckdb as db


def up(conn: db.DuckDBPyConnection) -> None:
    conn.execute(
        """
        CREATE TABLE products (
            id TEXT PRIMARY KEY DEFAULT nextval('serial'),
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    pass
