"""Package responsible for all the folder requests."""

from flask_sqlalchemy import SQLAlchemy

# Local modules
# pylint: disable=cyclic-import
from .storage_repository import get_object_by_id, save_project  # noqa

# pylint: disable=cyclic-import

db: SQLAlchemy = SQLAlchemy()
