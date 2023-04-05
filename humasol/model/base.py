"""Base definitions for a model."""

# Python Libraries
import itertools

from sqlalchemy.orm import DeclarativeMeta

# Local modules
from humasol import exceptions
from humasol.repository import db

BaseModel: DeclarativeMeta = db.Model


class ProjectElement:
    """Interface for any element related to a project."""

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
        for num, att in itertools.product(("is", "are"), ("legal", "valid")):
            try:
                if hasattr(
                    self, guard := f"{num}_{att}_{key}"
                ) and not getattr(self, guard)(value):
                    raise exceptions.IllegalArgumentException(
                        f"Illegal value for {key}."
                    )
            except AttributeError:
                # In initialization could be that not all variables have been
                # initialized. This should be foreseen, but to simplify things,
                # just catch the exception...
                ...

        super().__setattr__(key, value)
