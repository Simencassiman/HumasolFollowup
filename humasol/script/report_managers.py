"""Module containing report managers."""

# Python Libraries
import abc
import typing as ty
from functools import reduce

# Local modules
from humasol import model, utils
from humasol.script import reports

__all__ = ["ReportManager", "get_report_manager", "report_manager_exists"]

REPORT_MANAGERS = utils.CategorizedRegistry[
    model.ProjectCategory, "ReportManager"
]()


class ReportManager(abc.ABC):
    """Interface for classes responsible for making the analysis reports."""

    @abc.abstractmethod
    def generate_report(
        self, data: dict[str, ty.Any], save_data: bool = False
    ) -> tuple[str, str]:
        """Create a report of the performed analysis."""

    @abc.abstractmethod
    def save_data(self, data: dict) -> str:
        """Save the data to the drive."""


@REPORT_MANAGERS.register(model.ProjectCategory.ENERGY)
class EnergyReportManager(ReportManager):
    """Class for making energy system reports."""

    # TODO: implement functionality

    data_extension = "csv"

    def __init__(self, *_, **__) -> None:
        self.data: dict[str, ty.Any]
        self.report = reports.EnergyReport()

    def create_plot(self, data: dict[str, float]) -> dict:
        """Create a plot for visualisation."""
        # TODO: change to proper return type (plot)

    def generate_report(
        self, data: dict[str, ty.Any], save_data: bool = False
    ) -> tuple[str, str]:
        """Create a report of the performed analysis."""

    def save_data(self, data: dict[str, float]) -> str:
        """Save the data to the drive."""


def get_report_manager(
    category: model.ProjectCategory, manager: str, **kwargs
) -> ReportManager:
    """Instantiate the requested report manager with provided parameters."""
    # TODO: execute checks of existence
    cls = REPORT_MANAGERS[category][manager]
    return cls(**kwargs)


def report_manager_exists(
    manager: str, category: ty.Optional[model.ProjectCategory] = None
) -> bool:
    """Check whether the provided report manager exists.

    Check whether there is a class corresponding to the provided manager for
    the given category that implements the ReportManager interface.

    Parameters
    __________
    manager     -- Name of a class implementing the ReportManager interface
    category    -- Project category to which the manager pertains
    """
    if category and category in REPORT_MANAGERS:
        return manager in REPORT_MANAGERS[category]

    report_managers = reduce(
        lambda x, y: x.union(y),
        map(lambda d: set(d.keys()), REPORT_MANAGERS.values()),
    )

    return manager in report_managers
