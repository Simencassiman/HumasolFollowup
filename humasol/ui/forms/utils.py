"""Utilities module for forms."""

import inspect
from types import ModuleType
from typing import Type, TypeVar

T = TypeVar("T")


def get_subclasses(module: ModuleType, cls: Type[T]) -> list[Type[T]]:
    """Retrieve all subclasses of the provided type.

    Search the provided module for all strict subclasses of the provided type.

    Parameters
    __________
    module  -- Python module through which to search
    cls     -- Superclass bound

    Returns
    List of classes that are a strict subclass of cls and are defined in
    module.
    """
    return [
        m[1]
        for m in inspect.getmembers(module, inspect.isclass)
        if (
            m[1].__module__ == module.__name__
            and issubclass(m[1], cls)
            and not m[1] == cls
        )
    ]
