import os

import requests


def create_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def get_data_dir() -> str:
    return "data"


async def download_file(url: str, filepath: str) -> str:
    parent_dir = os.path.dirname(filepath)
    create_dir(parent_dir)

    with requests.get(url, stream=True) as response:
        response.raise_for_status()

        with open(filepath, "wb") as file_obj:
            for chunk in response.iter_content(chunk_size=8192):
                file_obj.write(chunk)

    return filepath


def delete_csv_files(dirpath: str, prefix: str | None = None) -> None:
    if not os.path.isdir(dirpath):
        return

    try:
        for filename in os.listdir(dirpath):
            if not filename.endswith(".csv"):
                continue
            if prefix and not filename.startswith(prefix):
                continue
            os.remove(os.path.join(dirpath, filename))
    except Exception as e:
        raise Exception(f"Error cleaning data dir: {e}")
