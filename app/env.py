from typing import TypeVar, Type

__settings = None
T = TypeVar("T")


class __Env:
    def __init__(self, env_file: str = ""):
        self.__parse_env_file(env_file)

    def __parse_env_file(self, env_file: str) -> None:
        try:
            with open(env_file, "r") as f:
                for line in f:
                    if line.strip() and not line.startswith("#"):
                        key, value = line.strip().split("=", 1)
                        setattr(self, key, value)
        except FileNotFoundError:
            print(f"File not found: {env_file}")
        except Exception as e:
            print(f"Error occurred while parsing env file: {e}")

    def get_attr_typed(self, attr_name: str, default: T, attr_type: Type[T]) -> T:
        value = getattr(self, attr_name, default)

        return attr_type(value)


class __Settings(__Env):
    env_file = ".env"

    def __init__(self):
        super().__init__(self.env_file)


__settings = __Settings()

TIMEZONE = __settings.get_attr_typed("TIMEZONE", "America/Sao_Paulo", str)
LOG_LEVEL = __settings.get_attr_typed("LOG_LEVEL", "INFO", str)
PROHORT_MONTHLY_URL = __settings.get_attr_typed("PROHORT_MONTHLY_URL", "", str)

API_HOST = __settings.get_attr_typed("API_HOST", "127.0.0.1", str)
API_PORT = __settings.get_attr_typed("API_PORT", 8000, int)

GEMINI_KEY = __settings.get_attr_typed("GEMINI_KEY", "", str)
