import logging

import pandas as pd

import app.database as db
import app.data as data

_LOGGER = logging.getLogger(__name__)


def _ingest_products(products: pd.DataFrame) -> dict:
    _LOGGER.debug(
        "Preparing product ingestion with %d candidate products.", len(products)
    )
    conn = db.get_db()

    conn.begin()

    initial_products_count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]

    conn.register("incoming_products", products)

    conn.execute(
        """
        INSERT INTO products (name)
        SELECT source_rows.name
        FROM incoming_products source_rows
        LEFT JOIN products target_rows
          ON target_rows.name = source_rows.name
        WHERE target_rows.name IS NULL
        """
    )

    final_products_count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    inserted = max(0, final_products_count - initial_products_count)

    _LOGGER.debug("Inserted products total_inserted=%d", inserted)

    conn.commit()

    if inserted > 0:
        db.refresh_products_fts_index(conn)

    conn.close()

    return {
        "inserted": inserted,
    }


async def ingest_products() -> dict:
    try:
        _LOGGER.info("Starting product ingestion.")
        monthly_filepath = await data.ensure_monthly_csv()

        _LOGGER.debug("Using monthly resource file for products: %s", monthly_filepath)
        products = await data.get_monthly_products(monthly_filepath)
        result = _ingest_products(products)

        _LOGGER.info("Product ingestion completed. inserted=%d", result["inserted"])

        return result
    except Exception as e:
        _LOGGER.exception("Product ingestion failed.")
        raise Exception(f"Error ingesting products: {e}")


async def ingest_prices() -> dict:
    try:
        _LOGGER.info("Starting price ingestion.")
        conn = db.get_db()
        conn.begin()

        monthly_filepath = await data.ensure_monthly_csv()
        _LOGGER.debug("Using monthly resource file for prices: %s", monthly_filepath)
        prices = await data.get_monthly_prices(monthly_filepath)
        total = len(prices)
        _LOGGER.debug("Loaded %d price rows from source.", total)

        initial_prices_count = conn.execute(
            "SELECT COUNT(*) FROM product_prices"
        ).fetchone()[0]

        conn.register("incoming_prices", prices)

        conn.execute(
            """
            WITH prepared AS (
                SELECT
                    p.id AS product_id,
                    s.price,
                    s.date,
                    s.municipality,
                    s.state,
                    s.region,
                    s.metric_unit,
                    s.source
                FROM incoming_prices s
                INNER JOIN products p ON p.name = s.product_name
            )
            INSERT INTO product_prices
            (product_id, price, date, municipality, state, region, metric_unit, source)
            SELECT
                source_rows.product_id,
                source_rows.price,
                source_rows.date,
                source_rows.municipality,
                source_rows.state,
                source_rows.region,
                source_rows.metric_unit,
                source_rows.source
            FROM prepared source_rows
            LEFT JOIN product_prices target_rows
              ON target_rows.product_id = source_rows.product_id
             AND target_rows.date = source_rows.date
             AND COALESCE(target_rows.municipality, '') = COALESCE(source_rows.municipality, '')
             AND COALESCE(target_rows.state, '') = COALESCE(source_rows.state, '')
             AND COALESCE(target_rows.source, '') = COALESCE(source_rows.source, '')
            WHERE target_rows.id IS NULL
            """
        )

        final_prices_count = conn.execute(
            "SELECT COUNT(*) FROM product_prices"
        ).fetchone()[0]

        inserted = max(0, final_prices_count - initial_prices_count)

        skipped = total - inserted

        conn.commit()
        conn.close()

        _LOGGER.info(
            "Price ingestion completed. inserted=%d skipped=%d total=%d",
            inserted,
            skipped,
            total,
        )

        return {
            "inserted": inserted,
            "skipped": skipped,
            "total": total,
        }
    except Exception as e:
        _LOGGER.exception("Price ingestion failed.")
        raise Exception(f"Error ingesting monthly prices: {e}")
