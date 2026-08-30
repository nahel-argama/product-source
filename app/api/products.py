import unicodedata

from decimal import Decimal


def normalize_query(query: str) -> str:
    transformed = query.lower().strip()
    normalized = (
        unicodedata.normalize("NFD", transformed)
        .encode("ascii", "ignore")
        .decode("utf-8")
    )

    return normalized.replace(" ", "")



def get_products_price_avg(products: list[dict]) -> Decimal:
    prices = [p["price"] for p in products]
    decimal_prices = [Decimal(str(p)) for p in prices if p is not None]

    avg = sum(decimal_prices) / Decimal(len(decimal_prices))

    return avg.quantize(Decimal("0.01"))
