"""Module providing forms for the GUI."""

# Python Libraries
from __future__ import annotations

import typing as ty
from abc import abstractmethod
from typing import Any, Optional

import wtforms
from wtforms import (
    BooleanField,
    FieldList,
    FileField,
    FloatField,
    FormField,
    HiddenField,
    IntegerField,
    PasswordField,
    RadioField,
    SelectField,
    SelectMultipleField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.fields import DateField
from wtforms.validators import ValidationError

# Local Modules
from humasol import exceptions, model
from humasol.model import model_interface
from humasol.model import model_validation as model_val
from humasol.ui import forms
from humasol.ui.forms import utils

P = ty.TypeVar("P", bound=model.Person)
F = ty.TypeVar("F", bound=model.FollowupJob)


class PersonForm(forms.ProjectElementForm[P], ty.Generic[P]):
    """Class for a generic person form."""

    person_name = StringField("Name")
    email = StringField("Email")
    phone = StringField("Phone number")
    contact = BooleanField("Contact Person")

    # LABEL will be a constant
    # pylint: disable=invalid-name
    @property
    @abstractmethod
    def LABEL(self) -> str:
        """Provide identifying label of the project component."""

    # pylint: enable=invalid-name

    def from_object(self, obj: P) -> None:
        """Fill in form from object."""
        self.person_name.data = obj.name
        self.email.data = obj.email
        self.phone.data = obj.phone if obj.phone is not None else ""

    def get_data(self) -> dict[str, Any]:
        """Return the data in the form fields.

        Returns
        _______
        Dictionary mapping attributes from the corresponding models to the data
        in the form fields.
        """
        return {
            "name": self.person_name.data,
            "email": self.email.data,
            "phone": self.phone.data,
        }

    def validate_person_name(self, name: wtforms.StringField) -> None:
        """Validate form input for name."""
        if name.data is not None:
            name.data = name.data.strip()

        if not model_val.is_legal_person_name(name.data):
            error = "Name must not be empty and made up of letters"
            self.person_name.errors.append(error)
            raise ValidationError(error)

    def validate_email(self, email: wtforms.StringField) -> None:
        """Validate form input for email."""
        if email.data is not None:
            email.data = email.data.strip()

        if not model_val.is_legal_person_email(email.data):
            error = "Email may not be empty and should be a valid address"
            self.email.errors.append(error)
            raise ValidationError(error)

    def validate_phone(self, phone: wtforms.StringField) -> None:
        """Validate from input for phone."""
        if phone.data is not None:
            phone.data = phone.data.strip()

        if phone.data == "":
            phone.data = None

        if not model_val.is_legal_person_phone(phone.data):
            error = (
                "Phone must be empty or a legal phone number of the form "
                "(+32)123456789"
            )
            self.phone.errors.append(error)
            raise ValidationError(error)


class StudentForm(PersonForm[model.Student]):
    """Class for a humasol student form."""

    LABEL = model_interface.get_student_label()

    university = StringField("University")
    field_of_study = StringField("Field of study")

    def from_object(self, obj: model.Student) -> None:
        """Fill in student from object."""
        super().from_object(obj)
        self.university.data = obj.university
        self.field_of_study.data = obj.field_of_study

    def get_data(self) -> dict[str, Any]:
        """Return the data in the form fields.

        Returns
        _______
        Dictionary mapping attributes from the corresponding models to the data
        in the form fields.
        """
        return {
            "university": self.university.data,
            "field_of_study": self.field_of_study.data,
            **super().get_data(),
        }

    def validate_university(self, uni) -> None:
        """Validate form input for university."""
        if uni.data is not None:
            uni.data = uni.data.strip()

        if not model_val.is_legal_student_university(uni.data):
            error = "Invalid university"
            self.university.errors.append(error)
            raise ValidationError(error)

    def validate_field_of_study(self, field) -> None:
        """Validate form input for field of study."""
        if field.data is not None:
            field.data = field.data.strip()

        if not model_val.is_legal_student_field_of_study(field.data):
            error = "Invalid field of study"
            self.field_of_study.errors.append(error)
            raise ValidationError(error)


class SupervisorForm(PersonForm[model.Supervisor]):
    """Class for a humasol team supervisor form."""

    LABEL = model_interface.get_supervisor_label()

    function = StringField("Function")

    def from_object(self, obj: model.Supervisor) -> None:
        """Fill in supervisor from object."""
        super().from_object(obj)
        self.function.data = obj.function

    def get_data(self) -> dict[str, Any]:
        """Return the data in the form fields.

        Returns
        _______
        Dictionary mapping attributes from the corresponding models to the data
        in the form fields.
        """
        return {"function": self.function.data, **super().get_data()}

    def validate_function(self, function) -> None:
        """Validate form input for supervisor function."""
        if function.data is not None:
            function.data = function.data.strip()

        if not model_val.is_legal_supervisor_function(function.data):
            error = "Invalid supervisor function"
            self.function.errors.append(error)
            raise ValidationError(error)


class PartnerForm(PersonForm[model.Partner]):
    """Class for a humasol partner form."""

    LABEL = model_interface.get_partner_label()

    belgian_partner_type = model_interface.get_belgian_partner_label()
    southern_partner_type = model_interface.get_southern_partner_label()

    class OrganizationForm(forms.HumasolSubform[model.Organization]):
        """Class for an external organization form."""

        organization_name = StringField("Name")
        # TODO: allow selection of logo and saving to file
        logo = FileField("Partner logo")
        country = StringField("Country")

        def __init__(self, **kwargs) -> None:
            """Instantiate form object."""
            super().__init__(**kwargs)
            self._validate = True
            self._partner_type = PartnerForm.belgian_partner_type

        def from_object(self, obj: model.Organization) -> None:
            """Fill in organization form from object."""
            self.organization_name.data = obj.name
            self.logo.data = obj.logo
            self._partner_type = obj.LABEL
            if obj.LABEL == PartnerForm.southern_partner_type:
                self.country.data = obj.country

        def get_data(self) -> dict[str, Any]:
            """Return the data in the form fields.

            Returns
            _______
            Dictionary mapping attributes from the corresponding models to the
            data in the form fields.
            """
            data = {
                "name": self.organization_name.data,
                "logo": self.logo.data,
                "partner_type": self._partner_type,
            }

            if self._partner_type == PartnerForm.southern_partner_type:
                data["country"] = self.country.data

            return data

        def set_validate(self, validate: bool) -> None:
            """Setter for validate flag.

            Indicator for whether the organization should be valdiated.
            """
            self._validate = validate

        def set_partner_type(self, p_type: str) -> None:
            """Set the type of partner.

            Indicates whether this is a southern of belgian partner.
            """
            self._partner_type = p_type

        def validate_organization_name(self, name) -> None:
            """Validate form input for the organization name."""
            if name.data is not None:
                name.data = name.data.strip()

            if self._validate and not model_val.is_legal_organization_name(
                name.data
            ):
                error = "Invalid organization name"
                self.organization_name.errors.append(error)
                raise ValidationError(error)

        def validate_logo(self, logo) -> None:
            """Validate form input for the organization logo."""
            # TODO: add proper logo validation

        def validate_country(self, country) -> None:
            """Validate from input for the organization country."""
            if country.data is not None:
                country.data = country.data.strip()

            if (
                self._validate
                and self._partner_type != PartnerForm.belgian_partner_type
                and not model_val.is_legal_southern_partner_country(
                    country.data
                )
            ):
                error = "Invalid organization country"
                self.country.errors.append(error)
                raise ValidationError(error)

    function = StringField("Function")
    partner_type = SelectField(
        "Type",
        choices=[
            (belgian_partner_type, "Belgian Partner"),
            (southern_partner_type, "Southern Partner"),
        ],
        default=belgian_partner_type,
    )
    organization = FormField(OrganizationForm)

    def from_object(self, obj: model.Partner) -> None:
        """Fill in partner from object."""
        super().from_object(obj)
        self.function.data = obj.function
        self.partner_type.data = obj.organization.LABEL
        self.organization.from_object(obj.organization)

    def get_data(self) -> dict[str, Any]:
        """Return the data in the form fields.

        Returns
        _______
        Dictionary mapping attributes from the corresponding models to the data
        in the form fields.
        """
        return {
            "function": self.function.data,
            "organization": self.organization.get_data(),
            "partner_type": self.partner_type.data,
            **super().get_data(),
        }

    def validate_function(self, function) -> None:
        """Validate form input for partner function."""
        if function.data is not None:
            function.data = function.data.strip()

        if not model_val.is_legal_partner_function(function.data):
            error = "Invalid partner function"
            self.function.errors.append(error)
            raise ValidationError(error)

    def validate_partner_type(self, p_type) -> None:
        """Set the organization partner type.

        Indicates to the organization form validators which partner type to
        consider.
        """
        self.organization.set_partner_type(p_type.data)


class LocationFrom(forms.HumasolSubform[model.Location]):
    """Class for a project location form."""

    street = StringField("Street")
    number = IntegerField("Street number")
    place = StringField("Place")
    country = StringField("Country")
    # TODO: allow the use of coordinates
    latitude = FloatField("Latitude")
    longitude = FloatField("Longitude")

    def from_object(self, obj: model.Location) -> None:
        """Fill in form from the provided location object."""
        self.street.data = obj.address.street
        self.number.data = obj.address.number
        self.place.data = obj.address.place
        self.country.data = obj.address.country
        self.latitude.data = obj.coordinates.latitude
        self.longitude.data = obj.coordinates.longitude

    def get_data(self) -> dict[str, Any]:
        """Return the data in the form fields.

        Returns
        _______
        Dictionary mapping attributes from the corresponding models to the data
        in the form fields.
        """
        return {
            "address": {
                "street": self.street.data,
                "number": self.number.data,
                "place": self.place.data,
                "country": self.country.data,
            },
            "coordinates": {
                "latitude": self.latitude.data,
                "longitude": self.longitude.data,
            },
        }

    def validate_street(self, street) -> None:
        """Validate form input for the street name."""
        if street.data is not None:
            street.data = street.data.strip()

        if not model_val.is_legal_address_street(street.data):
            error = "Invalid street name"
            self.street.errors.append("Invalid street name")
            raise ValidationError(error)

    def validate_number(self, number) -> None:
        """Validate form input for the street number."""
        if (
            self.street.data is not None
            and not model_val.is_legal_address_number(number.data)
        ):
            error = "Invalid street number"
            self.number.errors.append(error)
            raise ValidationError(error)

    def validate_place(self, place) -> None:
        """Validate form input for location place."""
        if place.data is not None:
            place.data = place.data.strip()

        if not model_val.is_legal_address_place(place.data):
            error = "Invalid place"
            self.place.errors.append(error)
            raise ValidationError(error)

    def validate_country(self, country) -> None:
        """Validate form input for location country."""
        if country.data is not None:
            country.data = country.data.strip()

        if not model_val.is_legal_address_country(country.data):
            error = "Invalid country"
            self.country.errors.append(error)
            raise ValidationError(error)

    def validate_latitude(self, latitude) -> None:
        """Validate form input for latitude."""
        if (
            latitude.data is not None
            and not model_val.is_legal_coordinates_latitude(latitude.data)
        ):
            error = "Invalid latitude"
            self.latitude.errors.append(error)
            raise ValidationError(error)

    def validate_longitude(self, longitude) -> None:
        """Validate form input for longitude."""
        if (
            longitude.data is not None
            and not model_val.is_legal_coordinates_longitude(longitude.data)
        ):
            error = "Invalid longitude"
            self.longitude.errors.append(error)
            raise ValidationError(error)


class DataSourceForm(forms.HumasolSubform[model.DataSource]):
    """Class for a project data source form."""

    # A data source is optional for a project,
    # validation should not fail if not provided
    _category: Optional[str] = None

    @staticmethod
    def _format_managers(
        managers: dict[str, set[str]]
    ) -> dict[str, tuple[str, ...]]:
        """Format manager choices for a select field with groups.

        Defined at the top so that it can be used for the variables below.
        """
        return {
            k.capitalize(): tuple(v)
            for k, v in (managers | {"": {"---"}}).items()
        }

    source = StringField("Data source address")
    username = StringField("Username")
    password = PasswordField("Password")
    # TODO: allow retrieval of token,
    #  activate it when appropriate API has been selected
    #  (build in check in API if token retrieval has been written,
    #  only activate if it exists)
    token = HiddenField("Token")
    api_manager = SelectField(
        "Data API manager",
        choices=_format_managers(model_interface.get_api_managers()),
        default="---",
    )
    data_manager = SelectField(
        "Data manager",
        choices=_format_managers(model_interface.get_data_managers()),
        default="---",
    )
    report_manager = SelectField(
        "Report manager",
        choices=_format_managers(model_interface.get_report_managers()),
        default="---",
    )

    def from_object(self, obj: model.DataSource) -> None:
        """Fill in datasource from object."""
        self.source.data = obj.source
        self.api_manager.data = obj.api_manager
        self.data_manager.data = obj.data_manager
        self.report_manager.data = obj.api_manager

    def get_data(self) -> dict[str, Any]:
        """Return the data in the form fields.

        Returns
        _______
        Dictionary mapping attributes from the corresponding models to the data
        in the form fields.
        """
        return {
            "source": self.source.data,
            "username": self.username.data,
            "password": self.password.data,
            "token": self.token.data,
            "api_manager": self.api_manager.data,
        }

    @property
    def has_data(self) -> bool:
        """Indicate whether there is data in this form."""
        return (
            self.source.data is not None and len(self.source.data.strip()) > 0
        )

    def set_category(self, category: str) -> None:
        """Set the selected project category."""
        self._category = category

    def validate(self, extra_validators=None) -> bool:
        """Validate form inputs if a data source is provided."""
        if not self.has_data:
            return True

        return super().validate(extra_validators)

    def validate_source(self, source) -> None:
        """Validate form input for datasource source."""
        if not model_val.is_legal_datasource_source(source.data):
            error = "Invalid data source"
            self.source.errors.append(error)
            raise ValidationError(error)

    def validate_username(self, username) -> None:
        """Validate form input for username."""
        if self.token.data is None and not model_val.is_legal_datasource_user(
            username.data
        ):
            error = "Invalid data source username"
            self.username.errors.append(error)
            raise ValidationError(error)

    def validate_password(self, password) -> None:
        """Validate form input for datasource password."""
        if len(password.data.strip()) == 0:
            password.data = None

        if (
            self.token.data is None
            and not model_val.is_legal_datasource_password(password.data)
        ):
            error = "Invalid data source password"
            self.password.errors.append(error)
            raise ValidationError(error)

    def validate_api_manager(self, api_manager) -> None:
        """Validate form input for API manager."""
        if self._category is None:
            error = "Please select a project category"
            self.api_manager.errors.append(error)
            raise ValidationError(error)

        category: str = self._category
        if not model_val.is_legal_api_manager(api_manager.data, category):
            error = "Invalid API manager for selected category"
            self.api_manager.errors.append(error)
            raise ValidationError(error)


class PeriodForm(forms.HumasolSubform[model.Period]):
    """Class for a project follow-up task period form."""

    interval = IntegerField("Interval length")
    unit = SelectField(
        "Interval unit",
        choices=model_interface.get_time_unit_items(),
    )
    start = DateField("Starting date")
    end = DateField("End date", validators=[wtforms.validators.Optional()])

    def from_object(self, obj: model.Period) -> None:
        """Fill in period from object."""
        self.interval.data = obj.interval
        self.unit.data = obj.unit.name
        self.start.data = obj.start
        self.end.data = obj.end

    def get_data(self) -> dict[str, Any]:
        """Return the data in the form fields.

        Returns
        _______
        Dictionary mapping attributes from the corresponding models to the data
        in the form fields.
        """
        return {
            "interval": self.interval.data,
            "unit": self.unit.data,
            "start_date": self.start.data,
            "end_date": self.end.data,
        }

    def validate_interval(self, interval) -> None:
        """Validate form input for the period's interval."""
        if not model_val.is_legal_period_interval(interval.data):
            error = f"Invalid period interval: {interval.data}"
            self.interval.errors.append(error)
            raise ValidationError(error)

    def validate_unit(self, unit) -> None:
        """Validate from input for the period's time unit."""
        if not model_val.is_legal_period_unit(unit.data):
            error = "Invalid period unit"
            self.unit.errors.append(error)
            raise ValidationError(error)

    def validate_start(self, date) -> None:
        """Validate form input for the period's start."""
        if not model_val.is_legal_period_start(date.data):
            error = "Invalid period start date"
            self.start.errors.append(error)
            raise ValidationError(error)

    def validate_end(self, date) -> None:
        """Validate form input for the period's end date."""
        error = None

        if not model_val.is_legal_period_end(date.data):
            error = "Invalid period end date"
            self.end.errors.append(error)

        if date.data is not None and date.data < self.start.data:
            error = "Invalid period end date. Should be after start date"
            self.end.errors.append(error)

        if error:
            raise ValidationError(error)


class FollowupJobForm(forms.HumasolSubform[F], ty.Generic[F]):
    """Class for a project follow-up work form."""

    # TODO: Allow the selection of existing people
    subscriber = FormField(
        forms.ProjectElementWrapper[PersonForm](
            PersonForm, default=StudentForm.LABEL
        )
    )
    periods = FieldList(FormField(PeriodForm), min_entries=1)

    def from_object(self, obj: F) -> None:
        """Fill in follow-up job from object."""
        self.subscriber.from_object(obj.subscriber)
        utils.fill_field_list(self.periods, obj.periods)

    def get_data(self) -> dict[str, Any]:
        """Return the data in the form fields.

        Returns
        _______
        Dictionary mapping attributes from the corresponding models to the data
        in the form fields.
        """
        return {
            "periods": [p.get_data() for p in self.periods],
            "subscriber": self.subscriber.get_data(),
        }


class SubscriptionForm(FollowupJobForm[model.Subscription]):
    """Class for a project subscription form."""


class TaskForm(FollowupJobForm[model.Task]):
    """Class for a project task form."""

    task_name = StringField("Task name")
    function = StringField("Task description")

    def from_object(self, obj: model.Task) -> None:
        """Fill in task from object."""
        super().from_object(obj)
        self.task_name.data = obj.name
        self.function.data = obj.function

    def get_data(self) -> dict[str, Any]:
        """Return the data in the form fields.

        Returns
        _______
        Dictionary mapping attributes from the corresponding models to the data
        in the form fields.
        """
        return {
            "name": self.task_name.data,
            "function": self.function.data,
            **super().get_data(),
        }

    def validate_task_name(self, name) -> None:
        """Validate form input for the task name."""
        if name.data is not None:
            name.data = name.data.strip()

        if not model_val.is_legal_task_name(name.data):
            error = "Invalid task name"
            self.task_name.errors.append(error)
            raise ValidationError(error)

    def validate_function(self, function) -> None:
        """Validate form input for the task function."""
        if function.data is not None:
            function.data = function.data.strip()

        if not model_val.is_legal_task_function(function.data):
            error = "Invalid task function"
            self.function.errors.append(error)
            raise ValidationError(error)


class ProjectSpecificForm(forms.HumasolSubform[model.Project]):
    """Class containing all elements of project specific forms.

    Add all project-specific forms as subform so that
    the FormField knows about all possible form fields
    Select which one should be validated based on the selected category.

    To add a new project specific section add the form and its category label:
    'new'_category = model_interface.get_category_'new'()
    new_subform = FormField(NewSubform)

    In the subform property method add a match case for the newly added
    subform (before the default case).
    """

    # Add sub-forms and category labels here
    energy_category = model_interface.get_category_energy()
    energy = FormField(forms.energy.EnergyProjectForm)

    def __init__(self, *args, **kwargs) -> None:
        """Instantiate form object."""
        super().__init__(*args, **kwargs)

        self.category: Optional[str] = None

    @property
    def subform(self) -> FormField:
        """Provide the active subform."""
        match self.category:
            case self.energy_category:
                return self.energy.form
            case _:
                raise exceptions.FormError(
                    "Unknown project category for specifics section"
                )

    def from_object(self, obj: model.Project) -> None:
        """Fill in project specifics from object."""
        self.category = obj.category
        self.subform.from_object(obj)

    def get_data(self) -> dict[str, Any]:
        """Return the data in the form fields.

        Returns
        _______
        Dictionary mapping attributes from the corresponding models to the data
        in the form fields.
        """
        return self.subform.get_data()

    def set_category(self, category: str) -> None:
        """Set the correct project category to be matched with a subform."""
        self.category = category

    def validate(self, extra_validators=None) -> bool:
        """Validate the form input."""
        try:
            return self.subform.validate(extra_validators)
        except exceptions.FormError:
            return False


class ProjectForm(forms.HumasolBaseForm[model.Project]):
    """Form for creating a project."""

    # TODO: Add asterisk for required fields
    # TODO: Add contact person input field
    # TODO: Transform SDGs to chip selector (drop down with chips)
    # TODO: Add extra data options for follow-up processing

    name = StringField("Project name")
    date = DateField("Implementation date")
    description = TextAreaField("Project description")
    category = RadioField(
        "Project category",
        choices=[
            (cat_k, cat_v.capitalize())
            for cat_k, cat_v in model_interface.get_project_categories()
        ],
    )
    location = FormField(LocationFrom)
    work_folder = StringField("Student work folder")
    students = FieldList(FormField(StudentForm), min_entries=3)
    supervisors = FieldList(FormField(SupervisorForm))
    partners = FieldList(FormField(PartnerForm))
    sdgs = SelectMultipleField(
        "SDGs",
        choices=model_interface.get_sdgs(),
    )

    specifics = FormField(ProjectSpecificForm)

    tasks = FieldList(FormField(TaskForm))
    data_source = FormField(DataSourceForm)
    dashboard = StringField("Dashboard URL")
    save_data = BooleanField("Should the data be saved?")
    subscriptions = FieldList(FormField(SubscriptionForm))

    submit = SubmitField("Save Project")

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Instantiate project form object.

        Initialize all form input fields. If a project is provided use the
        data to initialize the fields. This can be used for instance when a
        project should be edited.

        Parameters
        __________
        project     -- Optional project object as field data initializer
        should_populate     -- Whether the project data should be used
        """
        super().__init__(*args, **kwargs)

        if self.category.data:
            self.specifics.set_category(self.category.data)

    @property
    def has_followup(self) -> bool:
        """Indicate whether this form contains followup elements."""
        return (
            len(self.tasks) > 0
            or (
                self.data_source.source.data is not None
                and len(self.data_source.source.data) > 0
            )
            or len(self.subscriptions) > 0
        )

    def from_object(self, obj: model.Project) -> None:
        """Fill in the project form from the provided object."""
        # General section
        self.name.data = obj.name
        self.date.data = obj.implementation_date
        self.description.data = obj.description
        self.category.data = obj.category
        self.location.from_object(obj.location)
        self.work_folder.data = obj.work_folder
        utils.fill_field_list(self.students, obj.students)
        utils.fill_field_list(self.supervisors, obj.supervisors)
        utils.fill_field_list(self.partners, obj.partners)
        self.sdgs.process_formdata([sdg.name for sdg in obj.sdgs])

        self.specifics.from_object(obj)

        # Follow-up section
        utils.fill_field_list(self.tasks, obj.tasks)
        if obj.data_source:
            self.data_source.from_object(obj.data_source)
        self.dashboard.data = obj.dashboard
        self.save_data.data = obj.save_data
        utils.fill_field_list(self.subscriptions, obj.subscriptions)

    def get_data(self) -> dict[str, Any]:
        """Return the data in the form fields.

        Returns
        _______
        Dictionary mapping attributes from the corresponding models to the data
        in the form fields.
        """
        data = {
            "name": self.name.data,
            "implementation_date": self.date.data,
            "description": self.description.data,
            "category": self.category.data,
            "location": self.location.get_data(),
            "work_folder": self.work_folder.data,
            "students": [s.get_data() for s in self.students],
            "supervisors": [s.get_data() for s in self.supervisors],
            "partners": [p.get_data() for p in self.partners],
            "sdgs": self.sdgs.data,
            **self.specifics.get_data(),
        }

        data["contact_person"] = data["students"][0].copy()
        data["contact_person"]["type"] = model_interface.get_student_label()

        if len(self.tasks) > 0:
            data["tasks"] = [t.get_data() for t in self.tasks]

        if self.data_source.has_data:
            data["data_source"] = self.data_source.get_data()
            data["save_data"] = self.save_data.data

            if (
                self.dashboard.data is not None
                and len(self.dashboard.data) > 0
            ):
                data["dashboard"] = self.dashboard.data

            if len(self.subscriptions) > 0:
                data["subscriptions"] = [
                    s.get_data() for s in self.subscriptions
                ]

        return data

    def validate(self, extra_validators=None) -> bool:
        """Validate the form inputs."""
        self.specifics.set_category(self.category.data)
        self.data_source.set_category(self.category.data)

        return super().validate(extra_validators)

    def validate_name(self, name: wtforms.StringField) -> None:
        """Validate form input for project name."""
        if name.data is not None:
            name.data = name.data.strip()

        if not model_val.is_legal_project_name(name.data):
            error = "Invalid project name"
            self.name.errors.append(error)
            raise ValidationError(error)

    def validate_date(self, date: wtforms.DateField) -> None:
        """Validate form input for project implementation date."""
        if not model_val.is_legal_project_implementation_date(date.data):
            error = "Invalid project implementation date"
            self.date.errors.append(error)
            raise ValidationError(error)

    def validate_description(self, description: wtforms.TextAreaField) -> None:
        """Validate form input for project description."""
        if description.data is not None:
            description.data = description.data.strip()

        if not model_val.is_legal_project_description(description.data):
            error = "Invalid project description"
            self.description.errors.append(error)
            raise ValidationError(error)

    def validate_category(self, category: wtforms.RadioField) -> None:
        """Validate form input for project category."""
        if not model_val.is_legal_project_category(category.data):
            error = "Invalid project category"
            self.category.errors.append(error)
            raise ValidationError(error)

    def validate_work_folder(self, folder: wtforms.StringField) -> None:
        """Validate form input for project work folder."""
        if not model_val.is_legal_project_work_folder(folder.data):
            error = "Invalid project work folder"
            self.work_folder.errors.append(error)
            raise ValidationError(error)

    def validate_students(self, students: wtforms.FieldList) -> None:
        """Validate form input for project students."""
        if len(students.data) > model_interface.get_project_max_students():
            error = "Too many students for a project"
            self.students.errors.append(error)
            raise ValidationError(error)

    def validate_sdgs(self, sdgs: wtforms.FieldList) -> None:
        """Validate form input for project SDGs."""
        # TODO: do this through model interface
        if len(sdgs.data) == 0:
            error = "At least one SDG must be selected"
            self.sdgs.errors.append(error)
            raise ValidationError(error)

    def validate_dashboard(self, dashboard: wtforms.StringField) -> None:
        """Validate form input for project dashboard."""
        if dashboard.data is not None:
            dashboard.data = dashboard.data.strip()

        if (
            self.data_source.source.data is not None
            and len(self.data_source.source.data) != 0
            and not model_val.is_legal_project_dashboard(dashboard.data)
        ):
            error = f"Invalid project dashboard: {dashboard.data}"
            self.dashboard.errors.append(error)
            raise ValidationError(error)


if __name__ == "__main__":
    pass
