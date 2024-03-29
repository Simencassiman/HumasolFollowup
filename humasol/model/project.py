"""Project class and database relations.

Humasol projects are represented by the Project abstract base class. It
is subclassed by specific project categories which represent the main traits
of different types of projects. These classes are used to represent the
executed projects in the system and can be used to consult or update
interested parties.

Classes:
Project       -- Abstract base class for all Humasol projects
EnergyProject -- Class representing projects with a focus on an electrical
                    system
ProjectFactory -- Class providing static methods for project creation.
ProjectCategory -- Enum class providing the defined project categories and
                    matching classes.
"""

# Python Libraries
from __future__ import annotations

import copy
import datetime
import re
import typing as ty
from abc import abstractmethod
from enum import Enum
from functools import reduce

from sqlalchemy import orm
from sqlalchemy.orm import declared_attr

# Local modules
from humasol import exceptions, model
from humasol.model import utils
from humasol.model.snapshot import Snapshot
from humasol.repository import db

ExtraDatum = model.project_elements.ExtraDatum


# Relationship tables between database entities
project_students = db.Table(
    "project_student",
    db.Column(
        "project_id",
        db.Integer,
        db.ForeignKey("project.id", ondelete="CASCADE"),
    ),
    db.Column("student_id", db.Integer, db.ForeignKey("person.id")),
)
project_supers = db.Table(
    "project_super",
    db.Column(
        "project_id",
        db.Integer,
        db.ForeignKey("project.id", ondelete="CASCADE"),
    ),
    db.Column("supervisor_id", db.Integer, db.ForeignKey("person.id")),
)
project_partners = db.Table(
    "project_partners",
    db.Column(
        "project_id",
        db.Integer,
        db.ForeignKey("project.id", ondelete="CASCADE"),
    ),
    db.Column("partner_id", db.Integer, db.ForeignKey("person.id")),
)
project_contact = db.Table(
    "project_contact",
    db.Column(
        "project_id",
        db.Integer,
        db.ForeignKey("project.id", ondelete="CASCADE"),
    ),
    db.Column("contact_id", db.Integer, db.ForeignKey("person.id")),
)
project_sdg_table = db.Table(
    "project_sdg",
    db.Column(
        "project_id",
        db.Integer,
        db.ForeignKey("project.id", ondelete="CASCADE"),
    ),
    db.Column(
        "sdg",
        db.Enum(model.project_elements.SDG),
        db.ForeignKey("sdg_db.sdg"),
    ),
)


# --------------------------
# ----- Project models -----
# --------------------------

