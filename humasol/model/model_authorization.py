"""Provides functionality for authorization."""

from humasol.model.user import Role


def get_role_admin() -> Role:
    """Return admin role."""
    return Role.ADMIN


def get_role_admin_as_str() -> str:
    """Return admin role string."""
    return Role.ADMIN.content


def get_role_humasol_followup() -> Role:
    """Return Humasol followup member role."""
    return Role.HUMASOL_FOLLOWUP


def get_role_humasol_followup_as_str() -> str:
    """Return Humasol followup member role string."""
    return Role.HUMASOL_FOLLOWUP.content


def get_role_humasol_member() -> Role:
    """Return Humasol member role."""
    return Role.HUMASOL_MEMBER


def get_role_humasol_member_as_str() -> str:
    """Return Humasol member role string."""
    return Role.HUMASOL_MEMBER.content


def get_role_humasol_pr() -> str:
    """Return Humasol PR member role string."""
    return Role.HUMASOL_PR.content


def get_role_humasol_student() -> str:
    """Return Humasol student role string."""
    return Role.HUMASOL_STUDENT.content


def get_role_partner() -> str:
    """Return partner role string."""
    return Role.PARTNER.content


def get_roles_all() -> tuple[Role, ...]:
    """Return all defined roles as strings."""
    return Role.all()


def get_roles_humasol_member() -> tuple[Role, ...]:
    """Return all roles of people working for humasol."""
    return Role.humasol_members()


def get_roles_humasol() -> tuple[Role, ...]:
    """Return all roles of humasol people as strings."""
    return Role.humasol()
