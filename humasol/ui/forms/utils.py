"""Utilities module for forms."""

# Python Libraries
import inspect
import sys
import typing as ty
from types import ModuleType

from wtforms import FieldList

# Local modules
from humasol.ui import forms

T = ty.TypeVar("T")


def get_subclasses(
    cls: type[T], module: ty.Optional[ModuleType] = None
) -> list[type[T]]:
    """Retrieve all subclasses of the provided type.

    Search the provided module for all concrete subclasses of the provided
    type.

    Parameters
    __________
    cls     -- Superclass bound
    module  -- Python module through which to search

    Returns
    List of classes that are a strict subclass of cls and are defined in
    module.
    """
    if not module:
        module = sys.modules[cls.__module__]

    return [
        _cls_i
        # Get all classes in module
        for (_, _cls) in inspect.getmembers(module, inspect.isclass)
        # Get all inner classes (if any)
        for (_, _cls_i) in [("", _cls)]
        + inspect.getmembers(_cls, inspect.isclass)
        # Check that
        if (
            _cls.__module__ == module.__name__  # Cls defined in the module
            and issubclass(_cls_i, cls)  # Is indeed subclass
            and not inspect.isabstract(_cls_i)  # Is not abstract
        )
    ]


def unwrap(
    field_list: FieldList,
) -> forms.base.ProjectElementWrapper.Wrapper:
    """Unwraps the form field unbound form class.

    Creates an instance of the wrapper so that its form fields become
    accessible to be rendered.
    """
    return field_list.unbound_field.args[0]()
