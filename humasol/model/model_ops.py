"""Provides ModelOps interface.

All functions must be called from within an application context.
"""

# Python Libraries
from typing import Any

# Local modules
from humasol import exceptions, model
from humasol import repository as repo
from humasol.repository import db

# TODO: remove pylint disable
# pylint: disable=unused-argument


def _get_unique_attributes(
    obj: model.Model | list[model.Model],
) -> dict[str, Any] | list[dict[str, Any]]:
    """Retrieve all attributes of the object with a uniqueness constraint."""
    if isinstance(obj, list):
        return [
            {
                attr: getattr(ob, attr)
                for attr, val in type(ob).__dict__.items()
                if hasattr(val, "unique") and getattr(val, "unique")
            }
            for ob in obj
        ]

    return {
        attr: getattr(obj, attr)
        for attr, val in type(obj).__dict__.items()
        if hasattr(val, "unique") and getattr(val, "unique")
    }


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
def create_project(parameters: dict[str, Any]) -> model.Project:
    """Create a project from the provided project parameters.

    Parameters
    __________
    parameters  -- Parameters for the new project. Provided as a dictionary
                    with keys referring to the attribute

    Returns
    _______
    Project object created with the provided parameters and without ID.
    """
    try:
        # Create sub-objects
        parameters["location"] = model.Location(
            model.Address(**parameters["location"]["address"]),
            model.Coordinates(**parameters["location"]["coordinates"]),
        )
        category = model.ProjectCategory.from_string(
            parameters.pop("category")
        )

        # Create people objects
        parameters["students"] = [
            model.person.construct_person(model.Student, params)
            for params in parameters["students"]
        ]

        parameters["supervisors"] = [
            model.person.construct_person(model.Supervisor, params)
            for params in parameters["supervisors"]
        ]

        for params in parameters["partners"]:
            params["organization"]["logo"] = "logo.png"

        parameters["partners"] = [
            model.person.construct_person(model.Partner, params)
            for params in parameters["partners"]
        ]

        # parameters["contact_person"] = model.person.construct_person(
        #     model.person.get_constructor_from_type(
        #         parameters["contact_person"].pop("type")
        #     ),
        #     parameters["contact_person"],
        # )
        parameters["contact_person"] = parameters["students"][0]

        parameters["sdgs"] = [
            model.SDG.from_str(sdg) for sdg in parameters["sdgs"]
        ]

        # Create follow-up objects
        if "data_source" in parameters:
            parameters["data_source"] = model.DataSource(
                **parameters["data_source"]
            )

        if "tasks" in parameters and parameters["tasks"] is not None:
            for params in parameters["tasks"]:
                for period in params["periods"]:
                    period["unit"] = model.Period.TimeUnit.get_unit(
                        period["unit"]
                    )

            parameters["tasks"] = [
                model.followup_work.construct_followup_work(model.Task, params)
                for params in parameters["tasks"]
            ]

        if (
            "subscriptions" in parameters
            and parameters["subscriptions"] is not None
        ):
            parameters["subscriptions"] = [
                model.followup_work.construct_followup_work(
                    model.Subscription, params
                )
                for params in parameters["subscriptions"]
            ]

        if "components" in parameters:
            parameters["components"] = [
                model.ProjectFactory.get_project_component(comp)
                for comp in parameters["components"]
            ]
        # Create project object
        project = model.ProjectFactory.get_project(category, parameters)

    except KeyError as exc:
        # TODO: create proper exceptions structure
        raise exceptions.MissingArgumentException(
            f"Missing parameter: {str(exc)}"
        ) from exc

    except TypeError as exc:
        raise exceptions.ModelException(str(exc)) from exc

    return project


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
    try:
        project = repo.get_object_by_id(
            model.Project, project_id  # type: ignore
        )
    except exceptions.ObjectNotFoundException as exc:
        raise exceptions.ModelException(str(exc)) from exc

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


def save_project(project: model.Project) -> bool:
    """Save a new project to the database.

    By saving the project to the database, a new ID will be given to it.
    Therefore, it is important that the provided project has either no ID (the
    preferred method), or one that is known not to be in the database.
    """
    # TODO: add checks for uniqueness
    # Get all attributes with a uniqueness constraint from the project
    project_unique = _get_unique_attributes(project)
    project_match = repo.get_object_by_attributes(
        model.Project, project_unique  # type: ignore
    )
    print(project_match)
    if len(project_match) > 0:
        return False

    # Go through lists (students, etc.)
    _get_unique_attributes(project.contact_person)
    _get_unique_attributes(project.students)
    _get_unique_attributes(project.supervisors)
    _get_unique_attributes(project.partners)
    _get_unique_attributes(project.tasks)
    _get_unique_attributes(project.subscriptions)

    # TODO: unify existing objects with new ones
    repo.save_project(project)

    return True


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
    return repo.table_exists("user")


# pylint: enable=unused-argument


if __name__ == "__main__":
    pass
