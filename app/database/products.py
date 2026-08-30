import duckdb as db

from app.database import get_db


def refresh_products_fts_index(conn: db.DuckDBPyConnection) -> None:
    try:
        conn.execute("""
            PRAGMA create_fts_index('products', 'id', 'name',
                stemmer='portuguese',
                strip_accents=1,
                lower=1,
                overwrite=1,
                ignore='[().,;:/\\-]'
            )
            """)
    except Exception as e:
        raise Exception(f"Error refreshing FTS index: {e}")


def product_search(query: str, limit: int = 100) -> list[dict]:
    return jaro_winkler_similarity_search(query, limit)


def fts_product_search(query: str, limit: int = 100) -> list[dict]:
    conn = get_db()
    try:
        result = conn.execute(
            """
            SELECT
                p.id,
                p.name,
                p.created_at,
                p.presentation_name,
                fts_main_products.match_bm25(p.id, ?) as score
            FROM products p
            WHERE score IS NOT NULL
            ORDER BY score DESC
            LIMIT ?
            """,
            [query, limit],
        )

        rows = result.fetchall()
        columns = [desc[0] for desc in result.description]

        return [dict(zip(columns, row)) for row in rows]
    finally:
        conn.close()


def jaro_winkler_similarity_search(query: str, limit: int = 100) -> list[dict]:
    conn = get_db()

    try:
        result = conn.execute(
            """
            SELECT
                p.id,
                p.name,
                p.created_at,
                p.presentation_name,
                jaro_winkler_similarity(replace(p.name, ' ', ''), ?, 0.65) AS score
            FROM products p
            WHERE
                score > 0
            ORDER BY
                score DESC
            LIMIT ?
            """,
            [query, limit],
        )

        rows = result.fetchall()
        columns = [desc[0] for desc in result.description]

        return [dict(zip(columns, row)) for row in rows]
    finally:
        conn.close()


def get_products_without_presentation_name(limit: int = 20) -> list[dict]:
    conn = get_db()
    try:
        result = conn.execute(
            """
            SELECT
                id,
                name
            FROM products
            WHERE presentation_name IS NULL
            LIMIT ?
            """,
            [limit],
        )

        rows = result.fetchall()
        columns = [desc[0] for desc in result.description]

        return [dict(zip(columns, row)) for row in rows]
    finally:
        conn.close()


def update_product_context(
    conn: db.DuckDBPyConnection, product_id: str, presentation_name: str
) -> None:
    try:
        conn.execute(
            """
            UPDATE products
            SET presentation_name = ?
            WHERE id = ?
            """,
            [presentation_name, product_id],
        )
    except Exception as e:
        raise Exception(f"Error updating product context: {e}")


def get_product_by_id(product_id: str) -> dict | None:
    conn = get_db()
    try:
        result = conn.execute(
            """
            SELECT
                id,
                name,
                created_at,
                presentation_name
            FROM products
            WHERE id = ?
            """,
            [product_id],
        )

        row = result.fetchone()
        if row is None:
            return None

        columns = [desc[0] for desc in result.description]
        return dict(zip(columns, row))
    finally:
        conn.close()
