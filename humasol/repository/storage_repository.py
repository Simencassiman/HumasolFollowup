"""
Persistent storage interface.

Module responsible for the repository functionality to interface with
persistent storage.
"""

# Python Libraries
from __future__ import annotations

import json
import os
import typing as ty

import sqlalchemy
from sqlalchemy.orm import DeclarativeMeta

# Local modules
from humasol import exceptions
from humasol.config import config as cf
from humasol.repository import db

if ty.TYPE_CHECKING:
    from humasol import model


ENCODING = "utf-8"
BaseModel: DeclarativeMeta = db.Model
T = ty.TypeVar("T", bound=BaseModel)
# Params = dict[str, Union[str, float, "Params"]]


def _get_data_from_file(file: str) -> dict[str, str | float | dict]:
    """Retrieve data from a JSON file."""
    if not os.path.exists(file):
        return {}

    with open(os.path.join(cf.PROJECT_FILES, file), encoding=ENCODING) as data:
        params = json.load(data)

    return params


def _save_project_data_to_file(
    data: dict[str, str | float | dict], file: str
) -> None:
    """Save project data to a JSON file."""
    with open(
        os.path.join(cf.PROJECT_FILES, file), "w", encoding=ENCODING
    ) as data_file:
        json.dump(data, data_file)


def delete_project(project: model.Project) -> None:
    """Delete project from the database.

    Parameters
    __________
    project     -- Project to be deleted
    """
    try:
        session = db.session
        # pylint: disable=no-member
        session.delete(project)
        session.commit()
        # pylint: enable=no-member
    except sqlalchemy.exc.IntegrityError as exc:
        raise exceptions.IntegrityException(str(exc)) from exc


def get_object_by_attributes(
    cls: type[T], arguments: dict[str, ty.Any], disjunction: bool = True
) -> list[T]:
    """Retrieve objects matching the given attributes.

    Parameters
    __________
    cls     -- Class of objects to query
    arguments   -- Dictionary of attribute names and values on which to match
    disjunction -- Indicates whether the match is on a disjunction or a
                    conjunction of the provided attributes.

    Returns
    _______
    List of objects of the provided class (cls). Can be empty if non matched.
    """
    condition = sqlalchemy.or_ if disjunction else sqlalchemy.and_

    try:
        query = cls.query.filter(
            condition(
                *[
                    getattr(cls, attr) == str(value)
                    for attr, value in arguments.items()
                ]
            )
        )

        return query.all()

    except (AttributeError, sqlalchemy.exc.NoSuchTableError) as exc:
        raise exceptions.NotDatamodelClassException(str(exc)) from exc
    except (
        sqlalchemy.exc.DBAPIError,
        sqlalchemy.exc.DataError,
        sqlalchemy.exc.DatabaseError,
        sqlalchemy.exc.NoReferencedColumnError,
    ) as exc:
        raise exceptions.ObjectNotFoundException(str(exc)) from exc
    except sqlalchemy.exc.InvalidRequestError as exc:
        raise exceptions.InvalidRequestException(str(exc)) from exc
    except sqlalchemy.exc.SQLAlchemyError as exc:
        raise exceptions.RepositoryException(str(exc)) from exc


def get_object_by_id(obj_class: type[T], obj_id: int) -> T:
    """Retrieve an object of the given class from the database.

    Retrieve the object with the provided ID from the database.
    """
    try:
        obj = obj_class.query.get(obj_id)

    except (AttributeError, sqlalchemy.exc.NoSuchTableError) as exc:
        raise exceptions.NotDatamodelClassException(str(exc)) from exc
    except (
        sqlalchemy.exc.DBAPIError,
        sqlalchemy.exc.DataError,
        sqlalchemy.exc.DatabaseError,
        sqlalchemy.exc.NoReferencedColumnError,
    ) as exc:
        raise exceptions.ObjectNotFoundException(str(exc)) from exc
    except sqlalchemy.exc.InvalidRequestError as exc:
        raise exceptions.InvalidRequestException(str(exc)) from exc
    except sqlalchemy.exc.SQLAlchemyError as exc:
        raise exceptions.RepositoryException(str(exc)) from exc

    try:
        if hasattr(obj, "load_from_file"):
            obj.load_from_file(_get_data_from_file(obj.data_file))

    except (TypeError, KeyError) as exc:
        raise exceptions.IllegalFileContent(str(exc)) from exc

    return obj


def save_project(project: model.Project) -> None:
    """Save project object to database."""
    # TODO: rollback if error happens
    try:
        session = db.session

        # Save to db
        # pylint: disable=no-member
        session.merge(project)
        session.commit()
        # pylint: enable=no-member
    except sqlalchemy.exc.IntegrityError as exc:
        raise exceptions.IntegrityException(str(exc)) from exc

    # Save to file
    # TODO: figure out how to do it on heroku
    # _save_project_data_to_file(project.to_save_to_file(), project.data_file)


def table_exists(table: str) -> bool:
    """Check whether the database table has been created.

    Parameters
    __________
    table   -- Table name
    """
    return db.engine.execute(
        db.text(
            """
            SELECT EXISTS (
                SELECT FROM
                    pg_tables
                WHERE
                    schemaname = 'public' AND
                    tablename  = :table_name
            );
            """
        ),
        {"table_name": table},
    ).first()[0]
