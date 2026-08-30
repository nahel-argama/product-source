import duckdb as db


def up(conn: db.DuckDBPyConnection) -> None:
    conn.execute(
        """
        CREATE TABLE product_prices (
            id INTEGER PRIMARY KEY DEFAULT nextval('serial'),
            product_id TEXT NOT NULL,
            price DECIMAL(10, 2),
            date DATE NOT NULL,
            municipality TEXT,
            state TEXT,
            region TEXT,
            metric_unit TEXT,
            source TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
        """
    )

    conn.execute(
        "CREATE INDEX idx_product_prices_product_id_date ON product_prices(product_id, date)"
    )
    conn.execute("CREATE INDEX idx_product_prices_source ON product_prices(source)")
    pass
