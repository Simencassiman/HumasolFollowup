"""Package responsible for the UI."""

from ..repository import db
from .app import HumasolApp


def create_db_tables() -> None:
    """Create the database schemas defined in model."""
    app = HumasolApp()

    with app.app_context():
        db.create_all()
