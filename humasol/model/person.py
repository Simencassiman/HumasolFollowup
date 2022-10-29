"""Person data objects for follow-up work.

Projects are executed by and in cooperation with people. This module defines
a series of classes associated to each function a person can have with respect
to Humasol and one of its projects. Each person is also associated with a
certain organisation (either with Humasol itself or to one of its partners).
A project is executed by students (who are part of Humasol). There are a series
 of supervisors assigned to a certain project, they guide the students.
Supervisors are also part of Humasol and have a specific function.
Lastly, a project is executed with the help of partners. Partners are part of
their own organisation, which can be either from Belgium or from the
global south.

Classes:
Person          -- Abstract base class for people
Student         -- Class representing a project student
Supervisor      -- Class representing a project supervisor
Partner         -- Class representing a project partner from an external
                    organisation
Organization    -- Class representing an organisation with which people can
                    be associated (e.g., Humasol)
Humasol         -- Class representing Humasol as an organisation
BelgianPartner  -- Class representing an organisation from Belgium
SouthernPartner -- Class representing an organisation from a project country
"""


# Python Libraries
from __future__ import annotations

import re
from typing import Any, Callable, Dict, Optional, TypeVar

from sqlalchemy.ext.declarative import declared_attr

# Local modules
from ..repository import db

# TODO: add python setters to check new assignments