# These models are also used to create the database entities
# through the inheritance of db.Model
# pylint: disable=too-many-instance-attributes, too-many-public-methods
class Project(model.BaseModel):
    """Abstract base class for all Humasol project.

    Projects executed by Humasol teams can be represented by subclasses of
    this base class. It represents the common features of all projects and
    therefore contains information that should be available for all projects.
    Subclasses should declare common aspects that should be met by all
    projects in that category.

    Attributes
    __________
    id          -- Unique identifier for a project
    name        -- Title of the project
    code        -- Unique letter code
    date        -- Implementation or completion date
    description -- Description of the project
    category    -- Field of application of the project (e.g., energy, water)
    type        -- Subclass type used by the database ORM
    location    -- Project location
    work_folder -- URL to the folder containing all the preparation work
    dashboard   -- URL to the project folder dashboard (if available)
    save_data   -- Indicates whether retrieved project folder should be saved
                    to the Humasol drive for future teams to use
    project_data -- URL to the Humasol drive folder where the retrieved folder
                    are stored
    extra_data  -- Dictionary with additional settings for the project manager
    sdgs        -- SDG goals that the project aims to tackle
    data_source -- Address and credentials to access the folder logger
    students    -- Students that worked on the project
    supervisors -- Humasol members that guided the student team
    partners    -- Partners external to Humasol that contributed to the project
    contact_person  -- Person to contact in case there are questions about the
                        project
    subscriptions   -- List of subscription objects with people to update
    tasks       -- List of task objects with people to be reminded
    data_file   -- URI to the file containing folder of this project object
                    (data is partially stored in a database and partially
                    in a file)
    project_components -- Elements relevant to the description of a project.
                            Can be used by subclasses to define important
                            components.
    """

    MIN_SDGS = 1
    MIN_STUDENTS = 3
    MAX_STUDENTS = 4

    T = ty.TypeVar("T")
    V = ty.TypeVar("V")

    # Definitions for the database tables #
    __tablename__ = "project"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, index=True, nullable=False)
    creator = db.relationship("User", lazy=True)
    creator_id = db.Column(
        db.Integer, db.ForeignKey(model.User.id)  # type: ignore
    )
    code = db.Column(db.String, index=True, unique=True, nullable=False)
    creation_date = db.Column(db.DateTime, index=True, nullable=False)
    implementation_date = db.Column(db.DateTime, index=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String, index=True, nullable=False)
    type = db.Column(db.String(50))  # Used for internal mapping by SQLAlchemy
    location = db.relationship(
        "Location", lazy=True, uselist=False, cascade="all, delete-orphan"
    )
    work_folder = db.Column(db.String, unique=True, nullable=False)
    dashboard = db.Column(db.String)
    save_data = db.Column(db.Boolean, nullable=False)
    project_data = db.Column(db.String)
    extra_data_db = db.relationship("ExtraDatum", cascade="all, delete-orphan")
    sdgs_db = db.relationship(
        "SdgDB",
        secondary=project_sdg_table,
        lazy="subquery",
        backref=db.backref("projects", lazy=True),
    )
    data_source = db.relationship(
        "DataSource", lazy=True, cascade="all", uselist=False
    )
    students = db.relationship(
        "Student", secondary=project_students, lazy="subquery"
    )
    supervisors = db.relationship(
        "Supervisor", secondary=project_supers, lazy="subquery"
    )
    partners = db.relationship(
        "Partner", secondary=project_partners, lazy="subquery"
    )
    contact_person = db.relationship(
        "Person", secondary=project_contact, lazy="subquery", uselist=False
    )
    subscriptions = db.relationship(
        "Subscription", lazy=False, cascade="all, delete-orphan"
    )
    tasks = db.relationship("Task", lazy=False, cascade="all, delete-orphan")
    data_file = db.Column(db.String, unique=True, nullable=False)

    @declared_attr
    def project_components(self) -> orm.RelationshipProperty:
        """Provide database relation to subscriber."""
        return db.relationship(
            model.ProjectComponent, lazy=True, cascade="all, delete-orphan"
        )

    __mapper_args__ = {
        "polymorphic_on": type,
        "polymorphic_identity": "project",
    }

    # End of database definitions #

    class ProjectArgs(ty.TypedDict, total=False):
        """Class used for typing project arguments."""

        name: str
        implementation_date: datetime.date
        description: str
        location: dict[str, dict[str, str] | dict[str, int | float]]
        work_folder: str
        students: list[dict[str, ty.Any]]
        supervisors: list[dict[str, ty.Any]]
        contact_person: dict[str, ty.Any]
        partners: list[dict[str, ty.Any]]
        code: ty.Optional[str]
        sdgs: list[str]
        tasks: ty.Optional[list[dict[str, ty.Any]]]
        data_source: ty.Optional[dict[str, str]]
        dashboard: ty.Optional[str]
        save_data: bool
        project_data: ty.Optional[str]
        extra_data: ty.Optional[dict[str, ty.Any]]
        subscriptions: ty.Optional[list[dict[str, ty.Any]]]
        components: list[model.ProjectComponent]
        kwargs: dict[str, ty.Any]

    # pylint: disable=too-many-arguments, too-many-locals, too-many-branches
    # pylint: disable=too-many-statements
    @abstractmethod
    def __init__(
        self,
        *,  # Force usage of keywords
        name: str,
        creator: model.User,
        creation_date: datetime.date,
        implementation_date: datetime.date,
        description: str,
        category: ProjectCategory,
        location: model.project_elements.Location,
        work_folder: str,
        students: list[model.person.Student],
        supervisors: list[model.person.Supervisor],
        contact_person: model.person.Person,
        partners: list[model.person.Partner],
        sdgs: list[model.project_elements.SDG],
        tasks: ty.Optional[list[model.followup_work.Task]] = None,
        data_source: ty.Optional[model.project_elements.DataSource] = None,
        dashboard: ty.Optional[str] = None,
        save_data: bool = False,
        project_data: ty.Optional[str] = None,
        subscriptions: ty.Optional[
            list[model.followup_work.Subscription]
        ] = None,
        extra_data: ty.Optional[dict[str, ty.Any]] = None,
        **kwargs,
    ):
        """Instantiate a project object.

        Parameters
        __________
        name        -- Title of the project
        implementation_date     -- Implementation or completion date
        description -- Description of the project
        category    -- Field of application of the project
                        (e.g., energy, water)
        location    -- Project location
        work_folder -- URL to the folder containing all the preparation work
        students    -- Students that worked on the project
        supervisors -- Humasol members that guided the student team
        contact_person  -- Person to contact in case there are questions about
                            the project
        partners    -- Partners external to Humasol that contributed to
                        the project
        code        -- Unique letter code
        sdgs        -- SDG goals that the project aims to tackle
        tasks       -- List of task objects with people to be reminded
        data_source -- Address and credentials to access the folder logger
        dashboard   -- URL to the project folder dashboard (if available)
        save_data   -- Indicates whether retrieved project folder should be
                        saved to the Humasol drive for future teams to use
        project_data -- URL to the Humasol drive folder where the retrieved
                        folder are stored
        extra_data  -- Dictionary with additional settings for the project
                        manager
        subscriptions   -- List of subscription objects with people to update
        """
        # Parameter checks
        if not Project.is_legal_name(name):
            raise exceptions.IllegalArgumentException(
                "Parameter 'name' should be a non-empty string with "
                "only letters"
            )

        if not Project.is_legal_creator(creator):
            raise exceptions.IllegalArgumentException(
                "Parameter 'creator' should be of type User"
            )

        if not Project.is_legal_creation_date(creation_date):
            raise exceptions.IllegalArgumentException(
                "Parameter 'creation_date' should be of type datetime.date "
                "and can only be as recent as the current day"
            )

        if not Project.is_legal_implementation_date(implementation_date):
            raise exceptions.IllegalArgumentException(
                "Parameter 'implementation_date' has an illegal value. "
                "Only projects up to this year can be implemented"
            )

        if not Project.is_legal_description(description):
            raise exceptions.IllegalArgumentException(
                "Parameter 'description' has an illegal value. "
                "Should contain at least 1 letter"
            )

        if not Project.is_legal_location(location):
            raise exceptions.IllegalArgumentException(
                "Parameter 'location' should not be None and of type Location"
            )

        if not Project.is_legal_work_folder(work_folder):
            raise exceptions.IllegalArgumentException(
                "Parameter 'work_folder' should be a non-empty string"
            )

        if not Project.are_legal_students(students):
            raise exceptions.IllegalArgumentException(
                "Parameter 'students' should be a list containing 3 or 4 "
                "unique students"
            )

        if not Project.are_legal_supervisors(supervisors):
            raise exceptions.IllegalArgumentException(
                "Parameter 'supervisors' should be a list containing unique "
                "supervisors"
            )

        if not Project.is_legal_contact_person(contact_person):
            raise exceptions.IllegalArgumentException(
                "Parameter 'contact_person' should not be None and of "
                "type Person"
            )

        if not Project.are_legal_partners(partners):
            raise exceptions.IllegalArgumentException(
                "Parameter 'partners' should be a list containing unique "
                "partners"
            )

        if not Project.are_legal_sdgs(sdgs):
            raise exceptions.IllegalArgumentException(
                "Parameter 'sdgs' should be a non-empty list containing "
                "unique SDGs"
            )

        if not Project.are_legal_tasks(tasks):
            raise exceptions.IllegalArgumentException(
                "Parameter 'tasks' should be a list containing unique tasks"
            )

        if not Project.is_legal_data_source(data_source):
            raise exceptions.IllegalArgumentException(
                "Parameter 'data_source' should be None or of "
                "type DataSource"
            )

        if not Project.is_legal_dashboard(dashboard):
            raise exceptions.IllegalArgumentException(
                "Parameter 'dashboard' should be of type str or None"
            )

        if not Project.is_legal_save_data_flag(save_data):
            raise exceptions.IllegalArgumentException(
                "Parameter 'save_data' should be of type bool"
            )

        if not Project.is_legal_data_folder(project_data):
            raise exceptions.IllegalArgumentException(
                "Parameter 'project_data' should be of type str or None"
            )

        if not Project.are_legal_subscriptions(subscriptions):
            raise exceptions.IllegalArgumentException(
                "Parameter 'subscriptions' should be None or a list "
                "containing unique Subscriptions"
            )

        if not Project.are_legal_extra_data(extra_data):
            raise exceptions.IllegalArgumentException(
                "Parameter 'extra_data' should be a dictionary mapping "
                "strings to strings"
            )

        if data_source is None:
            pass
        else:
            pass

        # All checks passed, instantiate object

        super().__init__()

        self.name = name
        self.creator = creator
        self.creation_date = creation_date
        self.implementation_date = implementation_date
        self.description = description
        self.category = category.name
        self.location = location
        self.work_folder = work_folder
        self.students = students
        self.supervisors = supervisors
        self.partners = partners if partners is not None else []
        self.contact_person = contact_person

        self.extra_data = dict[str, str | list[str]]()
        self.extra_data_db = list[ExtraDatum]()
        self.set_extra_data(extra_data if extra_data is not None else {})

        self.sdgs = list[model.SDG]()
        self.sdgs_db = list[model.project_elements.SdgDB]()
        self.set_sdgs(sdgs)

        self.data_source = data_source
        self.dashboard = dashboard
        self.save_data = save_data
        self.project_data = project_data
        self.subscriptions = subscriptions if subscriptions is not None else []
        self.tasks = tasks if tasks is not None else []

        self.project_components = list[model.ProjectComponent]()

        if self.code is None:
            self._create_code()

        self.data_file = f"{self.code}.json"
        # TODO: generate project folder file

    # pylint: enable=too-many-statements, too-many-branches, too-many-locals
    # pylint: enable=too-many-arguments

    # Magic methods #
    def __repr__(self) -> str:
        """Provide a string representation for this instance."""
        return (
            f"name={self.name}, "
            f"date={self.implementation_date}, "
            f"description={self.description}, "
            f"category={self.category}, "
            f"location={repr(self.location)}, "
            f"work_folder={self.work_folder}, "
            f"students={repr([repr(s) for s in self.students])}, "
            f"supervisors={repr([repr(s) for s in self.supervisors])}, "
            f"partners={repr([repr(p) for p in self.partners])}, "
            f"code={self.code}, "
            f"sdgs={repr([repr(sdg) for sdg in self.sdgs])}, "
            f"tasks={repr([repr(t) for t in self.tasks])}, "
            f"data_source={repr(self.data_source)}, "
            f"dashboard={self.dashboard}, "
            f"save_data={self.save_data}, "
            f"project_data={self.project_data}, "
            f"extra_data={repr(self.extra_data)}, "
            f"subscriptions={repr([repr(s) for s in self.subscriptions])}"
        )

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

    # Static methods #
    # Validators #
    @staticmethod
    def are_legal_extra_data(data: ty.Optional[dict[str, str]]) -> bool:
        """Check whether the provided extra folder has a legal format."""
        return (
            data is None
            or isinstance(data, dict)
            and all(  # For all items:
                map(
                    lambda t: isinstance(t[0], str)  # Key is a string
                    and (
                        isinstance(t[1], str)  # Value is a string
                        or (  # Or list of strings
                            isinstance(t[1], list)
                            and all(map(lambda e: isinstance(e, str), t[1]))
                        )
                    ),
                    data.items(),
                )
            )
        )

    @staticmethod
    def are_legal_partners(partners: list[model.person.Partner]) -> bool:
        """Check whether the provided list is a legal partners list."""
        return (
            isinstance(partners, (list, tuple))
            and len(partners) > 0
            and all(map(Project.is_legal_partner, partners))
            and len(partners) == len(set(partners))
        )

    @staticmethod
    def are_legal_project_components(
        components: list[model.ProjectComponent],
    ) -> bool:
        """Check whether the provided list is a legal components list."""
        return isinstance(components, (list, tuple)) and all(
            map(Project.is_legal_project_component, components)
        )

    @staticmethod
    def are_legal_sdgs(sdgs: list[model.project_elements.SDG]) -> bool:
        """Check whether the provided SDG list is legal."""
        return (
            isinstance(sdgs, (list, tuple))
            and len(sdgs) >= Project.MIN_SDGS
            and all(map(Project.is_legal_sdg, sdgs))
        )

    @staticmethod
    def are_legal_students(students: list[model.person.Student]) -> bool:
        """Check whether the provided list is a legal student list."""
        return (
            isinstance(students, (list, tuple))
            and (Project.MIN_STUDENTS <= len(students) <= Project.MAX_STUDENTS)
            and all(map(Project.is_legal_student, students))
            and len(students) == len(set(students))
        )

    @staticmethod
    def are_legal_subscriptions(
        subscriptions: ty.Optional[list[model.followup_work.Subscription]],
    ) -> bool:
        """Check whether the provided list is a legal subscriptions list."""
        return subscriptions is None or (
            isinstance(subscriptions, (list, tuple))
            and all(map(Project.is_legal_subscription, subscriptions))
            and len(subscriptions) == len(set(subscriptions))
        )

    @staticmethod
    def are_legal_supervisors(supers: list[model.person.Supervisor]) -> bool:
        """Check whether the provided list is a legal supervisor list."""
        return (
            isinstance(supers, (list, tuple))
            and all(map(Project.is_legal_supervisor, supers))
            and len(supers) == len(set(supers))
        )

    @staticmethod
    def are_legal_tasks(
        tasks: ty.Optional[list[model.followup_work.Task]],
    ) -> bool:
        """Check whether the provided list is a legal tasks list."""
        return tasks is None or (
            isinstance(tasks, list)
            and all(map(Project.is_legal_task, tasks))
            and len(tasks) == len(set(tasks))
        )

    @staticmethod
    def is_legal_contact_person(contact: model.person.Person) -> bool:
        """Check whether the provided person is a legal person."""
        return isinstance(contact, model.person.Person)

    @staticmethod
    def is_legal_creation_date(date: datetime.date) -> bool:
        """Check whether the provided date is a legal creation date."""
        return (
            isinstance(date, datetime.date) and date <= datetime.date.today()
        )

    @staticmethod
    def is_legal_creator(creator: model.User) -> bool:
        """Check whether the provided creator is a legal User."""
        return isinstance(creator, model.User)

    @staticmethod
    def is_legal_dashboard(dashboard: ty.Optional[str]) -> bool:
        """Check whether the provided dashboard is legal."""
        return dashboard is None or (
            isinstance(dashboard, str) and len(dashboard) > 0
        )

    @staticmethod
    def is_legal_data_folder(folder: ty.Optional[str]) -> bool:
        """Check whether the provided data folder is a legal URL."""
        return folder is None or (isinstance(folder, str) and len(folder) > 0)

    @staticmethod
    def is_legal_data_source(
        source: ty.Optional[model.project_elements.DataSource],
    ) -> bool:
        """Check whether the provided source is a legal project data source."""
        return source is None or isinstance(
            source, model.project_elements.DataSource
        )

    @staticmethod
    def is_legal_description(description: str) -> bool:
        """Check whether the provided description has no illegal characters."""
        # TODO: Correct regex
        return (
            isinstance(description, str)
            and re.match(r"[A-Z]+", description.upper()) is not None
        )

    @staticmethod
    def is_legal_implementation_date(date: datetime.date) -> bool:
        """Check whether the provided date is legal as implementation date."""
        return (
            isinstance(date, datetime.date)
            and date.year <= datetime.date.today().year
        )

    @staticmethod
    def is_legal_location(location: model.project_elements.Location) -> bool:
        """Check whether the provided location is a legal location."""
        return isinstance(location, model.project_elements.Location)

    @staticmethod
    def is_legal_name(name: str) -> bool:
        """Check whether the provided name contains legal characters."""
        # TODO: Correct regex
        return (
            isinstance(name, str)
            and re.match(r"[A-Z]+", name.upper()) is not None
        )

    @staticmethod
    def is_legal_partner(partner: model.person.Partner) -> bool:
        """Check whether the provided partner is legal for a project."""
        return isinstance(partner, model.person.Partner)

    @staticmethod
    def is_legal_project_component(
        component: model.project_components.ProjectComponent,
    ) -> bool:
        """Check if the provided component is a legal project component."""
        return isinstance(component, model.project_components.ProjectComponent)

    @staticmethod
    def is_legal_save_data_flag(flag: bool) -> bool:
        """Check whether the provided flag is a legal flag."""
        return isinstance(flag, bool)

    @staticmethod
    def is_legal_sdg(sdg: model.project_elements.SDG) -> bool:
        """Check whether the provided SDG is legal."""
        return isinstance(sdg, model.project_elements.SDG)

    @staticmethod
    def is_legal_student(student: model.person.Student) -> bool:
        """Check whether the provided student is legal for a project."""
        return isinstance(student, model.person.Student)

    @staticmethod
    def is_legal_subscription(sub: model.followup_work.Subscription) -> bool:
        """Check whether the provided subscription is a legal subscription."""
        return isinstance(sub, model.followup_work.Subscription)

    @staticmethod
    def is_legal_supervisor(supervisor: model.person.Supervisor) -> bool:
        """Check whether the provided supervisor is legal for a project."""
        return isinstance(supervisor, model.person.Supervisor)

    @staticmethod
    def is_legal_task(task: ty.Any) -> bool:
        """Check whether the provided task is legal."""
        return isinstance(task, model.followup_work.Task)

    @staticmethod
    def is_legal_work_folder(folder: str) -> bool:
        """Check whether the provided folder is a legal URL."""
        # TODO: strengthen check
        return isinstance(folder, str) and len(folder) > 0

    # Private methods #

    def _create_code(self) -> None:
        """Create a short letter code based on the project name."""
        name_pieces = (
            re.sub(r'[,.$%&@#"]', "", self.name)
            .replace("-", " ")
            .split(sep=" ")
        )

        self.code = reduce(
            lambda x, y: x + y, map(lambda s: s[0], name_pieces)
        )

    def _filter_project_components(
        self, component_type: ty.Type[T]
    ) -> list[T]:
        """Retrieve Project components of the specified type."""
        return list(
            filter(
                lambda c: isinstance(c, component_type),  # type: ignore
                self.project_components,
            )
        )

    # pylint: disable=too-many-branches
    def _update_general(self, params: ProjectArgs) -> None:
        """Update the general attributes of this project.

        Update the attributes of this object that refer to general aspects of
        a project. These attributes are applicable to all projects.

        Uses a dictionary instead of individual parameters to distinguish
        between a value that is None and a value that is not present to update
        (without assigning arbitrary 'not-present' values to parameters).
        """
        # Tried to remove branches with loops over variables,
        # but TypedDict requires string literals as keys...

        if "name" in params:
            self.name = params["name"]

        if "implementation_date" in params:
            self.implementation_date = params["implementation_date"]

        if "description" in params:
            self.description = params["description"]

        if "work_folder" in params:
            self.work_folder = params["work_folder"]

        if "sdgs" in params:
            self.set_sdgs([model.SDG.from_str(s) for s in params["sdgs"]])

        if "extra_data" in params and params["extra_data"]:
            self.set_extra_data(params["extra_data"])

        if "location" in params:
            self.location.update(params["location"])

        if "contact_person" in params:
            self.contact_person.update(params["contact_person"])

        def merge_person_list(old_list, new_list, const):
            """Merge list of objects and dictionaries."""
            return utils.merge_update_list(
                old_list,
                new_list,
                [o["email"] for o in new_list],
                lambda p: p.email,
                lambda p, d: p.update(d),
                lambda d: const(**d),
            )

        if "students" in params:
            self.students = merge_person_list(
                self.students, params["students"], model.Student
            )

        if "supervisors" in params:
            self.supervisors = merge_person_list(
                self.supervisors, params["supervisors"], model.Supervisor
            )

        if "partners" in params:
            self.partners = merge_person_list(
                self.partners, params["partners"], model.Partner
            )

    def _update_followup(self, params: ProjectArgs) -> None:
        """Update the follow-up attributes of this project."""
        construct_fw = model.followup_work.construct_followup_work

        if "tasks" in params:
            if new_tasks := params["tasks"]:
                self.tasks = model.utils.merge_update_list(
                    self.tasks,
                    new_tasks,
                    list(map(lambda d: d["name"], new_tasks)),
                    lambda ta: ta.name,
                    lambda ta, dic: ta.update(dic),
                    lambda dic: construct_fw(model.followup_work.Task, dic),
                )
            else:
                self.set_tasks([])

        if "data_source" in params:
            if params["data_source"] is None:
                self.data_source = None
                self.set_subscriptions([])
                self.dashboard = None
                self.save_data = False
            else:
                if self.data_source is not None:
                    self.data_source.update(params["data_source"])
                else:
                    self.set_data_source(
                        self.build_data_source(params["data_source"])
                    )

        if self.data_source is not None:
            if "subscriptions" in params:
                if new_subs := params["subscriptions"]:
                    self.subscriptions = model.utils.merge_update_list(
                        self.subscriptions,
                        new_subs,
                        list(
                            map(
                                lambda dic: dic["subscriber"]["name"],
                                new_subs,
                            )
                        ),
                        lambda sub: sub.subscriber.name,
                        lambda sub, dic: sub.update(**dic),
                        lambda dic: construct_fw(
                            model.followup_work.Subscription, dic
                        ),
                    )
                else:
                    self.subscriptions = list[model.Subscription]()
            if "dashboard" in params:
                self.dashboard = params["dashboard"]
            if "save_data" in params:
                self.set_save_data(params["save_data"])

    # pylint: enable=too-many-branches

    # Public methods #
    def add_component(
        self, component: model.project_components.ProjectComponent
    ) -> None:
        """Add a project component to this project's components list."""
        if not self.is_legal_project_component(component):
            raise TypeError(
                "Argument 'component' should not be None and of type "
                "ProjectComponent"
            )

        self.project_components.append(component)

    def get_credentials(self) -> dict[str, ty.Any]:
        """Get the folder source credentials.

        Return a dictionary as provided by DataSource.get_credential,
        or and empty dictionary if not source is available.
        """
        return self.data_source.get_credentials() if self.data_source else {}

    @orm.reconstructor  # Function is called by the ORM on database load
    def init_on_load(self) -> None:
        """Prepare instance when it is loaded from the database."""
        self.sdgs = [s.sdg for s in self.sdgs_db]

        extra_data = dict[str, str | list[str]]()
        for ext_d in self.extra_data_db:
            if ext_d.key in extra_data:
                if isinstance(extra_data[ext_d.key], list):
                    extra_data[ext_d.key].append(ext_d.value)  # type: ignore
                else:
                    extra_data[ext_d.key] = [
                        extra_data[ext_d.key],  # type: ignore
                        ext_d.value,
                    ]
            else:
                extra_data[ext_d.key] = ext_d.value
        self.extra_data = extra_data

    def set_sdgs(self, sdgs: list[model.project_elements.SDG]) -> None:
        """Set the list of SDGs for this project."""
        self.sdgs = sdgs if sdgs else []
        self.sdgs_db = [model.project_elements.SdgDB(sdg) for sdg in self.sdgs]

    def set_extra_data(self, data: dict[str, str | list[str]]) -> None:
        """Set the extra folder for this project.

        Extra data can be used to configure project managers.
        """
        self.extra_data = copy.deepcopy(data)

        # Merge with existing data (modify database as little as possible)
        extra_data_db: dict[str, ExtraDatum | list[ExtraDatum]] = {}
        for ext_d in self.extra_data_db:
            if ext_d.key in extra_data_db:
                if isinstance(extra_data_db[ext_d.key], list):
                    extra_data_db[ext_d.key].append(ext_d)
                else:
                    extra_data_db[ext_d.key] = [
                        extra_data_db[ext_d.key],  # type: ignore
                        ext_d,
                    ]
            else:
                extra_data_db[ext_d.key] = ext_d

        new_extra_data_db = []

        def merge_lists(
            dkey: str, dval: list[str], db_val: list[ExtraDatum]
        ) -> None:
            """Merge new and old lists of extra data under the same key.

            Merge the new list of extra data with key 'dkey' and old list of db
            wrappers with key 'dkey'.
            Reuses as many rapper objects as possible by just modifying their
            value.
            """
            looper = iter(db_val)  # Create iterator to burn used elements
            missed = []  # Container for burnt but unused elements

            # Loop through old wrappers
            for item in looper:
                if item.value in dval:
                    # Same value in old and new lists -> just keep
                    dval.remove(item.value)
                    new_extra_data_db.append(item)
                else:
                    # Old value not in the new list -> hold to reuse wrapper
                    missed.append(item)
                if len(dval) == 0:
                    break
            else:
                # Only executes if there are still new values that haven't
                # been processed

                # Join existing but unused ExtraData wrapper objects
                remainder = list(looper) + missed

                # Loop through remaining new elements in list
                for elem in dval:
                    if len(remainder) > 0:
                        # There are still unused wrapper objects -> use them
                        new_el = remainder.pop(0)
                        new_el.value = elem
                    else:
                        # Nothing left to reuse -> create new one
                        new_el = ExtraDatum(dkey, elem)

                    # Add to the new list
                    new_extra_data_db.append(new_el)

        def merge_list_to_item(
            dkey: str, dval: list[str], db_val: ExtraDatum
        ) -> None:
            """Merge a new extra data list value to an old wrapper.

            Reuses the old wrapper if its value is in the new list or by
            replacing its value with the first one in the list.
            """
            if db_val.value in dval:
                # Old value is in the list -> just keep
                dval.remove(db_val.value)
            else:
                # Old value is not present anymore -> replace with
                # first value in the list
                db_val.value = dval.pop(0)
                # Add processed element to the new list
            new_extra_data_db.append(db_val)

            # Process all remaining new elements
            for elem in dval:
                new_extra_data_db.append(ExtraDatum(dkey, elem))

        for key, value in data.items():
            if key in extra_data_db:
                # Merge with existing
                match (value, extra_data_db[key]):
                    case (list(val), list(val_db)):
                        if len(val) == 0:
                            continue

                        merge_lists(key, val, val_db)

                    case (list(val), ExtraDatum(val_db)):
                        if len(val) == 0:
                            continue

                        merge_list_to_item(key, val, val_db)

                    case (str(val), list(val_db)):
                        val_db[0].value = val
                        new_extra_data_db.append(val_db[0])
                    case (str(val), ExtraDatum(val_db)):
                        val_db.value = val
                        new_extra_data_db.append(val_db)
            else:
                # Create new one, this key doesn't exist yet
                if isinstance(value, list):
                    for elem in value:
                        new_extra_data_db.append(ExtraDatum(key, elem))
                else:
                    new_extra_data_db.append(ExtraDatum(key, value))

        self.extra_data_db = new_extra_data_db

    @Snapshot.protect
    def update(self, params: ProjectArgs) -> Project:
        """Update this instance with the provided new parameters.

        Valid parameters are those defined in ProjectArgs.
        """
        self._update_general(params)
        self._update_followup(params)

        return self


