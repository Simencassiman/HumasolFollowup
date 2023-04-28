"""Person folder objects for follow-up work.

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
import typing as ty

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declared_attr

# Local modules
from humasol import exceptions, model
from humasol.model.snapshot import Snapshot
from humasol.repository import db


class Person(model.BaseModel, model.ProjectElement):
    """Abstract base class for a person working for/with Humasol.

    Attributes
    __________
    id      --  Identifier within people
    name    --  Personal name
    email   --  Personal email
    phone   --  Personal phone number
    type    --  Subtype of person, used for database mapping
    organisation    -- Affiliation of the person
    """

    # Definitions for the database tables #
    __tablename__ = "person"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False, index=True)
    email = db.Column(db.String, unique=True, nullable=False, index=True)
    phone = db.Column(db.String, unique=True)
    type = db.Column(db.String(20))  # Used by database ORM

    __mapper_args__ = {
        "polymorphic_identity": "person",
        "with_polymorphic": "*",
        "polymorphic_on": type,
    }

    @declared_attr
    def organization_name(self) -> SQLAlchemy.Colum:
        """Return organization name database column."""
        return db.Column(
            db.String, db.ForeignKey("organization.name", ondelete="SET NULL")
        )

    @declared_attr
    def organization(self) -> orm.RelationshipProperty:
        """Return database relationship object to Organization."""
        return db.relationship("Organization", lazy="subquery")

    # End of database definitions #

    def __init__(
        self,
        name: str,
        email: str,
        phone: ty.Optional[str],
        organization: Organization,
    ) -> None:
        """Instantiate Person object with provided arguments.

        Parameters
        __________
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

        if not Person.is_legal_name(name):
            raise exceptions.IllegalArgumentException(
                "Parameter 'name' should be of type str and "
                "made up of letters and white spaces"
            )

        if not Person.is_legal_email(email):
            raise exceptions.IllegalArgumentException(
                "Parameter 'email' should not be None and of type str."
                "Valid structure example myname@subdomain.email.com"
            )

        if not Person.is_legal_phone(phone):
            raise exceptions.IllegalArgumentException(
                "Parameter 'phone' should be of type str or None. "
                "Example of a valid structure (+ or 00)32123456789 "
                "or 123456789"
            )

        if not Person.is_legal_organization(organization):
            raise exceptions.IllegalArgumentException(
                "Parameter 'organization' should not be None and a subclass "
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
    def is_legal_email(email: str) -> bool:
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
    def is_legal_name(name: str) -> bool:
        """Check whether this is a legal name for a person."""
        if not isinstance(name, str):
            return False

        if len(name) == 0:
            return False

        regex = re.compile(r"[@_!#$%^&*()<>?/\\|}{~:]")
        if regex.search(name) is not None:
            return False

        return True

    @staticmethod
    def is_legal_organization(organization: Organization) -> bool:
        """Check whether the provided organisation is a legal organisation."""
        return isinstance(organization, Organization)

    @staticmethod
    def is_legal_phone(phone: ty.Optional[str]) -> bool:
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

    @Snapshot.protect
    def update(self, params: dict[str, ty.Any]) -> Person:
        """Update this instance with the new parameters.

        Valid parameters are those provided to the __init__ method.

        Returns
        _______
        Return reference to self.
        """
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
    """Class representing a Humasol student.

    Attributes
    __________
    id      --  Identifier within people
    name    --  Personal name
    email   --  Personal email
    phone   --  Personal phone number
    type    --  Subtype of person, used for database mapping
    organisation    -- Affiliation of the person
    university      -- Institution at which the student studies
    field_of_study  -- Domain of expertise of the student
    """

    LABEL = "student"

    # Definitions for the database tables #
    __tablename__ = "student"
    id = db.Column(
        None, db.ForeignKey("person.id", ondelete="CASCADE"), primary_key=True
    )

    __mapper_args__ = {
        "polymorphic_identity": "student",
        "with_polymorphic": "*",
    }

    university = db.Column(db.String, nullable=False, index=True)
    field_of_study = db.Column(db.String, nullable=False)

    @declared_attr
    def organization(self) -> orm.RelationshipProperty:
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
        phone: ty.Optional[str] = None,
    ) -> None:
        """Instantiate Student object with provided arguments.

        Parameters
        __________
        name    -- Name of the student
        email   -- Email of the student
        university      -- University at which the student studies
        field_of_study  -- Specialization of the student
        phone   -- Phone number of the student. Including country code
        """
        if not Student.is_legal_university(university):
            raise exceptions.IllegalArgumentException(
                "Parameter 'university' should not be None and of "
                "type str. The string should not be empty and should "
                "not contain special characters"
            )

        if not Student.is_legal_field_of_study(field_of_study):
            raise exceptions.IllegalArgumentException(
                "Parameter 'field_of_study' should not be None and of "
                "type str. The string should not be empty and "
                "should not contain special characters"
            )

        super().__init__(name, email, phone, Humasol())
        self.university = university
        self.field_of_study = field_of_study

    # pylint: enable-msg=too-many-arguments

    @staticmethod
    def is_legal_field_of_study(field: str) -> bool:
        """Check whether the provided field is a valid field of study."""
        if not isinstance(field, str):
            return False

        return re.fullmatch(r"[A-Z.,\s]+", field.upper()) is not None

    @staticmethod
    def is_legal_university(university: str) -> bool:
        """Check whether the provided university is a valid university name."""
        if not isinstance(university, str):
            return False

        return re.fullmatch(r"[A-Z.,\s]+", university.upper()) is not None

    @Snapshot.protect
    def update(self, params: dict[str, ty.Any]) -> Student:
        """Update this instance with the new parameters.

        Valid parameters are those passed to the __init__ method.

        Returns
        _______
        Return reference to self.
        """
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
    """Class representing a Humasol member supervising a project.

    Attributes
    __________
    id      --  Identifier within people
    name    --  Personal name
    email   --  Personal email
    phone   --  Personal phone number
    type    --  Subtype of person, used for database mapping
    organisation    -- Affiliation of the person
    function        -- Supervising function (e.g., coach)
    """

    LABEL = "supervisor"

    # Definitions for the database tables #
    __tablename__ = "supervisor"
    id = db.Column(
        None, db.ForeignKey("person.id", ondelete="CASCADE"), primary_key=True
    )

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
    def organization(self) -> orm.RelationshipProperty:
        """Return database relationship object to Organization."""
        return db.relationship("Organization", lazy="subquery")

    # End of database definitions #

    def __init__(
        self,
        name: str,
        email: str,
        function: str,
        phone: ty.Optional[str] = None,
    ) -> None:
        """Instantiate Student object with provided arguments.

        Parameters
        __________
        name     -- Name of the student
        email    -- Email of the student
        function -- Supervising function (e.g., coach)
        phone    -- Phone number of the supervisor. Including country code
        """
        if not Supervisor.is_legal_function(function):
            raise exceptions.IllegalArgumentException(
                "Parameter 'function' should not be None and of type "
                "str. There should be at least two letters."
            )

        super().__init__(name, email, phone, Humasol())
        self.function = function

    @staticmethod
    def is_legal_function(function: str) -> bool:
        """Check whether the provided function has valid content."""
        if not isinstance(function, str):
            return False

        return re.match("[A-Z]{2,}", function.upper()) is not None

    @Snapshot.protect
    def update(self, params: ty.Any) -> Supervisor:
        """Update this instance with the new parameters.

        Valid parameters are those passed to the __init__ method.

        Returns
        _______
        Return reference to self.
        """
        super().update(params)

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

    Attributes
    __________
    id      --  Identifier within people
    name    --  Personal name
    email   --  Personal email
    phone   --  Personal phone number
    type    --  Subtype of person, used for database mapping
    organisation    -- Affiliation of the person
    function        -- Function of the partner within the project
                        (e.g., technician)
    """

    LABEL = "partner"

    # Definitions for the database tables #
    __tablename__ = "partner"
    id = db.Column(
        None, db.ForeignKey("person.id", ondelete="CASCADE"), primary_key=True
    )

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

    # End of database definitions #

    # Disabling pylint because arguments are necessary
    # pylint: disable-msg=too-many-arguments
    def __init__(
        self,
        name: str,
        email: str,
        function: str,
        organization: Organization,
        phone: ty.Optional[str] = None,
    ) -> None:
        """Instantiate Student object with provided arguments.

        Parameters
        __________
        name     -- Name of the student
        email    -- Email of the student
        function -- Partner function (e.g., technician)
        phone    -- Phone number of the student. Including country code
        """
        if not Partner.is_legal_function(function):
            raise exceptions.IllegalArgumentException(
                "Parameter 'function' should not be None and of type "
                "str. There should be at least two letters."
            )

        super().__init__(name, email, phone, organization)
        self.function = function

    # pylint: enable-msg=too-many-arguments

    @staticmethod
    def is_legal_function(function: str) -> bool:
        """Check whether this function is valid for a partner.

        Check whether the characters in the string are valid.
        """
        if not isinstance(function, str):
            return False

        return re.match("[A-Z]{2,}", function.upper()) is not None

    def _construct_organization(
        self, partner_type: str, **kwargs: ty.Any
    ) -> Organization:
        """Update the current organization or create a new one.

        Parameters
        __________
        partner_type    -- Label of the type of organization
        kwargs          -- Parameters for the organization
        """
        types: dict[str, type] = {
            BelgianPartner.LABEL: BelgianPartner,
            SouthernPartner.LABEL: SouthernPartner,
        }

        if self.organization.LABEL == partner_type:
            return self.organization.update(kwargs)

        return types[partner_type](**kwargs)

    @Snapshot.protect
    def update(self, params: dict[str, ty.Any]) -> Partner:
        """Update this instance with the provided new parameters.

        Valid parameters are those passed to the __init__ method.

        Returns
        _______
        Return reference to self.
        """
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

        super().update(params)

        if "function" in params:
            self.function = params["function"]

        if "organization" in params:
            self.organization = self._construct_organization(
                **params["organization"]
            )

        return self

    def __repr__(self) -> str:
        """Provide string representation of this instance."""
        return "Partner(" + super().__repr__() + f", function={self.function})"


class Organization(model.BaseModel, model.ProjectElement):
    """Abstract base class representation of an organisation.

    People related to a project are also related to an organisation. This class
     represents the basic organisation.

    Attributes
    __________
    name    -- Name of the organisation
    logo    -- Local URI to logo
    type    -- Subclass, used by database mapper
    """

    # Definitions for the database tables #
    __tablename__ = "organization"

    name = db.Column(db.String, primary_key=True)
    logo = db.Column(db.String)
    type = db.Column(db.String(20))  # For internal database structure

    __mapper_args__ = {"polymorphic_on": type}

    # End of database definitions #

    def __init__(self, name: str, logo: str) -> None:
        """Instantiate organisation object.

        Parameters
        __________
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

        if not Organization.is_legal_name(name):
            raise exceptions.IllegalArgumentException(
                "Parameter 'name' should not be None and of type str. "
                "Names should contain at least one letter"
            )

        if not Organization.is_legal_logo(logo):
            raise exceptions.IllegalArgumentException(
                "Parameter 'logo' should not be None and of type str. "
                "It should be a valid path"
            )

        self.name = name
        self.logo = logo

    @staticmethod
    def is_legal_logo(logo: str) -> bool:
        """Check whether the provided logo is a valid URI.

        Check the structure of the URI (not whether it actually exists).
        """
        if not isinstance(logo, str):
            return False

        return (
            re.fullmatch(r"([A-Z_\-]+/)*[A-Z_\-]+\.[A-Z]{2,4}", logo.upper())
            is not None
        )

    @staticmethod
    def is_legal_name(name: str) -> bool:
        """Check if the provided name is valid for an organisation.

        Check for illegal characters. A name should only contain letters.
        """
        if not isinstance(name, str):
            return False

        # TODO: add whitespaces and Ü type characters
        return re.match(r"[A-Z]+", name.upper()) is not None

    @Snapshot.protect
    def update(self, params: dict[str, ty.Any]) -> Organization:
        """Update this instance with the provided new parameters.

        Valid parameters are those passed to the __init__ method.

        Returns
        _______
        Return reference to self.
        """
        if "name" in params:
            self.name = params["name"]

        if "logo" in params:
            self.logo = params["logo"]

        return self

    def __repr__(self) -> str:
        """Provide a string representation for this instance."""
        return f"name={self.name}, logo={self.logo}"


