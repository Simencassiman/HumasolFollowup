"""
Automatic reporting code.

Package containing all the code responsible for the automatic script that
keeps Humasol and partners informed about the projects' status and operations.
"""

# Python Libraries
from functools import reduce

# Local modules
from typing import Optional

from ..model.project_categories import ProjectCategory

# TODO: convert managers lists to automated class detections


API_MANAGERS = {ProjectCategory.ENERGY: {"VictronAPI"}}


def api_manager_exists(
    manager: str, category: Optional[ProjectCategory] = None
) -> bool:
    """Check whether the provided API manager exists.

    Check whether there is a class corresponding to the provided manager for
    the given category that implements the APIManager interface.

    Arguments:
    manager     -- Name of a class implementing the APIManager interface
    category    -- Project category to which the manager pertains
    """
    if category and category in API_MANAGERS:
        return manager in API_MANAGERS[category]

    api_managers = reduce(lambda x, y: x.union(y), API_MANAGERS.values())

    return manager in api_managers


DATA_MANAGERS = {
    ProjectCategory.ENERGY: {
        "GridDataManager",
        "BatteryDataManager",
        "GeneratorDataManager",
        "BatteryGridDataManager",
        "BatteryGridGeneratorDataManager",
        "BatteryGeneratorDataManager",
    }
}


def data_manager_exists(
    manager: str, category: Optional[ProjectCategory] = None
) -> bool:
    """Check whether the provided folder manager exists.

    Check whether there is a class corresponding to the provided manager for
    the given category that implements the DataManager interface.

    Arguments:
    manager     -- Name of a class implementing the DataManager interface
    category    -- Project category to which the manager pertains
    """
    if category and category in DATA_MANAGERS:
        return manager in DATA_MANAGERS[category]

    data_managers = reduce(lambda x, y: x.union(y), DATA_MANAGERS.values())

    return manager in data_managers


REPORT_MANAGERS = {ProjectCategory.ENERGY: {"EnergyReportManager"}}


def report_manager_exists(
    manager: str, category: Optional[ProjectCategory] = None
) -> bool:
    """Check whether the provided report manager exists.

    Check whether there is a class corresponding to the provided manager for
    the given category that implements the ReportManager interface.

    Arguments:
    manager     -- Name of a class implementing the ReportManager interface
    category    -- Project category to which the manager pertains
    """
    if category and category in REPORT_MANAGERS:
        return manager in REPORT_MANAGERS[category]

    report_managers = reduce(lambda x, y: x.union(y), REPORT_MANAGERS.values())
    return manager in report_managers


def same_category_managers(api: str, data: str, report: str) -> bool:
    """Check whether the provided managers belong to the same category.

    Arguments:
    api     -- Name of a class implementing the APIManager interface
    folder    -- Name of a class implementing the DataManager interface
    report  -- Name of a class implementing the ReportManager interface
    """
    for key, managers in API_MANAGERS.items():
        if api in managers:
            return not (
                (key not in DATA_MANAGERS or key not in REPORT_MANAGERS)
                or (
                    data not in DATA_MANAGERS[key]
                    and report not in REPORT_MANAGERS[key]
                )
            )
    return False
