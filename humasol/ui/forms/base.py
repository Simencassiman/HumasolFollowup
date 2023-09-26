"""Module providing base classes for Humasol forms."""

# Python Libraries
from __future__ import annotations

import typing as ty
from abc import ABC, ABCMeta, abstractmethod
from collections.abc import Iterator

from flask_wtf import FlaskForm
from wtforms import Form as NoCsrfForm
from wtforms import SelectField, ValidationError
from wtforms.form import FormMeta

# Local modules
from humasol import model
from humasol.ui import forms

U = ty.TypeVar("U", bound=model.Model)


class IHumasolForm(ABC, ty.Generic[U]):
    """Humasol form interface."""

    @abstractmethod
    def from_object(self, obj: U) -> None:
        """Fill the form from the object it represents.

        Parameters
        __________
        obj     -- Object containing the information to fill in the form
        """

    @abstractmethod
    def get_data(self) -> dict[str, ty.Any]:
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


class HumasolBaseForm(
    ty.Generic[U], FlaskForm, IHumasolForm[U], ABC, metaclass=MetaBaseForm
):
    """Base form to use for any Humasol form."""


class HumasolSubform(
    ty.Generic[U], NoCsrfForm, IHumasolForm[U], ABC, metaclass=MetaNoCsrfForm
):
    """Superclass to use with any subform."""


class ProjectElementForm(ty.Generic[U], HumasolSubform[U]):
    """Base form for all project component forms."""

    # LABEL will be a constant
    # pylint: disable=invalid-name
    @property
    @abstractmethod
    def LABEL(self) -> str:
        """Provide identifying label of the project component."""

    # pylint: enable=invalid-name


T = ty.TypeVar("T", bound=ProjectElementForm)
S = ty.TypeVar("S", bound=ProjectElementForm)


class ProjectElementWrapper(ty.Generic[T]):
    """Wraps the possible subclasses of an abstract element type T.

    Can be used to contain different subclasses of one supertype to allow
    dynamic selection in the created form. It provides access to the subform
    class attributes to render a form.
    When form data is provided and validated, this class takes care to only
    route it to the actively selected subclass.
    """

    class Wrapper(HumasolSubform[S], ty.Generic[S]):
        """Subform wrapping project element subclasses.

        Actual subform that provides the functionality to select the various
        subclasses of the specified form.
        """

        element_type = SelectField("Select element")

        def __init__(
            self,
            superclass: type[S],
            *args: ty.Any,
            default: str = None,
            **kwargs: ty.Any,
        ) -> None:
            """Instantiate wrapper object.

            Parameters
            __________
            superclass  -- Form superclass from which all elements inherit
            """
            self.kwargs = kwargs
            self._elements = {
                str(c.LABEL): c for c in forms.utils.get_subclasses(superclass)
            }

            super().__init__(*args, **kwargs)

            self.element_type.choices = classes = [
                (c, c.lower().capitalize()) for c in self._elements.keys()
            ]

            if not self.element_type.data:
                self.element_type.data = default or classes[0][0]

            self.form = self.element_class(*args, **kwargs)

        @property
        def element(self) -> S:
            """Return the currently instantiated element."""
            return self.form

        @property
        def element_class(self) -> type[S]:
            """Return the currently active element class."""
            return self._elements[self.element_type.data]

        @property
        def classes(self) -> tuple[type[S], ...]:
            """Return the wrapped classes."""
            return tuple(self._elements.values())

        def from_object(self, obj: S) -> None:
            """Fill in wrapper with object."""
            self.element_type.data = obj.LABEL
            self.form = self.element_class(prefix=self._prefix)
            self.element.from_object(obj)

        def get_data(self) -> dict[str, ty.Any]:
            """Return the data in the form fields.

            Returns
            _______
            Dictionary mapping attributes from the corresponding models to the
            data in the form fields.
            """
            return {
                "type": self.element_type.data,
                **(self.element.get_data()),
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

            if self.element_type.data:
                self.form = self.element_class(
                    formdata=formdata, prefix=self._prefix, **kwargs
                )

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

            return self.element_type.validate(
                self, extra
            ) and self.form.validate(extra_validators)

        def validate_component_type(self, comp_type) -> None:
            """Validate form input for component type."""
            if comp_type.data not in self._elements:
                error = "Invalid component label"
                self.element_type.errors.append(error)
                raise ValidationError(error)

        def __iter__(self) -> Iterator[str]:
            """Iterate over the classes contained in this wrapper."""
            return iter(self._elements)

        def __getitem__(self, name):
            """Retrieve and item by key.

            Returns
            _______
            If the key matches one of the component classes, returns the class.
            Otherwise, the key is used to access the item of the currently
            active component.
            """
            if name in self._elements:
                return self._elements[name]
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
        self.wrapper = lambda **kwg: ProjectElementWrapper.Wrapper[T](
            *args, **{**kwargs, **kwg}  # Joining kwargs avoids mypy error
        )

    def __call__(self, **kwargs) -> ProjectElementWrapper.Wrapper[T]:
        """Create the stored wrapper object.

        Create the object using the stored lambda and newly provided
        parameters, essentially unwrapping the initially intended object.
        """
        return self.wrapper(**kwargs)


if __name__ == "__main__":

    class MockComponent(ProjectElementForm):
        """Mock component object to instantiate the abstract superclass."""

        LABEL = "mock"

        def from_object(self, obj: U) -> None:
            """Nothing to do..."""

        def get_data(self) -> dict[str, ty.Any]:
            """Return the data in the form fields.

            Returns
            _______
            Dictionary mapping attributes from the corresponding models to
            the data in the form fields.
            """
            return {}

    f = ProjectElementWrapper[MockComponent](MockComponent)

    print(f().element_type.choices)
