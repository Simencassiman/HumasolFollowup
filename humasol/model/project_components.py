"""Module containing objects that compose a project.

A project object is composed of many smaller parts (project components).
This module defines all these components that are then mapped to a database
schema using the database object from the repository.

Classes:
Address         -- Street address of a project location
Coordinate      -- Geographical coordinates of a project location
Location        -- Class representing a physical location as indicated on a map
SDG             -- Enum class containing all SDG goals as defined by the UN
SdgDb           -- Wrapper class to store SDG enum values in the database
DataSource      -- Class containing all the information to access a project's
                    logged data
ProjectComponent        -- Abstract base class for elements of a project
EnergyProjectComponent  -- Abstract superclass of all component related to
                            an energy installation.
Source          -- Abstract class for electrical sources
Generator       -- Class representing an electrical generator
Grid            -- Class representing an electrical grid
PV              -- Class representing a PV installation
Storage         -- Abstract class for electrical storage systems
Battery         -- Class representing an electrical battery
Consumption     --
"""

# Python Libraries
from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, unique
from typing import Any, Dict, Optional, Union

# Local modules
from ..repository import db
from ..script import (
    api_manager_exists,
    data_manager_exists,
    report_manager_exists,
    same_category_managers,
)


# TODO: implement RSA
def encrypt(value: str) -> str:
    """Encrypt value using RSA."""
    if len(value) == 0:
        return value
    return value[1:] + value[0]


def decrypt(value: str) -> str:
    """Decrypt value using RSA."""
    if len(value) == 0:
        return value
    return value[-1] + value[:-1]


