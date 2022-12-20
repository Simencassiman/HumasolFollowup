"""Utilities module for forms."""

import inspect
import sys
from typing import Type, TypeVar

T = TypeVar("T")


def get_subclasses(cls: Type[T]) -> list[Type[T]]:
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
    module = sys.modules[cls.__module__]

    return [
        _cls
        for (_, _cls) in inspect.getmembers(module, inspect.isclass)
        if (_cls.__module__ == module.__name__ and issubclass(_cls, cls))
    ]
