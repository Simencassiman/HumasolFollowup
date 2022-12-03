"""Module providing configuration settings."""

# Python Libraries
import os
import re
from typing import Union, get_type_hints

dir_path = os.path.dirname(os.path.realpath(__file__))
PROJECT_FILES = os.path.join(dir_path, "project_files")

# Disable some pylint checks which should be ok
# pylint: disable=no-member
# pylint: disable=too-few-public-methods


class AppConfigError(Exception):
    """Exception specific to the AppConfig class."""


# pylint: disable=unidiomatic-typecheck
def _parse_bool(val: Union[str, bool]) -> bool:
    """Parse a boolean environment variable."""
    return val if type(val) == bool else val.lower() in ["true", "yes", "1"]


# pylint: enable=unidiomatic-typecheck


# AppConfig class with required fields, default values, type checking,
# and typecasting for int and bool values
class AppConfig:
    """Class to load config environment variables."""

    # File access #
    PROJECT_FILES = os.path.join(dir_path, "ui/project_files")

    # Database #
    SECRET_KEY: str
    SECURITY_PASSWORD_SALT: str
    DATABASE_URL: str

    # Humasol #
    ADMIN_EMAIL: str
    ADMIN_PWD: str

    """
    Map environment variables to class fields according to these rules:
      - Field won't be parsed unless it has a type annotation
      - Field will be skipped if not in all caps
      - Class field and environment variable name are the same
    """

    def __init__(self):
        """Load relevant environment variables for app configuration."""
        env = os.environ

        for field in self.__annotations__:
            if not field.isupper():
                continue

            # Raise AppConfigError if required field not supplied
            default_value = getattr(self, field, None)
            if default_value is None and env.get(field) is None:
                raise AppConfigError(f"The {field} field is required")

            # Cast env var value to expected type and raise
            # AppConfigError on failure
            var_type = None
            try:
                var_type = get_type_hints(AppConfig)[field]
                if var_type == bool:
                    value = _parse_bool(env.get(field, default_value))
                else:
                    value = var_type(env.get(field, default_value))

                self.__setattr__(field, value)
            except ValueError as exc:
                raise AppConfigError(
                    f'Unable to cast value of "{env[field]}" to type '
                    f'"{var_type}" for "{field}" field'
                ) from exc

        self._correct_sql_dialect()

    # pylint: disable=invalid-name
    def _correct_sql_dialect(self) -> None:
        """Convert the sql dialect to the correct name for SQLAlchemy."""
        if matched := re.match(r"postgres(://.*)", self.DATABASE_URL):
            self.DATABASE_URL = f"postgresql{matched.groups()[0]}"

    # pylint: enable=invalid-name

    def __repr__(self):
        """Provide a representation of this instance."""
        return str(self.__dict__)


# pylint: enable=too-few-public-methods
# pylint: enable=no-member

# Expose Config object for app to import
config = AppConfig()