# TODO: Use composition of Address and Coordinates
class Location(db.Model):
    """Class representing a physical location in the world."""

    # Definitions for the database tables #
    project_id = db.Column(
        db.Integer, db.ForeignKey("project.id"), primary_key=True
    )
    street = db.Column(db.String)
    number = db.Column(db.Integer)
    place = db.Column(db.String, nullable=False, index=True)
    country = db.Column(db.String, nullable=False, index=True)
    longitude = db.Column(db.Float, nullable=False)
    latitude = db.Column(db.Float, nullable=False)

    # End database definitions #

    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-branches
    def __init__(
        self,
        latitude: float,
        longitude: float,
        country: str,
        place: str,
        street: Optional[str] = None,
        number: Optional[int] = None,
    ):
        """Instantiate location object.

        Arguments:
        latitude    -- Geographical coordinate
        longitude   -- Geographical coordinate
        country     -- Country of the location
        place       -- City or town (e.g., Leuven)
        street      -- Street name
        number      -- Street number
        """
        # TODO: call only validators instead of branching
        if street is not None and not isinstance(street, str):
            raise TypeError("Argument 'street' should be of type str or None")
        if not self.is_valid_street(street):
            raise ValueError(
                "Argument 'street' should contain only letters "
                "(at least one), spaces, hyphens, commas and "
                "periods"
            )

        if number is not None and not isinstance(number, int):
            raise TypeError("Argument 'number' should be of type int or None")
        if not self.is_valid_number(number):
            raise ValueError(
                "Argument 'number' should be a valid street "
                "number (positive, etc.)"
            )
        if street is None and number is not None:
            raise ValueError(
                "Argument 'number' should be None if 'street' is None"
            )

        if not isinstance(place, str):
            raise TypeError(
                "Argument 'place' should not be none and of type str"
            )
        if not self.is_valid_place(place):
            raise ValueError(
                "Argument 'place' should only contain letters "
                "(at least one), spaces, hyphens,"
                "commas and periods"
            )

        if not isinstance(country, str):
            raise TypeError(
                "Argument 'country' should not be None and of type str"
            )
        if not self.is_valid_country(country):
            raise ValueError(
                "Argument 'country' should only contain letters "
                "(at least one), space, hyphens,"
                "commas and periods"
            )

        if not isinstance(latitude, (float, int)):
            raise TypeError(
                "Argument 'latitude' should not be None and of type float"
            )
        if not self.is_valid_latitude(latitude):
            raise ValueError(
                "Argument 'latitude' should be in the range [-90,90]"
            )

        if not isinstance(longitude, (float, int)):
            raise TypeError(
                "Argument 'longitude' should not be None and of type float"
            )
        if not self.is_valid_longitude(longitude):
            raise ValueError(
                "Argument 'longitude' should be in the range [-180,180]"
            )

        self.street = street
        self.number = number
        self.place = place
        self.country = country
        self.longitude = longitude
        self.latitude = latitude

    # pylint: enable=too-many-branches
    # pylint: enable=too-many-arguments

    @staticmethod
    def is_valid_street(street: Optional[str]) -> bool:
        """Check whether the provided street name has valid characters."""
        # TODO: allow characters of type ü
        if street is None:
            return True
        if not isinstance(street, str):
            return False

        return (
            re.fullmatch(r"^[A-Z]([A-Z\s,.]-?)*", street.upper()) is not None
        )

    @staticmethod
    def is_valid_number(number: Optional[int]) -> bool:
        """Check whether the provided number is a valid street number."""
        if number is None:
            return True
        if not isinstance(number, int):
            return False
        return number > 0

    @staticmethod
    def is_valid_place(place: str) -> bool:
        """Check whether the provided place has valid characters."""
        # TODO: allow characters of type ü
        if not isinstance(place, str):
            return False

        return re.fullmatch(r"[A-Z]([A-Z\s,.]-?)*", place.upper()) is not None

    @staticmethod
    def is_valid_country(country: str) -> bool:
        """Check whether the provided country is a valid country."""
        # TODO: check from countries list
        if not isinstance(country, str):
            return False

        return (
            re.fullmatch(r"[A-Z]([A-Z\s,.]-?)*", country.upper()) is not None
        )

    @staticmethod
    def is_valid_latitude(latitude: float) -> bool:
        """Check whether the provided latitude is a valid coordinate value."""
        if not isinstance(latitude, (float, int)):
            return False

        return -90 <= latitude <= 90

    @staticmethod
    def is_valid_longitude(longitude: float) -> bool:
        """Check whether the provided longitude is a valid coordinate value."""
        if not isinstance(longitude, (float, int)):
            return False

        return -180 <= longitude <= 180

    # TODO: convert to python setter
    def set_street(self, street: Optional[str]) -> None:
        """Set the street name for this location."""
        if not self.is_valid_street(street):
            raise ValueError(
                "Argument 'street' should contain only letters "
                "(at least one), spaces, hyphens,"
                "commas and periods"
            )

        if street is None:
            self.number = None
        self.street = street

    # TODO: convert to python setter
    def set_number(self, number: Union[int, None]) -> None:
        """Set the street number for this location."""
        if not self.is_valid_number(number):
            raise ValueError(
                "Argument 'number' should be a valid street "
                "number (integer, positive, etc.)"
            )
        if self.street is None and number is not None:
            raise ValueError(
                "Argument 'number' should be None if the street is None"
            )

        self.number = number

    # TODO: convert to python setter
    def set_place(self, place: str) -> None:
        """Set the place for this location."""
        if not self.is_valid_place(place):
            raise ValueError(
                "Argument 'place' should be a string and only "
                "contain letters (at least one), spaces,"
                " hyphens, commas and periods"
            )

        self.place = place

    # TODO: convert to python setter
    def set_country(self, country: str) -> None:
        """Set the country for this location."""
        if not self.is_valid_country(country):
            raise ValueError(
                "Argument 'country' should be a string and only "
                "contain letters (at least one), space,"
                " hyphens, commas and periods"
            )

        self.country = country

    # TODO: convert to python setter
    def set_latitude(self, latitude: float) -> None:
        """Set the latitude coordinate for this location."""
        if not self.is_valid_latitude(latitude):
            raise ValueError(
                "Argument 'latitude' should be a float in "
                "the range [-90,90]"
            )

        self.latitude = latitude

    # TODO: convert to python setter
    def set_longitude(self, longitude: float) -> None:
        """Set the longitude coordinate for this location."""
        if not self.is_valid_longitude(longitude):
            raise ValueError(
                "Argument 'longitude' should be a float in "
                "the range [-180,180]"
            )

        self.longitude = longitude

    def update(self, **params: Any) -> Location:
        """Update this instance with the provided new parameters.

        Provided parameters should match those of the __init__ method.
        """
        if "street" in params:
            self.set_street(params["street"])

        if "number" in params:
            self.set_number(params["number"])

        if "place" in params:
            self.set_place(params["place"])

        if "country" in params:
            self.set_country(params["country"])

        if "latitude" in params:
            self.set_latitude(params["latitude"])

        if "longitude" in params:
            self.set_longitude(params["longitude"])

        return self

    def __repr__(self) -> str:
        """Provide a string representation of this instance."""
        return (
            f"Location("
            f"street={self.street}, "
            f"number={self.number}, "
            f"place={self.place}, "
            f"country={self.country}, "
            f"latitude={self.latitude}, "
            f"longitude={self.longitude}"
            f")"
        )


