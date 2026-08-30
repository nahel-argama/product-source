import duckdb as db


def up(conn: db.DuckDBPyConnection) -> None:
    conn.execute("CREATE SEQUENCE serial")
    pass