# pylint: enable=too-many-instance-attributes, too-many-public-methods


class AgricultureProject(Project):
    """Class representing projects developing an agricultural system."""

    # Definitions for the database tables #
    __mapper_args__ = {"polymorphic_identity": "AGRICULTURE"}

    # End database definitions #

    def __init__(self, **kwargs) -> None:
        """Init project object."""
        super().__init__(category=ProjectCategory.AGRICULTURE, **kwargs)


class ElectronicsDevelopmentProject(Project):
    """Class representing projects developing electronics."""

    # Definitions for the database tables #
    __mapper_args__ = {"polymorphic_identity": "ELECTRONICS_DEVELOPMENT"}

    # End database definitions #

    def __init__(self, **kwargs) -> None:
        """Init project object."""
        super().__init__(
            category=ProjectCategory.ELECTRONICS_DEVELOPMENT, **kwargs
        )


class EnergyProject(Project):
    """Class representing projects installing an energy system."""

    # Definitions for the database tables #
    power = db.Column(db.Float)

    project_components = db.relationship(
        "EnergyProjectComponent", cascade="all, delete-orphan"
    )

    __mapper_args__ = {"polymorphic_identity": "ENERGY"}

    # End database definitions #

    class EnergyProjectArgs(Project.ProjectArgs, total=False):
        """Class used for EnergyProject update parameters."""

        power: int | float

    def __init__(
        self,
        *,
        power: float,
        **kwargs,
    ):
        """Instantiate object of this class.

        Parameters
        __________
        power       -- Power rating of the system
        kwargs      -- Parameters for superclasses
        """
        # Check arguments
        if not EnergyProject.is_legal_power(power):
            raise exceptions.IllegalArgumentException(
                "Parameter 'power' should be a non-negative float or integer"
            )

        super().__init__(category=ProjectCategory.ENERGY, **kwargs)

        self.power = power

    def __repr__(self) -> str:
        """Provide a string representation for this instance."""
        return (
            f"EnergyProject("
            f"{super().__repr__()}, "
            f"power={self.power}"
            f")"
        )

    @staticmethod
    def is_legal_power(power: float) -> bool:
        """Check whether the provided power is a legal power setting."""
        return isinstance(power, (float, int)) and power >= 0

    @staticmethod
    def is_legal_project_component(
        component: model.EnergyProjectComponent,
    ) -> bool:
        """Check if the provided component is a legal project component."""
        return isinstance(component, model.EnergyProjectComponent)

    # A more specific data class is ok in this case, doesn't violate LSP
    # since it has no behavior
    @Snapshot.protect
    def update(  # type: ignore[override]
        self, params: EnergyProjectArgs
    ) -> EnergyProject:
        """Update this instance with the provided new parameters."""
        super().update(params)

        if "power" in params:
            self.power = params["power"]

        if "components" in params:
            # for component in params["components"]:
            #     # utils.merge_update_list()
            #     for c, comp in self.project_components:
            #         pass
            #     else:
            #         pass
            pass

        return self