class SDG(Enum):
    """Enum containing all UN defined SDG goals."""

    GOAL_1 = "Goal 1"
    GOAL_2 = "Goal 2"
    GOAL_3 = "Goal 3"
    GOAL_4 = "Goal 4"
    GOAL_5 = "Goal 5"
    GOAL_6 = "Goal 6"
    GOAL_7 = "Goal 7"
    GOAL_8 = "Goal 8"
    GOAL_9 = "Goal 9"
    GOAL_10 = "Goal 10"
    GOAL_11 = "Goal 11"
    GOAL_12 = "Goal 12"
    GOAL_13 = "Goal 13"
    GOAL_14 = "Goal 14"
    GOAL_15 = "Goal 15"
    GOAL_16 = "Goal 16"
    GOAL_17 = "Goal 17"

    # pylint doesn't recognize enum subclasses (yet)
    # pylint: disable=no-member
    @property
    def goal_name(self) -> str:
        """Provide the name of the goal."""
        return self._value_

    # pylint: enable=no-member

    @property
    def number(self) -> Optional[str]:
        """Provide the number of the goal."""
        # if m := re.search(r"[0-9]{1,2}$", self.goal_name):
        #     return m[0]
        # return None
        return self.goal_name.split()[1]

    @property
    def icon(self) -> str:
        """Provide the URI for the goal icon."""
        return f'img/{self.value.lower().replace(" ", "_")}.svg'

    @property
    def link(self) -> str:
        """Provide the URL to the UN page explaining the goal."""
        return (
            f'https://sdgs.un.org/goals/{self.value.lower().replace(" ", "")}'
        )

    def __repr__(self) -> str:
        """Provide a string representation for the goal."""
        return self.goal_name


# Disable pylint complaint. Wrapper class is needed for the database.
# pylint: disable=too-few-public-methods
class SdgDB(db.Model):
    """Wrapper class for the SDG enum.

    The wrapper class is used to store the custom enum values in the database
    and allow them to be unique while having relations to the projects.
    """

    # Definitions for the database tables #
    __tablename__ = "sdg_db"

    sdg = db.Column(db.Enum(SDG), primary_key=True)

    # End of database definitions #

    def __init__(self, sdg):
        """Instantiate wrapper.

        Arguments:
        sdg     -- SDG enum value
        """
        self.sdg = sdg


# pylint: enable=too-few-public-methods


