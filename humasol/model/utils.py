"""Utility functions for the modules in the model package."""

# Python Libraries
from typing import Any, Callable, Dict, List, TypeVar

# Generic type variables
T = TypeVar("T")
V = TypeVar("V")


# pylint: disable=too-many-arguments
def merge_update_list(
    old: List[T],
    new: List[Dict[str, Any]],
    identifiers: List[V],
    identifier_mapper: Callable[[T], V],
    merge_mapper: Callable[[T, Dict[str, Any]], T],
    constructor: Callable[[Dict[str, Any]], T],
) -> List[T]:
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
