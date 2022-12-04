"""Module providing utility functions for Flask and app setup."""
# Python Libraries
from functools import reduce
from typing import TypeVar

# Local modules
from humasol.model import Project

T = TypeVar("T")


def add_to_dict(
    dic: dict[str, list[T]], key: str, value: T
) -> dict[str, list[T]]:
    """Add the provided value to the dictionary with corresponding key.

    Append the given value to the list correspinding to the given key in the
    dictionary.

    Parameters
    __________
    dic     -- Dictionary with keys mapping to lists
    key     -- Key on which to index dic
    value   -- Object to add to the dictionary
    """
    if key in dic:
        dic[key].append(value)
    else:
        dic[key] = [value]

    return dic


def categorize_projects(projects: list[Project]) -> dict[str, list[Project]]:
    """Group projects by category."""
    if projects is None:
        return {}

    return reduce(
        lambda dic, kv: add_to_dict(dic, *kv),
        map(lambda pr: (pr.category.category_name, pr), projects),
        {},
    )
