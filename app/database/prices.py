import datetime

from app.database import get_db


def get_product_prices(
    product_id: str,
    from_date: datetime.datetime,
    to_date: datetime.datetime,
    state: str | None = None,
) -> list[dict]:
    conn = get_db()

    query = """
        SELECT
            id,
            product_id,
            price,
            date,
            municipality,
            state,
            region,
            metric_unit,
            source,
            created_at
        FROM product_prices
        WHERE product_id = ?
    """

    params = [product_id]

    if state is not None:
        query += " AND state = ?"
        params.append(state)

    if from_date:
        query += " AND date >= ?"
        params.append(from_date.date().isoformat())

    if to_date:
        query += " AND date <= ?"
        params.append(to_date.date().isoformat())

    query += " ORDER BY date DESC"

    result = conn.execute(query, params)

    columns = [desc[0] for desc in result.description]
    rows = result.fetchall()

    conn.close()

    return [dict(zip(columns, row)) for row in rows]
