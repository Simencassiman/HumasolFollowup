"""Base definitions for a model."""

# Python Libraries
from __future__ import annotations

import abc
import typing as ty

from sqlalchemy.orm import DeclarativeMeta

# Local modules
from humasol.model import utils
from humasol.model.snapshot import Snapshot
from humasol.repository import db

BaseModel: DeclarativeMeta = db.Model


class ProjectElement:
    """Interface for any element related to a project."""

    @abc.abstractmethod
    @Snapshot.protect
    def update(self, params: dict[str, ty.Any]) -> ProjectElement:
        """Update element parameters.

        Function in concrete class should be decorated with @Snapshot.protect
        to roll back if any values were incorrect.
        """

    def __setattr__(self, key, value) -> None:
        """Set the attribute of this object.

        If the object has defined a guard of the form
        is/are_legal/valid_{key}
        then this guard will first be checked.

        Parameters
        __________
        key: name of the attribute
        value: new value for the attribute
        """
        utils.check_guards(self, key, value)
        super().__setattr__(key, value)
