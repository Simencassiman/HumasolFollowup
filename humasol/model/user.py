"""User of the webapp.

Users of the webapp need to be authenticated for certain requests. The users
defined according to the User class in this module. They can have a certain
associated role. The role of a user gives it permissions for different
functionalities.

Classes:
UserRole    -- Set of privileges for a user
User        -- User dataclass of a webapp user, used for authentication
"""


# Python Libraries
from __future__ import annotations

from enum import Enum

from flask_security import RoleMixin, UserMixin

# Local modules
from ..repository import db

users_role = db.Table(
    "users_role",
    db.Column(
        "user_id", db.Integer(), db.ForeignKey("user.id", ondelete="CASCADE")
    ),
    db.Column(
        "user_role_id",
        db.Integer(),
        db.ForeignKey("user_role.id", ondelete="CASCADE"),
    ),
)

# Disable pylint. These are dataclasses to be represented in the database
# They don't necessarily need functionality
# pylint: disable=too-few-public-methods


class Role(Enum):
    """Enumeration of valid roles defined by Humasol."""

    ADMIN = "admin"
    HUMASOL_FOLLOWUP = "humasol_followup"
    HUMASOL_PR = "humasol_pr"
    HUMASOL_MEMBER = "humasol_member"
    HUMASOL_STUDENT = "humasol_student"
    PARTNER = "partner"

    @staticmethod
    def humasol() -> tuple[Role, ...]:
        """Return a list of all roles of Humasol people."""
        return (
            Role.HUMASOL_FOLLOWUP,
            Role.HUMASOL_PR,
            Role.HUMASOL_MEMBER,
            Role.HUMASOL_STUDENT,
        )

    @staticmethod
    def humasol_members() -> tuple[Role, ...]:
        """Return a list of all roles working for Humasol."""
        return Role.HUMASOL_FOLLOWUP, Role.HUMASOL_PR, Role.HUMASOL_MEMBER

    @staticmethod
    def all() -> tuple[Role, ...]:
        """Return all values of this enum."""
        return tuple(Role.__members__.values())

    # pylint doesn't recognize enum subclasses (yet)
    # pylint: disable=no-member
    @property
    def content(self) -> str:
        """Return the value of the enum object."""
        return self._value_

    # pylint: enable=no-member


class UserRole(db.Model, RoleMixin):
    """Webapp user's role with respect to Humasol.

    Users of the webapp can have one of a set of roles associated to them.
    These roles are defined with respect to Humasol (e.g., Humasol member,
    student, ...). The role of a user specifies which privileges they have.
    """

    __tablename__ = "user_role"

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.Enum(Role), nullable=False)


class User(db.Model, UserMixin):
    """Webapp user dataclass used for authentication purposes."""

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship(
        "UserRole",
        secondary=users_role,
        backref=db.backref("users", lazy="dynamic"),
        cascade="all, delete",
    )


# pylint: enable=too-few-public-methods
