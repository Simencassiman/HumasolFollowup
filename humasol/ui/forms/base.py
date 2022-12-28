"""Module providing base classes for Humasol forms."""
from __future__ import annotations

from abc import ABC, ABCMeta, abstractmethod
from collections.abc import Iterator
from typing import Any, Generic, TypeVar

from flask_wtf import FlaskForm
from wtforms import Form as NoCsrfForm
from wtforms import SelectField, ValidationError
from wtforms.form import FormMeta

from humasol.ui import forms


class IHumasolForm(ABC):
    """Humasol form interface."""

    @abstractmethod
    def get_data(self) -> dict[str, Any]:
        """Return the data in the form fields.

        Returns
        _______
        Dictionary mapping attributes from the corresponding models to the data
        in the form fields.
        """


class MetaBaseForm(type(FlaskForm), ABCMeta):  # type: ignore
    """Combine superclasses with distinct meta classes into one meta class."""


class MetaNoCsrfForm(FormMeta, ABCMeta):
    """Combine superclasses with distinct meta classes into one meta class."""


class HumasolBaseForm(FlaskForm, IHumasolForm, ABC, metaclass=MetaBaseForm):
    """Base form to use for any Humasol form."""


class HumasolSubform(NoCsrfForm, IHumasolForm, ABC, metaclass=MetaNoCsrfForm):
    """Superclass to use with any subform."""


class ProjectComponentForm(HumasolSubform):
    """Base form for all project component forms."""

    # LABEL will be a constant
    # pylint: disable=invalid-name
    @property
    @abstractmethod
    def LABEL(self) -> str:
        """Provide identifying label of the project component."""

    # pylint: enable=invalid-name


T = TypeVar("T", bound=ProjectComponentForm)
S = TypeVar("S", bound=ProjectComponentForm)


class ProjectComponentWrapper(Generic[T]):
    """Wraps the possible subclasses of an abstract component type T.

    Can be used to contain different subclasses of one supertype to allow
    dynamic selection in the created form. It provides access to the subform
    class attributes to render a form.
    When form data is provided and validated, this class takes care to only
    route it to the actively selected subclass.
    """

    class Wrapper(HumasolSubform, Generic[S]):
        """Subform wrapping project component subclasses.

        Actual subform that provides the functionality to select the various
        subclasses of the specified form.
        """

        # Should be overriden in subclass
        component_type = SelectField("Select component")

        def __init__(
            self, superclass: type[S], *args: Any, **kwargs: Any
        ) -> None:
            """Instantiate wrapper object.

            Parameters
            __________
            superclass  -- Form superclass from which all components inherit
            """
            self.kwargs = kwargs

            self._components = {
                str(c.LABEL): c for c in forms.utils.get_subclasses(superclass)
            }

            super().__init__(*args, **kwargs)

            self.component_type.choices = classes = [
                (c, c.lower()) for c in self._components.keys()
            ]

            if not self.component_type.data:
                self.component_type.data = classes[0][0]

            self.form = self.component_class(*args, **kwargs)

        @property
        def component(self) -> S:
            """Return the currently instantiated component."""
            return self.form

        @property
        def component_class(self) -> type[S]:
            """Return the currently active component class."""
            return self._components[self.component_type.data]

        @property
        def classes(self) -> tuple[type[S], ...]:
            """Return the wrapped classes."""
            return tuple(self._components.values())

        def get_data(self) -> dict[str, Any]:
            """Return the data in the form fields.

            Returns
            _______
            Dictionary mapping attributes from the corresponding models to the
            data in the form fields.
            """
            return {
                "type": self.component_type.data,
                **(self.component.get_data()),
            }

        def process(
            self,
            formdata=None,
            obj=None,
            data=None,
            extra_filters=None,
            **kwargs,
        ) -> None:
            """Process default and input data with each field.

            Parameters
            __________
            formdata    -- Input data coming from the client, usually
                            ``request.form`` or equivalent. Should provide a
                            "multidict" interface to get a list of values for
                            a given key, such as what Werkzeug, Django, and
                            WebOb provide.
            obj     -- Take existing data from attributes on this object
                        matching form field attributes. Only used if
                        ``formdata`` is  not passed.
            data    -- Take existing data from keys in this dict matching
                        form field attributes. ``obj`` takes precedence if it
                        also has a matching attribute. Only used if
                        ``formdata`` is not passed.
            extra_filters   -- A dict mapping field attribute names to
                                lists of extra filter functions to run. Extra
                                filters run after filters passed when creating
                                the field. If the form has
                                ``filter_<fieldname>``, it is the last extra
                                filter.
            kwargs  -- Merged with ``data`` to allow passing existing data as
                        parameters. Overwrites any duplicate keys in ``data``.
                        Only used if ``formdata`` is not passed.
            """
            super().process(
                formdata=formdata,
                obj=obj,
                data=data,
                extra_filters=extra_filters,
                **kwargs,
            )

            if self.component_type.data:
                self.form = self.component_class(formdata=formdata, **kwargs)

        def validate(self, extra_validators=None) -> bool:
            """Validate form input for component type."""
            if (
                extra_validators is not None
                and "component_type" in extra_validators
            ):
                extra = extra_validators["component_type"]
            else:
                extra = tuple()

            if not self.form:
                return False

            return self.component_type.validate(
                self, extra
            ) and self.form.validate(extra_validators)

        def validate_component_type(self, comp_type) -> None:
            """Validate form input for component type."""
            if comp_type.data not in self._components:
                raise ValidationError("Invalid component label")

        def __iter__(self) -> Iterator[str]:
            """Iterate over the classes contained in this wrapper."""
            return iter(self._components)

        def __getitem__(self, name):
            """Retrieve and item by key.

            Returns
            _______
            If the key matches one of the component classes, returns the class.
            Otherwise, the key is used to access the item of the currently
            active component.
            """
            if name in self._components:
                return self._components[name]
            return self.form[name]

    def __init__(self, *args, **kwargs) -> None:
        """Instantiate a project component wrapper.

        The wrapper creates a lambda to defer the form instantiation until the
        FormField does it. This allows the correct prefixes to be created.

        Parameters
        __________
        Parameters to configure the Wrapper object. See its __init__ method
        for more details.
        """
        self.wrapper = lambda **kwg: ProjectComponentWrapper.Wrapper[T](
            *args, **{**kwargs, **kwg}  # Joining kwargs avoids mypy error
        )

    def __call__(self, **kwargs) -> ProjectComponentWrapper.Wrapper[T]:
        """Create the stored wrapper object.

        Create the object using the stored lambda and newly provided
        parameters, essentially unwrapping the initially intended object.
        """
        return self.wrapper(**kwargs)


if __name__ == "__main__":

    class MockComponent(ProjectComponentForm):
        """Mock component object to instantiate the abstract superclass."""

        LABEL = "mock"

        def get_data(self) -> dict[str, Any]:
            """Return the data in the form fields.

            Returns
            _______
            Dictionary mapping attributes from the corresponding models to
            the data in the form fields.
            """
            return {}

    f = ProjectComponentWrapper[MockComponent](MockComponent)

    print(f().component_type.choices)
