# Price Scrapper

Simple service to download public produce price data from CONAB Prohort, ingest it into DuckDB, and expose it through a small FastAPI API.

## What this project does

- Downloads the monthly source CSV file.
- Ingests products and prices into a local DuckDB database.
- Exposes endpoints to search products and calculate average prices by period/state.

Main components:

- CLI entrypoint: `cli.py`
- API entrypoint: `api.py`
- Database file: `database/database.db`

## Requirements

- Python 3.14+

## Setup

### 1. Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
python -m pip install -e .
```

## Environment variables

Copy the `.env.example` file to `.env` and change what you need

```bash
cp .env.example .env
```

Notes:

- `PROHORT_MONTHLY_URL` is required to download source data.
- Other variables are optional and have defaults in the code.

## Updating database data

You only must run this if you want to update the database data with a new month entry. The database is versionized, so you can skip this

Check the available CLI commands:

```bash
python cli.py help
```

1. Run migrations (Only if there are migrations to run):

```bash
python cli.py migrate
```

1. Download monthly file:

```bash
python cli.py download-resource
```

1. Ingest products and prices:

```bash
python cli.py ingest-products
python cli.py ingest-prices
```

## Running the API

```bash
python api.py
```

Quick check:

```bash
# The url here will match the defined host and port in the .env file
curl "http://127.0.0.1:8000/health"
```

## OpenCollection and Bruno docs

Project API collection and generated static docs are in `collections/`:

- OpenCollection: `collections/opencollection.yml`
- Bruno collections: `collections/Products.yml`, `collections/Prices.yml`
- Generated static HTML documentation (Bruno): `collections/Price Scrapper-documentation.html`

Open the HTML file in your browser to navigate the documented requests.
