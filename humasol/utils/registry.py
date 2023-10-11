"""Registry classes for registering classes."""

# Python Libraries
import typing as ty

__all__ = ["Registry", "CategorizedRegistry"]

_T = ty.TypeVar("_T")
K = ty.TypeVar("K")
V = ty.TypeVar("V")


class Registry(dict[str, type[V]], ty.Generic[V]):
    """Registry class for collecting related classes.

    A registry is a dictionary that can be used as a decorator for class
    definitions to collect them in the same registry object. The classes
    can then be retrieved by their name.

    Class names are made case-insensitive.
    """

    def __getitem__(self, item: str) -> type[V]:
        """Retrieve registry item by case-insensitive key."""
        return super().__getitem__(item.casefold())

    def get(
        self, __key: str, default: type[V] | _T = None  # type: ignore
    ) -> type[V] | _T:
        """Retrieve registry item by case-insensitive key with fallback."""
        return super().get(__key.casefold(), default)

    def register(self) -> ty.Callable[[type[V]], None]:
        """Decorate class to register them in this registry."""

        def _register(cls: type[V]) -> None:
            self[cls.__name__.casefold()] = cls

        return _register


class CategorizedRegistry(dict[K, dict[str, type[V]]], ty.Generic[K, V]):
    """Categorized registry class for collecting related classes in categories.

    A registry is a dictionary that can be used as a decorator for class
    definitions to collect them in the same registry object. The classes
    can then be retrieved by their name. On top of that, this is a two-level
    registry, where the first level is the category or group of elements, and
    the second level is the actual class registry.

    Class names are made case-insensitive.
    """

    def register(self, key: K) -> ty.Callable[[type[V]], None]:
        """Decorate class to register them in this registry.

        Parameters
        __________
        key    -- Key of the subcollection in which to register the decorated
                class
        """

        def _register(cls: type[V]) -> None:
            if key not in self:
                # Use the registry class to use case-insensitive indexing
                self[key] = Registry[V]()

            self[key][cls.__name__.casefold()] = cls

        return _register
