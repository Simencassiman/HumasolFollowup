"""Module containing objects that compose a project.

A project object is composed of many smaller parts (project components).
This module defines all these components that are then mapped to a database
schema using the database object from the repository.

Classes
_______
Address         -- Street address of a project location
Coordinate      -- Geographical coordinates of a project location
Location        -- Class representing a physical location as indicated on a map
SDG             -- Enum class containing all SDG goals as defined by the UN
SdgDb           -- Wrapper class to store SDG enum values in the database
DataSource      -- Class containing all the information to access a project's
                    logged data
"""

# Python Libraries
from __future__ import annotations

import re
from enum import Enum
from typing import Any, Optional, Union

# Local modules
import humasol
from humasol import exceptions, model
from humasol.repository import db


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


class Address(model.BaseModel, model.ProjectElement):
    """Class representing an address of a physical place.

    Attributes
    __________
    street  -- Street name
    number  -- Street number
    place   -- Town or city of the spot
    country -- Country in which the spot can be found
    """

    # Definitions for database tables #
    location_id = db.Column(
        db.Integer,
        db.ForeignKey("location.project_id", ondelete="CASCADE"),
        primary_key=True,
    )
    street = db.Column(db.String)
    number = db.Column(db.Integer)
    place = db.Column(db.String, nullable=False, index=True)
    country = db.Column(db.String, nullable=False, index=True)

    # End database definitions #

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
            raise exceptions.IllegalArgumentException(
                "Parameter 'street' should be of type str or None."
                " It should contain only letters (at least one), spaces, "
                "hyphens, commas and periods"
            )

        if street is None and number is not None:
            raise exceptions.IllegalArgumentException(
                "Cannot have a street number without a street"
            )

        if not Address.is_legal_number(number):
            raise exceptions.IllegalArgumentException(
                "Parameter 'number' should be a positive integer or None"
            )

        if not Address.is_legal_place(place):
            raise exceptions.IllegalArgumentException(
                "Parameter 'place' should not be none and of type str. It "
                "should only contain letters (at least one), spaces, hyphens,"
                "commas and periods"
            )

        if not Address.is_legal_country(country):
            raise exceptions.IllegalArgumentException(
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


class Coordinates(model.BaseModel, model.ProjectElement):
    """Class representing geographical coordinates of a physical place.

    Attributes
    __________
    latitude
    longitude
    """

    # Definitions for database tables #
    location_id = db.Column(
        db.Integer,
        db.ForeignKey("location.project_id", ondelete="CASCADE"),
        primary_key=True,
    )
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
            raise exceptions.IllegalArgumentException(
                "Parameter 'latitude' should not be None and of type "
                "float. It should be in the range from -90º to 90º"
            )

        if not Coordinates.is_legal_longitude(longitude):
            raise exceptions.IllegalArgumentException(
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


class Location(model.BaseModel, model.ProjectElement):
    """Class representing a physical location in the world."""

    # Definitions for the database tables #
    project_id = db.Column(
        db.Integer,
        db.ForeignKey("project.id", ondelete="CASCADE"),
        primary_key=True,
    )
    address = db.relationship(
        Address, lazy=True, cascade="all, delete", uselist=False
    )
    coordinates = db.relationship(
        Coordinates, lazy=True, cascade="all, delete", uselist=False
    )

    # End database definitions #

    def __init__(self, address: Address, coordinates: Coordinates) -> None:
        """Instantiate location object.

        Parameters
        __________
        address     -- Address to find the location on a map
        coordinates -- Geographical coordinates of the location
        """
        if not Location.is_legal_address(address):
            raise exceptions.IllegalArgumentException(
                "Parameter 'address' should be of type Address"
            )

        if not Location.are_legal_coordinates(coordinates):
            raise exceptions.IllegalArgumentException(
                "Parameter 'coordinates' should be of type Coordinates"
            )

        self.address = address
        self.coordinates = coordinates

    @staticmethod
    def are_legal_coordinates(coordinates: Coordinates) -> bool:
        """Check whether the provided coordinates are legal."""
        return isinstance(coordinates, Coordinates)

    @staticmethod
    def is_legal_address(address: Address) -> bool:
        """Check whether the provided address is a legal location address."""
        return isinstance(address, Address)

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
            f"street={self.address.street}, "
            f"number={self.address.number}, "
            f"place={self.address.place}, "
            f"country={self.address.country}, "
            f"latitude={self.coordinates.latitude}, "
            f"longitude={self.coordinates.longitude}"
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

    @staticmethod
    def from_str(name: str) -> SDG:
        """Provide SDG by name."""
        if name not in SDG.__members__:
            raise exceptions.IllegalArgumentException("Unexpected SDG name.")

        return SDG.__members__[name]

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
class SdgDB(model.BaseModel):
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


class ExtraDatum(db.Model):
    """Extra data wrapper for database mapping."""

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    project_id = db.Column(
        db.Integer,
        db.ForeignKey("project.id", ondelete="CASCADE"),
    )
    key = db.Column(db.String, nullable=False)
    value = db.Column(db.String)

    def __init__(self, key: str, value: str) -> None:
        """Wrap dictionary entry."""
        self.key = key
        self.value = value


# pylint: enable=too-few-public-methods


class DataSource(model.BaseModel, model.ProjectElement):
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
            raise exceptions.IllegalArgumentException(
                "Parameter 'source' should be a non-empty string."
            )

        if not DataSource.is_legal_user(user):
            raise exceptions.IllegalArgumentException(
                "Parameter 'user' should be of type str or None"
            )

        if not DataSource.is_legal_password(password):
            raise exceptions.IllegalArgumentException(
                "Parameter 'password' should be of type str or None"
            )

        if not DataSource.is_legal_token(token):
            raise exceptions.IllegalArgumentException(
                "Parameter 'token' should be of type str or None"
            )

        if not DataSource.are_legal_managers(
            api_manager, data_manager, report_manager
        ):
            raise exceptions.IllegalArgumentException(
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
        return humasol.script.same_category_managers(
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

    def set_user(self, user: str) -> None:
        """Set the user for this data source."""
        self.user = encrypt(user) if user is not None else user

    def set_password(self, password: str) -> None:
        """Set the password for this data source."""
        self.password = encrypt(password) if password is not None else password

    def set_token(self, token: str) -> None:
        """Set the token for this data source."""
        self.token = encrypt(token) if token is not None else token

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
        if not humasol.script.same_category_managers(api, data, report):
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
