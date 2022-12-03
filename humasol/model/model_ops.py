"""Provides ModelOps interface.

All functions must be called from within an application context.
"""

# Python Libraries
import json
import os

# Local modules
from .. import config as cf
from .. import model
from ..repository import db

# TODO: remove pylint disable
# pylint: disable=unused-argument


def admin_exists() -> bool:
    """Check whether there is a user with admin rights registered."""


def archive_project(project_id: int) -> None:
    """Archive the project with provided project ID.

    Parameters
    __________
    project_id  -- Project identifier in the database
    """


def create_db_tables() -> None:
    """Create database tables for all the defined models."""
    db.create_all()


# Pylint doesn't seem to detect inner class
# pylint: disable=no-member
def create_project(parameters: model.Project.ProjectArgs) -> model.Project:
    """Create a project from the provided project parameters.

    Parameters
    __________
    parameters  -- Parameters for the new project. Provided as a dictionary
                    with keys referring to the attribute

    Returns
    _______
    Project object created with the provided parameters and without ID.
    """


# pylint: enable=no-member


# Pylint doesn't seem to detect inner class
# pylint: disable=no-member
def edit_project(
    project: model.Project, new_parameters: model.Project.ProjectArgs
) -> model.Project:
    """Update the provided project with the new parameters.

    Parameters
    __________
    project -- Existing project in its unmodified state
    new_parameters  -- Values to update from the original project. Provided
                        as a dictionary with keys referring to the attribute

    Returns
    _______
    Project in its updated state.
    """


# pylint: enable=no-member


def get_project(project_id: int) -> model.Project:
    """Retrieve project with provided ID from the database.

    Parameters
    __________
    project_id  -- Project identifier in the database
    """
    project = model.Project.query.get(project_id)

    with open(
        os.path.join(cf.PROJECT_FILES, project.data_file), encoding="utf-8"
    ) as data:
        project.load_from_file(json.load(data))

    return project


def get_projects() -> list[model.Project]:
    """Retrieve all projects from the database.

    Returns
    _______
    Unsorted list of all projects.
    """
    return model.Project.query.all()


def register_user(email: str, password: str, role: model.Role) -> model.User:
    """Create a new user and save it to the database.

    Parameters
    __________
    email    -- User's valid email. Used as a username and contact method
    password -- Password to log into the system
    role     -- Role of the user with respect to Humasol. Will dictate the
                user's rights

    Returns
    _______
    Newly created user object.
    """


def save_project(project: model.Project) -> None:
    """Save a new project to the database.

    By saving the project to the database, a new ID will be given to it.
    Therefore, it is important that the provided project has either no ID (the
    preferred method), or one that is known not to be in the database.
    """


def search(value: str) -> list[model.Project]:
    """Search the database for projects with attributes matching the value.

    Parameters
    __________
    value   -- Sequence to match project attributes on

    Returns
    _______
    Unsorted list of projects with attributes (partially) matching the
    provided value.
    """


def tables_exist() -> bool:
    """Check whether the database tables have been created."""
    return db.engine.execute(
        db.text(
            """
            SELECT EXISTS (
                SELECT FROM
                    pg_tables
                WHERE
                    schemaname = 'public' AND
                    tablename  = 'user'
            );
            """
        )
    ).first()[0]


# pylint: enable=unused-argument
