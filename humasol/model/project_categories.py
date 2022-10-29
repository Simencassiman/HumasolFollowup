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

    @property
    def categories(self) -> tuple[ProjectCategory, ...]:
        """Provide a list of all project categories."""
        return tuple(ProjectCategory.__members__.values())
