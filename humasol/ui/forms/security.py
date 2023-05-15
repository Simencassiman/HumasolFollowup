"""Module with forms required for security purposes."""


# Python Libraries
import typing as ty

import flask_security.forms as sec_forms
from wtforms import SelectMultipleField, SubmitField, ValidationError

# Local modules
from humasol.model import model_authorization as ma
from humasol.ui import forms


class RegisterForm(
    forms.HumasolBaseForm,
    sec_forms.UniqueEmailFormMixin,
    sec_forms.PasswordFormMixin,
):
    """Form for user registration."""

    roles = SelectMultipleField(
        "Roles",
        choices=[(r.name, r.content) for r in ma.get_roles_all()],
    )
    submit = SubmitField(sec_forms.get_form_field_label("register"))

    def get_data(self) -> dict[str, ty.Any]:
        """Return the data in the form fields.

        Returns
        _______
        Dictionary containing 'email', 'password' and 'roles'.
        """
        return {
            "email": self.email.data,
            "password": self.password.data,
            "roles": self.roles.data,
        }

    def validate_roles(self, roles: SelectMultipleField) -> None:
        """Validate form input for user roles."""
        # TODO: do this through model interface
        if len(roles.data) == 0:
            raise ValidationError("At least one role must be selected")
