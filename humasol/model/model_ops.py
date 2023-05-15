"""Provides ModelOps interface.

All functions must be called from within an application context.
"""
# Python Libraries
import typing as ty

import sqlalchemy

# Local modules
from humasol import exceptions, model
from humasol import repository as repo
from humasol.repository import db

# TODO: remove pylint disable
# pylint: disable=unused-argument


T = ty.TypeVar("T", bound=model.ProjectElement)


def _get_unique_attributes(
    obj: model.Model | ty.Iterable[model.Model],
) -> dict[str, ty.Any] | list[dict[str, ty.Any]]:
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


def _merge_on_uniqueness(
    new_objs: list[T], merge_identifier: ty.Callable[[T, T], None]
) -> list[str]:
    cls = type(new_objs[0])

    objs = [
        repo.get_object_by_attributes(cls, obj)  # type: ignore
        for obj in _get_unique_attributes(new_objs)
    ]

    problem_elements = list[str]()
    for i, (new, old) in enumerate(zip(new_objs, objs)):
        if len(old) == 1:
            merge_identifier(new, old[0])
        elif len(old) > 1:
            problem_elements.append(f"{type(new).__name__} {i + 1}")

    return problem_elements


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
# pylint: disable=no-member, too-many-branches
def create_project(parameters: dict[str, ty.Any]) -> model.Project:
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
        people = {}

        parameters["students"] = [
            model.person.construct_person(model.Student, params)
            for params in parameters["students"]
        ]
        people.update({stu.email: stu for stu in parameters["students"]})

        parameters["supervisors"] = [
            model.person.construct_person(model.Supervisor, params)
            for params in parameters["supervisors"]
        ]
        people.update({sup.email: sup for sup in parameters["supervisors"]})

        for params in parameters["partners"]:
            params["organization"]["logo"] = "logo.png"

        parameters["partners"] = [
            model.person.construct_person(model.Partner, params)
            for params in parameters["partners"]
        ]
        people.update({par.email: par for par in parameters["partners"]})

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
            # TODO: Remove this when the input is added to the form
            parameters["data_source"]["data_manager"] = "EnergyDataManager"
            parameters["data_source"]["report_manager"] = "EnergyReportManager"
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
            for t_idx, task in enumerate(parameters["tasks"]):
                if task.subscriber.email in people:
                    parameters["tasks"][t_idx].subscriber = people[
                        task.subscriber.email
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
            for s_idx, sub in enumerate(parameters["subscriptions"]):
                if sub.subscriber.email in people:
                    parameters["subscriptions"][s_idx].subscriber = people[
                        sub.subscriber.email
                    ]

        # Create project object
        project = model.ProjectFactory.get_project(category, parameters)
        if "components" in parameters:
            components = [
                model.ProjectFactory.get_project_component(comp)
                for comp in parameters["components"]
            ]
            for comp in components:
                project.add_component(comp)

    except KeyError as exc:
        # TODO: create proper exceptions structure
        raise exceptions.MissingArgumentException(
            f"Missing parameter: {str(exc)}"
        ) from exc

    except TypeError as exc:
        raise exceptions.ModelException(str(exc)) from exc

    return project


def delete_project(project: model.Project) -> None:
    """Delete the provided project from the database.

    Parameters
    __________
    project     -- Project to be deleted
    """
    # TODO: remove any additional objects that are no longer referenced
    repo.delete_project(project)


def edit_project(
    project: model.Project, new_parameters: model.Project.ProjectArgs
) -> None:
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
    people = {
        pers["email"]: pers
        for pers in (
            new_parameters["students"]
            + new_parameters["supervisors"]
            + new_parameters["partners"]
        )
    }
    jobs = list[dict[str, ty.Any]]()
    if "tasks" in new_parameters:
        jobs += new_tasks if (new_tasks := new_parameters["tasks"]) else []
    if "subscriptions" in new_parameters:
        jobs += (
            new_subs if (new_subs := new_parameters["subscriptions"]) else []
        )
    for job in jobs:
        if job["subscriber"]["email"] in people:
            job["subscriber"] = people[job["subscriber"]["email"]]

    try:
        project.update(new_parameters)
        repo.commit()
    except exceptions.RepositoryException as exc:
        raise exceptions.ModelException(exc) from exc


# pylint: enable=no-member, too-many-branches


def get_my_associated_projects(user: model.User) -> list[model.Project]:
    """Retrieve all projects to which the user is associated.

    A user is associated if they are listed under the people who collaborated.
    """
    return model.Project.query.filter(
        sqlalchemy.or_(
            model.Project.students.any(model.Student.email == user.email),
            model.Project.supervisors.any(
                model.Supervisor.email == user.email
            ),
            model.Project.partners.any(model.Partner.email == user.email),
        )
    ).all()


def get_my_projects(user: model.User) -> list[model.Project]:
    """Retrieve all projects created by the provided user.

    Parameters
    __________
    user    -- Creator of the projects to be retrieved
    """
    return repo.get_object_by_attributes(
        model.Project, {"creator_id": user.id}  # type: ignore
    )


def get_my_subscriptions(user: model.User) -> list[model.Project]:
    """Retrieve projects to which the user is subscribed."""
    return model.Project.query.filter(
        model.Project.id.in_(
            model.Project.query.with_entities(model.Project.id)
            .filter(
                model.Project.subscriptions.any(
                    model.Subscription.id.in_(
                        model.Subscription.query.with_entities(
                            model.Subscription.id
                        )
                        .join(model.Person)
                        .filter(model.Person.email == user.email)
                        .scalar_subquery()
                    )
                )
            )
            .scalar_subquery()
        )
    ).all()


def get_my_tasks(user: model.User) -> list[model.Project]:
    """Retrieve all projects for which the user has a task."""
    return model.Project.query.filter(
        model.Project.id.in_(
            model.Project.query.with_entities(model.Project.id)
            .filter(
                model.Project.tasks.any(
                    model.Task.id.in_(
                        model.Task.query.with_entities(model.Task.id)
                        .join(model.Person)
                        .filter(model.Person.email == user.email)
                        .scalar_subquery()
                    )
                )
            )
            .scalar_subquery()
        )
    ).all()


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


def get_users() -> list[model.User]:
    """Retrieve all users from the database.

    Returns
    _______
    List of users
    """
    return model.User.query.all()


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


def save_project(
    project: model.Project,
) -> tuple[ty.Literal[False], str] | tuple[ty.Literal[True], None]:
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

    if len(project_match) > 0:
        return False, "Some project attributes violate uniqueness constraint"

    # Go through lists (students, etc.)
    def merge_id(new, old) -> None:
        new.id = old.id

    problem_elements = (
        _merge_on_uniqueness(project.students, merge_id)
        + _merge_on_uniqueness(project.supervisors, merge_id)
        + _merge_on_uniqueness(project.partners, merge_id)
    )
    # contact_person = repo.get_object_by_attributes(
    #     model.Person, _get_unique_attributes(project.contact_person)
    # )

    if len(problem_elements):
        return (
            False,
            f"Elements {problem_elements} have attributes that "
            f"violate uniqueness constraints",
        )

    # TODO: unify existing objects with new ones
    repo.save_project(project)

    return True, None


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
    ...