class Humasol(Organization):
    """Class representing Humasol as an Organisation."""

    LABEL = "hs"

    # Definitions for the database tables #
    __mapper_args__ = {"polymorphic_identity": "humasol"}

    # End database definitions #

    def __init__(self) -> None:
        """Instantiate Humasol organisation."""
        # TODO: add correct logo URI
        super().__init__("Humasol", "logo.png")

    def __repr__(self) -> str:
        """Provide a string representation for Humasol."""
        return "Humasol(" + super().__repr__() + ")"


class BelgianPartner(Organization):
    """Class representing a belgian organisation."""

    LABEL = "bp"

    # Definitions for the database tables #
    __mapper_args__ = {"polymorphic_identity": "belgian_partner"}

    # End database definitions #

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

    def __init__(self, name: str, logo: str, country: str) -> None:
        """Instantiate obeject of this class.

        Parameters
        __________
        name    -- Name of the organisation
        logo    -- URI of the image of the organisation
        country -- Country of origin of the organisation or where it has its
                    HQ
        """
        if not SouthernPartner.is_legal_country(country):
            raise exceptions.IllegalArgumentException(
                "Parameter 'country' has invalid content. A country should be "
                "made up of letters"
                "(spaces, periods and commas are also accepted)"
            )
        super().__init__(name, logo)
        self.country = country

    @staticmethod
    def is_legal_country(country: str) -> bool:
        """Check whether this is a valid country for a southern partner."""
        # TODO: Check from list
        return country is None or (
            isinstance(country, str)
            and re.fullmatch(r"^[A-Z][A-Z\s.,]*", country.upper()) is not None
        )

    @Snapshot.protect
    def update(self, params: dict[str, ty.Any]) -> Organization:
        """Update this instance with the provided new parameters.

        Valid parameters are those passed to the __init__ method.

        Returns
        _______
        Return reference to self.
        """
        super().update(params)

        if "country" in params:
            self.set_country(params["country"])

        return self

    def __repr__(self) -> str:
        """Provide a string representation for this organisation."""
        return (
            "SouthernPartner("
            + super().__repr__()
            + f", country={self.country}"
            f")"
        )


