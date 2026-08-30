import logging
from sys import argv

import app.cli as cli
import app.env as env


def _configure_logging() -> None:
    level_name = (env.LOG_LEVEL).upper()
    level = getattr(logging, level_name, logging.INFO)

    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


def get_command_str() -> tuple[str, list[str]]:
    if len(argv) < 2:
        return "help", []

    args = []
    if len(argv) > 2:
        args = argv[2:]

    return argv[1], args


def main():
    _configure_logging()

    try:
        command_str, command_args = get_command_str()
        command = cli.parse_command(command_str)
        command.handler(command_args)
    except cli.CommandNotFoundError as e:
        print(e)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()