class WaterProject(Project):
    """Class representing projects installing a water system."""

    # Definitions for the database tables #
    __mapper_args__ = {"polymorphic_identity": "WATER"}

    # End database definitions #

    def __init__(self, **kwargs) -> None:
        """Init project object."""
        super().__init__(category=ProjectCategory.WATER, **kwargs)


class WasteManagementProject(Project):
    """Class representing projects developing a waste management solution."""

    # Definitions for the database tables #
    __mapper_args__ = {"polymorphic_identity": "WASTE_MANAGEMENT"}

    # End database definitions #

    def __init__(self, **kwargs) -> None:
        """Init project object."""
        super().__init__(category=ProjectCategory.WASTE_MANAGEMENT, **kwargs)


# -----------------------------
# ----- Project factories -----
# -----------------------------


class ProjectFactory:
    """Factory class used for constructing energy projects."""

    project_components: dict[str, ty.Callable] = {
        model.project_components.Generator.LABEL: (
            model.project_components.Generator
        ),
        model.project_components.Grid.LABEL: model.project_components.Grid,
        model.project_components.PV.LABEL: model.project_components.PV,
        model.project_components.Battery.LABEL: (
            model.project_components.Battery.from_form
        ),
        model.project_components.ConsumptionComponent.LABEL: (
            model.project_components.ConsumptionComponent
        ),
    }

    @staticmethod
    def get_project(
        category: ProjectCategory, params: dict[str, ty.Any]
    ) -> Project:
        """Construct project with the provided parameters."""
        project_class = category.class_name
        return project_class(**params)

    @staticmethod
    def get_project_component(
        params: dict[str, ty.Any]
    ) -> model.project_components.ProjectComponent:
        """Construct the project component with the provided parameters."""
        # TODO: Write factory function
        if "type" not in params:
            raise exceptions.MissingArgumentException(
                "Component parameters must contain an entry for 'type'"
            )

        try:
            return ProjectFactory.project_components[params.pop("type")](
                **params
            )
        except KeyError as exc:
            raise exceptions.IllegalArgumentException(
                f"Unknown project component: {str(exc)}"
            ) from exc


