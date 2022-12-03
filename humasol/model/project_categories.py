"""Contains all the definitions of existing project categories.

Humasol project are executed within the scope of a project category, which
describes the main objectives of the project or used resources (e.g., energy).

Classes:
ProjectCategory -- Enumeration defining all project categories
"""

# Python Libraries
from __future__ import annotations

from enum import Enum


class ProjectCategory(Enum):
    """Definition of recognized project categories."""

    AGRICULTURE = "agriculture"
    ENERGY = "energy"
    WASTE = "waste"

    @staticmethod
    def categories() -> tuple[ProjectCategory, ...]:
        """Provide a list of all project categories."""
        return tuple(ProjectCategory.__members__.values())

    # Pylint doesn't detect the members of enum subclasses (as of 2.12.2022)
    # pylint: disable=no-member
    @property
    def content(self) -> str:
        """Provide value of the category."""
        return self._value_

    # pylint: enable=no-member

    @staticmethod
    def from_string(category: str) -> ProjectCategory:
        """Provide enum value representing the given string."""
        if (category := category.lower()) not in (
            vals := ProjectCategory.__members__
        ):
            raise ValueError("Unexpected category.")

        return vals[category]
