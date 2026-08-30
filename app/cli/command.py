import asyncio
import sys

import app.database as db
import app.data as data


class CommandNotFoundError(Exception):
    pass


class ICommand:
    @property
    def command(self) -> str:
        pass

    @property
    def title(self) -> str:
        return ""

    @property
    def help(self) -> str:
        return """"""

    def handler(self, args: list[str]) -> None:
        pass


_COMMAND_REGISTRY = {}


def _register_command(cmd_class) -> ICommand:
    cmd_instance = cmd_class()
    _COMMAND_REGISTRY[cmd_instance.command()] = cmd_instance
    return cmd_class


@_register_command
class HelpCommand(ICommand):
    def command(self) -> str:
        return "help"

    def title(self) -> str:
        return "Show this help message"

    def help(self) -> str:
        return "Show this help message."

    def handler(self, args: list[str]) -> None:
        print("Available commands:\n")

        commands = _COMMAND_REGISTRY.values()

        for cmd in commands:
            title_text = f"{cmd.command()}:"
            help_text = cmd.help()

            print(f"{' ' * 5}{title_text}")
            print(f"{' ' * 8}{help_text}\n")


@_register_command
class Migrate(ICommand):
    def command(self) -> str:
        return "migrate"

    def title(self) -> str:
        return "Run database migrations"

    def help(self) -> str:
        return "Create the necessary tables in the database if they don't exist."

    def handler(self, args: list[str]) -> None:
        try:
            db.migrate()
            print("Database migrated successfully.")
        except Exception as e:
            print(f"Error migrating database: {e}", file=sys.stderr)


@_register_command
class CreateMigrationCommand(ICommand):
    def command(self) -> str:
        return "create-migration"

    def title(self) -> str:
        return "Create a new database migration file"

    def help(self) -> str:
        return "Create a new database migration file with the given name."

    def handler(self, args: list[str]) -> None:
        name = ""
        if len(args) > 0:
            name = args[0].strip()

        if not name:
            print("Migration name cannot be empty.", file=sys.stderr)
            return

        try:
            db.create_migration(name)
            print(f"Migration '{name}' created successfully.")
        except Exception as e:
            print(f"Error creating migration: {e}", file=sys.stderr)


@_register_command
class IngestProductsCommand(ICommand):
    def command(self) -> str:
        return "ingest-products"

    def title(self) -> str:
        return "Ingest products"

    def help(self) -> str:
        return "Ingest product names from the configured source into the database."

    def handler(self, args: list[str]) -> None:
        try:
            result = asyncio.run(data.ingest_products())

            print(f"Products ingested: {result['inserted']} inserted.")
        except Exception as e:
            print(f"Error ingesting products: {e}", file=sys.stderr)


@_register_command
class IngestPricesCommand(ICommand):
    def command(self) -> str:
        return "ingest-prices"

    def title(self) -> str:
        return "Ingest prices"

    def help(self) -> str:
        return "Ingest product prices from the configured source into the database."

    def handler(self, args: list[str]) -> None:
        try:
            monthly_result = asyncio.run(data.ingest_prices())
            print(
                f"Prices ingested: {monthly_result['inserted']} inserted, {monthly_result['skipped']} skipped, {monthly_result['total']} total."
            )
        except Exception as e:
            print(f"Error ingesting prices: {e}", file=sys.stderr)


@_register_command
class DownloadResourceCommand(ICommand):
    def command(self) -> str:
        return "download-resource"

    def title(self) -> str:
        return "Download source data"

    def help(self) -> str:
        return "Download the current source file and store it in the managed resource directory."

    def handler(self, args: list[str]) -> None:
        try:
            result = asyncio.run(data.download_monthly_csv())
            print(f"Source data downloaded successfully in file: {result}")
        except Exception as e:
            print(f"Error downloading monthly data: {e}", file=sys.stderr)


@_register_command
class DeleteDataCommand(ICommand):
    def command(self) -> str:
        return "delete-data"

    def title(self) -> str:
        return "Delete data files"

    def help(self) -> str:
        return "Delete all managed resource files from local storage."

    def handler(self, args: list[str]) -> None:
        try:
            data.delete_data_dir()
        except Exception as e:
            print(f"Error deleting data: {e}", file=sys.stderr)


def parse_command(command_str: str) -> ICommand:
    cmd = _COMMAND_REGISTRY.get(command_str)
    if not cmd:
        raise CommandNotFoundError(
            f"Command '{command_str}' not found. Use 'help' to see available commands."
        )
    return cmd


@_register_command
class UpdateProductContextCommand(ICommand):
    def command(self) -> str:
        return "update-product-context"

    def title(self) -> str:
        return "Update product context"

    def help(self) -> str:
        return "Generate and update the presentation name and context for products that are missing this information."

    def handler(self, args: list[str]) -> None:
        from app.ai.generation import run_batch_update

        try:
            run_batch_update()
        except Exception as e:
            print(f"Error updating product context: {e}", file=sys.stderr)
