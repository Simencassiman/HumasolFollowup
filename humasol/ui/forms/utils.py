"""Utilities module for forms."""

# Python Libraries
import inspect
import sys
import typing as ty
from types import ModuleType

import wtforms.fields.core
from wtforms import FieldList

# Local modules
from humasol.ui import forms

T = ty.TypeVar("T")


def field_list_class(field: wtforms.fields.core.UnboundField) -> type:
    """Extract form type from the provided unbound FieldList.

    When binding a field to class attribute without providing it with a filled
    in form, it returns an UnboundField, with its arguments stored in the
    'args' attribute, and its class stored in the 'field_class' attribute.
    A FieldList takes as argument a Field, which is stored as the field_class.
    If this class is a FormField, it will store the actual form class in its
    arguments too. See 'form_field_class' for more info.
    """
    unbound_field = field.args[0]
    if issubclass(unbound_field.field_class, wtforms.FormField):
        return form_field_class(unbound_field)
    return unbound_field.field_class


def fill_field_list(field: wtforms.FieldList, objs: list[ty.Any]) -> None:
    """Fill in a form field list with the provided objects."""
    len_field = len(field)
    for i, obj in enumerate(objs):
        if len_field >= i + 1:
            field[i].from_object(obj)
        else:
            field.append_entry()
            field[-1].from_object(obj)


def form_field_class(field: wtforms.fields.core.UnboundField) -> type:
    """Extract form type from the provided unbound FormField.

    When binding a field to class attribute without providing it with a filled
    in form, it returns an UnboundField, with its arguments stored in the
    'args' attribute, and its class stored in the 'field_class' attribute.
    The FormField takes as first argument the form class it wraps, which is
    stored as the first argument of the 'args' attribute.
    """
    return field.args[0]


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
