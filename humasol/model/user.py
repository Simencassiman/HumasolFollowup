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
from humasol import model
from humasol.repository import db

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

    ADMIN = "Admin"
    HUMASOL_FOLLOWUP = "Humasol Follow-up"
    HUMASOL_PR = "Humasol PR"
    HUMASOL_MEMBER = "Humasol Member"
    HUMASOL_STUDENT = "Humasol Student"
    PARTNER = "Partner"

    @staticmethod
    def all() -> tuple[Role, ...]:
        """Return all values of this enum."""
        return tuple(Role.__members__.values())

    @staticmethod
    def get(name: str) -> Role:
        """Return enum element from name."""
        return Role.__members__[name.upper()]

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

    @property
    def content(self) -> str:
        """Return the value of the enum object."""
        return self.value


class UserRole(RoleMixin, model.BaseModel):
    """Webapp user's role with respect to Humasol.

    Users of the webapp can have one of a set of roles associated to them.
    These roles are defined with respect to Humasol (e.g., Humasol member,
    student, ...). The role of a user specifies which privileges they have.
    """

    __tablename__ = "user_role"

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.Enum(Role), nullable=False)


class User(UserMixin, model.BaseModel):
    """Webapp user dataclass used for authentication purposes."""

    id = db.Column(db.Integer, primary_key=True)
    # TODO: update database
    # first_name = db.Column(db.String(255), nullable=False)
    # last_name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    fs_uniquifier = db.Column(db.String(255), unique=True, nullable=False)
    roles = db.relationship(
        "UserRole",
        secondary=users_role,
        backref=db.backref("users", lazy="dynamic"),
        cascade="all, delete",
    )


# pylint: enable=too-few-public-methods
