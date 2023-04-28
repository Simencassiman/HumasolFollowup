"""Module with snapshot object.

Classes
_______
Snapshot    -- Creates a snapshot of the provided object
"""

# Python Libraries
from __future__ import annotations

import copy
import typing as ty

T = ty.TypeVar("T")
U = ty.TypeVar("U")


class Snapshot(ty.Generic[T]):
    """Class used to create snapshots of an object's state.

    Can be used to recover state after a certain action.
    Provides static protect method to protect a function against errors
    providing rollback functionality.
    """

    def __init__(self, obj: T, attrs: tuple[str, ...]) -> None:
        """Initialize snapshot.

        Parameters
        __________
        obj     -- Object of which to take a snapshot
        attrs   -- Attributes to recover
        """
        self._obj = obj
        self._snap = copy.deepcopy(obj)
        self._attrs = attrs

    def __enter__(self) -> Snapshot:
        """Enter context."""
        # Mark entry of snapshot context, avoids nested calls when calling
        # super methods
        self._obj.snapshot = True  # type: ignore
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Exit context.

        If an exception was raised, recover the initial state of the snapshot.
        """
        # Leaving snapshot context, delete flag
        del self._obj.snapshot  # type: ignore

        if exc_type:
            self.recover()
            return False

        return True

    @staticmethod
    def protect(func) -> ty.Callable:
        """Wrap function to roll back object attributes after error."""

        def _protected_apply(obj: U, *args, **kwargs) -> None:
            """Apply called function with potential rollback.

            Only rolls back attributes specified by keywords to the function
            call.
            """
            if not hasattr(obj, "snapshot"):
                with Snapshot[U](obj, tuple(kwargs.keys())):
                    func(obj, *args, **kwargs)

        return _protected_apply

    def recover(self) -> None:
        """Recover state from the snapshot object.

        If there is a particular order the object state should be set, it must
        provide an update method. Otherwise, the attributes will simply be set
        in the order they are fetched. Preference is given to the update
        method.

        Parameters
        __________
        obj -- Object who's state to recover
        """
        for attr in self._attrs:
            # Bypass guards, resetting to proper state (but unknown order)
            # pylint: disable=bad-super-call
            super(type(self._obj), self._obj).__setattr__(  # type: ignore
                attr, getattr(self._snap, attr)
            )
            # pylint: enable=bad-super-call
