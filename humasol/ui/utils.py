"""Module providing utility functions for Flask and app setup."""


from ..repository import db
from .app import HumasolApp


def create_db_tables() -> None:
    """Create the database schemas defined in model."""
    app = HumasolApp(__name__)
    db.init_app(app)

    with app.app_context():
        db.create_all()
