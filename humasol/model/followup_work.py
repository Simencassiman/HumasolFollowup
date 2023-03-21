"""Follow-up work folder classes.

A project could be followed by receiving updates about its folder or by
performing specific tasks. This module defines a task and subscription class
for this purpose.

Classes:
FollowupWork    -- Abstract base class for work related to project followup
Subscription    -- Class for a project folder subscription
Task            -- Class representing a task for a project
Period          -- Class containing information about the period during wich
                    such work is to be carried out
"""

# Python Libraries
from __future__ import annotations

import datetime
import re
from datetime import date
from enum import Enum, unique
from typing import Any, Dict, List, Optional, Type, TypeVar

from dateutil.relativedelta import relativedelta
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declared_attr

# Local modules
from humasol import exceptions, model
from humasol.model import person, utils
from humasol.repository import db


class FollowupJob(model.BaseModel, model.ProjectElement):
    """Abstract base class for work related to project follow-up.

    Humasol is interested in carrying out various tasks to follow a finished
    project's operations. It is also interested in keeping people updated
    about the project's operations.
    Work related to followup should subclass this base class.

    Attributes
    __________
    id          -- Work identifier
    subscriber  -- Person interested/responsible in the work
    periods     -- Periods of activity for this work
    last_notification -- Date on which the subscriber was last notified
    """

    T = TypeVar("T")
    V = TypeVar("V")

    # Definitions for the database tables

    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Certain attributes are declared as functions to allow the creation
    # of separate tables for the subclasses
    @declared_attr
    def subscriber_id(self) -> SQLAlchemy.Column:
        """Provide subscriber ID database column."""
        return db.Column(
            db.Integer, db.ForeignKey(person.Person.id), nullable=False
        )

    @declared_attr
    def subscriber(self) -> orm.RelationshipProperty:
        """Provide database relation to subscriber."""
        return db.relationship(person.Person, lazy=False, uselist=False)

    @declared_attr
    def project_id(self) -> SQLAlchemy.Column:
        """Provide project ID database column."""
        return db.Column(
            db.Integer, db.ForeignKey("project.id"), nullable=False
        )

    @declared_attr
    def periods(self) -> orm.RelationshipProperty:
        """Provide database relation to periods."""
        return db.relationship(
            "Period", lazy=False, cascade="all, delete-orphan"
        )

    last_notification = db.Column(db.DateTime)

    # End database definitions

    def __init__(
        self,
        subscriber: person.Person,
        periods: List[Period],
        last_notification: Optional[date] = None,
    ) -> None:
        """Instantiate this object.

        Parameters
        __________
        subscriber  -- Person interested in this job
        periods     -- List of periods when this job should be active and the
                        subscriber should be notified
        last_notification   -- Date on which the last notification was sent
        """
        # Disable pylint. Need type to ignore subclasses
        # pylint: disable=unidiomatic-typecheck
        if type(self) == FollowupJob:
            raise exceptions.IllegalArgumentException(
                "FollowupWork is an abstract class and cannot be instantiated"
            )
        # pylint: enable=unidiomatic-typecheck

        if not FollowupJob.is_legal_subscriber(subscriber):
            raise exceptions.IllegalArgumentException(
                "Parameter 'subscriber' should not be None and of a "
                "subclass of Person"
            )

        if not FollowupJob.are_legal_periods(periods):
            raise exceptions.IllegalArgumentException(
                "Parameter 'periods' must be a list and contain unique Periods"
            )

        if not FollowupJob.is_legal_last_notification(last_notification):
            raise exceptions.IllegalArgumentException(
                "Parameter 'last_notification' should be a date "
                "(of type datetime.date) in the future, or None"
            )

        self.subscriber = subscriber
        self.periods = periods
        self.last_notification = last_notification

    @staticmethod
    def are_legal_periods(periods: List[Period]) -> bool:
        """Check if the provided periods are valid periods."""
        if not isinstance(periods, list):
            return False

        if len(periods) == 0:
            return False

        if any(
            map(
                lambda pe: not isinstance(pe, Period)
                or pe.has_past(date.today()),
                periods,
            )
        ):
            return False

        for i, period in enumerate(periods[:-1]):
            for per in periods[i + 1 :]:
                if (
                    period.start <= per.start
                    and not period.has_past(per.start)
                ) or (
                    per.start <= period.start
                    and not per.has_past(period.start)
                ):
                    return False

        return True

    @staticmethod
    def is_legal_last_notification(last_notification: Optional[date]) -> bool:
        """Check whether the provided date is valid for a last notification."""
        if last_notification is None:
            return True

        if not isinstance(last_notification, date):
            return False

        return last_notification <= date.today()

    @staticmethod
    def is_legal_subscriber(sub: person.Person) -> bool:
        """Check if the provided subscriber is a valid subscriber."""
        return isinstance(sub, person.Person)

    # TODO: convert to python setter
    def set_subscriber(self, subscriber: person.Person) -> None:
        """Set the subscriber for this job."""
        if not self.is_legal_subscriber(subscriber):
            raise ValueError(
                "Argument 'subscriber' should not be None and of a subclass "
                "of Person"
            )

        self.subscriber = subscriber

    # TODO: Add getter to avoid unauthorized list editing
    # TODO: Convert to python setter
    def set_periods(self, periods: List[Period]) -> None:
        """Set the periods for this job."""
        if not self.are_legal_periods(periods):
            raise ValueError(
                "Argument 'periods' should be a non-empty list containing "
                "periods"
            )

        self.periods = periods

    # TODO: Convert to python setter
    def set_last_notification(self, last_notification: date) -> None:
        """Set the last notification date for this job."""
        if not self.is_legal_last_notification(last_notification):
            raise ValueError(
                "Argument 'last_notification' has an invalid value. "
                "Last notification should be None or a date in the past."
            )

        self.last_notification = last_notification

    def add_period(self, period: Period) -> None:
        """Add the provided period to the job's periods list."""
        if not self.is_valid_period(period):
            raise exceptions.IllegalArgumentException(
                "Invalid period was provided. Make sure it doesn't "
                "overlap with existing periods"
            )

        self.periods += [period]

    def clean_periods(self) -> None:
        """Remove any passed periods."""
        items_to_pop = [
            i for i, p in enumerate(self.periods) if p.has_past(date.today())
        ]

        for idx in reversed(items_to_pop):
            self.periods.pop(idx)

    def is_valid_period(self, period: Period) -> bool:
        """Check whether this is a valid period for this instance.

        Checks whether this period is valid for this particular instance with
        its particular periods.
        """
        return self.are_legal_periods(list(self.periods) + [period])

    def remove_period(self, period: Period) -> None:
        """Remove the given period from this job's periods list."""
        if period in self.periods:
            if len(self.periods) == 1:
                raise exceptions.IllegalStateException(
                    "Invalid operation. Cannot remove only period"
                )
            self.periods.remove(period)

    def should_notify(self) -> bool:
        """Indicate whether the subscriber should be notified.

        The subscriber should be notified if one of the periods of this job is
        active and if the time since the last notification is at least equal
        to the time interval indicated by that period.

        Returns
        _______
        Return true if the subscriber should be notified. False otherwise.
        """
        return any(
            map(
                lambda p: p.should_update(self.last_notification), self.periods
            )
        )

    def update(self, **params: Any) -> FollowupJob:
        """Update this instance with the provided new parameters.

        Valid parameters are those passed to the __init__ method.

        Returns
        _______
        Return reference to self.
        """
        if "last_notification" in params:
            self.set_last_notification(params["last_notification"])

        if "subscriber" in params:
            self.subscriber.update(**params["subscriber"])

        if "periods" in params:
            utils.merge_update_list(
                self.periods,
                params["periods"],
                list(map(lambda d: d["start"], params["periods"])),
                lambda p: p.start,
                lambda p, d: p.update(**d),
                lambda d: Period(**d),
            )

        return self

    # TODO: Move logic to individual python setters
    def __setattr__(self, key, value):
        """Control access to certain attributes."""
        if key == "last_notification" and (
            (value is None and self.last_notification is not None)
            or (
                self.last_notification is not None
                and value < self.last_notification
            )
        ):
            raise ValueError(f"Invalid value for last notification: {value}")

        if key == "periods" and not self.are_legal_periods(value):
            raise ValueError("Argument 'periods' contains invalid periods")

        super().__setattr__(key, value)

    def __repr__(self) -> str:
        """Provide a string representation for this instance."""
        return (
            f"subscriber={repr(self.subscriber)}, "
            f"periods={[repr(p) for p in self.periods]}, "
            f"last_notification={self.last_notification}"
        )


