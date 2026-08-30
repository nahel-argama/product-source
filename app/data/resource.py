import logging
import os
from datetime import datetime
from zoneinfo import ZoneInfo

import app.env as env
from app.data import delete_csv_files, download_file, get_data_dir

_MONTHLY_PREFIX = "prohort_monthly"
_LOGGER = logging.getLogger(__name__)


def get_monthly_dir() -> str:
    return os.path.join(get_data_dir(), "monthly")


def get_month_filename() -> str:
    tz = ZoneInfo(env.TIMEZONE)
    month = datetime.now(tz).strftime("%Y-%m")
    filename = f"{_MONTHLY_PREFIX}_{month}.csv"
    filepath = os.path.join(get_monthly_dir(), filename)
    _LOGGER.debug("Resolved monthly resource filepath: %s", filepath)
    return filepath


async def download_monthly_csv() -> str:
    filepath = get_month_filename()
    _LOGGER.info("Downloading monthly resource to: %s", filepath)
    return await download_file(env.PROHORT_MONTHLY_URL, filepath)


async def ensure_monthly_csv() -> str:
    filepath = get_month_filename()
    if os.path.exists(filepath):
        _LOGGER.debug("Monthly resource already exists at: %s", filepath)
        return filepath
    _LOGGER.info("Monthly resource not found. Starting download: %s", filepath)
    return await download_monthly_csv()


def delete_data_dir() -> None:
    _LOGGER.info(
        "Deleting managed monthly resource files in: %s (prefix=%s)",
        get_monthly_dir(),
        _MONTHLY_PREFIX,
    )
    delete_csv_files(get_monthly_dir(), prefix=_MONTHLY_PREFIX)


def get_today_filename() -> str:
    return get_month_filename()


async def download_daily_csv() -> str:
    return await download_monthly_csv()
