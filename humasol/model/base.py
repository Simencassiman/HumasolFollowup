"""Base definitions for a model."""

from sqlalchemy.orm import DeclarativeMeta

from humasol.repository import db

BaseModel: DeclarativeMeta = db.Model


class ProjectElement:
    """Interface for any element related to a project."""
