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
Grid            -- Class representing an electrical grid
PV              -- Class representing a PV installation
Generator       -- Class representing an electrical generator
Storage         -- Abstract class for electrical storage systems
Battery         -- Class representing an electrical battery
ConsumptionComponent    -- Class representing an electrical consumer element
"""

# Python Libraries
from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, unique
from typing import Any, Optional, Union

# Local modules
from ..repository import db
from ..script import same_category_managers


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


class Address(db.Model):
    """Class representing an address of a physical place.

    Attributes
    __________
    street  -- Street name
    number  -- Street number
    place   -- Town or city of the spot
    country -- Country in which the spot can be found
    """

    # Definitions for database tables #
    street = db.Column(db.String)
    number = db.Column(db.Integer)
    place = db.Column(db.String, nullable=False, index=True)
    country = db.Column(db.String, nullable=False, index=True)

    # End database definitions #

    # TODO: Add setters

    def __init__(
        self,
        place: str,
        country: str,
        street: Optional[str] = None,
        number: Optional[int] = None,
    ) -> None:
        """Instantiate an address object.

        Parameters
        __________
        street  -- Street name
        number  -- Street number
        place   -- Town or city of the spot
        country -- Country in which the spot can be found
        """
        if not Address.is_legal_street(street):
            raise ValueError(
                "Parameter 'street' should be of type str or None."
                " It should contain only letters (at least one), spaces, "
                "hyphens, commas and periods"
            )

        if street is None and number is not None:
            raise ValueError("Cannot have a street number without a street")

        if not Address.is_legal_number(number):
            raise ValueError(
                "Parameter 'number' should be a positive integer or None"
            )

        if not Address.is_legal_place(place):
            raise ValueError(
                "Parameter 'place' should not be none and of type str. It "
                "should only contain letters (at least one), spaces, hyphens,"
                "commas and periods"
            )

        if not Address.is_legal_country(country):
            raise ValueError(
                "Parameter 'country' should not be None and of type str. It "
                "should only contain letters (at least one), space, hyphens,"
                "commas and periods"
            )

        self.street = street
        self.number = number
        self.place = place
        self.country = country

    @staticmethod
    def is_legal_country(country: str) -> bool:
        """Check whether the provided country is a legal country."""
        # TODO: check from countries list
        if not isinstance(country, str):
            return False

        return (
            re.fullmatch(r"[A-Z]([A-Z\s,.]-?)*", country.upper()) is not None
        )

    @staticmethod
    def is_legal_number(number: Optional[int]) -> bool:
        """Check whether the provided number is a legal street number."""
        return number is None or (isinstance(number, int) and number > 0)

    @staticmethod
    def is_legal_place(place: str) -> bool:
        """Check whether the provided place is a legal place name."""
        # TODO: allow characters of type ü
        if not isinstance(place, str):
            return False

        return re.fullmatch(r"[A-Z]([A-Z\s,.]-?)*", place.upper()) is not None

    @staticmethod
    def is_legal_street(street: Optional[str]) -> bool:
        """Check whether the provided street is a legal street name."""
        return street is None or (
            isinstance(street, str)
            and re.fullmatch(r"^[A-Z]([A-Z\s,.]-?)*", street.upper())
            is not None
        )

    def update(self, params: dict[str, Any]) -> Address:
        """Update this instance with the provided new parameters.

        Valid parameters are those passed to the __init__ method.

        Returns
        _______
        Return reference to self.
        """
        if street_present := "street" in params:
            if not Address.is_legal_street(params["street"]):
                raise ValueError(
                    "Parameter 'street' should be of type str or None."
                    " It should contain only letters (at least one), spaces, "
                    "hyphens, commas and periods"
                )

            if (
                not params["street"]
                and "number" in params
                and params["number"]
            ):
                raise ValueError(
                    "Cannot have a street number without a street"
                )

        if (
            number_present := "number" in params
        ) and not Address.is_legal_number(params["number"]):
            raise ValueError(
                "Parameter 'number' should be a positive integer or None"
            )

        if (place_present := "place" in params) and not Address.is_legal_place(
            params["place"]
        ):
            raise ValueError(
                "Parameter 'place' should not be none and of type str. It "
                "should only contain letters (at least one), spaces, hyphens,"
                "commas and periods"
            )

        if (
            country_present := "country" in params
        ) and not Address.is_legal_country(params["country"]):
            raise ValueError(
                "Parameter 'country' should not be None and of type str. It "
                "should only contain letters (at least one), space, hyphens,"
                "commas and periods"
            )

        if street_present:
            self.street = params["street"]

        if number_present:
            self.number = params["number"]

        if self.street is None:
            self.number = None

        if place_present:
            self.place = params["place"]

        if country_present:
            self.country = params["country"]

        return self


class Coordinates(db.Model):
    """Class representing geographical coordinates of a physical place.

    Attributes
    __________
    latitude
    longitude
    """

    # Definitions for database tables #
    longitude = db.Column(db.Float, nullable=False)
    latitude = db.Column(db.Float, nullable=False)

    # End database definitions #

    def __init__(self, latitude: float, longitude: float) -> None:
        """Instantiate coordinates object.

        Parameters
        __________
        latitude    -- Geographical coordinate between -90º and 90º
        longitude   -- Geographical coordinate between -180º and 180
        """
        if not Coordinates.is_legal_latitude(latitude):
            raise ValueError(
                "Parameter 'latitude' should not be None and of type "
                "float. It should be in the range from -90º to 90º"
            )

        if not Coordinates.is_legal_longitude(longitude):
            raise ValueError(
                "Parameter 'longitude' should not be none and of type "
                "float. It should be in the range from -180º to 180"
            )

        self.latitude = latitude
        self.longitude = longitude

    @staticmethod
    def is_legal_latitude(latitude: float) -> bool:
        """Check whether the provided coordinate is a legal latitude."""
        return isinstance(latitude, (float, int)) and -90 <= latitude <= 90

    @staticmethod
    def is_legal_longitude(longitude: float) -> bool:
        """Check whether the provided coordinate is a legal longitude."""
        return isinstance(longitude, (float, int)) and -180 <= longitude <= 180

    def update(self, params: dict[str, Any]) -> Coordinates:
        """Update this instance with the provided new parameters.

        Valid parameters are those passed to the __init__ method.

        Returns
        _______
        Return reference to self.
        """
        if (
            latitude_present := "latitude" in params
        ) and not Coordinates.is_legal_latitude(params["latitude"]):
            raise ValueError(
                "Parameter 'latitude' should not be None and of type "
                "float. It should be in the range from -90º to 90º"
            )

        if (
            longitude_present := "longitude" in params
        ) and not Coordinates.is_legal_longitude(params["longitude"]):
            raise ValueError(
                "Parameter 'longitude' should not be none and of type "
                "float. It should be in the range from -180º to 180"
            )

        if latitude_present:
            self.latitude = params["latitude"]
        if longitude_present:
            self.longitude = params["longitude"]

        return self


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
    ) -> None:
        """Instantiate location object.

        Parameters
        __________
        latitude    -- Geographical coordinate
        longitude   -- Geographical coordinate
        country     -- Country of the location
        place       -- City or town (e.g., Leuven)
        street      -- Street name
        number      -- Street number
        """
        if not Address.is_legal_street(street):
            raise ValueError(
                "Parameter 'street' should be of type str or None."
                " It should contain only letters (at least one), spaces, "
                "hyphens, commas and periods"
            )

        if street is None and number is not None:
            raise ValueError("Cannot have a street number without a street")

        if not Address.is_legal_number(number):
            raise ValueError(
                "Parameter 'number' should be a positive integer or None"
            )

        if not Address.is_legal_place(place):
            raise ValueError(
                "Parameter 'place' should not be none and of type "
                "str. It should only contain letters (at least one), spaces, "
                "hyphens, commas and periods"
            )

        if not Address.is_legal_country(country):
            raise ValueError(
                "Parameter 'country' should not be None and of type "
                "str. It should only contain letters (at least one), space, "
                "hyphens, commas and periods"
            )

        if not isinstance(latitude, (float, int)):
            raise TypeError(
                "Argument 'latitude' should not be None and of type float"
            )
        if not self.is_valid_latitude(latitude):
            raise ValueError(
                "Argument 'latitude' should be in the range [-90,90]"
            )

        if not Coordinates.is_legal_latitude(latitude):
            raise ValueError(
                "Parameter 'latitude' should not be None and of type "
                "float. It should be in the range from -90º to 90º"
            )

        if not Coordinates.is_legal_longitude(longitude):
            raise ValueError(
                "Parameter 'longitude' should not be none and of type "
                "float. It should be in the range from -180º to 180"
            )

        self.street = street
        self.number = number
        self.place = place
        self.country = country
        self.longitude = longitude
        self.latitude = latitude

    # pylint: enable=too-many-branches
    # pylint: enable=too-many-arguments

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
    def set_number(self, number: Optional[int]) -> None:
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

    def __init__(self, sdg) -> None:
        """Instantiate wrapper.

        Arguments:
        role     -- SDG enum value
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

    Attributes
    __________
    project_id  -- Identifier of the project it belongs to
    source      -- Internet address of the data source
    user        -- Username for authentication with the data service
    password    -- Matching password for authentication
    token       -- Token for automatic authentication with the data service
    api_manager -- Name of class to use for interfacing with the data API
    data_manager    -- Name of class to use for data manipulation
    report_manager  -- Name of class for report generation
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
        user: Optional[str] = None,
        password: Optional[str] = None,
        token: Optional[str] = None,
    ) -> None:
        """Instantiate data source object.

        Parameters
        __________
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
        if not DataSource.is_legal_source(source):
            raise ValueError(
                "Parameter 'source' should be a non-empty string."
            )

        if not DataSource.is_legal_user(user):
            raise ValueError("Parameter 'user' should be of type str or None")

        if not DataSource.is_legal_password(password):
            raise ValueError(
                "Parameter 'password' should be of type str or None"
            )

        if not DataSource.is_legal_token(token):
            raise ValueError("Parameter 'token' should be of type str or None")

        if not DataSource.are_legal_managers(
            api_manager, data_manager, report_manager
        ):
            raise ValueError(
                "Parameters 'api_manager', 'data_manager' and "
                "'report_manager' should be of type string and "
                "reference existing classes of the same project category"
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
    def are_legal_managers(
        api_manager: str, data_manager: str, report_manager: str
    ) -> bool:
        """Check if the provided managers and their combination are legal."""
        return same_category_managers(
            api_manager, data_manager, report_manager
        )

    @staticmethod
    def is_legal_password(password: Optional[str]) -> bool:
        """Check whether the password is a legal password string."""
        return password is None or isinstance(password, str)

    @staticmethod
    def is_legal_source(source: str) -> bool:
        """Check if the source is legal for a data source."""
        return isinstance(source, str) and len(source) > 0

    @staticmethod
    def is_legal_token(token: Optional[str]) -> bool:
        """Check whether the provided token is a legal token string."""
        return token is None or isinstance(token, str)

    @staticmethod
    def is_legal_user(user: Optional[str]) -> bool:
        """Check whether the provided user is a legal user string."""
        return user is None or isinstance(user, str)

    # TODO: convert to python setter
    def set_source(self, source: str) -> None:
        """Set the source for this data source."""
        if not self.is_legal_source(source):
            raise ValueError("Argument 'source' should be a non-empty string")

        self.source = source

    # TODO: convert to python setter
    def set_user(self, user: str) -> None:
        """Set the user for this data source."""
        if not self.is_legal_user(user):
            raise ValueError("Argument 'user' should be of type str or None")

        self.user = encrypt(user) if user is not None else user

    # TODO: convert to python setter
    def set_password(self, password: str) -> None:
        """Set the password for this data source."""
        if not self.is_legal_password(password):
            raise ValueError(
                "Argument 'password' should be of type str or None"
            )

        self.password = encrypt(password) if password is not None else password

    # TODO: convert to python setter
    def set_token(self, token: str) -> None:
        """Set the token for this data source."""
        if not self.is_legal_token(token):
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

    def get_credentials(self) -> dict[str, Any]:
        """Provide the access and credentials for this data source.

        Returns
        _______
        Return a dictionary of the form (key -- value):
        source      -- data source address
        user        -- username
        password    -- password
        token       -- token
        """
        creds: dict[str, Any] = {
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

    def update(self, params: dict[str, Any]) -> DataSource:
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


# ------------------------------
# ----- Project components -----
# ------------------------------


@dataclass
class ProjectComponent(ABC):
    """Interface for a project component.

    Project components are elements specific to a certain project domain
    that have been used to complete the project. Components with relevant
    states that provide interesting data can be represented as a class
    implementing this interface.
    (E.g., energy components are used to build a project of the energy
    category. Interesting components might be the grid or a battery.)
    These objects can be used during the reporting operations to provide
    meaningful context or comparisons in the analyses.
    """

    def as_dict(self) -> dict[str, Any]:
        """Provide the contents of this instance as a dictionary."""
        return self.__dict__ | {"label": self.LABEL}

    # Capital case attribute doesn't conform to snake-casing
    # Used here because it represents a class constant that has to be defined
    # pylint: disable=invalid-name
    @property
    @abstractmethod
    def LABEL(self) -> str:
        """Provide identifying label for a component."""

    # pylint: enable=invalid-name

    @abstractmethod
    def update(self, params: dict[str, Any]) -> ProjectComponent:
        """Update this instance with the provided new parameters."""


# -------------------------------------
# ----- Energy project components -----
# -------------------------------------

# TODO: add proper subclasses
class EnergyProjectComponent(ProjectComponent, ABC):
    """Abstract superclass of all components related to an EnergyProject.

    Attributes
    __________
    power       -- Power rating of the component
    is_primary  -- Whether this is a primary component, opposed to
                    backup or auxiliary
    """

    def __init__(self, power: float, is_primary: bool = True) -> None:
        """Instantiate EnergyProjectComponent.

        Parameters
        __________
        power       -- Power rating of the component
        is_primary  -- Whether this is a primary component, opposed to
                        backup or auxiliary. Default: primary
        """
        if not EnergyProjectComponent.is_legal_power(power):
            raise ValueError(
                "Parameter 'power' should be a non-negative float"
            )

        if not EnergyProjectComponent.is_legal_primary_flag(is_primary):
            raise ValueError("Parameter 'is_primary' should be of type bool")

        super().__init__()

        self.power = power
        self.is_primary = is_primary

    @staticmethod
    def is_legal_power(power: float) -> bool:
        """Check if the provided power is legal for an energy component."""
        return isinstance(power, (float, int)) and power >= 0

    @staticmethod
    def is_legal_primary_flag(flag: bool) -> bool:
        """Check whether this is a legal flag."""
        return isinstance(flag, bool)

    def update(self, params: dict[str, Any]) -> EnergyProjectComponent:
        """Update this instance with the provided new parameters.

        Parameters
        __________
        params  -- Parameters with new values. Valid parameters are those
                    passed to the __init__ method

        Returns
        _______
        Return reference to self
        """
        if (
            power_present := "power" in params
        ) and not EnergyProjectComponent.is_legal_power(params["power"]):
            raise ValueError(
                "Parameter 'power' should be a non-negative float"
            )

        if (
            primary_present := "is_primary" in params
        ) and EnergyProjectComponent.is_legal_primary_flag(
            params["is_primary"]
        ):
            raise ValueError("Parameter 'is_primary' should be of type bool")

        if power_present:
            self.power = params["power"]
        if primary_present:
            self.is_primary = params["is_primary"]

        return self


# -----------------------------
# ----- Source components -----
# -----------------------------


class SourceComponent(EnergyProjectComponent, ABC):
    """Abstract class representing electrical sources.

    Attributes
    __________
    power       -- Power rating of the component
    is_primary  -- Whether this is a primary component, opposed to
                    backup or auxiliary
    price   -- Price of electricity from this source (€/kWh)
    """

    def __init__(self, price: float, **kwargs: Any) -> None:
        """Instantiate object of this class.

        Parameters
        __________
        price   -- Price of electricity from this source (€/kWh)
        kwargs  -- Additional parameters for the superclasses
        """
        if not SourceComponent.is_legal_price(price):
            raise ValueError(
                "Parameter 'price' should be a non-negative float."
            )

        super().__init__(**kwargs)

        self.price = price

    @staticmethod
    def is_legal_price(price: float) -> bool:
        """Check whether the provided price is a legal energy cost."""
        return isinstance(price, (float, int)) and price >= 0

    def update(self, params: dict[str, Any]) -> SourceComponent:
        """Update this instance with the provided new parameters.

        Parameters
        __________
        params  -- Parameters with new values. Valid parameters are those
                    passed to the __init__ method

        Returns
        _______
        Return reference to self
        """
        if (
            price_present := "price" in params
        ) and not SourceComponent.is_legal_price(params["price"]):
            raise ValueError(
                "Parameter 'price' should be a non-negative float."
            )

        super().update(params)

        if price_present:
            self.price = params["price"]

        return self


class Grid(SourceComponent):
    """Class representing an electric grid.

    Class containing certain attributes of an electric grid that can be
    configured for each project.

    Attributes
    __________
    power       -- Power rating of the component
    is_primary  -- Whether this is a primary component, opposed to
                    backup or auxiliary
    price       -- Price of electricity from this source (€/kWh)
    blackout_threshold  -- Power level at which the grid is considered to fail
    injection_price  -- Price (or remuneration if negative) for injecting
                        electricity back into the grid (if available)
    """

    LABEL = "grid"

    def __init__(
        self,
        blackout_threshold: Optional[float] = None,
        injection_price: Optional[float] = None,
        **kwargs: Any,
    ):
        """Instantiate grid object.

        Parameters
        __________
        energy_cost     -- Price for buying electricity (€/kWh)
        blackout_threshold  -- Power level at which the grid is considered
                                to fail
        injection_price  -- Price (or remuneration if negative) for injecting
                            electricity back into the grid (if available)
        """
        if not Grid.is_legal_blackout_threshold(blackout_threshold):
            raise ValueError(
                "Parameter 'blackout_threshold' should be a non-negative "
                "float or None"
            )

        if not Grid.is_lega_injection_price(injection_price):
            raise ValueError(
                "Parameter 'injection_price' should be of type float or None"
            )

        super().__init__(**kwargs)

        self.blackout_threshold = blackout_threshold
        self.injection_price = injection_price

    @staticmethod
    def is_legal_blackout_threshold(threshold: Optional[float]) -> bool:
        """Check whether the provided threshold is valid for blackouts.

        A blackout threshold should be a non-negative float or integer.
        """
        return threshold is None or (
            isinstance(threshold, (float, int)) and threshold >= 0
        )

    @staticmethod
    def is_lega_injection_price(cost: Optional[float]) -> bool:
        """Check whether the provided cost is a valid injection price.

        An injection price should be a float or integer. Make no assumptions
        on whether it is a cost or remuneration.
        """
        return cost is None or isinstance(cost, (float, int))

    # TODO: convert to python setter
    def set_blackout_threshold(self, threshold: float) -> None:
        """Set the blackout threshold for this grid."""
        if not self.is_legal_blackout_threshold(threshold):
            raise ValueError(
                "Argument 'blackout_threshold' has an illegal "
                "value. Should be a non-negative float"
            )

        self.blackout_threshold = threshold

    # TODO: convert to python setter
    def set_injection_cost(self, cost: float) -> None:
        """Set the injection cost (€/kWh) for this grid."""
        if not self.is_lega_injection_price(cost):
            raise ValueError(
                "Argument 'injection_price' has an illegal value. "
                "Costs should be a float"
            )

        self.injection_price = cost

    def update(self, params: dict[str, Any]) -> Grid:
        """Update this instance with the provided new parameters.

        Parameters
        __________
        params  -- Parameters with new values. Valid parameters are those
                    passed to the __init__ method

        Returns
        _______
        Return reference to self
        """
        if (
            threshold_present := "blackout_threshold" in params
        ) and not Grid.is_legal_blackout_threshold(
            params["blackout_threshold"]
        ):
            raise ValueError(
                "Parameter 'blackout_threshold' should be a non-negative "
                "float or None"
            )

        if (
            injection_present := "injection_price" in params
        ) and not Grid.is_lega_injection_price(params["injection_price"]):
            raise ValueError(
                "Parameter 'injection_price' should be of type float or None"
            )

        super().update(params)

        if threshold_present:
            self.blackout_threshold = params["blackout_threshold"]

        if injection_present:
            self.injection_price = params["injection_price"]

        return self


class PV(SourceComponent):
    """Class representing a PV installation.

    Attributes
    __________
    power       -- Power rating of the component
    is_primary  -- Whether this is a primary component, opposed to
                    backup or auxiliary
    price       -- Price of electricity from this source (€/kWh)
    """

    LABEL = "PV"


class Generator(SourceComponent):
    """Class representing an electricity generator.

    Class containing certain attributes of an electric generator that can be
    configured for each project.

    Attributes
    __________
    power       -- Power rating of the component
    is_primary  -- Whether this is a primary component, opposed to
                    backup or auxiliary
    price       -- Price of electricity from this source (€/kWh)
    efficiency  -- Fuel conversion factor (kWh/L)
    fuel_cost        -- Price for fuel (€/L)
    overheats        -- Flag indicating whether the generator overheats during
                        operation
    overheating_time -- Operation time before the generator overheats
                        (in seconds)
    cooldown_time    -- Time required by to cool down and restart working after
                         it has overheated (in seconds)
    """

    LABEL = "generator"

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        efficiency: float,
        fuel_cost: float,
        overheats: bool = False,
        overheating_time: Optional[float] = None,
        cooldown_time: Optional[float] = None,
        **kwargs: Any,
    ):
        """Instantiate an object of this class.

        Parameters
        __________
        efficiency       -- Fuel conversion factor (kWh/L)
        fuel_cost        -- Price for fuel (€/L)
        overheats        -- Flag indicating whether the generator overheats
                            during operation
        overheating_time -- Operation time before the generator overheats
                            (in seconds)
        cooldown_time    -- Time required by to cool down and restart working
                            after it has overheated (in seconds)
        kwargs           -- Parameters for superclasses
        """
        if not Generator.is_legal_efficiency(efficiency):
            raise ValueError(
                "Parameter 'efficiency' should be a positive float"
            )

        if not Generator.is_legal_fuel_cost(fuel_cost):
            raise ValueError(
                "Parameter 'fuel_cost' should be a non-negative float"
            )

        if not Generator.is_legal_overheats_flag(overheats):
            raise TypeError("Parameter 'overheats' should be of type bool")

        if not Generator.is_legal_overheating_time(overheating_time):
            raise ValueError(
                "Parameter 'overheating_time' should be a non-negative float "
                "or None"
            )

        if not Generator.is_legal_cooldown_time(cooldown_time):
            raise ValueError(
                "Parameter 'cooldown_time' should be a non-negative float "
                "or None"
            )

        if overheats and (overheating_time is None or cooldown_time is None):
            raise ValueError(
                "A generator that overheats must have an operation and "
                "cooldown time"
            )

        if not overheats and (overheating_time or cooldown_time):
            raise ValueError(
                "A generator that does not overheat cannot have an "
                "'overheating_time' nor a 'cooldown_time'"
            )

        super().__init__(**kwargs)

        self.efficiency = efficiency
        self.fuel_cost = fuel_cost
        self.overheats = overheats
        self.overheating_time = overheating_time
        self.cooldown_time = cooldown_time

    # pylint: enable=too-many-arguments

    @staticmethod
    def is_legal_cooldown_time(time: Optional[float]) -> bool:
        """Check whether the provided cooldown time is a legal duration."""
        return time is None or (isinstance(time, (float, int)) and time >= 0)

    @staticmethod
    def is_legal_efficiency(factor: float) -> bool:
        """Check whether the provided efficiency is a legal fuel efficiency."""
        return isinstance(factor, (float, int)) and factor > 0

    @staticmethod
    def is_legal_fuel_cost(cost: float) -> bool:
        """Check whether the provided cost is legal."""
        return isinstance(cost, (float, int)) and cost >= 0

    @staticmethod
    def is_legal_overheating_time(time: Optional[float]) -> bool:
        """Check whether the provided time is a legal duration."""
        return time is None or (isinstance(time, (float, int)) and time >= 0)

    @staticmethod
    def is_legal_overheats_flag(flag: bool) -> bool:
        """Check whether the provide flag is a legal flag."""
        return isinstance(flag, bool)

    # TODO: Convert to python setter
    def set_fuel_cost(self, cost: float) -> None:
        """Set the fuel cost for this generator."""
        if not self.is_legal_fuel_cost(cost):
            raise ValueError(
                "Argument 'fuel_cost' has an illegal value. Cost should be "
                "a non-negative float"
            )

        self.fuel_cost = cost

    # TODO: Convert to python setter
    def set_overheats(self, overheats: bool) -> None:
        """Set whether this generator overheats."""
        if not self.is_legal_overheats_flag(overheats):
            raise ValueError("Argument 'overheats' should be of type bool")

        if not overheats:
            self.cooldown_time = None

        self.overheats = overheats

    # TODO: Convert to python setter
    def set_cooldown_time(self, time: float) -> None:
        """Set the time required to cool down after overheating."""
        if not self.is_legal_cooldown_time(time):
            raise ValueError(
                "Argument 'cooldown_time' has an illegal value. Should be "
                "a non-negative float"
            )
        if not self.overheats and time is not None:
            raise ValueError(
                "Argument 'cooldown_time' has an illegal value. If the "
                "generator does not overheat it should be None"
            )

        self.cooldown_time = time

    def update(self, params: dict[str, Any]) -> Generator:
        """Update this instance with the provided new parameters.

        Parameters
        __________
        params  -- Parameters with new values. Valid parameters are those
                    passed to the __init__ method

        Returns
        _______
        Return reference to self
        """
        # Check input first
        if (
            efficiency_present := "efficiency" in params
        ) and not Generator.is_legal_efficiency(params["efficiency"]):
            pass

        if (
            fuel_present := "fuel_cost" in params
        ) and not Generator.is_legal_fuel_cost(params["fuel_cost"]):
            pass

        if (
            overheats_present := "overheats" in params
        ) and not Generator.is_legal_overheats_flag(params["overheats"]):
            pass

        if (
            overheating_present := "overheating_time" in params
        ) and not Generator.is_legal_overheating_time(
            params["overheating_time"]
        ):
            pass

        if (
            cooldown_present := "cooldown_time" in params
        ) and not Generator.is_legal_cooldown_time(params["cooldown_time"]):
            pass

        # Assign input
        super().update(params)

        if efficiency_present:
            self.efficiency = params["efficiency"]

        if fuel_present:
            self.fuel_cost = params["fuel_cost"]

        if overheats_present:
            self.overheats = params["overheats"]

        if overheating_present:
            self.overheating_time = params["overheating_time"]

        if cooldown_present:
            self.cooldown_time = params["cooldown_time"]

        return self


# ------------------------------
# ----- Storage components -----
# ------------------------------


class StorageComponent(EnergyProjectComponent, ABC):
    """Class representing project elements for electrical storage.

    Attributes
    __________
    power       -- Power rating of the component
    is_primary  -- Whether this is a primary component, opposed to
                    backup or auxiliary
    capacity    -- Electrical storage capacity (kWh)
    """

    def __init__(self, capacity: float, **kwargs: Any) -> None:
        """Instantiate object of this class.

        Parameters
        __________
        capacity    -- Storage capacity (kWh)
        kwargs      --  Parameters for the superclasses
        """
        if not StorageComponent.is_legal_capacity(capacity):
            raise ValueError(
                "Parameter 'capacity' should be a non-negative float"
            )

        super().__init__(**kwargs)

        self.capacity = capacity

    @staticmethod
    def is_legal_capacity(capacity: float) -> bool:
        """Check whether the provided amount is a legal capacity."""
        return isinstance(capacity, (float, int)) and capacity >= 0

    def update(self, params: dict[str, Any]) -> StorageComponent:
        """Update this instance with the provided new parameters.

        Parameters
        __________
        params  -- Parameters with new values. Valid parameters are those
                    passed to the __init__ method

        Returns
        _______
        Return reference to self
        """
        if (
            capacity_present := "capacity" in params
        ) and not StorageComponent.is_legal_capacity(params["capacity"]):
            raise ValueError(
                "Parameter 'capacity' should be a non-negative float"
            )

        super().update(params)

        if capacity_present:
            self.capacity = params["capacity"]

        return self


class Battery(StorageComponent):
    """Class representing an electric battery.

    Class containing certain attributes of an electric battery that can be
    configured for each project.

    Attributes
    __________
    power       -- Power rating of the component
    is_primary  -- Whether this is a primary component, opposed to
                    backup or auxiliary
    capacity    -- Electrical storage capacity (kWh)
    battery_type        -- Type of electrical battery (e.g., Lithium Ion)
    base_soc    -- Base state of charge
    min_soc     -- Minimally allowed state of charge
    max_soc     -- Maximally allowed state of charge
    """

    LABEL = "battery"

    def __init__(
        self,
        battery_type: BatteryType,
        base_soc: float,
        min_soc: float = 50,
        max_soc: float = 90,
        **kwargs: Any,
    ) -> None:
        """Instantiate a battery object.

        Parameters
        __________
        battery_type      -- Type of electrical battery (e.g., Lithium Ion).
                        Value should be from Battery.BatteryType enum
        base_soc    -- Base state of charge
        min_soc     -- Minimally allowed state of charge
        max_soc     -- Maximally allowed state of charge
        kwargs      -- Parameters for the superclasses
        """
        if not Battery.is_legal_type(battery_type):
            raise ValueError(
                "Parameter 'battery_type' should not be None and of "
                "type BatteryType"
            )

        if not Battery.is_legal_base_soc(base_soc):
            raise ValueError(
                "Parameter 'base_soc' should be a float in the range [0,100]"
            )

        if not Battery.is_legal_min_soc(min_soc):
            raise ValueError(
                "Parameter 'min_soc' should be a float in the range [0,100]"
            )

        if not Battery.is_legal_max_soc(max_soc):
            raise ValueError(
                "Parameter 'max_soc' should be a float in the range [0,100]"
            )

        if max_soc < min_soc:
            raise ValueError("Parameter 'max_soc' cannot be below 'min_soc'")

        if not min_soc <= base_soc <= max_soc:
            raise ValueError(
                "Parameter 'base_soc' should be in the range "
                "[min_soc, max_soc]"
            )

        super().__init__(**kwargs)

        self.battery_type = battery_type
        self.base_soc = base_soc
        self.min_soc = min_soc
        self.max_soc = max_soc

    @staticmethod
    def _is_legal_soc(soc: float) -> bool:
        """Check whether the provided state of charge is legal."""
        return isinstance(soc, (float, int)) and 0 <= soc <= 100

    @staticmethod
    def is_legal_base_soc(soc: float) -> bool:
        """Check whether the provided soc is a legal base state of charge."""
        return Battery._is_legal_soc(soc)

    @staticmethod
    def is_legal_max_soc(soc: float) -> bool:
        """Check if the provided soc is a legal maximal state of charge."""
        return Battery._is_legal_soc(soc)

    @staticmethod
    def is_legal_min_soc(soc: float) -> bool:
        """Check if the provided soc is a legal minimal state of charge."""
        return Battery._is_legal_soc(soc)

    @staticmethod
    def is_legal_type(battery_type: BatteryType) -> bool:
        """Check whether the provided type is a legal battery type."""
        return isinstance(battery_type, Battery.BatteryType)

    # TODO: convert to python setter
    def set_base_soc(self, soc: float) -> None:
        """Set the base state of charge of this battery."""
        if not self.is_legal_base_soc(soc):
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
        if not self.is_legal_min_soc(soc):
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
        """Set the battery_type of this battery."""
        if not self.is_legal_type(b_type):
            raise ValueError(
                "Parameter 'battery_type' should not be None and of "
                "type BatteryType"
            )

        self.battery_type = b_type

    def update(self, params: dict[str, Any]) -> Battery:
        """Update this instance with the provided new parameters.

        Parameters
        __________
        params  -- Parameters with new values. Valid parameters are those
                    passed to the __init__ method

        Returns
        _______
        Return reference to self.
        """
        if (
            base_present := "base_soc" in params
        ) and not Battery.is_legal_base_soc(params["base_soc"]):
            raise ValueError(
                "Parameter 'base_soc' should be a float in the range [0,100]"
            )

        if (
            min_present := "min_soc" in params
        ) and not Battery.is_legal_min_soc(params["min_soc"]):
            raise ValueError(
                "Parameter 'min_soc' should be a float in the range [0,100]"
            )

        if (
            max_present := "max_soc" in params
        ) and not Battery.is_legal_max_soc(params["max_soc"]):
            raise ValueError(
                "Parameter 'max_soc' should be a float in the range [0,100]"
            )

        if (
            type_present := "battery_type" in params
        ) and not Battery.is_legal_type(params["battery_type"]):
            raise ValueError(
                "Parameter 'battery_type' should not be None and of "
                "type BatteryType"
            )

        base_soc = params["base_soc"] if base_present else self.base_soc
        min_soc = params["min_soc"] if min_present else self.min_soc
        max_soc = params["max_soc"] if max_present else self.max_soc

        if max_soc < min_soc:
            raise ValueError("Parameter 'max_soc' cannot be below 'min_soc'")

        if not min_soc <= base_soc <= max_soc:
            raise ValueError(
                "Parameter 'base_soc' should be in the range "
                "[min_soc, max_soc]"
            )

        super().update(params)

        if base_present or min_present or max_present:
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
                self.min_soc = min_soc
                self.base_soc = base_soc
                self.max_soc = max_soc
            else:
                self.max_soc = max_soc
                self.base_soc = base_soc
                self.min_soc = min_soc

        if type_present:
            self.battery_type = params["battery_type"]

        return self

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


# ----------------------------------
# ----- Consumption components -----
# ----------------------------------


class ConsumptionComponent(EnergyProjectComponent):
    """Class representing an electrical consumption element.

    Attributes
    __________
    power       -- Power rating of the component
    is_primary  -- Whether this is a primary component, opposed to
                    backup or auxiliary
    is_critical -- Whether it should be ensured that this component is
                    always powered
    """

    LABEL = "consumer"

    def __init__(self, is_critical: bool, **kwargs: Any) -> None:
        """Instantiate object of this class.

        Parameters
        __________
        is_critical -- Flag indicating whether this element's power should be
                        prioritized
        """
        if not ConsumptionComponent.is_legal_critical_flag(is_critical):
            raise ValueError("Parameter 'is_critical' should be of type bool")

        super().__init__(**kwargs)

        self.is_critical = is_critical

    @staticmethod
    def is_legal_critical_flag(flag: bool) -> bool:
        """Check whether the provided flag is a legal flag."""
        return isinstance(flag, bool)

    def update(self, params: dict[str, Any]) -> ConsumptionComponent:
        """Update this instance with the provided new parameters.

        Parameters
        __________
        params  -- Parameters with new values. Valid parameters are those
                    passed to the __init__ method

        Returns
        _______
        Return reference to self.
        """
        if (
            critical_present := "is_critical" in params
        ) and not ConsumptionComponent.is_legal_critical_flag(
            params["is_critical"]
        ):
            pass

        super().update(params)

        if critical_present:
            self.is_critical = params["is_critical"]

        return self
