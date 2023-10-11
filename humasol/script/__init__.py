"""Automatic reporting code.

Package containing all the code responsible for the automatic script that
keeps Humasol and partners informed about the projects' status and operations.
"""

# Local modules
from humasol import model

from .api_managers import *
from .data_managers import *
from .report_managers import *


def same_category_managers(api: str, data: str, report: str) -> bool:
    """Check whether the provided managers belong to the same category.

    Arguments:
    api     -- Name of a class implementing the APIManager interface
    folder    -- Name of a class implementing the DataManager interface
    report  -- Name of a class implementing the ReportManager interface
    """
    for category in model.ProjectCategory.categories():
        if api_manager_exists(api, category):
            break
    else:
        return False

    return data_manager_exists(data, category) and report_manager_exists(
        report, category
    )
