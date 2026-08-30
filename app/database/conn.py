import os
from datetime import datetime

import duckdb as db

_migrations_path = "app/database/migrations"


def get_db() -> db.DuckDBPyConnection:
    return db.connect("database/database.db")


def migrate() -> None:
    conn = get_db()

    conn.execute(
        "CREATE TABLE IF NOT EXISTS migrations (name TEXT PRIMARY KEY, applied_at TIMESTAMP)"
    )

    migrations = []
    for filename in os.listdir(_migrations_path):
        migrations.append(filename)

    applied_migrations = set(
        row[0] for row in conn.execute("SELECT name FROM migrations").fetchall()
    )

    current_migration = ""

    try:
        conn.begin()

        for migration in sorted(migrations):
            if migration not in applied_migrations:
                if not migration.endswith(".py"):
                    continue

                current_migration = migration

                module_name = migration[:-3]
                module_path = f"{_migrations_path.replace('/', '.')}.{module_name}"

                mod = __import__(module_path, fromlist=["up"])
                mod.up(conn)
                conn.execute(
                    "INSERT INTO migrations (name, applied_at) VALUES (?, ?)",
                    [migration, datetime.now()],
                )
                print(f"Applied migration: {migration}")

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise Exception(f"Error applying migration {current_migration}: {e}")

    conn.close()


def create_migration(name: str) -> None:
    os.makedirs(_migrations_path, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{_migrations_path}/{timestamp}_{name}.py"

    with open(filename, "w") as f:
        f.write(
            """
import duckdb as db

def up(conn: db.DuckDBPyConnection) -> None:
    # Write SQL commands to apply the migration here
    pass

"""
        )
