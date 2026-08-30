import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import app.database as db
import app.api.products as products

router = APIRouter(prefix="/api")


class SearchResponse(BaseModel):
    model_config = {"extra": "ignore"}

    id: str
    name: str | None
    normal_name: str
    created_at: datetime.datetime


class PriceResponse(BaseModel):
    model_config = {"extra": "ignore"}

    product_id: str
    from_date: datetime.date
    to_date: datetime.date
    name: str | None
    normal_name: str
    state: str
    avg_price: float
    is_fallback: bool
    price_entries: dict[datetime.date, float] | None


@router.get("/products/search")
def search_products_endpoint(query: str, limit: int = 10):
    if not query or len(query.strip()) == 0:
        raise HTTPException(status_code=400, detail="Query parameter is required")

    normalized_query = products.normalize_query(query)

    results = db.product_search(normalized_query, limit)

    response = []
    for r in results:
        response.append(
            SearchResponse(
                id=r["id"],
                name=r["presentation_name"],
                normal_name=r["name"],
                created_at=r["created_at"],
            )
        )

    return response


@router.get("/products/{product_id}/prices")
def get_prices_endpoint(
    product_id: str,
    from_date: datetime.datetime,
    to_date: datetime.datetime,
    state: str,
):
    is_fallback = False
    prices = db.get_product_prices(product_id, from_date, to_date, state)
    if not prices:
        is_fallback = True
        prices = db.get_product_prices(product_id, from_date, to_date, None)

    if not prices:
        raise HTTPException(
            status_code=404,
            detail=f"No price data found for the specified product and date range at {state}",
        )

    avg_price = products.get_products_price_avg(prices)
    product = db.get_product_by_id(product_id)

    price_entries = None

    if not is_fallback:
        price_entries = {}
        for p in prices:
            date = p["date"]
            price_entries[date] = float(p["price"])

    return PriceResponse(
        from_date=from_date,
        to_date=to_date,
        product_id=product_id,
        name=product["presentation_name"],
        normal_name=product["name"],
        state=state,
        avg_price=avg_price,
        is_fallback=is_fallback,
        price_entries=price_entries,
    )


@router.get("/products/{product_id}")
def get_product_endpoint(product_id: str):
    product = db.get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return SearchResponse(
        id=product["id"],
        name=product["presentation_name"],
        normal_name=product["name"],
        created_at=product["created_at"],
    )