T = ty.TypeVar("T", bound=Person)


def construct_person(constructor: ty.Type[T], params: dict[str, ty.Any]) -> T:
    """Construct a person object.

    Constructs an object subclassing Person with the provided parameters. Do
    this using the provided class constructor.

    Parameters
    __________
    constructor -- Class constructor of the appropriate subtype
    params      -- Parameters for populating the person object
    is_partner  -- Indicates whether the subtype is Partner

    Returns
    _______
    Return object subclassing Person.
    """
    if issubclass(constructor, Partner):
        match (partner_type := params["organization"].pop("type")):
            case BelgianPartner.LABEL:
                params["organization"] = BelgianPartner(
                    **params["organization"]
                )
            case SouthernPartner.LABEL:
                params["organization"] = SouthernPartner(
                    **params["organization"]
                )
            case _:
                raise exceptions.IllegalArgumentException(
                    f"Unexpected partner type. Expected one of "
                    f"{BelgianPartner.LABEL} or "
                    f"{SouthernPartner.LABEL}. Got: {partner_type}."
                )

    return constructor(**params)


def get_constructor_from_type(person_type: str) -> ty.Type[Person]:
    """Return class constructor associated with the given person_type label.

    Provides the constructor callable for a subclass of person.

    Parameters
    __________
    person_type -- Identifier of the desired class (classes have LABEL
                    attribute for this purpose)

    Returns
    _______
    Return constructor for a subclass of person.
    """
    match person_type:
        case Student.LABEL:
            return Student
        case Supervisor.LABEL:
            return Supervisor
        case Partner.LABEL:
            return Partner

    raise exceptions.IllegalArgumentException(
        f"Unexpected person person_type. Got: {person_type}"
    )