class DataSource(db.Model):
    """Class representing a project data source.

    Projects can log data about their operations. These get collected in some
    sort of data logger, which can vary from one project to the next. This
    class provides a generic data object to store the access address and
    credentials for such a source. It also contains information on what
    managers should be used to access it and to handle the incoming data.
    """

    # Definitions for database tables #
    project_id = db.Column(
        db.Integer, db.ForeignKey("project.id"), primary_key=True
    )
    source = db.Column(db.String, primary_key=True)
    user = db.Column(db.String)
    api_manager = db.Column(db.String, nullable=False)
    data_manager = db.Column(db.String, nullable=False)
    report_manager = db.Column(db.String, nullable=False)
    password = db.Column(db.String)
    token = db.Column(db.String)

    # End of database definitions #

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        source: str,
        api_manager: str,
        data_manager: str,
        report_manager: str,
        user: str = None,
        password: str = None,
        token: str = None,
    ):
        """Instantiate data source object.

        Arguments:
        source          -- Address from which to retrieve the data (e.g., URL)
        api_manager     -- Name of a class implementing the APIManager
                            interface
        data_manager    -- Name of a class implementing the DataManager
                            interface
        report_manager  -- Name of a class implementing the ReportManager
                            interface
        user            -- Username to access the data
        password        -- Password associated with the username to access the
                            data
        token           -- Authentication token to access the data. Some
                            sources can offer this as an alternative to
                            username + password authentication
        """
        if not isinstance(source, str):
            raise TypeError(
                "Argument 'source' should not be None and of type str"
            )
        if not self.is_valid_source(source):
            raise ValueError("Argument 'source' cannot be an empty string")

        if not self.is_valid_user(user):
            raise TypeError("Argument 'user' should be of type str or None")
        if not self.is_valid_password(password):
            raise TypeError(
                "Argument 'password' should be of type str or None"
            )
        if not self.is_valid_token(token):
            raise TypeError("Argument 'token' should be of type str or None")

        if not isinstance(api_manager, str):
            raise TypeError(
                "Argument 'api_manager' should not be None and of type str"
            )
        if not self.is_valid_api_manager(api_manager):
            raise ValueError("Argument 'api_manager' has an invalid value")

        if not isinstance(data_manager, str):
            raise TypeError(
                "Argument 'data_manager' should not be None and of type str"
            )
        if not self.is_valid_data_manager(data_manager):
            raise ValueError("Argument 'data_manager' has an invalid value")

        if not isinstance(report_manager, str):
            raise TypeError(
                "Argument 'report_manager' should not be None "
                "and of type str"
            )
        if not self.is_valid_report_manager(report_manager):
            raise ValueError("Argument 'report_manager' has an invalid value")

        if not same_category_managers(
            api_manager, data_manager, report_manager
        ):
            raise ValueError(
                "Arguments 'api_manager', 'data_manager' and "
                "'report_manager' "
                "should belong to the same project category"
            )

        self.source = source
        self.user = encrypt(user) if user is not None else user
        self.password = encrypt(password) if password is not None else password
        self.token = encrypt(token) if token is not None else token
        self.api_manager = api_manager
        self.data_manager = data_manager
        self.report_manager = report_manager

    # pylint: enable=too-many-arguments

    @staticmethod
    def is_valid_source(source: str) -> bool:
        """Check if the source is valid for a data source."""
        if not isinstance(source, str):
            return False

        return len(source) > 0

    @staticmethod
    def is_valid_user(user: Optional[str]) -> bool:
        """Check whether the provided user is a valid user string."""
        return user is None or isinstance(user, str)

    @staticmethod
    def is_valid_password(password: Optional[str]) -> bool:
        """Check whether the password is a valid password string."""
        return password is None or isinstance(password, str)

    @staticmethod
    def is_valid_token(token: Optional[str]) -> bool:
        """Check whether the provided token is a valid token string."""
        return token is None or isinstance(token, str)

    @staticmethod
    def is_valid_api_manager(manager: str) -> bool:
        """Check whether the provided manager is a valid API manager."""
        if not isinstance(manager, str):
            return False
        return api_manager_exists(manager)

    @staticmethod
    def is_valid_data_manager(manager: str) -> bool:
        """Check whether the provided manager is a valid data manager."""
        if not isinstance(manager, str):
            return False
        return data_manager_exists(manager)

    @staticmethod
    def is_valid_report_manager(manager: str) -> bool:
        """Check whether the provided manager is a valid report manager."""
        if not isinstance(manager, str):
            return False

        return report_manager_exists(manager)

    # TODO: convert to python setter
    def set_source(self, source: str) -> None:
        """Set the source for this data source."""
        if not self.is_valid_source(source):
            raise ValueError("Argument 'source' should be a non-empty string")

        self.source = source

    # TODO: convert to python setter
    def set_user(self, user: str) -> None:
        """Set the user for this data source."""
        if not self.is_valid_user(user):
            raise ValueError("Argument 'user' should be of type str or None")

        self.user = encrypt(user) if user is not None else user

    # TODO: convert to python setter
    def set_password(self, password: str) -> None:
        """Set the password for this data source."""
        if not self.is_valid_password(password):
            raise ValueError(
                "Argument 'password' should be of type str or None"
            )

        self.password = encrypt(password) if password is not None else password

    # TODO: convert to python setter
    def set_token(self, token: str) -> None:
        """Set the token for this data source."""
        if not self.is_valid_token(token):
            raise ValueError("Argument 'token' should be of type str or None")

        self.token = encrypt(token) if token is not None else token

    # TODO: create individual python setters
    def set_managers(
        self,
        *,
        api_manager: Union[str, None] = None,
        data_manager: Union[str, None] = None,
        report_manager: Union[str, None] = None,
    ) -> None:
        """Set the managers for this data source."""
        if api_manager is not None and not self.is_valid_api_manager(
            api_manager
        ):
            raise ValueError("Argument 'api_manager' has an invalid value")
        if data_manager is not None and not self.is_valid_data_manager(
            data_manager
        ):
            raise ValueError("Argument 'data_manager' has an invalid value")
        if report_manager is not None and not self.is_valid_report_manager(
            report_manager
        ):
            raise ValueError("Argument 'report_manager' has an invalid value")

        api = api_manager if api_manager is not None else self.api_manager
        data = data_manager if data_manager is not None else self.data_manager
        report = (
            report_manager
            if report_manager is not None
            else self.report_manager
        )
        if not same_category_managers(api, data, report):
            raise ValueError(
                "Arguments 'api_manager', 'data_manager' "
                "and 'report_manager' "
                "should belong to the same project category"
            )

        if api_manager is not None:
            self.api_manager = api_manager

        if data_manager is not None:
            self.data_manager = data_manager

        if report_manager is not None:
            self.report_manager = report_manager

    def get_credentials(self) -> Dict[str, Any]:
        """Provide the access and credentials for this data source.

        Provide a dictionary of the form (key -- value):
        source      -- data source address
        user        -- username
        password    -- password
        token       -- token
        """
        creds: Dict[str, Any] = {
            "source": self.source,
            "user": decrypt(self.user) if self.user is not None else self.user,
            "password": decrypt(self.password)
            if self.password is not None
            else self.password,
            "token": decrypt(self.token)
            if self.token is not None
            else self.token,
        }

        return creds

    def update(self, **params: Any) -> DataSource:
        """Update this instance with the provided new parameters.

        Provided parameters should match those of the __init__ method.
        """
        if "source" in params:
            self.set_source(params["source"])

        if "user" in params:
            self.set_user(params["user"])

        if "password" in params:
            self.set_password(params["password"])

        if "token" in params:
            self.set_token(params["token"])

        api_manager = (
            params["api_manager"] if "api_manager" in params else None
        )
        data_manager = (
            params["data_manager"] if "data_manager" in params else None
        )
        report_manager = (
            params["report_manager"] if "report_manager" in params else None
        )
        self.set_managers(
            api_manager=api_manager,
            data_manager=data_manager,
            report_manager=report_manager,
        )

        return self

    def __repr__(self) -> str:
        """Provide a string representation of this instance."""
        return (
            f"DataSource("
            f"source={self.source}, "
            f"user={self.user}, "
            f"password={self.password}, "
            f"token={self.token}, "
            f"api_manager={self.api_manager}, "
            f"data_manager={self.data_manager}, "
            f"report_manager={self.report_manager}"
            f")"
        )


