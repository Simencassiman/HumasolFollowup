"""User of the webapp.

Users of the webapp need to be authenticated for certain requests. The users
defined according to the User class in this module. They can have a certain
associated role. The role of a user gives it permissions for different
functionalities.

Classes:
Role    -- Set of privileges for a user
User    -- User dataclass of a webapp user, used for authentication
"""


# Python Libraries
from flask_security import RoleMixin, UserMixin

# Local modules
from ..repository import db

roles_users = db.Table(
    "roles_users",
    db.Column("user_id", db.Integer(), db.ForeignKey("user.id")),
    db.Column("role_id", db.Integer(), db.ForeignKey("role.id")),
)

# Disable pylint. These are dataclasses to be represented in the database
# They don't necessarily need functionality
# pylint: disable=too-few-public-methods


class Role(db.Model, RoleMixin):
    """Webapp user's role with respect to Humasol.

    Users of the webapp can have one of a set of roles associated to them.
    These roles are defined with respect to Humasol (e.g., Humasol member,
    student, ...). The role of a user specifies which privileges they have.
    """

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))


class User(db.Model, UserMixin):
    """Webapp user dataclass used for authentication purposes."""

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship(
        "Role",
        secondary=roles_users,
        backref=db.backref("users", lazy="dynamic"),
    )
