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
"""
# Python Libraries
from __future__ import annotations

import datetime
import re
from abc import abstractmethod
from functools import reduce
from typing import Any, Dict, List, Optional, Type, TypedDict, TypeVar, Union

from sqlalchemy import orm

from ..repository import db
from ..script import DATA_MANAGERS
from . import followup_work as fw
from . import person
from . import project_components as pc
from . import utils

# Local modules
from .project_categories import ProjectCategory

# Relationship tables between database entities
project_students = db.Table(
    "project_student",
    db.Column("project_id", db.Integer, db.ForeignKey("project.id")),
    db.Column("student_id", db.Integer, db.ForeignKey("person.id")),
)
project_supers = db.Table(
    "project_super",
    db.Column("project_id", db.Integer, db.ForeignKey("project.id")),
    db.Column("supervisor_id", db.Integer, db.ForeignKey("person.id")),
)
project_partners = db.Table(
    "project_partners",
    db.Column("project_id", db.Integer, db.ForeignKey("project.id")),
    db.Column("partner_id", db.Integer, db.ForeignKey("person.id")),
)
project_contact = db.Table(
    "project_contact",
    db.Column("project_id", db.Integer, db.ForeignKey("project.id")),
    db.Column("contact_id", db.Integer, db.ForeignKey("person.id")),
)
project_sdg_table = db.Table(
    "project_sdg",
    db.Column("project_id", db.Integer, db.ForeignKey("project.id")),
    db.Column("sdg", db.Enum(pc.SDG), db.ForeignKey("sdg_db.sdg")),
)


# Project models #


# These models are also used to create the database entities
# through the inheritance of db.Model
# TODO: check if can remove pylint deactivation when used setters
# pylint: disable=too-many-public-methods
# pylint: disable=too-many-instance-attributes
class Project(db.Model):
    """Abstract base class for all Humasol project.

    Projects executed by Humasol teams can be represented by subclasses of
    this base class. It represents the common features of all projects and
    therefore contains information that should be available for all projects.
    Subclasses should declare common aspects that should be met by all
    projects in that category.

    Attributes:
    id          -- Unique identifier for a project
    name        -- Title of the project
    code        -- Unique letter code
    date        -- Implementation or completion date
    description -- Description of the project
    category    -- Field of application of the project (e.g., energy, water)
    type        -- Subclass type used by the database ORM
    location    -- Project location
    work_folder -- URL to the folder containing all the preparation work
    dashboard   -- URL to the project data dashboard (if available)
    save_data   -- Indicates whether retrieved project data should be saved
                    to the Humasol drive for future teams to use
    project_data -- URL to the Humasol drive folder where the retrieved data
                    are stored
    extra_data  -- Dictionary with additional settings for the project manager
    sdgs        -- SDG goals that the project aims to tackle
    data_source -- Address and credentials to access the data logger
    students    -- Students that worked on the project
    supervisors -- Humasol members that guided the student team
    partners    -- Partners external to Humasol that contributed to the project
    contact_person  -- Person to contact in case there are questions about the
                        project
    subscriptions   -- List of subscription objects with people to update
    tasks       -- List of task objects with people to be reminded
    data_file   -- URI to the file containing data of this project object
                    (data is partially stored in a database and partially in a
                    file)
    project_components -- Elements relevant to the description of a project.
                            Can be used by subclasses to define important
                            components.
    """

    MAX_STUDENTS = 4
    T = TypeVar("T")
    V = TypeVar("V")

    # Definitions for the database tables #
    __tablename__ = "project"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, index=True, nullable=False)
    code = db.Column(db.String, index=True, unique=True, nullable=False)
    date = db.Column(db.DateTime, index=True, nullable=False)
    # description saved to file
    category = db.Column(db.String, index=True, nullable=False)
    type = db.Column(db.String(50))  # Used for internal mapping by SQLAlchemy
    location = db.relationship(
        "Location", lazy=True, uselist=False, cascade="all, delete-orphan"
    )
    work_folder = db.Column(db.String, unique=True, nullable=False)
    dashboard = db.Column(db.String)
    save_data = db.Column(db.Boolean, nullable=False)
    project_data = db.Column(db.String)
    # extra data saved to file
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
    # project components saved to file

    __mapper_args__ = {
        "polymorphic_on": type,
        "polymorphic_identity": "project",
    }

    # End of database definitions #

    class ProjectArgs(TypedDict, total=False):
        """Class used for typing project arguments."""

        name: str
        implementation_date: datetime.date
        description: str
        location: Dict[str, str | int | float]
        work_folder: str
        students: List[Dict[str, Any]]
        supervisors: List[Dict[str, Any]]
        contact_person: person.Person
        partners: List[Dict[str, Any]]
        code: Optional[str]
        sdgs: Optional[List[pc.SDG]]
        tasks: Optional[List[Dict[str, Any]]]
        data_source: Optional[Dict[str, str]]
        dashboard: Optional[str]
        save_data: bool
        project_data: Optional[str]
        extra_data: Optional[Dict[str, Any]]
        subscriptions: Optional[List[Dict[str, Any]]]
        kwargs: dict[str, Any]

    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-statements
    @abstractmethod
    def __init__(
        self,
        *,
        name: str,
        implementation_date: datetime.date,
        description: str,
        category: ProjectCategory,
        location: pc.Location,
        work_folder: str,
        students: List[person.Student],
        supervisors: List[person.Supervisor],
        contact_person: person.Person,
        partners: List[person.Partner],
        code: Optional[str] = None,
        sdgs: Optional[List[pc.SDG]] = None,
        tasks: Optional[List[fw.Task]] = None,
        data_source: Optional[pc.DataSource] = None,
        dashboard: Optional[str] = None,
        save_data: bool = False,
        project_data: Optional[str] = None,
        extra_data: Optional[Dict[str, Any]] = None,
        subscriptions: Optional[List[fw.Subscription]] = None,
        **kwargs,
    ):
        """Instantiate a project object.

        Arguments:
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
        data_source -- Address and credentials to access the data logger
        dashboard   -- URL to the project data dashboard (if available)
        save_data   -- Indicates whether retrieved project data should be
                        saved to the Humasol drive for future teams to use
        project_data -- URL to the Humasol drive folder where the retrieved
                        data are stored
        extra_data  -- Dictionary with additional settings for the project
                        manager
        subscriptions   -- List of subscription objects with people to update
        """
        # Argument checks
        # TODO: Use single check per argument
        if not self.is_valid_name(name):
            raise ValueError(
                "Argument 'name' has an illegal value. Should contain at "
                "least one letter"
            )

        if not isinstance(implementation_date, datetime.date):
            raise TypeError(
                "Argument 'implementation_date' should not be None and of "
                "type datetime.date"
            )
        if not self.is_valid_date(implementation_date):
            raise ValueError(
                "Argument 'implementation_date' has an illegal value. "
                "Only projects up to this year can be implemented"
            )

        if not isinstance(description, str):
            raise TypeError(
                "Argument 'description' should not be None and of type str"
            )
        if not self.is_valid_description(description):
            raise ValueError(
                "Argument 'description' has an illegal value. "
                "Should contain at least 1 letter"
            )

        if not self.is_valid_location(location):
            raise TypeError(
                "Argument 'location' should not be None and of type Location"
            )

        if not isinstance(work_folder, str):
            raise TypeError(
                "Argument 'work_folder' should not be None and of type str"
            )
        if not self.is_valid_work_folder(work_folder):
            raise ValueError(
                "Argument 'work_folder' has an illegal value. Should not "
                "be empty"
            )

        if not isinstance(students, list):
            raise TypeError(
                "Argument 'students' should not be None and of type list"
            )
        if not self.is_valid_student_list(students):
            raise ValueError(
                "Argument 'students' has an illegal value. "
                "Should be a non-empty lists containing unique Students"
            )

        if not isinstance(supervisors, list):
            raise TypeError(
                "Argument 'supervisors' should not be None and of type list"
            )
        if not self.is_valid_supervisor_list(supervisors):
            raise ValueError(
                "Argument 'supervisors' has an illegal value. Should be a "
                "non-empty list containing unique Supervisors"
            )

        if not self.is_valid_contact_person(contact_person):
            raise TypeError(
                "Argument 'contact_person' should not be None and of "
                "type Person"
            )

        if not isinstance(partners, list):
            raise TypeError(
                "Argument 'partners' should not be None nad of type list"
            )
        if not self.is_valid_partner_list(partners):
            raise ValueError(
                "Argument 'partners' has an illegal value. It should be a "
                "non-empty list containing unique Partners"
            )

        if code is not None and not isinstance(code, str):
            raise TypeError("Argument 'code' should be of type str or None")
        if not self.is_valid_code(code):
            raise ValueError(
                "Argument 'code' should be a non-empty str containing "
                "only letters"
            )

        if not self.is_valid_sdg_list(sdgs):
            raise ValueError(
                "Argument 'sdgs' has an illegal value. Should be non-empty "
                "and only contain SDGs"
            )

        if tasks is not None and not isinstance(tasks, list):
            raise TypeError("Argument 'tasks' should be of type list or None")
        if not self.is_valid_task_list(tasks):
            raise ValueError(
                "Argument 'tasks' has an illegal value. Should only "
                "contain unique Tasks"
            )

        if data_source is not None:
            if not Project.is_valid_data_source(data_source):
                raise TypeError(
                    "Argument 'data_source' should be None ore of "
                    "type DataSource"
                )

            if dashboard is not None and not isinstance(dashboard, str):
                raise TypeError(
                    "Argument 'dashboards' should be of type str or None"
                )
            if not self.is_valid_dashboard(dashboard):
                raise ValueError(
                    "Argument 'dashboard' should not be empty if it is "
                    "not None"
                )

            if not self.is_valid_save_data(save_data):
                raise TypeError(
                    "Argument 'save_data' should be of type bool or None"
                )

            if project_data is not None and not isinstance(project_data, str):
                raise TypeError(
                    "Argument 'project_data' should be of type str or None"
                )
            if not self.is_valid_project_data(project_data):
                raise ValueError(
                    "Argument 'project_data' has an illegal value. "
                    "Should be non-empty"
                )

            if subscriptions is not None and not isinstance(
                subscriptions, list
            ):
                raise TypeError(
                    "Argument 'subscriptions' should be of type list or None"
                )
            if not self.is_valid_subscription_list(subscriptions):
                raise ValueError(
                    "Argument 'subscriptions' has an illegal value. "
                    "Should be non-empty and contain only "
                    "unique Subscriptions"
                )

        elif not (
            dashboard is None
            and not save_data
            and project_data is None
            and extra_data is None
        ):  # and subscriptions is None
            raise ValueError(
                "If no data source is provided the optional arguments "
                "'dashboard', 'save_data', 'project_data', 'extra_data' "
                "and 'subscriptions' should not be provided with a value "
                "other than None"
            )

        # All checks passed, instantiate object

        super().__init__()

        self.name = name
        self.code = code
        self.date = implementation_date
        self.description = description
        self.category = category
        self.location = location
        self.work_folder = work_folder
        self.dashboard = dashboard
        self.save_data = save_data
        self.project_data = project_data
        self.extra_data = extra_data if extra_data is not None else {}
        self.sdgs = sdgs if sdgs is not None else []
        self.sdgs_db = [pc.SdgDB(sdg) for sdg in self.sdgs]
        self.data_source = data_source
        self.students = students
        self.supervisors = supervisors
        self.partners = partners if partners is not None else []
        self.contact_person = contact_person
        self.subscriptions = subscriptions if subscriptions is not None else []
        self.tasks = tasks if tasks is not None else []

        self._updated = False
        self.project_components: List[pc.ProjectComponent] = []

        if self.code is None:
            self._create_code()

        self.data_file = f"{self.code}.json"
        # TODO: generate project data file

    # pylint: enable=too-many-statements
    # pylint: enable=too-many-branches
    # pylint: enable=too-many-locals
    # pylint: enable=too-many-arguments

    # Validators #
    @staticmethod
    def is_valid_name(name: str) -> bool:
        """Check whether the provided name contains valid characters."""
        # TODO: Correct regex
        return (
            isinstance(name, str)
            and re.match(r"[A-Z]+", name.upper()) is not None
        )

    @staticmethod
    def is_valid_date(date: datetime.date) -> bool:
        """Check whether the provided date is valid as implementation date."""
        return (
            isinstance(date, datetime.date)
            and date.year <= datetime.date.today().year
        )

    @staticmethod
    def is_valid_description(description: str) -> bool:
        """Check whether the provided description has no illegal characters."""
        # TODO: Correct regex
        return (
            isinstance(description, str)
            and re.match(r"[A-Z]+", description.upper()) is not None
        )

    @staticmethod
    def is_valid_location(location: pc.Location) -> bool:
        """Check whether the provided location is a legal location."""
        return isinstance(location, pc.Location)

    @staticmethod
    def is_valid_work_folder(folder: str) -> bool:
        """Check whether the provided folder is a legal URL."""
        # TODO: strengthen check
        return isinstance(folder, str) and len(folder) > 0

    @staticmethod
    def is_valid_student_list(students: List[person.Student]) -> bool:
        """Check whether the provided list is a valid student list."""
        return (
            isinstance(students, list)
            and 3 <= len(students) <= Project.MAX_STUDENTS
            and all(map(lambda s: isinstance(s, person.Student), students))
            and len(students) == len(set(students))
        )

    @staticmethod
    def is_valid_supervisor_list(supers: List[person.Supervisor]) -> bool:
        """Check whether the provided list is a valid supervisor list."""
        return (
            isinstance(supers, list)
            and len(supers) > 0
            and all(map(lambda s: isinstance(s, person.Supervisor), supers))
            and len(supers) == len(set(supers))
        )

    @staticmethod
    def is_valid_contact_person(contact: person.Person) -> bool:
        """Check whether the provided person is a legal person."""
        return isinstance(contact, person.Person)

    @staticmethod
    def is_valid_partner_list(partners: List[person.Partner]) -> bool:
        """Check whether the provided list is a valid partners list."""
        return (
            isinstance(partners, list)
            and len(partners) > 0
            and all(map(lambda p: isinstance(p, person.Partner), partners))
            and len(partners) == len(set(partners))
        )

    @staticmethod
    def is_valid_code(code: Optional[str]) -> bool:
        """Check whether the provided code is a valid identifier code."""
        return code is None or (
            isinstance(code, str)
            and re.fullmatch(r"[A-Z]+", code.upper()) is not None
        )

    @staticmethod
    def is_valid_sdg(sdg: pc.SDG) -> bool:
        """Check whether the provided SDG is legal."""
        return isinstance(sdg, pc.SDG)

    @staticmethod
    def is_valid_sdg_list(sdgs: Optional[List[pc.SDG]]) -> bool:
        """Check whether the provided SDG list is legal."""
        return sdgs is None or (
            isinstance(sdgs, list)
            and len(sdgs) > 0
            and all(map(Project.is_valid_sdg, sdgs))
        )

    @staticmethod
    def is_valid_data_source(source: Optional[pc.DataSource]) -> bool:
        """Check whether the provided source is a legal project data source."""
        return source is None or isinstance(source, pc.DataSource)

    @staticmethod
    def is_valid_task_list(tasks: Optional[List[fw.Task]]) -> bool:
        """Check whether the provided list is a legal tasks list."""
        return tasks is None or (
            isinstance(tasks, list)
            and all(map(Project.is_valid_task, tasks))
            and len(tasks) == len(set(tasks))
        )

    @staticmethod
    def is_valid_task(task: Any) -> bool:
        """Check whether the provided task is legal."""
        return isinstance(task, fw.Task)

    @staticmethod
    def is_valid_dashboard(dashboard: Optional[str]) -> bool:
        """Check whether the provided dashboard is legal."""
        return dashboard is None or (
            isinstance(dashboard, str) and len(dashboard) > 0
        )

    @staticmethod
    def is_valid_save_data(flag: bool) -> bool:
        """Check whether the provided flag is a legal flag."""
        return isinstance(flag, bool)

    @staticmethod
    def is_valid_project_data(data: Optional[str]) -> bool:
        """Check whether the provided data folder is a legal URL."""
        return data is None or (isinstance(data, str) and len(data) > 0)

    @staticmethod
    def is_valid_subscription_list(
        subs: Optional[List[fw.Subscription]],
    ) -> bool:
        """Check whether the provided list is a legal subscriptions list."""
        return subs is None or (
            isinstance(subs, list)
            and all(map(Project.is_valid_subscription, subs))
            and len(subs) == len(set(subs))
        )

    @staticmethod
    def is_valid_subscription(sub: fw.Subscription) -> bool:
        """Check whether the provided subscription is a legal subscription."""
        return isinstance(sub, fw.Subscription)

    @staticmethod
    def is_valid_extra_data(data: Dict[str, str]) -> bool:
        """Check whether the provided extra data has a legal format."""
        return isinstance(data, dict) and all(
            map(
                lambda t: isinstance(t[0], str) and isinstance(t[1], str),
                data.items(),
            )
        )

    # Setters #

    # TODO: Convert to python setter
    def set_name(self, name: str) -> None:
        """Set the name of this project."""
        if not self.is_valid_name(name):
            raise ValueError(
                "Argument 'name' has an illegal value. Should be a string "
                "containing at least one letter"
            )

        self.name = name

    # TODO: Convert to python setter
    def set_date(self, date: datetime.date) -> None:
        """Set the implementation date for this project."""
        if not self.is_valid_date(date):
            raise ValueError(
                "Argument 'implementation_date' has an illegal value. "
                "Should be a datetime.date and only projects up to "
                "(and including) this year can be implemented"
            )

        self.date = date

    # TODO: Convert to python setter
    def set_description(self, description: str) -> None:
        """Set the description for this project."""
        if not self.is_valid_description(description):
            raise ValueError(
                "Argument 'description' has an illegal value. Should be a "
                "string containing at least 1 letter"
            )

        self.description = description

    # TODO: Convert to python setter
    def set_location(self, location: pc.Location) -> None:
        """Set the location for this project."""
        if not self.is_valid_location(location):
            raise ValueError(
                "Argument 'location' should not be None and of type Location"
            )

        self.location = location

    # TODO: Convert to python setter
    def set_work_folder(self, work_folder: str) -> None:
        """Set the work folder (preparation work) for this project."""
        if not self.is_valid_work_folder(work_folder):
            raise ValueError(
                "Argument 'work_folder' has an illegal value. Should be a "
                "non-empty string"
            )

        self.work_folder = work_folder

    # TODO: Add python getter
    # TODO: Add addition and removal functions for SDG
    # TODO: Convert to python setter
    def set_sdgs(self, sdgs: Optional[List[pc.SDG]]) -> None:
        """Set the list of SDGs for this project."""
        if not self.is_valid_sdg_list(sdgs):
            raise ValueError(
                "Argument 'sdgs' has an illegal value. Should be non-empty "
                "and only contain SDGs"
            )

        self.sdgs = sdgs if sdgs else []
        self.sdgs_db = [pc.SdgDB(sdg) for sdg in self.sdgs]

    # TODO: Convert to python setter
    def set_contact_person(self, contact: person.Person) -> None:
        """Set the contact person for this project."""
        if not self.is_valid_contact_person(contact):
            raise ValueError(
                "Argument 'contact_person' should not be None and of type "
                "Person"
            )

        self.contact_person = contact

    # TODO: Add getter
    # TODO: Add addition and removal methods
    # TODO: Convert to python setter
    def set_students(self, students: List[person.Student]) -> None:
        """Set the students for this project."""
        if not self.is_valid_student_list(students):
            raise ValueError(
                "Argument 'students' has an illegal value. Should be a "
                "non-empty lists containing unique Students"
            )

        self.students = students

    # TODO: Add getter
    # TODO: Add addition and removal methods
    # TODO: Convert to python setter
    def set_supervisors(self, supers: List[person.Supervisor]) -> None:
        """Set the supervisors for this project."""
        if not self.is_valid_supervisor_list(supers):
            raise ValueError(
                "Argument 'supervisors' has an illegal value. Should be a "
                "non-empty list containing unique Supervisors"
            )

        self.supervisors = supers

    # TODO: Add getter
    # TODO: Add addition and removal methods
    # TODO: Convert to python setter
    def set_partners(self, partners: List[person.Partner]) -> None:
        """Set the partners for this project."""
        if not self.is_valid_partner_list(partners):
            raise ValueError(
                "Argument 'partners' has an illegal value. It should be a "
                "non-empty list containing unique Partners"
            )

        self.partners = partners

    # TODO: Convert to python setter
    def set_data_source(self, source: Optional[pc.DataSource]) -> None:
        """Set the datasource for this project."""
        if not self.is_valid_data_source(source):
            raise ValueError(
                "Argument 'data_source' should be None ore of type DataSource"
            )

        if source is None:
            # self.set_dashboard(None)
            # self.set_project_data(None)
            self.set_save_data(False)
            self.set_subscriptions([])

        self.data_source = source

    # TODO: Convert to python setter
    def set_dashboard(self, dashboard: Optional[str]) -> None:
        """Set the dashboard for this project."""
        if not self.is_valid_dashboard(dashboard):
            raise ValueError(
                "Argument 'dashboard' should not be empty if it is not None"
            )
        if self.data_source is None and dashboard is not None:
            raise ValueError(
                "Project cannot have a dashboard if it does not have a data "
                "source"
            )

        self.dashboard = dashboard

    # TODO: Convert to python setter
    def set_save_data(self, save: bool) -> None:
        """Set the save data flag for this project."""
        if not self.is_valid_save_data(save):
            raise ValueError(
                "Argument 'save_data' should be of type bool or None"
            )
        if self.data_source is None and save:
            raise ValueError(
                "Project cannot save data if it does not have a data source"
            )

        self.save_data = save

    # TODO: Convert to python setter
    def set_project_data(self, folder: Optional[str]) -> None:
        """Set URL to project data folder."""
        if not self.is_valid_project_data(folder):
            raise ValueError(
                "Argument 'project_data' should be of type str or None"
            )

        self.project_data = folder

    # TODO: Convert to python setter
    def set_extra_data(self, data: Dict[str, str]) -> None:
        """Set the extra data for this project.

        Extra data can be used to configure project managers.
        """
        if not self.is_valid_extra_data(data):
            raise ValueError(
                "Illegal value for extra data. Should be a dict mapping "
                "strings to strings"
            )

        self.extra_data = data

    # TODO: Add getter
    # TODO: Add addition and removal methods
    # TODO: Convert to python setter
    def set_tasks(self, tasks: List[fw.Task]) -> None:
        """Set the tasks for this project."""
        if not self.is_valid_task_list(tasks):
            raise ValueError("Provided tasks list is invalid")

        self.tasks = tasks

    # TODO: Add getter
    # TODO: Add addition and removal methods
    # TODO: Convert to python setter
    def set_subscriptions(self, subs: List[fw.Subscription]) -> None:
        """Set the subscriptions for this project."""
        if not self.is_valid_subscription_list(subs):
            raise ValueError("Provided subscriptions list is invalid")

        if self.data_source is None and len(subs) != 0:
            raise ValueError(
                "Cannot subscribe to a project without a source of data"
            )

        self.subscriptions = subs

    # Other methods #

    def subscribe(self, sub: fw.Subscription) -> None:
        """Add the provided subscription to the project's subscriptions."""
        if not self.is_valid_subscription(sub):
            raise ValueError("Provided subscription is not valid")
        if self.data_source is None:
            raise ValueError(
                "Cannot subscribe to a project without a source of data"
            )
        if sub in self.subscriptions:
            raise ValueError(
                "Provided Subscription is already subscribed to this project"
            )

        self.subscriptions.append(sub)

    def unsubscribe(self, sub: fw.Subscription) -> None:
        """Remove the given subscription from the project's subscriptions."""
        if not self.is_valid_subscription(sub):
            raise ValueError("Provided subscription is invalid")

        if sub in self.subscriptions:
            self.subscriptions.remove(sub)

    def add_task(self, task: fw.Task) -> None:
        """Add the provided task to the project's tasks."""
        if not self.is_valid_task(task):
            raise ValueError("Provided task is not valid")

        if task in self.tasks:
            raise ValueError(
                "Provided task is already listed for this project"
            )

        self.tasks.append(task)

    def remove_task(self, task: fw.Task) -> None:
        """Remove the provided task from the project's tasks."""
        if not self.is_valid_task(task):
            raise ValueError("Provided task is invalid")

        if task in self.tasks:
            self.tasks.remove(task)

    def build_data_source(self, data: Dict[str, Any]) -> pc.DataSource:
        """Build a correct data source for this instance."""
        return pc.DataSource(**data)

    def _update_params_check(self, params: ProjectArgs) -> None:
        """Check whether the provided update parameters a legal."""
        if "name" in params and not self.is_valid_name(params["name"]):
            raise ValueError(
                "Argument 'name' has an illegal value for updating."
            )

        if "implementation_date" in params and not self.is_valid_date(
            params["implementation_date"]
        ):
            raise ValueError(
                "Argument 'date' has an illegal value for updating."
            )

        if "description" in params and not self.is_valid_description(
            params["description"]
        ):
            raise ValueError(
                "Argument 'description' has an illegal value for updating."
            )

        if "work_folder" in params and not self.is_valid_work_folder(
            params["work_folder"]
        ):
            raise ValueError(
                "Argument 'work_folder' has an illegal value for updating."
            )

        if "sdgs" in params and not self.is_valid_sdg_list(params["sdgs"]):
            raise ValueError(
                "Argument 'sdgs' has an illegal value for updating."
            )

    # pylint: disable=too-many-branches
    def _update_general(self, params: ProjectArgs) -> None:
        """Update the general attributes of this project.

        Update the attributes of this object that refer to general aspects of
        a project. These attributes are applicable to all projects.
        """
        if "location" in params:
            # TODO: find a way to separate checks (di and snapshot maybe)
            self.location.update(**params["location"])

        if "name" in params:
            self.name = params["name"]

        if "implementation_date" in params:
            self.date = params["implementation_date"]

        if "description" in params:
            self.description = params["description"]

        if "work_folder" in params:
            self.work_folder = params["work_folder"]

        if "sdgs" in params:
            self.set_sdgs(params["sdgs"])

        if "students" in params:
            self.set_students(
                utils.merge_update_list(
                    self.students,
                    params["students"],
                    list(map(lambda dic: dic["email"], params["students"])),
                    lambda stu: stu.email,
                    lambda stu, dic: stu.update(**dic),
                    lambda dic: person.construct_person(
                        lambda stu: person.Student(**stu), dic
                    ),
                )
            )
        if "supervisors" in params:
            self.set_supervisors(
                utils.merge_update_list(
                    self.supervisors,
                    params["supervisors"],
                    list(map(lambda dic: dic["email"], params["supervisors"])),
                    lambda sup: sup.email,
                    lambda sup, dic: sup.update(**dic),
                    lambda dic: person.construct_person(
                        lambda sup: person.Supervisor(**sup), dic
                    ),
                )
            )
        if "partners" in params:
            self.set_partners(
                utils.merge_update_list(
                    self.partners,
                    params["partners"],
                    list(map(lambda dic: dic["email"], params["partners"])),
                    lambda par: par.email,
                    lambda par, dic: par.update(**dic),
                    lambda dic: person.construct_person(
                        lambda par: person.Partner(**par), dic, True
                    ),
                )
            )
        if "contact_person" in params:
            # First use the existing people as a contact person
            # if that person already exists
            for per in self.students + self.supervisors + self.partners:
                if per.email == params["contact_person"]["email"]:
                    self.contact_person = per
                    break
            else:
                # This code block is only executed if the beak
                # statement wasn't called
                contact = person.construct_person(
                    person.get_constructor_from_type(
                        params["contact_person"].pop("contact_type")
                    ),
                    params["contact_person"],
                )

                if not self.is_valid_contact_person(contact):
                    raise ValueError(
                        "Argument 'contact_person' has an illegal value "
                        "for updating."
                    )

                self.contact_person = contact

    # pylint: enable=too-many-branches

    # pylint: disable=too-many-branches
    def _update_followup(self, params: ProjectArgs) -> None:
        """Update the follow-up attributes of this project."""
        if "tasks" in params:
            if new_tasks := params["tasks"]:
                self.set_tasks(
                    utils.merge_update_list(
                        self.tasks,
                        new_tasks,
                        list(map(lambda d: d["name"], new_tasks)),
                        lambda ta: ta.name,
                        lambda ta, dic: ta.update(**dic),
                        lambda dic: fw.construct_followup_work(
                            lambda ta: fw.Task(**ta), dic
                        ),
                    )
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
                    self.data_source.update(**params["data_source"])
                else:
                    self.set_data_source(
                        self.build_data_source(params["data_source"])
                    )

        if self.data_source is not None:
            if "subscriptions" in params:
                if new_subs := params["subscriptions"]:
                    self.set_subscriptions(
                        utils.merge_update_list(
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
                            lambda dic: fw.construct_followup_work(
                                lambda sub: fw.Subscription(**sub), dic
                            ),
                        )
                    )
                else:
                    self.set_subscriptions([])
            if "dashboard" in params:
                self.set_dashboard(params["dashboard"])
            if "save_data" in params:
                self.set_save_data(params["save_data"])

    # pylint: enable=too-many-branches

    @abstractmethod
    def update(self, params: ProjectArgs) -> Project:
        """Update this instance with the provided new parameters.

        Valid parameters are those defined in ProjectArgs.
        """
        # TODO: Reorder function, first checks, then apply changes

        self._update_params_check(params)

        self._update_general(params)

        self._update_followup(params)

        return self

    def get_credentials(self) -> Dict[str, Any]:
        """Get the data source credentials.

        Return a dictionary as provided by DataSource.get_credential,
        or and empty dictionary if not source is available.
        """
        return self.data_source.get_credentials() if self.data_source else {}

    def to_save_to_file(self) -> Dict[str, Any]:
        """Provide a dictionary containing all data for file storage.

        Provide all the data from this instance that should be stored in the
        project file rather than in the database.
        """
        data = {
            "description": self.description,
            "extra_data": self.extra_data,
            "components": {
                k: v
                for c in self.project_components
                for k, v in c.as_dict().items()
            },
        }

        return data

    @orm.reconstructor  # Function is called by the ORM on database load
    def init_on_load(self) -> None:
        """Prepare instance when it is loaded from the database."""
        # Project doesn't know anything about files, do this from repository
        # self._load_from_file()
        self.sdgs = [s.sdg for s in self.sdgs_db]
        self.project_components = []

    def load_from_file(self, data: Dict[str, Any]) -> None:
        """Prepare instance with data from file."""
        # TODO: add project components.
        if "description" in data:
            self.description = data["description"]
        if "extra_data" in data:
            self.extra_data = data["extra_data"]

    def _add_component(self, component: pc.ProjectComponent) -> None:
        """Add a project component to this project's components list."""
        if not isinstance(component, pc.ProjectComponent):
            raise TypeError(
                "Argument 'component' should not be None and of type "
                "ProjectComponent"
            )

        # TODO: Check whether this is a correct component for this instance

        self.project_components.append(component)

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

    def _filter_project_components(self, component_type: Type[T]) -> List[T]:
        """Retrieve Project components of the specified type."""
        return list(
            filter(
                lambda c: isinstance(c, component_type),  # type: ignore
                self.project_components,
            )
        )

    # Magic methods #
    def __repr__(self) -> str:
        """Provide a string representation for this instance."""
        return (
            f"name={self.name}, "
            f"date={self.date}, "
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


# pylint: enable=too-many-instance-attributes
# pylint: enable=too-many-public-methods


class EnergyProject(Project):
    """Class representing projects installing an energy system."""

    # Definitions for the database tables #
    power = db.Column(db.Float)

    # End database definitions #

    class EnergyProjectArgs(Project.ProjectArgs, total=False):
        """Class used for EnergyProject update parameters."""

        power: Union[int, float]

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        *,
        power: float,
        data_source: str,
        api_manager: str,
        data_manager: str,
        user: str = None,
        password: str = None,
        token: str = None,
        **kwargs,
    ):
        """Instantiate object of this class.

        Arguments:
        power           -- Power rating of the system
        data_source     -- Data source address
        api_manager     -- Name of API manager class
        data_manager    -- Name of data manager class
        user            -- Username for the data source
        password        -- Password to authenticate with the data source
        token           -- Key to automatically authenticate with the data
                            source
        """
        # Check arguments
        if not isinstance(power, (float, int)):
            raise TypeError(
                "Argument 'power' should not be None and of type float"
            )
        if not self.is_valid_power(power):
            raise ValueError(
                "Argument 'power' has an illegal value. Should be non-negative"
            )

        if data_source is not None:
            if not self.is_valid_data_manager(data_manager):
                raise ValueError(
                    "Argument 'data_manager' is not a valid manager for an "
                    "Energy project"
                )

            data_source = self.build_data_source(
                {
                    "data_source": data_source,
                    "api_manager": api_manager,
                    "report_manager": "EnergyReportManager",
                    "user": user,
                    "password": password,
                    "token": token,
                }
            )

        super().__init__(
            category=ProjectCategory.ENERGY, data_source=data_source, **kwargs
        )

        self.power = power

    # pylint: enable=too-many-arguments

    @staticmethod
    def is_valid_power(power: float) -> bool:
        """Check whether the provided power is a valid power setting."""
        return isinstance(power, (float, int)) and power >= 0

    @staticmethod
    def is_valid_data_manager(manager: str) -> bool:
        """Check whether the given manager is a valid energy data manager."""
        return manager in DATA_MANAGERS[ProjectCategory.ENERGY]

    # TODO: Convert to python setter
    def set_power(self, power: float) -> None:
        """Set the power rating for this project."""
        if not self.is_valid_power(power):
            raise ValueError(
                "Argument 'power' has an illegal value. Should be a "
                "non-negative float"
            )

        self.power = power

    # A more specific data class is ok in this case, doesn't violate LSP
    # since it has no behavior
    def update(  # type: ignore[override]
        self, params: EnergyProjectArgs
    ) -> EnergyProject:
        """Update this instance with the provided new parameters."""
        super().update(params)

        if "power" in params:
            self.set_power(params["power"])

        return self

    def load_from_file(self, data: Dict[str, Any]) -> None:
        """Populate this instance with information loaded from file."""
        super().load_from_file(data)

        for comp, params in data["components"].items():
            if comp == pc.Battery.LABEL:
                params["type"] = pc.Battery.BatteryType.from_str(
                    params["type"]
                )
                self._add_component(pc.Battery(**params))
            elif comp == pc.Grid.LABEL:
                self._add_component(pc.Grid(**params))
            elif comp == pc.Generator.LABEL:
                self._add_component(pc.Generator(**params))

    def __repr__(self) -> str:
        """Provide a string representation for this instance."""
        return (
            f"EnergyProject("
            f"{super().__repr__()}, "
            f"power={self.power}"
            f")"
        )


# Factories #


class ProjectFactory:
    """Factory class used for constructing energy projects."""

    @staticmethod
    def get_project() -> Project:
        """Construct project with the provided parameters."""
        # TODO: Write factory function

    @staticmethod
    def get_project_component() -> pc.ProjectComponent:
        """Construct the project component with the provided parameters."""
        # TODO: Write factory function