@dataclass
class ProjectComponent(ABC):
    """Abstract base class for a project component.

    Project components are elements specific to a certain project domain
    that have been used to complete the project. Components with relevant
    states that provide interesting data can be represented as a subclass.
    (E.g., energy components are used to build a project of the energy
    category. Interesting components might be the grid or a battery.)
    These objects can be used during the reporting operations to provide
    meaningful context or comparisons in the analyses.
    """

    def as_dict(self) -> Dict[str, Any]:
        """Provide the contents of this instance as a dictionary."""
        return self.__dict__

    @abstractmethod
    def update(self, **params: Any) -> ProjectComponent:
        """Update this instance with the provided new parameters."""


# TODO: add proper subclasses


class Battery(ProjectComponent):
    """Class representing an electric battery.

    Class containing certain attributes of an electric battery that can be
    configured for each project:
    capacity    -- Electrical capacity of the battery (Ah)
    type        -- Type of electrical battery (e.g., Lithium Ion)
    base_soc    -- Base state of charge
    min_soc     -- Minimally allowed state of charge
    max_soc     -- Maximally allowed state of charge
    """

    LABEL = "battery"

    def __init__(
        self,
        capacity: float,
        b_type: BatteryType,
        base_soc: float,
        min_soc: float = 50,
    ):
        """Instantiate a battery object.

        Arguments:
        capacity    -- Electrical capacity of the battery (Ah)
        b_type      -- Type of electrical battery (e.g., Lithium Ion).
                        Value should be from Battery.BatteryType enum
        base_soc    -- Base state of charge
        min_soc     -- Minimally allowed state of charge
        max_soc     -- Maximally allowed state of charge
        """
        if not isinstance(capacity, (float, int)):
            raise TypeError(
                "Argument 'capacity' should not be None and of type float"
            )
        if not self.is_valid_capacity(capacity):
            raise ValueError("Argument 'capacity' should be non-negative")

        if not self.is_valid_battery_type(b_type):
            raise TypeError(
                "Argument 'b_type' should not be None and of "
                "type BatteryType"
            )

        if not isinstance(base_soc, (float, int)):
            raise TypeError(
                "Argument 'base_soc' should not be None and of type float"
            )
        if not self.is_valid_base_soc(base_soc):
            raise ValueError(
                "Argument 'base_soc' should be in the range [min_soc,100]"
            )

        if not isinstance(min_soc, (float, int)):
            raise TypeError(
                "Argument 'min_soc' should not be None and of type float"
            )
        if not self.is_valid_min_soc(min_soc):
            raise ValueError(
                "Argument 'min_soc' should be in the range [0,base_soc]"
            )

        if base_soc < min_soc:
            raise ValueError("Argument 'base_soc' cannot be below 'min_soc'")

        self.capacity = capacity
        self.base_soc = base_soc
        self.min_soc = min_soc
        self.type = b_type

    @staticmethod
    def is_valid_capacity(capacity: float) -> bool:
        """Check whether the provided capacity is a legal capacity."""
        if not isinstance(capacity, (float, int)):
            return False
        return capacity >= 0

    @staticmethod
    def is_valid_battery_type(b_type: BatteryType) -> bool:
        """Check whether the provided battery type is a legal type."""
        return isinstance(b_type, Battery.BatteryType)

    @staticmethod
    def is_valid_base_soc(soc: float) -> bool:
        """Check whether the provided soc is a valid base state of charge."""
        if not isinstance(soc, (float, int)):
            return False
        return 0 <= soc <= 100

    @staticmethod
    def is_valid_min_soc(soc: float) -> bool:
        """Check if the provided soc is a valid minimal state of charge."""
        if not isinstance(soc, (float, int)):
            return False
        return 0 <= soc <= 100

    def set_capacity(self, capacity: float) -> None:
        """Check if the provided soc is a valid maximal state of charge."""
        if not self.is_valid_capacity(capacity):
            raise ValueError(
                "Argument 'capacity' should be a non-negative float"
            )

        self.capacity = capacity

    # TODO: convert to python setter
    def set_base_soc(self, soc: float) -> None:
        """Set the base state of charge of this battery."""
        if not self.is_valid_base_soc(soc):
            raise ValueError(
                "Argument 'base_soc' should be a float in "
                "the range [min_soc,1]"
            )
        if soc < self.min_soc:
            raise ValueError(
                "Argument 'base_soc' should be a float in the "
                "range [min_soc,1]"
            )

        self.base_soc = soc

    # TODO: convert to python setter
    def set_min_soc(self, soc: float) -> None:
        """Set minimally allowed state of charge of this battery."""
        if not self.is_valid_min_soc(soc):
            raise ValueError(
                "Argument 'min_soc' should be a float in the "
                "range [0,base_soc]"
            )
        if soc > self.base_soc:
            raise ValueError(
                "Argument 'min_soc' should be a float in the "
                "range [0,base_soc]"
            )

        self.min_soc = soc

    # TODO: add setter for max_soc

    # TODO: convert to python setter
    def set_type(self, b_type: BatteryType) -> None:
        """Set the type of this battery."""
        if not self.is_valid_battery_type(b_type):
            raise ValueError(
                "Argument 'b_type' should not be None and of "
                "type BatteryType"
            )

        self.type = b_type

    def as_dict(self) -> Dict[str, Dict[str, Any]]:
        """Provide dictionary representation of this battery.

        Provide a dictionary representation of this object where the keys are
        the names of the attributes and the values are the attribute values.
        """
        data = super().as_dict()
        data["type"] = str(data["type"])
        return {self.LABEL: data}

    def update(self, **params: Any) -> Battery:
        """Update this instance with the provided new parameters.

        Provided parameters should match those of the __init__ method.
        """
        if "capacity" in params:
            self.set_capacity(params["capacity"])

        if "base_soc" in params and "min_soc" in params:
            base_soc = params["base_soc"]
            min_soc = params["min_soc"]

            # Allow to lower minimal state of charge before lowering base
            # state of charge below the previous minimal level, otherwise it
            # might be impossible to change to new values.
            # Consider: change from (base, min) = (80,70) to (50, 20)
            #     is impossible when always setting the base first,
            #     the setter won't allow going under the minimal state of
            #     charge.
            # Consider: change from (50, 20) to (80, 70) is impossible when
            #     always setting minimal state of charge first, the setter
            #     won't allow to go above the base state of charge.
            if base_soc < self.min_soc:
                self.set_min_soc(min_soc)
                self.set_base_soc(base_soc)
            else:
                self.set_base_soc(base_soc)
                self.set_min_soc(min_soc)
        elif "base_soc" in params:
            self.set_base_soc(params["base_soc"])
        elif "min_soc" in params:
            self.set_min_soc(params["min_soc"])

        if "type" in params:
            self.set_type(params["type"])

        return self

    def __repr__(self) -> str:
        """Provide string representation of this instance."""
        return (
            f"Battery("
            f"capacity={self.capacity}, "
            f"base_soc={self.base_soc}, "
            f"min_soc={self.min_soc}, "
            f"type={repr(self.type)}"
            f")"
        )

    @unique
    class BatteryType(Enum):
        """Enum class for battery types."""

        LITHIUM_ION = "Lithium ion"
        LEAD_ACID = "Lead acid"

        @staticmethod
        def from_str(label):
            """Provide enum element from the provided label string."""
            if label in (
                "Lithium ion",
                "LITHIUM_ION",
                "BatteryType.LITHIUM_ION",
            ):
                return Battery.BatteryType.LITHIUM_ION
            if label in ("Lead acid", "LEAD_ACID", "BatteryType.LEAD_ACID"):
                return Battery.BatteryType.LEAD_ACID

            raise NotImplementedError

        # pylint doesn't recognise subclass of enum, disable the error
        # pylint: disable=no-member
        def __repr__(self) -> str:
            """Provide a string representation of the element."""
            return self._value_

        def __str__(self) -> str:
            """Provide a string version of the element."""
            return self._value_

        # pylint: enable=no-member


