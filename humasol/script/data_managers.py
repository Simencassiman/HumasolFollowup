"""Module containing data managers."""

# Python Libraries
import abc
import typing as ty
from functools import reduce

# Local modules
from humasol import model, utils

__all__ = ["DataManager", "data_manager_exists", "get_data_manager"]

DATA_MANAGERS = utils.CategorizedRegistry[
    model.ProjectCategory, "DataManager"
]()


class DataManager(abc.ABC):
    """Interface for data processing classes."""

    @abc.abstractmethod
    def create_summary(self) -> dict[str, ty.Any]:
        """Create a short summary of the processed data."""

    @abc.abstractmethod
    def get_status(self) -> str:
        """Get the system status."""

    @abc.abstractmethod
    def handle_extensive_data(self) -> dict[str, ty.Any]:
        """Create the full analysis overview of the processed data."""

    @abc.abstractmethod
    def process_data(self, data: dict) -> dict[str, ty.Any]:
        """Process retrieved system data."""


@DATA_MANAGERS.register(model.ProjectCategory.ENERGY)
class EnergyDataManager(DataManager):
    """Energy data processing class.

    Processes and analyses the incoming data for energy projects.
    """

    # TODO: implement functionality

    def __init__(self, *_, **__) -> None:
        self.data: dict

    def create_summary(self) -> dict[str, ty.Any]:
        """Create a short summary of the processed data."""

    def get_status(self) -> str:
        """Get the system status."""

    def handle_extensive_data(self) -> dict[str, ty.Any]:
        """Create the full analysis overview of the processed data."""

    def process_data(self, data: dict) -> dict[str, ty.Any]:
        """Process retrieved system data."""


def data_manager_exists(
    manager: str, category: ty.Optional[model.ProjectCategory] = None
) -> bool:
    """Check whether the provided folder manager exists.

    Check whether there is a class corresponding to the provided manager for
    the given category that implements the DataManager interface.

    Parameters
    __________
    manager     -- Name of a class implementing the DataManager interface
    category    -- Project category to which the manager pertains
    """
    if category and category in DATA_MANAGERS:
        return manager in DATA_MANAGERS[category]

    data_managers = reduce(
        lambda x, y: x.union(y),
        map(lambda d: set(d.keys()), DATA_MANAGERS.values()),
    )

    return manager in data_managers


def get_data_manager(
    category: model.ProjectCategory, manager: str, **kwargs
) -> DataManager:
    """Instantiate the requested data manager with the provided parameters."""
    # TODO: execute checks of existence
    cls = DATA_MANAGERS[category][manager]
    return cls(**kwargs)
