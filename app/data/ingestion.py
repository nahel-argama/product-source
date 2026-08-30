import logging

import app.database as db
import app.data as data

_LOGGER = logging.getLogger(__name__)

async def ingest_products() -> dict:
    try:
        _LOGGER.info("Starting product ingestion.")
        monthly_filepath = await data.ensure_monthly_csv()

        _LOGGER.debug("Using monthly resource file for products: %s", monthly_filepath)

        conn = db.get_db()
        conn.begin()

        initial_products_count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]

        conn.execute(f"""
            INSERT INTO products (name)
            SELECT DISTINCT lower(trim(dsc_produto))
            FROM read_csv('{monthly_filepath}', delim=';', header=True, encoding='ISO_8859_1')
            WHERE lower(trim(dsc_produto)) NOT IN ('outros generos', 'itens diversos')
              AND lower(trim(dsc_produto)) NOT IN (SELECT name FROM products)
              AND dsc_produto IS NOT NULL
        """)

        final_products_count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        inserted = max(0, final_products_count - initial_products_count)

        _LOGGER.debug("Inserted products total_inserted=%d", inserted)

        conn.commit()

        if inserted > 0:
            db.refresh_products_fts_index(conn)

        conn.close()

        _LOGGER.info("Product ingestion completed. inserted=%d", inserted)

        return {
            "inserted": inserted,
        }
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

        total = conn.execute(f"SELECT COUNT(*) FROM read_csv('{monthly_filepath}', delim=';', header=True, encoding='ISO_8859_1')").fetchone()[0]

        _LOGGER.debug("Loaded %d price rows from source.", total)

        initial_prices_count = conn.execute("SELECT COUNT(*) FROM product_prices").fetchone()[0]

        conn.execute(f"""
            INSERT INTO product_prices
            (product_id, price, date, municipality, state, region, metric_unit, source)
            SELECT
                p.id AS product_id,
                CAST(REPLACE(REPLACE(CAST(s.valor_comercializado AS VARCHAR), '.', ''), ',', '.') AS DECIMAL) / 
                CAST(REPLACE(REPLACE(CAST(s.qtd_comercializada_kg AS VARCHAR), '.', ''), ',', '.') AS DECIMAL) AS price,
                make_date(CAST(s.id_ano_comercializacao AS INTEGER), CAST(s.id_mes_comercializacao AS INTEGER), 1) AS date,
                lower(trim(s.municipio_ceasa)) AS municipality,
                lower(trim(s.uf_ceasa)) AS state,
                lower(trim(s.dsc_ceasa)) AS region,
                'kg' AS metric_unit,
                'monthly' AS source
            FROM read_csv('{monthly_filepath}', delim=';', header=True, encoding='ISO_8859_1') s
            INNER JOIN products p ON p.name = lower(trim(s.dsc_produto))
            WHERE s.dsc_produto IS NOT NULL
              AND s.valor_comercializado IS NOT NULL
              AND s.qtd_comercializada_kg IS NOT NULL
              AND CAST(REPLACE(REPLACE(CAST(s.qtd_comercializada_kg AS VARCHAR), '.', ''), ',', '.') AS DECIMAL) > 0
            ON CONFLICT DO NOTHING;
        """)

        final_prices_count = conn.execute("SELECT COUNT(*) FROM product_prices").fetchone()[0]

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
