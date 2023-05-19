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
from functools import update_wrapper

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


def _get_data_from_file(file: str) -> dict[str, str | float | dict]:
    """Retrieve data from a JSON file."""
    if not os.path.exists(file):
        return {}

    with open(os.path.join(cf.PROJECT_FILES, file), encoding=ENCODING) as data:
        params = json.load(data)

    return params


def _recurse_relations(obj_class: type, seen: list = None) -> list[tuple]:
    """Recursively enumerate all paths relationship paths to relationships.

    Recurse down into relationships to retrieve all relationships. Providing a
    path from the initial parent through the relationships to all other
    relationships. E.g., if Parent has a relationship children with Child, and
    Child has a relationship friends with Child. Then the relationship
    paths will be given by (Parent.children) and
    (Parent.children, Child.friends).

    Parameters
    __________
    obj_class   -- Class for which to extract relationships
    seen        -- Seen classes since the root call

    Returns
    _______
    List of paths (tuples of consecutive relationship attributes) to all
    relationships.
    """
    # Keep track of seen classes to avoid cyclic paths leading to
    # infinite recursion
    if not seen:
        seen = []
    seen.append(obj_class)

    # Retrieve all relationships of the class
    relationships = sqlalchemy.inspection.inspect(obj_class).relationships

    # Container for all recursive relationships
    relations = list[tuple[ty.Any, ...]]()

    # Loop through all relationships
    for attr, rel in relationships.items():
        if rel.back_populates:
            # If it is a backreference relationship skip it
            continue

        # Create leaf for this relationship
        relation = getattr(obj_class, attr)
        relations.append((relation,))

        if (_class := rel.mapper.class_) not in seen:
            # Recurse
            relations += [
                (relation, *_rel)  # Create path to recursive relationships
                for _rel in _recurse_relations(_class, seen)
            ]

    return relations


def _recursive_expunge(obj) -> None:
    """Recursively remove all objects from the database session.

    Parameters
    __________
    obj     -- Object to remove from the session
    """
    # Retrieve relational information from the object
    _instance_state = sqlalchemy.inspection.inspect(obj)
    _mapper = _instance_state.mapper

    try:
        # Remove the object itself
        # pylint: disable=no-member
        db.session.expunge(obj)
        # pylint: enable=no-member
    except (
        sqlalchemy.orm.exc.UnmappedInstanceError,
        sqlalchemy.exc.InvalidRequestError,
    ):
        ...

    if _mapper:
        # Collect related objects
        _loaded_rels = [
            i
            for i in _mapper.relationships.items()
            if i[0] not in _instance_state.unloaded
        ]

        # Loop over loaded related objects
        for _name, _rel in _loaded_rels:
            # Get relation object
            _loaded_rel_data = getattr(obj, _name)

            # Recurse (with possibility of a list or not)
            if _loaded_rel_data:
                if not _rel.uselist:
                    _recursive_expunge(_loaded_rel_data)
                else:
                    for _i in _loaded_rel_data:
                        _recursive_expunge(_i)


def _save_project_data_to_file(
    data: dict[str, str | float | dict], file: str
) -> None:
    """Save project data to a JSON file."""
    with open(
        os.path.join(cf.PROJECT_FILES, file), "w", encoding=ENCODING
    ) as data_file:
        json.dump(data, data_file)


def commit() -> None:
    """Commit changes made to persisted objects."""
    try:
        # pylint: disable=no-member
        db.session.commit()
        # pylint: enable=no-member
    except sqlalchemy.exc.IntegrityError as exc:
        raise exceptions.IntegrityException(str(exc))
    except sqlalchemy.exc.InvalidRequestError as exc:
        raise exceptions.InvalidRequestException(str(exc)) from exc
    except sqlalchemy.exc.SQLAlchemyError as exc:
        raise exceptions.RepositoryException(str(exc)) from exc


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


def expunge(obj: model.Model, recursive: bool = False) -> None:
    """Detaches object from the databased session.

    Parameters
    __________
    obj     -- Object to remove from the session
    recurse -- Whether to recursively remove all related object from the
                session
    """
    if recursive:
        _recursive_expunge(obj)
        return

    # pylint: disable=no-member
    db.session.expunge(obj)
    # pylint: disable=no-member


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


def get_object_by_id(
    obj_class: type[T], obj_id: int, eager: bool = False
) -> T:
    """Retrieve an object of the given class from the database.

    Retrieve the object with the provided ID from the database.

    Parameters
    __________
    obj_class   -- Class of the object to load
    obj_id      -- ID of the object to load
    eager       -- Whether to force eager loading of relationships
    """
    try:
        query = obj_class.query

        if eager:
            # Create orm query options to force eager loading
            loaders = [
                sqlalchemy.orm.selectinload(*attr)
                for attr in _recurse_relations(obj_class)
            ]

            # Adjust the query
            query = query.options(*loaders)

        obj = query.get(obj_id)

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


def merge(obj: model.Model) -> None:
    """Merge an object with internal database state.

    Parameters
    __________
    obj     -- Object who's state to merge
    """
    try:
        # Merge with db
        # pylint: disable=no-member
        db.session.merge(obj)
        db.session.commit()
        # pylint: enable=no-member
    except sqlalchemy.exc.IntegrityError as exc:
        raise exceptions.IntegrityException(str(exc)) from exc


def no_autoflush(func):
    """Prevent database from automatically flushing.

    To be used as a decorator.

    Parameter
    _________
    func    -- Function during which to disable automatic flushing
    """

    def wrapper(*args, **kw):
        session = db.session
        # Save current setting
        autoflush = session.autoflush
        # Disable automatic flush
        session.autoflush = False
        try:
            # Execute decorated function
            return func(*args, **kw)
        finally:
            # Reset automatic flushing to previous behaviour
            session.autoflush = autoflush

    return update_wrapper(wrapper, func)


def save_project(project: model.Project) -> None:
    """Save project object to database."""
    # TODO: rollback if error happens
    try:
        session = db.session

        # Save to db
        # pylint: disable=no-member
        new_project = session.merge(project)
        session.flush()
        project.id = new_project.id
        session.commit()
        # pylint: enable=no-member
    except sqlalchemy.exc.IntegrityError as exc:
        raise exceptions.IntegrityException(str(exc)) from exc


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
