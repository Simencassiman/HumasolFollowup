"""Provides functionality for authorization."""

from humasol import exceptions
from humasol.model import user


def get_role(role: str) -> user.Role:
    """Retrieve enum value from string."""
    try:
        return user.Role.get(role)
    except KeyError as exc:
        raise exceptions.ModelException(exc) from exc


def get_role_admin() -> user.Role:
    """Return admin role."""
    return user.Role.ADMIN


def get_role_admin_as_str() -> str:
    """Return admin role string."""
    return user.Role.ADMIN.content


def get_role_humasol_followup() -> user.Role:
    """Return Humasol followup member role."""
    return user.Role.HUMASOL_FOLLOWUP


def get_role_humasol_followup_as_str() -> str:
    """Return Humasol followup member role string."""
    return user.Role.HUMASOL_FOLLOWUP.content


def get_role_humasol_member() -> user.Role:
    """Return Humasol member role."""
    return user.Role.HUMASOL_MEMBER


def get_role_humasol_member_as_str() -> str:
    """Return Humasol member role string."""
    return user.Role.HUMASOL_MEMBER.content


def get_role_humasol_pr() -> str:
    """Return Humasol PR member role string."""
    return user.Role.HUMASOL_PR.content


def get_role_humasol_student() -> str:
    """Return Humasol student role string."""
    return user.Role.HUMASOL_STUDENT.content


def get_role_partner() -> str:
    """Return partner role string."""
    return user.Role.PARTNER.content


def get_roles_all() -> tuple[user.Role, ...]:
    """Return all defined roles as strings."""
    return user.Role.all()


def get_roles_humasol_member() -> tuple[user.Role, ...]:
    """Return all roles of people working for humasol."""
    return user.Role.humasol_members()


def get_roles_humasol() -> tuple[user.Role, ...]:
    """Return all roles of humasol people as strings."""
    return user.Role.humasol()
