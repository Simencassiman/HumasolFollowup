"""Utility functions for the modules in the model package."""

# Python Libraries
import itertools
import typing as ty

# Local modules
from humasol import exceptions

# Generic type variables
T = ty.TypeVar("T")
V = ty.TypeVar("V")


def check_guards(obj: ty.Any, key: str, value: ty.Any) -> None:
    """Check all defined guards of the object for the provided key.

    Check if all guards are valid for the given attribute value pair if any are
    defined for the given object.

    Guards are detected in the form of is/are_legal/valid_{key}.
    E.g., for an attribute name, the guards could be is_legal_name or
    is_valid_name. For an attribute names, the plural forms should be used
    (though this is not enforced).

    Parameters
    __________
    obj     -- Object on which to check the guards
    key     -- Attribute for which to check the guards
    value   -- Value with which to check the guards
    """
    for num, att in itertools.product(("is", "are"), ("legal", "valid")):
        try:
            if hasattr(obj, guard := f"{num}_{att}_{key}") and not getattr(
                obj, guard
            )(value):
                raise exceptions.IllegalArgumentException(
                    f"Illegal value for {key}."
                )
        except (AttributeError, TypeError):
            # In initialization could be that not all variables have been
            # initialized. This should be foreseen, but to simplify things,
            # just catch the exception...
            ...


# pylint: disable=too-many-arguments


def merge_update_list(
    old: list[T],
    new: list[dict[str, ty.Any]],
    identifiers: list[V],
    identifier_mapper: ty.Callable[[T], V],
    merge_mapper: ty.Callable[[T, dict[str, ty.Any]], T],
    constructor: ty.Callable[[dict[str, ty.Any]], T],
) -> list[T]:
    """Merge the old and new lists of objects.

    Update the old list with the new list of parameters. Remove if not
    present in new list, update if present in both lists, construct object if
    not present in old list.

    Arguments:
    old          -- Old list of object to be updated
    new          -- New list of parameter dictionaries which should be merged
                     with the old list
    identifiers  -- List of identifiers (of the new list) based on which the
                     objects and parameters can be linked
    identifier_mapper -- Callable mapping the old objects to their identifiers
    merge_mapper -- Callable used to merge the parameters with an existing
                     object
    constructor  -- Constructor callable to construct a new object instance.
                     To use when there is no existing old object matching the
                     new parameters
    """
    # TODO: Check correctness
    new_objects = []

    for obj in old:
        if identifier_mapper(obj) in identifiers:
            idx = identifiers.index(identifier_mapper(obj))
            new_objects.append(merge_mapper(obj, new.pop(idx)))
            identifiers.pop(idx)

    new_objects += [constructor(obj) for obj in new]

    return new_objects


# pylint: enable=too-many-arguments
