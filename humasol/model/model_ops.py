"""Provides ModelOps interface."""

from . import Project, Role, User

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


# Pylint doesn't seem to detect inner class
# pylint: disable=no-member
def create_project(parameters: Project.ProjectArgs) -> Project:
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
    project: Project, new_parameters: Project.ProjectArgs
) -> Project:
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


def get_project(project_id: int) -> Project:
    """Retrieve project with provided ID from the database.

    Parameters
    __________
    project_id  -- Project identifier in the database
    """


def get_projects() -> list[Project]:
    """Retrieve all projects from the database.

    Returns
    _______
    Unsorted list of all projects.
    """
    return []


def register_user(email: str, password: str, role: Role) -> User:
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


def save_project(project: Project) -> None:
    """Save a new project to the database.

    By saving the project to the database, a new ID will be given to it.
    Therefore, it is important that the provided project has either no ID (the
    preferred method), or one that is known not to be in the database.
    """


def search(value: str) -> list[Project]:
    """Search the database for projects with attributes matching the value.

    Parameters
    __________
    value   -- Sequence to match project attributes on

    Returns
    _______
    Unsorted list of projects with attributes (partially) matching the
    provided value.
    """


# pylint: enable=unused-argument