class Subscription(FollowupJob):
    """Class representing a subscription to a project.

    A project can log data about its operations. People related to Humasol can
    subscribe to folder updates of a project to keep up to date with its
    operations.
    """

    # Definitions for database tables #
    __tablename__ = "subscription"
    __mapper_args__ = {"polymorphic_identity": "subscription"}

    # End database definitions

    def __init__(
        self,
        subscriber: person.Person,
        periods: List[Period],
        last_notification: date = None,
    ) -> None:
        """Instantiate object of this class.

        For arguments see FollowupWork.__init__.
        """
        super().__init__(subscriber, periods, last_notification)

    def __repr__(self) -> str:
        """Provide a string representation for this instance."""
        return "Subscription(" + super().__repr__() + ")"


class Task(FollowupJob):
    """Class representing a project task.

    To follow up a project certain tasks might need to be executed (e.g.,
    maintenance). This class can be used to represent such a task and to
    notify responsible people in a timely fashion.

    Attributes
    __________
    id          -- Work identifier
    subscriber  -- Person interested/responsible in the work
    periods     -- Periods of activity for this work
    last_notification -- Date on which the subscriber was last notified
    name        -- Task title
    function    -- Description of the task
    """

    # Definitions for database tables #
    __tablename__ = "task"
    __mapper_args__ = {"polymorphic_identity": "task"}

    name = db.Column(db.String, nullable=False)
    function = db.Column(db.String, nullable=False)

    # End database definitions #

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        subscriber: person.Person,
        periods: List[Period],
        name: str,
        function: str,
        last_notification: date = None,
    ) -> None:
        """Instantiate object of this class.

        Parameters
        __________
        subscriber  -- Person interested/responsible in the work
        periods     -- Periods of activity for this work
        name        -- Task title
        function    -- Description of the task
        last_notification -- Date on which the subscriber was last notified
        """
        if not Task.is_legal_name(name):
            raise exceptions.IllegalArgumentException(
                "Parameter 'name' should be of type str and only "
                "contain letters (at least one) and white spaces"
            )

        if not Task.is_legal_function(function):
            raise exceptions.IllegalArgumentException(
                "Parameter 'function' should only contain letters "
                "(at least one), white spaces, commas or periods"
            )

        super().__init__(subscriber, periods, last_notification)
        self.name = name
        self.function = function

    # pylint: enable=too-many-arguments

    @staticmethod
    def is_legal_function(function: str) -> bool:
        """Check whether the provided function contains valid characters."""
        if not isinstance(function, str):
            return False

        return re.fullmatch(r"^[A-Z][A-Z\s,.]*", function.upper()) is not None

    @staticmethod
    def is_legal_name(name: str) -> bool:
        """Check whether the provided name is composed of valid characters."""
        if not isinstance(name, str):
            return False

        return re.fullmatch(r"^[A-Z][A-Z\s]*", name.upper()) is not None

    # TODO: Convert to python setter
    def set_name(self, name: str) -> None:
        """Set the name of this task."""
        if not self.is_legal_name(name):
            raise ValueError(
                "Argument 'name' should be a string containing only "
                "letters (at least one) and white spaces"
            )

        self.name = name

    # TODO: Convert to python setter
    def set_function(self, function: str) -> None:
        """Set the function of this task."""
        if not self.is_legal_function(function):
            raise ValueError(
                "Argument 'function' should only contain letters "
                "(at least one), white spaces, commas or periods"
            )

        self.function = function

    def update(self, **params: Any) -> FollowupJob:
        """Update this instance with the provided new parameters.

        Valid parameters are those passed to the __init__ method.
        """
        if "name" in params and not self.is_legal_name(params["name"]):
            raise ValueError(
                "Argument 'name' should be a string containing only "
                "letters (at least one) and white spaces"
            )
        if "function" in params and not self.is_legal_function(
            params["function"]
        ):
            raise ValueError(
                "Argument 'function' should only contain letters "
                "(at least one), white spaces, commas or periods"
            )

        super().update(**params)

        if "name" in params:
            self.set_name(params["name"])

        if "function" in params:
            self.set_function(params["function"])

        return self

    def __repr__(self) -> str:
        """Provide a string representation for this instance."""
        return (
            f"Task("
            f"{super().__repr__()}, "
            f"name={self.name}, "
            f"function={self.function}"
            f")"
        )