class Grid(ProjectComponent):
    """Class representing an electric grid.

    Class containing certain attributes of an electric grid that can be
    configured for each project:
    energy_cost     -- Price for buying electricity (€/kWh)
    blackout_threshold  -- Power level at which the grid is considered to fail
    injection_cost  -- Price (or remuneration if negative) for injecting
                        electricity back into the grid (if available)
    """

    LABEL = "grid"

    def __init__(
        self,
        energy_cost: float,
        blackout_threshold: Optional[float] = None,
        injection_cost: Optional[float] = None,
    ):
        """Instantiate grid object.

        Arguments:
        energy_cost     -- Price for buying electricity (€/kWh)
        blackout_threshold  -- Power level at which the grid is considered
                                to fail
        injection_cost  -- Price (or remuneration if negative) for injecting
                            electricity back into the grid (if available)
        """
        if not isinstance(energy_cost, (float, int)):
            raise TypeError(
                "Argument 'energy_cost' should not be None and "
                "of type float"
            )
        if not self.is_valid_cost(energy_cost):
            raise ValueError(
                "Argument 'energy_cost' has an illegal value. "
                "Costs should be non-negative"
            )

        if blackout_threshold is not None and not isinstance(
            blackout_threshold, (float, int)
        ):
            raise TypeError(
                "Argument 'blackout_threshold' should be of "
                "type float or None"
            )
        if not self.is_valid_blackout_threshold(blackout_threshold):
            raise ValueError(
                "Argument 'blackout_threshold' has an illegal "
                "value. Should be non-negative"
            )

        if injection_cost is not None and not isinstance(
            injection_cost, (float, int)
        ):
            raise TypeError(
                "Argument 'injection_cost' should not be None "
                "and of type float"
            )
        if not self.is_valid_injection_price(injection_cost):
            raise ValueError(
                "Argument 'injection_cost' has an illegal value. "
                "Costs should be non-negative"
            )

        self.energy_cost = energy_cost
        self.blackout_threshold = blackout_threshold
        self.injection_cost = injection_cost

    @staticmethod
    def is_valid_cost(cost: float) -> bool:
        """Check whether the provided cost is a valid cost for a grid.

        A cost should be a non-negative float or integer.
        """
        if not isinstance(cost, (float, int)):
            return False
        return cost >= 0

    @staticmethod
    def is_valid_blackout_threshold(threshold: Optional[float]) -> bool:
        """Check whether the provided threshold is valid for blackouts.

        A blackout threshold should be a non-negative float or integer.
        """
        if threshold is None:
            return True
        if not isinstance(threshold, (float, int)):
            return False
        return threshold >= 0

    @staticmethod
    def is_valid_injection_price(cost: Optional[float]) -> bool:
        """Check whether the provided cost is a valid injection price.

        An injection price should be a float or integer.
        """
        if cost is None:
            return True

        # for now don't enforce sign,
        # maybe somewhere you have to pay for injection
        return isinstance(cost, (float, int))

    # TODO: convert to python setter
    def set_energy_cost(self, cost: float) -> None:
        """Set the cost for energy (€/kWh) of this grid."""
        if not self.is_valid_cost(cost):
            raise ValueError(
                "Argument 'energy_cost' has an illegal value. "
                "Costs should be a non-negative float"
            )

        self.energy_cost = cost

    # TODO: convert to python setter
    def set_blackout_threshold(self, threshold: float) -> None:
        """Set the blackout threshold for this grid."""
        if not self.is_valid_blackout_threshold(threshold):
            raise ValueError(
                "Argument 'blackout_threshold' has an illegal "
                "value. Should be a non-negative float"
            )

        self.blackout_threshold = threshold

    # TODO: convert to python setter
    def set_injection_cost(self, cost: float) -> None:
        """Set the injection cost (€/kWh) for this grid."""
        if not self.is_valid_injection_price(cost):
            raise ValueError(
                "Argument 'injection_cost' has an illegal value. "
                "Costs should be a float"
            )

        self.injection_cost = cost

    def as_dict(self) -> Dict[str, Dict[str, Any]]:
        """Provide a dictionary representing this instance.

        The provided dictionary contains the attributes of this object as keys
        with associated values.
        """
        return {self.LABEL: super().as_dict()}

    def update(self, **params: Any) -> Grid:
        """Update this instance with the provided new parameters.

        Valid parameters are those passed to the __init__ method.
        """
        if "energy_cost" in params:
            self.set_energy_cost(params["energy_cost"])

        if "blackout_threshold" in params:
            self.set_blackout_threshold(params["blackout_threshold"])

        if "injection_cost" in params:
            self.set_injection_cost(params["injection_cost"])

        return self

    def __repr__(self) -> str:
        """Provide a string representation for this instance."""
        return (
            f"Grid("
            f"energy_cost={self.energy_cost}, "
            f"blackout_threshold={self.blackout_threshold}, "
            + f"injection_cost={self.injection_cost}"
            f")"
        )
