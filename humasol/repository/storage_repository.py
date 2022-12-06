"""
Persistent storage interface.

Module responsible for the repository functionality to interface with
persistent storage.
"""

# Python Libraries
from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING, Type, TypeVar, Union

from sqlalchemy.orm import DeclarativeMeta

# Local modules
from humasol.config import config as cf
from humasol.repository import db

if TYPE_CHECKING:
    from humasol import model


ENCODING = "utf-8"
BaseModel: DeclarativeMeta = db.Model
T = TypeVar("T", bound=BaseModel)
# Params = dict[str, Union[str, float, "Params"]]


def _get_data_from_file(file: str) -> dict[str, Union[str, float, dict]]:
    """Retrieve data from a JSON file."""
    if not os.path.exists(file):
        return {}

    with open(os.path.join(cf.PROJECT_FILES, file), encoding=ENCODING) as data:
        params = json.load(data)

    return params


def _save_project_data_to_file(
    data: dict[str, Union[str, float, dict]], file: str
) -> None:
    """Save project data to a JSON file."""
    with open(
        os.path.join(cf.PROJECT_FILES, file), "w", encoding=ENCODING
    ) as data_file:
        json.dump(data, data_file)


def get_object_by_id(obj_class: Type[T], obj_id: int) -> T:
    """Retrieve an object of the given class from the database.

    Retrieve the object with the provided ID from the database.
    """
    obj = obj_class.query.get(obj_id)

    if hasattr(obj, "load_from_file"):
        obj.load_from_file(_get_data_from_file(obj.data_file))

    return obj


def save_project(project: model.Project) -> None:
    """Save project object to database."""
    # TODO: rollback if error happens
    session = db.session

    # Save to db
    # pylint: disable=no-member
    session.merge(project)
    session.commit()
    # pylint: enable=no-member

    # Save to file
    _save_project_data_to_file(project.to_save_to_file(), project.data_file)
