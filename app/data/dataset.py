import unicodedata

import pandas as pd


def _normalize_string(name: str) -> str:
    ss = name.strip().lower()
    return unicodedata.normalize("NFD", ss).encode("ascii", "ignore").decode("ascii")


def _normalize_optional_string(value: object) -> str | None:
    if not isinstance(value, str):
        return None

    normalized = _normalize_string(value)
    return normalized if normalized else None


async def get_monthly_products(filepath: str) -> pd.DataFrame:
    df = _read_monthly_data_frame(filepath)

    products = pd.DataFrame(
        {
            "name": df["dsc_produto"].map(_normalize_optional_string),
        }
    )

    products = products.dropna(subset=["name"]).drop_duplicates(
        subset=["name"],
        keep="first",
    )

    blacklist = [
        "outros generos",
        "itens diversos",
    ]

    products = products[~products["name"].isin(blacklist)]

    return products


async def get_monthly_prices(filepath: str) -> pd.DataFrame:
    df = _read_monthly_data_frame(filepath)

    prices = pd.DataFrame(
        {
            "product_name": df["dsc_produto"].map(_normalize_optional_string),
            "price": pd.to_numeric(df["preco_mensal"], errors="coerce"),
            "date": df["data_preco"].dt.strftime("%Y-%m-%d"),
            "municipality": df["municipio_ceasa"].map(_normalize_optional_string),
            "state": df["uf_ceasa"].map(_normalize_optional_string),
            "region": df["dsc_ceasa"].map(_normalize_optional_string),
            "metric_unit": "kg",
            "source": "monthly",
        }
    )

    prices = prices.drop_duplicates(
        subset=["product_name", "date", "municipality", "state", "source"],
        keep="first",
    ).reset_index(drop=True)

    return prices


def _read_monthly_data_frame(filepath: str) -> pd.DataFrame:
    df = pd.read_csv(filepath, delimiter=";", encoding="iso-8859-1")

    df = _normalize_frame(df)

    df["qtd_comercializada_kg"] = _parse_month_decimal(df["qtd_comercializada_kg"])
    df["valor_comercializado"] = _parse_month_decimal(df["valor_comercializado"])

    df["id_ano_comercializacao"] = pd.to_numeric(
        df["id_ano_comercializacao"], errors="coerce"
    )
    df["id_mes_comercializacao"] = pd.to_numeric(
        df["id_mes_comercializacao"], errors="coerce"
    )

    df["data_preco"] = pd.to_datetime(
        {
            "year": df["id_ano_comercializacao"],
            "month": df["id_mes_comercializacao"],
            "day": 1,
        },
        errors="coerce",
    )

    df["preco_mensal"] = df["valor_comercializado"] / df["qtd_comercializada_kg"]
    df["preco_mensal"] = pd.to_numeric(df["preco_mensal"], errors="coerce")

    df = df.dropna(subset=["dsc_produto", "data_preco"]).reset_index(drop=True)

    return df


def _normalize_frame(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = df.columns.str.strip().str.lower()
    df = df.map(lambda s: s.lower().strip() if isinstance(s, str) else s)
    return df


def _parse_month_decimal(series: pd.Series) -> pd.Series:
    return pd.to_numeric(
        series.astype(str)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False),
        errors="coerce",
    )