class Period(model.BaseModel, model.ProjectElement):
    """Class representing a period over which a job is active.

    Jobs can be active for different intervals during different extents of
    time. The activity of a job can be controlled using this class.

    Attributes
    __________
    id          -- Period identifier
    period      -- Number of time units between activity
    unit        -- Unit of time of the interval (e.g., month)
    start       -- Start date of the job or period of activity
    end         -- End date for the period of activity (or none for indefinite
                    periods)
    """

    # Pylint doesn't recognize enum subclasses
    # pylint: disable=no-member
    @unique
    class TimeUnit(Enum):
        """Enumeration defining available interval time units."""

        WEEK = "week"
        MONTH = "month"
        YEAR = "year"

        @staticmethod
        def get_unit(unit: str) -> Period.TimeUnit:
            """Provide a time unit object from a string."""
            unit = unit.upper()

            if unit not in Period.TimeUnit.__members__:
                raise exceptions.IllegalArgumentException(
                    "Parameter 'unit' has an unknown value"
                )

            return Period.TimeUnit.__members__[unit]

        def __str__(self) -> str:
            """Convert instance to string."""
            return self._value_

        def __repr__(self) -> str:
            """Provide a string representation of this instance."""
            return self.__str__()

        # TODO: Define seconds property in enum
        @property
        def seconds(self) -> int:
            """Provide the amount of seconds in the unit."""
            return -1

    # pylint: enable=no-member

    # Definitions for the database tables  #
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    subscription_id = db.Column(db.Integer, db.ForeignKey(Subscription.id))
    task_id = db.Column(db.Integer, db.ForeignKey(Task.id))
    interval = db.Column(db.Integer, nullable=False)
    unit = db.Column(db.Enum(TimeUnit), nullable=False)
    start = db.Column(db.DateTime, nullable=False)
    end = db.Column(db.DateTime)

    # End database definitions

    def __init__(
        self,
        interval: int,
        unit: TimeUnit,
        *,
        start: date,
        end: Optional[date] = None,
    ) -> None:
        """Instantiate object of this class.

        Parameters
        __________
        interval    -- Interval between activities (in number of units)
        unit        -- Unit of the period interval
        start       -- Start date of the period of activity
        end         -- End date of the period of activity (none for indefinite)
        """
        if not Period.is_legal_interval(interval):
            raise exceptions.IllegalArgumentException(
                "Parameter 'interval' has an invalid value. Only positive "
                "integers are allowed"
            )

        if not Period.is_legal_unit(unit):
            raise exceptions.IllegalArgumentException(
                "Parameter 'unit' should not be None and of type "
                "Period.TimeUnit"
            )

        if not Period.is_legal_start(start):
            raise exceptions.IllegalArgumentException(
                "Parameter 'start' should not be None and of type "
                "datetime.date"
            )

        if not Period.is_legal_end(end):
            raise exceptions.IllegalArgumentException(
                "Parameter 'end' should be of type datetime.date or None"
            )

        if not Period.are_legal_dates(start, end):
            raise exceptions.IllegalArgumentException(
                "Parameter 'end' has invalid content. End date should be "
                "after start date"
            )

        self.interval = interval
        self.unit = unit
        self.start = start
        self.end = end

    @staticmethod
    def are_legal_dates(start: date, end: Optional[date]) -> bool:
        """Check whether the combination of dates is legal."""
        return (
            Period.is_legal_start(start)
            and Period.is_legal_end(end)
            and (end is None or end > start)
        )

    @staticmethod
    def is_legal_end(end: Optional[date]) -> bool:
        """Check whether the provided end date is valid for a period."""
        return end is None or isinstance(end, date)

    @staticmethod
    def is_legal_interval(interval: int) -> bool:
        """Check if the provided period is a valid interval length."""
        if not isinstance(interval, int):
            return False

        return interval > 0

    @staticmethod
    def is_legal_start(start: date) -> bool:
        """Check whether the provided start date is valid for a period."""
        return isinstance(start, date)

    @staticmethod
    def is_legal_unit(unit: Period.TimeUnit) -> bool:
        """Check whether the provided unit is a valid time unit."""
        return isinstance(unit, Period.TimeUnit)

    # TODO: Convert to python setter
    def set_period(self, period: int) -> None:
        """Set the period interval for this instance."""
        if not self.is_legal_interval(period):
            raise ValueError(
                "Argument 'period' has an invalid value. Only positive "
                "integers are allowed"
            )

        self.interval = period

    # TODO: Convert to python setter
    def set_unit(self, unit: TimeUnit) -> None:
        """Set the time unit of this period interval."""
        if not self.is_legal_unit(unit):
            raise ValueError(
                "Argument 'unit' should not be None and of type "
                "Period.TimeUnit"
            )

        self.unit = unit

    # TODO: Convert to python setter
    def set_start_date(self, start: date) -> None:
        """Set the start date for this period."""
        if not self.is_legal_start(start):
            raise ValueError(
                "Argument 'start_date' should not be None and of type "
                "datetime.date"
            )

    # TODO: Convert to python setter
    def set_end_date(self, end: date) -> None:
        """Set the end date for this period."""
        if not self.is_valid_end(end):
            raise ValueError(
                "Argument 'end_date' has invalid content. End date should be "
                "after start date"
            )

        self.end = end

    def get_unit(self) -> str:
        """Provide the unit of this period as a string."""
        return str(self.unit)

    def has_past(self, day: date) -> bool:
        """Check whether this period has passed.

        A period has passed if the current date is past its end date.

        Parameters
        __________
        day     -- Date for which to check if the period has passed

        Returns
        _______
        Return true if the end date of this period has past on the given day.
        False otherwise.
        """
        return self.end is not None and day > self.end

    def is_applicable(self, day: date) -> bool:
        """Check whether this period is active on the provided date.

        Parameters
        __________
        day     -- Date for which to check if the period is applicable

        Returns
        _______
        Return true if the period is active on the give day. False otherwise.
        """
        if day is None:
            return False

        after_start = day >= self.start
        before_end = self.end is None or day <= self.end
        return after_start and before_end

    def is_valid_end(self, end: Optional[date]) -> bool:
        """Check if the provided end date is legal for this instance."""
        if not self.is_legal_end(end):
            return False

        return end is None or end > self.start

    # Decorator used to call function when the object is loaded from the db
    @orm.reconstructor
    def on_load(self) -> None:
        """Convert datetimes to pure dates.

        When loaded from the database convert datetime object (with time) to
        date objects (no time).
        """
        if isinstance(self.start, datetime.datetime):
            self.start = self.start.date()
        if isinstance(self.end, datetime.datetime):
            self.end = self.end.date()

    def should_update(self, last_notification: date) -> bool:
        """Check whether an update is required.

        Check whether this period indicates that its parent job should notify
        its subscriber based on the last notification date and the current
        date.

        Parameters
        __________
        last_notification   -- Date on which the last notification was sent
                                about the parent job of this period

        Returns
        _______
        Return true if the subscriber should be updated on the current day.
        False otherwise.
        """
        if last_notification is None or last_notification < self.start:
            return self.first_ckeck_today()

        if self.is_applicable(last_notification):
            time_passed = relativedelta(
                date.today(), last_notification
            ).normalized()
            years, months = time_passed.years, time_passed.months

            if self.unit is Period.TimeUnit.YEAR:
                return years >= self.interval
            if self.unit is Period.TimeUnit.MONTH:
                return months + years * 12 >= self.interval
            if self.unit is Period.TimeUnit.WEEK:
                days = (date.today() - last_notification).days // 7
                return days >= self.interval

        return False

    def update(self, **params: Any) -> Period:
        """Update this instance with the provided new parameters.

        Valid parameters are those passed to the __init__ method.

        Returns
        _______
        Return reference to self.
        """
        # TODO: Complete error messages
        if "period" in params and not self.is_legal_interval(params["period"]):
            raise ValueError
        if "unit" in params and not self.is_legal_unit(params["unit"]):
            raise ValueError
        if "start_date" in params and not self.is_legal_start(
            params["start_date"]
        ):
            raise ValueError
        if "end_date" in params and (
            not self.is_legal_end(params["end_date"]) or self.end is not None
        ):
            raise ValueError

        if "period" in params:
            self.set_period(params["period"])

        if "unit" in params:
            self.set_unit(params["unit"])

        if "start_date" in params:
            self.set_start_date(params["start_date"])

        if "end_date" in params:
            self.set_end_date(params["end_date"])

        return self

    def __repr__(self) -> str:
        """Provide a string representation for this instance."""
        return (
            f"Period("
            f"period={self.interval}, "
            f"unit={repr(self.unit)}, "
            f"start={repr(self.start)}, "
            f"end={repr(self.end)})"
        )


def filter_dict(params: dict[str, Any], keys: list[str]) -> dict[str, Any]:
    """Filter the dictionary based on the provided keys.

    Parameters
    __________
    params -- Dictionary to be filtered
    keys   -- Keys to keep in the filtered dictionary

    Returns
    _______
    Return a dictionary with desired entries.
    """
    return {key: params["subscriber"][key] for key in keys}


T = TypeVar("T", bound=FollowupJob)


def construct_followup_work(constructor: Type[T], params: Dict[str, Any]) -> T:
    """Construct the appropriate follow-up work.

    Construct the correct class of followup work based on a factory method
    using the provided constructor and parameters.

    Parameters
    __________
    constructor -- Constructor function for the desired object class
    params      -- Parameters to pass to the constructor

    Returns
    _______
    An object subclassing FollowupWork.
    """
    params["subscriber"] = person.construct_person(
        person.get_constructor_from_type(params["subscriber"].pop("type")),
        params["subscriber"],
    )

    params["periods"] = list(map(lambda p: Period(**p), params["periods"]))

    return constructor(**params)
