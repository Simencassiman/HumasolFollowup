"""Module containing data API managers."""

# Python Libraries
import abc
import typing as ty
from functools import reduce

# Local modules
from humasol import model, utils

__all__ = ["APIManager", "api_manager_exists", "get_api_manager"]

API_MANAGERS = utils.CategorizedRegistry[model.ProjectCategory, "APIManager"]()


class APIManager(abc.ABC):
    """Interface for communication managers with third party APIs."""

    @abc.abstractmethod
    def authenticate(self, credentials: dict[str, ty.Any]) -> str:
        """Retrieve and authentication token from the data source."""

    @abc.abstractmethod
    def get_data(
        self, link: str, method: str, extra_data: dict[str, ty.Any] = None
    ) -> dict:
        """Retrieve the requested data from the data source."""


@API_MANAGERS.register(model.ProjectCategory.ENERGY)
class VictronAPI(APIManager):
    """Class responsible for communicating with the Victron data API."""

    # TODO: implement functionality

    base_url = ""
    attribute_codes = list[str]()
    url_extensions = dict[str, str]

    def __init__(self, *_, **__) -> None:
        """Instantiate object of this class."""
        super().__init__()

    def authenticate(self, credentials: dict[str, ty.Any]) -> str:
        """Retrieve and authentication token from the Victron API."""

    def get_data(
        self, link: str, method: str, extra_data: dict[str, ty.Any] = None
    ) -> dict:
        """Retrieve the requested data from the Victron data API."""


def api_manager_exists(
    manager: str, category: ty.Optional[model.ProjectCategory] = None
) -> bool:
    """Check whether the provided API manager exists.

    Check whether there is a class corresponding to the provided manager for
    the given category that implements the APIManager interface.

    Parameters
    __________
    manager     -- Name of a class implementing the APIManager interface
    category    -- Project category to which the manager pertains
    """
    if category and category in API_MANAGERS:
        return manager in API_MANAGERS[category]

    api_managers = reduce(
        lambda x, y: x.union(y),
        map(lambda d: set(d.keys()), API_MANAGERS.values()),
    )

    return manager in api_managers


def get_api_manager(
    category: model.ProjectCategory, manager: str, **kwargs
) -> APIManager:
    """Instantiate the requested API manager with the provided parameters."""
    # TODO: execute checks of existence
    cls = API_MANAGERS[category][manager]
    return cls(**kwargs)