class Person(db.Model):
    """Abstract base class for a person working for/with Humasol."""

    # Definitions for the database tables #
    __tablename__ = "person"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False, index=True)
    email = db.Column(db.String, unique=True, nullable=False, index=True)
    phone = db.Column(db.String, unique=True)
    type = db.Column(db.String(20))

    __mapper_args__ = {
        "polymorphic_identity": "person",
        "with_polymorphic": "*",
        "polymorphic_on": type,
    }

    @declared_attr
    def organization_name(self):
        """Return organization name database column."""
        return db.Column(db.String, db.ForeignKey("organization.name"))

    @declared_attr
    def organization(self):
        """Return database relationship object to Organization."""
        return db.relationship("Organization", lazy="subquery")

    # End of database definitions #

    def __init__(
        self,
        name: str,
        email: str,
        phone: Optional[str],
        organization: Organization,
    ):
        """Instantiate Person object with provided arguments.

        Arguments:
        name    -- Name of the person
        email   -- Email of the person
        phone   -- Phone number of the person. Including country code
        organization -- Organization to which the person is associated
        """
        # Disable pylint. Need type to avoid subclasses
        # pylint: disable=unidiomatic-typecheck
        if type(self) is Person:
            raise TypeError(
                "Person is an abstract class and cannot be instantiated"
            )
        # pylint: enable=unidiomatic-typecheck

        if not self.is_valid_name(name):
            raise ValueError("Argument 'name' should be made up of letters")

        if not isinstance(email, str):
            raise TypeError(
                "Argument 'email' should not be None and of type str"
            )
        if not self.is_valid_email(email):
            raise ValueError(
                "Argument 'email' has an invalid structure. "
                "Valid example myname@subdomain.email.com"
            )

        if phone is not None and not isinstance(phone, str):
            raise TypeError("Argument 'email' should be of type str or None")
        if not self.is_valid_phone(phone):
            raise ValueError(
                "Argument 'phone' has an invalid structure. "
                "Example of a valid "
            )

        if not isinstance(organization, Organization):
            raise TypeError(
                "Argument 'organization' should not be None and a subclass "
                "of Organization"
            )

        self.name = name
        self.email = email

        phone_regex = r"^[0]{1,2}.*"
        if phone is not None and re.match(phone_regex, phone):
            phone = "+" + phone.lstrip("0")
        self.phone = phone.replace(" ", "") if phone is not None else phone

        self.organization = organization

    @staticmethod
    def is_valid_name(name: str) -> bool:
        """Check whether this is a legal name for a person."""
        if not isinstance(name, str):
            return False

        if len(name) == 0:
            return False

        regex = re.compile("[@_!#$%^&*()<>?/\\|}{~:]")
        if regex.search(name) is not None:
            return False

        return True

    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Check whether this is a legal email.

        Check based on the structure and contents, not whether it is actually
        in use.
        """
        if not isinstance(email, str):
            return False

        regex = (
            r"^(?=[A-Z0-9][A-Z0-9@._%+-]{5,253}$)[A-Z0-9._%+-]{1,64}@"
            r"(?:(?=[A-Z0-9-]{1,63}\.)[A-Z0-9]+"
            r"(?:-[A-Z0-9]+)*\.){1,8}[A-Z]{2,63}$"
        )
        if not re.fullmatch(regex, email.upper()):
            return False

        return True

    @staticmethod
    def is_valid_phone(phone: Optional[str]) -> bool:
        """Check whether this is a legal phone number.

        Check based on the structure and contents, not whether it is actually
        in use.
        """
        if phone is None:
            return True
        if not isinstance(phone, str):
            return False

        phone = phone.replace(" ", "")
        regex = r"^((\+|00)[1-9]{1,3}){0,1}[0-9]{9,12}"
        return re.fullmatch(regex, phone) is not None

    def update(self, **params: Any) -> Person:
        """Update this instance with the new parameters."""
        if "email" not in params or self.email != params["email"]:
            raise ValueError(
                "The provided parameters dictionary does not contain "
                "a matching email"
            )
        if "name" in params and not self.is_valid_name(params["name"]):
            raise ValueError(
                "Argument 'name' has an illegal value. It should be made "
                "up of letters"
            )
        if "phone" in params and not self.is_valid_phone(params["phone"]):
            raise ValueError(
                "Argument 'phone' has an invalid structure. "
                "Example of a valid "
            )

        if "name" in params:
            self.name = params["name"]

        if "phone" in params:
            self.phone = params["phone"]

        return self

    def __repr__(self) -> str:
        """Provide a string representing this instance."""
        return (
            f"name={self.name}, email={self.email}, phone={self.phone}, "
            f"organization={repr(self.organization)}"
        )


class Student(Person):
    """Class representing a Humasol student."""

    LABEL = "stu"

    # Definitions for the database tables #
    __tablename__ = "student"
    id = db.Column(None, db.ForeignKey("person.id"), primary_key=True)

    __mapper_args__ = {
        "polymorphic_identity": "student",
        "with_polymorphic": "*",
    }

    university = db.Column(db.String, nullable=False, index=True)
    field_of_study = db.Column(db.String, nullable=False)

    @declared_attr
    def organization(self):
        """Return database relationship object to Organization."""
        return db.relationship("Organization", lazy="subquery")

    # End database definitions #

    # Disabling pylint because arguments are necessary
    # pylint: disable-msg=too-many-arguments
    def __init__(
        self,
        name: str,
        email: str,
        university: str,
        field_of_study: str,
        phone: Optional[str] = None,
    ):
        """Instantiate Student object with provided arguments.

        Arguments:
        name    -- Name of the student
        email   -- Email of the student
        university      -- University at which the student studies
        field_of_study  -- Specialization of the student
        phone   -- Phone number of the student. Including country code
        """
        if not isinstance(university, str):
            raise TypeError(
                "Argument 'university' should not be None and of type str"
            )
        if not self.is_valid_university(university):
            raise ValueError(
                "Argument 'university' has invalid content. "
                "The string should not be empty and should not contain "
                "special characters"
            )
        if not isinstance(field_of_study, str):
            raise TypeError(
                "Argument 'field_of_study' should not be None and of type str"
            )
        if not self.is_valid_field_of_study(field_of_study):
            raise ValueError(
                "Argument 'field_of_study' has invalid content. "
                "The string should not be empty and should not contain "
                "special characters"
            )

        super().__init__(name, email, phone, Humasol())
        self.university = university
        self.field_of_study = field_of_study

    # pylint: enable-msg=too-many-arguments

    @staticmethod
    def is_valid_university(university: str) -> bool:
        """Check whether the provided university is a valid university name."""
        if not isinstance(university, str):
            return False

        return re.fullmatch(r"[A-Z.,\s]+", university.upper()) is not None

    @staticmethod
    def is_valid_field_of_study(field: str) -> bool:
        """Check whether the provided field is a valid field of study."""
        if not isinstance(field, str):
            return False

        return re.fullmatch(r"[A-Z.,\s]+", field.upper()) is not None

    def update(self, **params: Any) -> Student:
        """Update this instance with the new parameters."""
        if "university" in params and not self.is_valid_university(
            params["university"]
        ):
            raise ValueError(
                "Argument 'university' has invalid content. "
                "The string should not be empty and should not contain "
                "special characters"
            )
        if "field_of_study in" in params and not self.is_valid_field_of_study(
            params["field_of_study"]
        ):
            raise ValueError(
                "Argument 'field_of_study' has invalid content. "
                "The string should not be empty and should not contain "
                "special characters"
            )

        super().update(**params)

        if "university" in params:
            self.university = params["university"]
        if "field_of_study" in params:
            self.field_of_study = params["field_of_study"]

        return self

    def __repr__(self) -> str:
        """Provide a string representing this instance."""
        return (
            "Student("
            + super().__repr__()
            + f", university={self.university}, "
            + f"field_of_study={self.field_of_study})"
        )


class Supervisor(Person):
    """Class representing a Humasol member supervising a project."""

    LABEL = "sup"

    # Definitions for the database tables #
    __tablename__ = "supervisor"
    id = db.Column(None, db.ForeignKey("person.id"), primary_key=True)

    __mapper_args__ = {
        "polymorphic_identity": "supervisor",
        "with_polymorphic": "*",
    }

    # function = db.Column(db.String, nullable=False)

    @declared_attr
    def function(self):
        """Return database attribute for the function of the supervisor."""
        return Person.__table__.c.get(
            "function", db.Column(db.String, nullable=False)
        )

    @declared_attr
    def organization(self):
        """Return database relationship object to Organization."""
        return db.relationship("Organization", lazy="subquery")

    # End of database definitions #

    def __init__(
        self, name: str, email: str, function: str, phone: Optional[str] = None
    ):
        """Instantiate Student object with provided arguments.

        Arguments:
        name     -- Name of the student
        email    -- Email of the student
        function -- Supervising function (e.g., coach)
        phone    -- Phone number of the supervisor. Including country code
        """
        if not self.is_valid_function(function):
            raise ValueError(
                "Argument 'function' has invalid content. There should be at "
                "least two letters."
            )

        super().__init__(name, email, phone, Humasol())
        self.function = function

    @staticmethod
    def is_valid_function(function: str) -> bool:
        """Check whether the provided function has valid content."""
        if not isinstance(function, str):
            return False

        return re.match("[A-Z]{2,}", function.upper()) is not None

    def update(self, **params: Any) -> Supervisor:
        """Update this instance with the new parameters."""
        if "function" in params and not self.is_valid_function(
            params["function"]
        ):
            raise ValueError(
                "Argument 'function' has invalid content. There should be at "
                "least two letters."
            )

        super().update(**params)

        if "function" in params:
            self.function = params["function"]

        return self

    def __repr__(self) -> str:
        """Provide a string representing this instance."""
        return (
            "Supervisor(" + super().__repr__() + f", function={self.function})"
        )


class Partner(Person):
    """Class representing a Humasol partner for a project.

    Partners of Humasol work for an external organisation supporting one of
    the projects.
    """

    LABEL = "par"

    # Definitions for the database tables #
    __tablename__ = "partner"
    id = db.Column(None, db.ForeignKey("person.id"), primary_key=True)

    __mapper_args__ = {
        "polymorphic_identity": "partner",
        "with_polymorphic": "*",
    }

    @declared_attr
    def function(self):
        """Return database attribute for the function of the partner."""
        return Person.__table__.c.get(
            "function", db.Column(db.String, nullable=False)
        )

    @declared_attr
    def organization(self):
        """Return database relationship object to Organization."""
        return db.relationship("Organization", lazy="subquery")

    # End of database definitions #

    # Disabling pylint because arguments are necessary
    # pylint: disable-msg=too-many-arguments
    def __init__(
        self,
        name: str,
        email: str,
        function: str,
        organization: Organization,
        phone: Optional[str] = None,
    ):
        """Instantiate Student object with provided arguments.

        Arguments:
        name     -- Name of the student
        email    -- Email of the student
        function -- Partner function (e.g., technician)
        phone    -- Phone number of the student. Including country code
        """
        if not self.is_valid_function(function):
            raise ValueError(
                "Argument 'function' has invalid content. There should be at "
                "least two letters."
            )

        super().__init__(name, email, phone, organization)
        self.function = function

    # pylint: enable-msg=too-many-arguments

    @staticmethod
    def is_valid_function(function: str) -> bool:
        """Check whether this function is valid for a partner.

        Check whether the characters in the string are valid.
        """
        if not isinstance(function, str):
            return False

        return re.match("[A-Z]{2,}", function.upper()) is not None

    def update(self, **params: Any) -> Partner:
        """Update this instance with the provided new parameters."""
        if "function" in params and not self.is_valid_function(
            params["function"]
        ):
            raise ValueError(
                "Argument 'function' has invalid content. There should be at "
                "least two letters."
            )
        if "organization" in params:
            if "partner_type" not in params:
                raise ValueError(
                    "Cannot determine the correct organization constructor "
                    "without partner type information"
                )
            if (
                params["partner_type"] != BelgianPartner.LABEL
                and params["partner_type"] != SouthernPartner.LABEL
            ):
                raise RuntimeError(
                    f"Unexpected partner type. Expected one of "
                    f"{BelgianPartner.LABEL} or "
                    f"{SouthernPartner.LABEL}. "
                    f'Got: {params["partner_type"]}.'
                )

        super().update(**params)

        if "function" in params:
            self.function = params["function"]

        if "organization" in params:
            if params["partner_type"] == BelgianPartner.LABEL:
                if (
                    isinstance(self.organization, BelgianPartner)
                    and params["organization"]["name"]
                    == self.organization.name
                ):
                    self.organization.update(**params["organization"])
                else:
                    organization = BelgianPartner(
                        name=params["organization"]["name"],
                        logo=params["organization"]["logo"],
                    )
                    self.organization = organization
            else:
                if (
                    isinstance(self.organization, SouthernPartner)
                    and params["organization"]["name"]
                    == self.organization.name
                ):
                    self.organization.update(**params["organization"])
                else:
                    organization = SouthernPartner(
                        name=params["organization"]["name"],
                        logo=params["organization"]["logo"],
                        country=params["organization"]["country"],
                    )
                    self.organization = organization

        return self

    def __repr__(self) -> str:
        """Provide string representation of this instance."""
        return "Partner(" + super().__repr__() + f", function={self.function})"


class Organization(db.Model):
    """Abstract base class representation of an organisation.

    People related to a project are also related to an organisation. This class
     represents the basic organisation.
    """

    # Definitions for the database tables #
    __tablename__ = "organization"

    name = db.Column(db.String, primary_key=True)
    logo = db.Column(db.String)
    type = db.Column(db.String(20))  # For internal database structure

    __mapper_args__ = {"polymorphic_on": type}

    # End of database definitions #

    def __init__(self, name: str, logo: str):
        """Instantiate organisation object.

        Arguments:
        name    -- Name of the organisation
        logo    -- URI of the image of the organisation
        """
        # Disable pylint. Need type to avoid subclasses
        # pylint: disable=unidiomatic-typecheck
        if type(self) is Organization:
            raise TypeError(
                "Organization is an abstract class and cannot be instantiated"
            )
        # pylint: enable=unidiomatic-typecheck

        if not self.is_valid_name(name):
            raise ValueError(
                "Argument 'name' has invalid content. Names should contain "
                "at least one letter"
            )

        if not isinstance(logo, str):
            raise TypeError(
                "Argument 'logo' should not be None and of type str"
            )
        if not self.is_valid_logo(logo):
            raise ValueError(
                "Argument 'logo' contains invalid content. "
                "It should be a valid path"
            )

        self.name = name
        self.logo = logo

    @staticmethod
    def is_valid_name(name: str) -> bool:
        """Check if the provided name is valid for an organisation.

        Check for illegal characters. A name should only contain letters.
        """
        if not isinstance(name, str):
            return False

        # TODO: add whitespaces and Ü type characters
        return re.match(r"[A-Z]+", name.upper()) is not None

    @staticmethod
    def is_valid_logo(logo: str) -> bool:
        """Check whether the provided logo is a valid URI.

        Check the structure of the URI (not whether it actually exists).
        """
        if not isinstance(logo, str):
            return False

        return (
            re.fullmatch(r"([A-Z_\-]+/)*[A-Z_\-]+\.[A-Z]{2,4}", logo.upper())
            is not None
        )

    # TODO: convert to python setter
    def set_name(self, name: str) -> None:
        """Set the name of this organisation."""
        if not self.is_valid_name(name):
            raise ValueError("Illegal 'name' for an organization")

        self.name = name

    # TODO: convert to python setter
    def set_logo(self, logo: str) -> None:
        """Set the logo of this organisation."""
        if not self.is_valid_logo(logo):
            raise ValueError("Illegal logo path for an organization")

        self.logo = logo

    def update(self, **params: Any) -> Organization:
        """Update this instance with the provided new parameters."""
        # TODO: create method to update instance

    def __repr__(self) -> str:
        """Provide a string representation for this instance."""
        return f"name={self.name}, logo={self.logo}"


class Humasol(Organization):
    """Class representing Humasol as an Organisation."""

    LABEL = "hs"

    # Definitions for the database tables #
    __mapper_args__ = {"polymorphic_identity": "humasol"}

    # End database definitions #

    def __init__(self):
        """Instantiate Humasol organisation."""
        # TODO: add correct logo URI
        super().__init__("Humasol", "logo.png")

    # Disable pylint. Argument is necessary for inheritance
    # pylint: disable-msg=unused-argument
    def update(self, **params: Any) -> Humasol:
        """Update this instance with the provided new parameters.

        A Humasol instance should not need to be changed. Simply don't do
        anything.
        """
        return self

    # pylint: enable-msg=unused-argument

    def __repr__(self) -> str:
        """Provide a string representation for Humasol."""
        return "Humasol(" + super().__repr__() + ")"


class BelgianPartner(Organization):
    """Class representing a belgian organisation."""

    LABEL = "bp"

    # Definitions for the database tables #
    __mapper_args__ = {"polymorphic_identity": "belgian_partner"}

    # End database definitions #

    def update(self, **params: Any) -> Organization:
        """Update instance with provided new parameters."""
        # TODO: call super when it is implemented
        if "name" in params and not self.is_valid_name(params["name"]):
            raise ValueError("Illegal name for BelgianPartner update")
        if "logo" in params and not self.is_valid_logo(params["logo"]):
            raise ValueError("Illegal logo path for BelgianPartner update")

        if "name" in params:
            self.set_name(params["name"])
        if "logo" in params:
            self.set_logo(params["logo"])

        return self

    def __repr__(self) -> str:
        """Provide string representation for this organisation."""
        return "BelgianPartner(" + super().__repr__() + ")"


class SouthernPartner(Organization):
    """Class representing an organisation from one of the project countries."""

    LABEL = "sp"

    # Definitions for the database tables #
    __mapper_args__ = {"polymorphic_identity": "southern_partner"}

    country = db.Column(db.String)

    # End database definitions #

    def __init__(self, name: str, logo: str, country: str):
        """Instantiate obeject of this class.

        Arguments:
        name    -- Name of the organisation
        logo    -- URI of the image of the organisation
        country -- Country of origin of the organisation or where it has its
                    HQ
        """
        if country is not None and not isinstance(country, str):
            raise TypeError("Argument 'country' should be of type str or None")
        if not self.is_valid_country(country):
            raise ValueError(
                "Argument 'country' has invalid content. A country should be "
                "made up of letters"
                "(spaces, periods and commas are also accepted)"
            )
        super().__init__(name, logo)
        self.country = country

    @staticmethod
    def is_valid_country(country: str) -> bool:
        """Check whether this is a valid country for a southern partner."""
        if country is None:
            return True
        if not isinstance(country, str):
            return False

        return re.fullmatch(r"^[A-Z][A-Z\s.,]*", country.upper()) is not None

    def set_country(self, country: str) -> None:
        """Set the country for this organisation."""
        # TODO: implement as python setter
        if not self.is_valid_country(country):
            raise ValueError("Illegal country for an organization")

        self.country = country

    def update(self, **params: Any) -> Organization:
        """Update this instance with the provided new parameters."""
        # TODO: call super when it is implemented
        if "name" in params and not self.is_valid_name(params["name"]):
            raise ValueError("Illegal name for SouthernPartner update")
        if "logo" in params and not self.is_valid_logo(params["logo"]):
            raise ValueError("Illegal logo path for SouthernPartner update")
        if "country" in params and not self.is_valid_country(
            params["country"]
        ):
            raise ValueError("Illegal country name for SouthernPartner update")

        if "name" in params:
            self.set_name(params["name"])
        if "logo" in params:
            self.set_logo(params["logo"])
        if "country" in params:
            self.set_country(params["country"])

        return self

    def __repr__(self) -> str:
        """Provide a string representation for this organisation."""
        return (
            "SouthernPartner("
            + super().__repr__()
            + f", country={self.country})"
        )


T = TypeVar("T", bound=Person)


def construct_person(
    constructor: Callable[[Dict], T],
    params: Dict[str, Any],
    is_partner: bool = False,
) -> T:
    """Construct a person object.

    Constructs an object subclassing Person with the provided parameters. Do
    this using the provided class constructor.

    Arguments:
    constructor -- Class constructor of the appropriate subtype
    params      -- Parameters for populating the person object
    is_partner  -- Indicates whether the subtype is Partner
    """
    # TODO: check if it's a partner based on the constructor
    if is_partner:
        params["organization"]["logo"] = "logo.png"

        partner_type = params.pop("partner_type")
        if partner_type == BelgianPartner.LABEL:
            organization = BelgianPartner(
                name=params["organization"]["name"],
                logo=params["organization"]["logo"],
            )
        elif partner_type == SouthernPartner.LABEL:
            organization = SouthernPartner(
                name=params["organization"]["name"],
                logo=params["organization"]["logo"],
                country=params["organization"]["country"],
            )
        else:
            raise RuntimeError(
                f"Unexpected partner type. Expected one of "
                f"{BelgianPartner.LABEL} or "
                f"{SouthernPartner.LABEL}. Got: {partner_type}."
            )

        params["organization"] = organization

    if "partner_type" in params:
        del params["partner_type"]

    return constructor(params)


def get_constructor_from_type(person_type: str) -> Callable[[Dict], Person]:
    """Return class constructor associated with the provided type label.

    Provides the constructor callable for a subclass of person.

    Arguments:
    person_type -- Identifier of the desired class (classes have LABEL
                    attribute for this purpose)
    """
    # TODO: convert to dict access
    # Lambda is necessary for the correct return type
    # pylint: disable=unnecessary-lambda
    if person_type == Student.LABEL:
        return lambda p: Student(**p)
    if person_type == Supervisor.LABEL:
        return lambda p: Supervisor(**p)
    if person_type == Partner.LABEL:
        return lambda p: Partner(**p)
    # pylint: enable=unnecessary-lambda

    raise ValueError(f"Unexpected person type. Got: {person_type}")