# --------------------------
# --- Project Categories ---
# --------------------------
# Placed in the same file to directly link to classes without circular imports
# Placed at the end so that classes are already known
# (they are not type hints anymore)


class ProjectCategory(Enum):
    """Definition of recognized project categories.

    Humasol project are executed within the scope of a project category, which
    describes the main objectives of the project or used resources
    (e.g., energy).

    Definitions contain:
    ENUM_VALUE = (category name, matching project class)
    """

    AGRICULTURE = ("agriculture", AgricultureProject)
    ELECTRONICS_DEVELOPMENT = (
        "electronics development",
        ElectronicsDevelopmentProject,
    )
    ENERGY = ("energy", EnergyProject)
    WATER = ("water", WaterProject)
    WASTE_MANAGEMENT = ("waste management", WasteManagementProject)

    @property
    def category_name(self) -> str:
        """Provide lower case name of the category."""
        return self.value[0]

    @property
    def class_name(self) -> type[Project]:
        """Provide class corresponding to the project category."""
        return self.value[1]

    @staticmethod
    def categories() -> tuple[ProjectCategory, ...]:
        """Provide a list of all project categories."""
        return tuple(ProjectCategory.__members__.values())

    @staticmethod
    def from_string(category: str) -> ProjectCategory:
        """Provide enum value representing the given string."""
        if category not in ProjectCategory.__members__:
            raise exceptions.IllegalArgumentException(
                f"Unexpected category: {category}"
            )

        return ProjectCategory.__members__[category]


if __name__ == "__main__":
    print("Hello World!")
