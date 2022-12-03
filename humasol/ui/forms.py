"""Module providing forms for the GUI."""

# Python Libraries
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

import wtforms
from flask_wtf import FlaskForm
from wtforms import BooleanField, FieldList, FileField, FloatField
from wtforms import Form as NoCsrfForm
from wtforms import (
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
from wtforms.fields import DateField, DecimalRangeField
from wtforms.validators import ValidationError

# Local Modules
from ..model import model_interface
from ..model import model_validation as model_val

if TYPE_CHECKING:
    from .. import model


class PersonForm(NoCsrfForm):
    """Class for a generic person form."""

    person_name = StringField("Name")
    email = StringField("Email")
    phone = StringField("Phone number")

    @staticmethod
    def person_to_dict(pers: model.Person) -> dict[str, Any]:
        """Create a dictionary with the data from the given person object.

        Returns
        _______
        A dictionary with keys matching the form items and as values
        the data from the provided person.
        """
        return {
            "person_name": pers.name,
            "email": pers.email,
            "phone": pers.phone,  # if pers.phone is not None else ''
        }

    def validate_person_name(self, name: wtforms.StringField) -> None:
        """Validate form input for name."""
        if name.data is not None:
            name.data = name.data.strip()

        if not model_val.is_legal_person_name(name.data):
            raise ValidationError(
                "Name must not be empty and made up of letters"
            )

    def validate_email(self, email: wtforms.StringField) -> None:
        """Validate form input for email."""
        if email.data is not None:
            email.data = email.data.strip()

        if not model_val.is_legal_person_email(email.data):
            raise ValidationError(
                "Email may not be empty and should be a valid address"
            )

    def validate_phone(self, phone: wtforms.StringField) -> None:
        """Validate from input for phone."""
        if phone.data is not None:
            phone.data = phone.data.strip()

        if phone.data == "":
            phone.data = None

        if not model_val.is_legal_person_phone(phone.data):
            raise ValidationError(
                "Phone must be empty or a legal phone number of the form "
                "(+32)123456789"
            )


class StudentForm(PersonForm):
    """Class for a humasol student form."""

    university = StringField("University")
    field_of_study = StringField("Field of study")

    @staticmethod
    def student_to_dict(student: model.Student) -> dict[str, Any]:
        """Create a dictionary with the data from the given student object.

        Returns
        _______
        A dictionary with keys matching the form items and as values
        the data from the provided student.
        """
        data = PersonForm.person_to_dict(student)

        data["university"] = student.university
        data["field_of_study"] = student.field_of_study

        return data

    def validate_university(self, uni) -> None:
        """Validate form input for university."""
        if uni.data is not None:
            uni.data = uni.data.strip()

        if not model_val.is_legal_student_university(uni.data):
            raise ValidationError("Invalid university")

    def validate_field_of_study(self, field) -> None:
        """Validate form input for field of study."""
        if field.data is not None:
            field.data = field.data.strip()

        if not model_val.is_legal_student_field_of_study(field.data):
            raise ValidationError("Invalid field of study")


class SupervisorForm(PersonForm):
    """Class for a humasol team supervisor form."""

    function = StringField("Function")

    @staticmethod
    def supervisor_to_dict(supervisor: model.Supervisor) -> dict[str, Any]:
        """Create a dictionary with the data from the given supervisor object.

        Returns
        _______
        A dictionary with keys matching the form items and as values
        the data from the provided supervisor.
        """
        data = PersonForm.person_to_dict(supervisor)

        data["function"] = supervisor.function

        return data

    def validate_function(self, function) -> None:
        """Validate form input for supervisor function."""
        if function.data is not None:
            function.data = function.data.strip()

        if not model_val.is_legal_supervisor_function(function.data):
            raise ValidationError("Invalid supervisor function")


class PartnerForm(PersonForm):
    """Class for a humasol partner form."""

    belgian_partner_type = model_interface.get_belgian_partner_label()
    southern_partner_type = model_interface.get_southern_partner_label()

    class OrganizationForm(NoCsrfForm):
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

        @staticmethod
        def organization_to_dict(
            organization: model.Organization,
        ) -> tuple[str, dict[str, Any]]:
            """Create a dictionary with the data from the given organization.

            Returns
            _______
            A dictionary with keys matching the form items and as values
            the data from the provided organization.
            """
            partner_type, country = (
                (PartnerForm.southern_partner_type, organization.country)
                if isinstance(organization, model.SouthernPartner)
                else (PartnerForm.belgian_partner_type, "")
            )

            data = {
                "organization_name": organization.name,
                # TODO: Check how filling in the logo works
                "logo": organization.logo,
                "country": country,
            }

            return partner_type, data

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
                raise ValidationError("Invalid organization name")

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
                raise ValidationError("Invalid organization country")

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

    @staticmethod
    def partner_to_dict(partner: model.Partner) -> dict[str, Any]:
        """Create a dictionary with the data from the given partner object.

        Returns
        _______
        A dictionary with keys matching the form items and as values
        the data from the provided partner.
        """
        data = PersonForm.person_to_dict(partner)

        data["function"] = partner.function
        (
            data["partner_type"],
            data["organization"],
        ) = PartnerForm.OrganizationForm.organization_to_dict(
            partner.organization
        )

        return data

    def validate_function(self, function) -> None:
        """Validate form input for partner function."""
        if function.data is not None:
            function.data = function.data.strip()

        if not model_val.is_legal_partner_function(function.data):
            raise ValidationError("Invalid partner function")

    def validate_partner_type(self, p_type) -> None:
        """Set the organization partner type.

        Indicates to the organization form validators which partner type to
        consider.
        """
        self.organization.set_partner_type(p_type.data)


class SubscriberForm(StudentForm, SupervisorForm, PartnerForm):
    """Class for a subscriber form.

    A subscriber can be any type of person.
    Overrides the form field validators to select an appropriate subset when
    the subscriber type is known.
    """

    student_type = model_interface.get_student_label()
    supervisor_type = model_interface.get_supervisor_label()
    partner_type = model_interface.get_partner_label()

    def __init__(self, **kwargs) -> None:
        """Instantiate the subscriber form."""
        super().__init__(**kwargs)
        self._sub_type: Optional[str] = None

    def set_sub_type(self, sub: str) -> None:
        """Set the type of subscriber.

        The type is important to use the appropriate validators.
        """
        self._sub_type = sub

    def validate(self, extra_validators=None) -> bool:
        """Validate the form inputs.

        Configure the organization subform for correct validation.
        Call super method to continue normal validation flow.
        """
        if self._sub_type == self.partner_type:
            self.organization.set_validate(True)
        else:
            self.organization.set_validate(False)

        return super().validate(extra_validators)

    def validate_university(self, uni) -> None:
        """Validate form input for university.

        Only validate this input when the subscriber is a student.
        """
        if self._sub_type == self.student_type:
            super().validate_university(uni)

    def validate_field_of_study(self, field) -> None:
        """Validate form input for field of study.

        Only validate this input when the subscriber is a student.
        """
        if self._sub_type == self.student_type:
            super().validate_field_of_study(field)

    def validate_function(self, function) -> None:
        """Validate form input for function.

        Only validate this input if the subscriber is a supervisor or a
        partner, and select the appropriate one.
        """
        if self._sub_type == self.supervisor_type:
            SupervisorForm.validate_function(self, function)
        elif self._sub_type == self.partner_type:
            PartnerForm.validate_function(self, function)


class LocationFrom(NoCsrfForm):
    """Class for a project location form."""

    street = StringField("Street")
    number = IntegerField("Street number")
    place = StringField("Place")
    country = StringField("Country")
    # TODO: allow the use of coordinates
    latitude = FloatField("Latitude")
    longitude = FloatField("Longitude")

    @staticmethod
    def location_to_dict(location: model.Location) -> dict[str, Any]:
        """Create a dictionary with the data from the given location object.

        Returns
        _______
        A dictionary with keys matching the form items and as values
        the data from the provided location.
        """
        return {
            "street": location.address.street,
            "number": location.address.number,
            "place": location.address.place,
            "country": location.address.country,
            "latitude": location.coordinates.latitude,
            "longitude": location.coordinates.longitude,
        }

    def validate_street(self, street) -> None:
        """Validate form input for the street name."""
        if street.data is not None:
            street.data = street.data.strip()

        if not model_val.is_legal_address_street(street.data):
            raise ValidationError("Invalid street name")

    def validate_number(self, number) -> None:
        """Validate form input for the street number."""
        if (
            self.street.data is not None
            and not model_val.is_legal_address_number(number.data)
        ):
            raise ValidationError("Invalid street number")

    def validate_place(self, place) -> None:
        """Validate form input for location place."""
        if place.data is not None:
            place.data = place.data.strip()

        if not model_val.is_legal_address_place(place.data):
            raise ValidationError("Invalid place")

    def validate_country(self, country) -> None:
        """Validate form input for location country."""
        if country.data is not None:
            country.data = country.data.strip()

        if not model_val.is_legal_address_country(country.data):
            raise ValidationError("Invalid country")

    def validate_latitude(self, latitude) -> None:
        """Validate form input for latitude."""
        if (
            latitude.data is not None
            and not model_val.is_legal_coordinates_latitude(latitude.data)
        ):
            raise ValidationError("Invalid latitude")

    def validate_longitude(self, longitude) -> None:
        """Validate form input for longitude."""
        if (
            longitude.data is not None
            and not model_val.is_legal_coordinates_longitude(longitude.data)
        ):
            raise ValidationError("Invalid longitude")


class DataSourceForm(NoCsrfForm):
    """Class for a project data source form."""

    # A data source is optional for a project,
    # validation should not fail if not provided
    _category: Optional[str] = None

    source = StringField("Data source address")
    username = StringField("Username")
    password = PasswordField("Password")
    # TODO: allow retrieval of token,
    #  activate it when appropriate API has been selected
    #  (build in check in API if token retrieval has been written,
    #  only activate if it exists)
    token = HiddenField("Token")
    # TODO: Add correct API managers dynamically on category selection
    # api_manager =
    # SelectField("Data API manager", choices=[('', '---')]) VictronAPI
    api_manager = SelectField(
        "Data API manager",
        choices=[("VictronAPI", "Victron Energy")],
        default="VictronAPI",
    )

    @staticmethod
    def data_source_to_dict(data_source: model.DataSource) -> dict[str, Any]:
        """Create a dictionary with the data from the given datasource object.

        Returns
        _______
        A dictionary with keys matching the form items and as values
        the data from the provided datasource.
        """
        return {
            "source": data_source.source,
            "username": "",
            "password": "",
            "token": "",
            "api_manager": data_source.api_manager,
        }

    def set_category(self, category: str) -> None:
        """Set the selected project category."""
        self._category = category

    def validate(self, extra_validators=None) -> bool:
        """Validate form inputs if a data source is provided."""
        if self.source.data is None or len(self.source.data) != 0:
            return True

        return super().validate(extra_validators)

    def validate_source(self, source) -> None:
        """Validate form input for datasource source."""
        if not model_val.is_legal_datasource_source(source.data):
            raise ValidationError("Invalid data source")

    def validate_username(self, username) -> None:
        """Validate form input for username."""
        if self.token.data is None and not model_val.is_legal_datasource_user(
            username.data
        ):
            raise ValidationError("Invalid data source username")

    def validate_password(self, password) -> None:
        """Validate form input for datasource password."""
        if (
            self.token.data is None
            and not model_val.is_legal_datasource_password(password.data)
        ):
            raise ValidationError("Invalid data source password")

    def validate_api_manager(self, api_manager) -> None:
        """Validate form input for API manager."""
        if self._category is None:
            raise ValidationError(
                "Invalid API manager for unselected category"
            )

        category: str = self._category
        if not model_val.is_legal_api_manager(api_manager.data, category):
            raise ValidationError("Invalid API manager for selected category")


class PeriodForm(NoCsrfForm):
    """Class for a project follow-up task period form."""

    interval = IntegerField("Interval length")
    unit = SelectField(
        "Interval unit",
        choices=model_interface.get_time_unit_items(),
    )
    start = DateField("Starting date")
    end = DateField("End date")

    @staticmethod
    def period_to_dict(period: model.Period) -> dict[str, Any]:
        """Create a dictionary with the data from the given period object.

        Returns
        _______
        A dictionary with keys matching the form items and as values
        the data from the provided period.
        """
        return {
            "period": period.interval,
            "unit": period.unit.name,
            "start": period.start,
            "end": period.end,
        }

    def validate_interval(self, interval) -> None:
        """Validate form input for the period's interval."""
        if not model_val.is_legal_period_interval(interval.data):
            raise ValidationError(f"Invalid period interval: {interval.data}")

    def validate_unit(self, unit) -> None:
        """Validate from input for the period's time unit."""
        if not model_val.is_legal_period_unit(unit.data):
            raise ValidationError("Invalid period unit")

    def validate_start(self, date) -> None:
        """Validate form input for the period's start."""
        if not model_val.is_legal_period_start(date.data):
            raise ValidationError("Invalid period start date")

    def validate_end(self, date) -> None:
        """Validate form input for the period's end date."""
        if not model_val.is_legal_period_end(date.data):
            raise ValidationError("Invalid period end date")
        if date.data is not None and date.data < self.start.data:
            raise ValidationError(
                "Invalid period end date. Should be after start date"
            )


class FollowupWorkForm(NoCsrfForm):
    """Class for a project follow-up work form."""

    student_type = SubscriberForm.student_type
    supervisor_type = SubscriberForm.supervisor_type
    partner_type = SubscriberForm.partner_type

    sub_type = SelectField(
        "Subscriber type",
        choices=[
            (student_type, "Student"),
            (supervisor_type, "Supervisor"),
            (partner_type, "Partner"),
        ],
    )
    # TODO: Allow the selection of existing people
    subscriber = FormField(SubscriberForm)
    periods = FieldList(FormField(PeriodForm), min_entries=1)

    @staticmethod
    def followup_work_to_dict(
        work: model.FollowupWork,
    ) -> dict[str, Any | dict[str, Any] | list[dict[str, Any]]]:
        """Create a dictionary with the data from the given work object.

        Returns
        _______
        A dictionary with keys matching the form items and as values
        the data from the provided follow-up work.
        """
        data: dict[str, Any | dict[str, Any] | list[dict[str, Any]]] = {
            "periods": list(map(PeriodForm.period_to_dict, work.periods))
        }

        if isinstance(work.subscriber, model.Student):
            data["sub_type"] = FollowupWorkForm.student_type
            data["subscriber"] = StudentForm.student_to_dict(work.subscriber)
        elif isinstance(work.subscriber, model.Supervisor):
            data["sub_type"] = FollowupWorkForm.supervisor_type
            data["subscriber"] = SupervisorForm.supervisor_to_dict(
                work.subscriber
            )
        elif isinstance(work.subscriber, model.Partner):
            data["sub_type"] = FollowupWorkForm.partner_type
            data["subscriber"] = PartnerForm.partner_to_dict(work.subscriber)
        else:
            raise RuntimeError(
                f"Unexpected subscriber type for follow-up work: "
                f"{type(work.subscriber)}"
            )

        return data

    def validate(self, extra_validators=None) -> bool:
        """Validate form input.

        Set the subscriber subform to the correct type for correct validation.
        """
        self.subscriber.set_sub_type(self.sub_type.data)
        return super().validate(extra_validators)


class SubscriptionForm(FollowupWorkForm):
    """Class for a project subscription form."""

    @staticmethod
    def subscription_to_dict(
        subscription: model.Subscription,
    ) -> dict[str, Any]:
        """Create a dictionary with the data from the given subscription.

        Returns
        _______
        A dictionary with keys matching the form items and as values
        the data from the provided subscription.
        """
        return FollowupWorkForm.followup_work_to_dict(subscription)


class TaskForm(FollowupWorkForm):
    """Class for a project subscription form."""

    task_name = StringField("Task name")
    function = StringField("Task description")

    @staticmethod
    def task_to_dict(task: model.Task) -> dict[str, Any]:
        """Create a dictionary with the data from the given task object.

        Returns
        _______
        A dictionary with keys matching the form items and as values
        the data from the provided task.
        """
        data = FollowupWorkForm.followup_work_to_dict(task)

        data["task_name"] = task.name
        data["function"] = task.function

        return data

    def validate_task_name(self, name) -> None:
        """Validate form input for the task name."""
        if name.data is not None:
            name.data = name.data.strip()

        if not model_val.is_legal_task_name(name.data):
            raise ValidationError("Invalid task name")

    def validate_function(self, function) -> None:
        """Validate form input for the task function."""
        if function.data is not None:
            function.data = function.data.strip()

        if not model_val.is_legal_task_function(function.data):
            raise ValidationError("Invalid task function")


class EnergyProjectForm(NoCsrfForm):
    """Class for en energy project's specific section form.

    The form contains all the inputs for details specific to an energy form.
    """

    # TODO: Show individual power ratings only when there are
    #  multiple sources (PowerDivision)
    # TODO: Adjust form to new energy project format with multiple objects
    #  of each type of component

    power = FloatField("System power rating [kW]", default=0)

    battery = BooleanField("There is a battery")
    battery_power = FloatField("Battery power rating [kW]", default=0)
    battery_is_primary = BooleanField("Battery as a primary source")
    battery_capacity = FloatField("Battery capacity [kWh]", default=0)
    battery_type = SelectField(
        "Battery Type",
        choices=model_interface.get_battery_type_values(),
    )
    # TODO: set slider markers and/or show value
    battery_base_soc = DecimalRangeField("Base State of Charge (%)")
    battery_min_soc = DecimalRangeField("Minimum State of Charge (%)")

    grid = BooleanField("There is a grid connection")
    grid_power = FloatField("Grid power rating [kW]", default=0)
    grid_is_primary = BooleanField("Grid as a primary source")
    grid_energy_cost = FloatField("Electricity buying cost [€/kWh]", default=0)
    grid_blackout_threshold = FloatField("Grid blackout threshold", default=0)
    grid_injection_cost = FloatField(
        "Electricity injection cost [€/kWh]", default=0
    )

    generator = BooleanField("There is a generator")
    generator_power = FloatField("Generator power rating [kW]", default=0)
    generator_is_primary = BooleanField("Generator as a primary source")
    generator_fuel_cost = FloatField("Fuel cost [€/kWh]", default=0)
    generator_overheats = BooleanField("The generator overheats")
    # TODO: Deactivate cool-down time if overheating is not selected
    generator_cooldown_time = FloatField("Generator cool-down time", default=0)

    def validate_power(self, power) -> None:
        """Validate form input for this project's power."""
        if not model_val.is_legal_energy_project_power(power.data):
            raise ValidationError("Invalid power for an Energy project")

    def validate_battery(self, battery) -> None:
        """Validate from input for the battery selector."""
        if not battery.data and not self.grid.data and not self.generator.data:
            raise ValidationError(
                "Energy system should have at least one component"
            )

    def validate_battery_power(self, power) -> None:
        """Validate form input for the battery power."""
        if (
            self.battery.data
            and not model_val.is_legal_energy_project_component_power(
                power.data
            )
        ):
            raise ValidationError("Invalid battery power")

    def validate_battery_capacity(self, capacity) -> None:
        """Validate form input for the battery capacity."""
        if (
            self.battery.data
            and not model_val.is_legal_storage_component_capacity(
                capacity.data
            )
        ):
            raise ValidationError("Invalid battery capacity")

    def validate_battery_type(self, btype) -> None:
        """Validate form input for the battery type."""
        if self.battery.data and not model_val.is_legal_battery_type(
            btype.data
        ):
            raise ValidationError("Invalid battery type")

    def validate_battery_base_soc(self, soc) -> None:
        """Validate form input for the battery base SOC."""
        if self.battery.data and not model_val.is_legal_battery_base_soc(
            float(soc.data)
        ):
            raise ValidationError("Invalid battery base state of charge")

    def validate_battery_min_soc(self, soc) -> None:
        """Validate form input for the battery minimal SOC."""
        if self.battery.data and not model_val.is_legal_battery_min_soc(
            float(soc.data)
        ):
            raise ValidationError("Invalid battery minimum SOC")

        if self.battery.data and soc.data > self.battery_base_soc.data:
            raise ValidationError(
                "Invalid battery minimum state of charge. "
                "Minimum must be below base SOC"
            )

    def validate_grid_power(self, power) -> None:
        """Validate form input for the grid power."""
        if (
            self.grid.data
            and not model_val.is_legal_energy_project_component_power(
                power.data
            )
        ):
            raise ValidationError("Invalid grid power")

    def validate_grid_energy_cost(self, cost) -> None:
        """Validate form input for grid energy cost."""
        if self.grid.data and not model_val.is_legal_source_component_price(
            cost.data
        ):
            raise ValidationError("Invalid grid cost")

    def validate_grid_blackout_threshold(self, threshold) -> None:
        """Validate form input for grid blackout threshold."""
        if self.grid.data and not model_val.is_legal_grid_blackout_threshold(
            threshold.data
        ):
            raise ValidationError("Invalid grid blackout threshold")

    def valid_grid_injection_cost(self, cost) -> None:
        """Validate form input for grid injection cost."""
        if self.grid.data and not model_val.is_legal_grid_injection_price(
            cost.data
        ):
            raise ValidationError("Invalid grid injection cost")

    def validate_generator_power(self, power) -> None:
        """Validate form input for generator power."""
        if (
            self.generator.data
            and not model_val.is_legal_energy_project_component_power(
                power.data
            )
        ):
            raise ValidationError("Invalid generator power")

    def validate_generator_fuel_cost(self, cost) -> None:
        """Validate form input for generator fuel cost."""
        if self.generator.data and not model_val.is_legal_generator_fuel_cost(
            cost.data
        ):
            raise ValidationError("Invalid generator cost")

    def validate_generator_cooldown_time(self, time) -> None:
        """Validate form input for generator cool down time."""
        if (
            self.generator.data
            and self.generator_overheats.data
            and not model_val.is_legal_generator_cooldown_time(time.data)
        ):
            raise ValidationError("Invalid generator cool-down time")


class ProjectSpecificForm(EnergyProjectForm):
    """Class containing all elements of project specific forms.

    Add all project-specific forms as superclasses so that
    the FormField knows about all possible form fields
    Select which one should be validated based on the selected category
    """

    # TODO: create this as superclass with subforms,
    #  at validation select correct subform to validate


class ProjectForm(FlaskForm):
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
        choices=[
            (str(n), member)
            for n, (_, member) in enumerate(model_interface.get_sdgs())
        ],
    )

    specifics = FormField(ProjectSpecificForm)

    tasks = FieldList(FormField(TaskForm))
    data_source = FormField(DataSourceForm)
    dashboard = StringField("Dashboard URL")
    save_data = BooleanField("Should the data be saved?")
    subscriptions = FieldList(FormField(SubscriptionForm))

    submit = SubmitField("Save Project")

    def __init__(self, project: model.Project = None) -> None:
        """Instantiate project form object.

        Initialize all form input fields. If a project is provided use the
        data to initialize the fields. This can be used for instance when a
        project should be edited.

        Parameters
        __________
        project     -- Optional project object as field data initializer
        should_populate     -- Whether the project data should be used
        """
        super().__init__()

        self.project = project

    @classmethod
    def get_attributes(cls) -> dict[str, None | list | str | bool]:
        """Provide all attributes of this form in a dictionary.

        Returns
        _______
        Dictionary with as keys the names of the attributes of this form and
        either None or a list as value.
        """
        return {
            "name": None,
            "date": None,
            "description": None,
            "category": None,
            "location": None,
            "work_folder": None,
            "students": [],
            "supervisors": [],
            "partners": [],
            "sdgs": [],
            "tasks": [],
            "data_source": None,
            "dashboard": None,
            "save_data": False,
            # 'extra_data'
            "subscriptions": [],
        }

    def validate(self, extra_validators=None) -> bool:
        """Validate form input.

        Set state of subforms for correct validation.
        """
        if (
            self.data_source.source.data is not None
            and len(self.data_source.source.data) != 0
        ):
            self.data_source.set_should_validate(True)
            self.data_source.set_category(self.category.data)
        else:
            self.data_source.set_should_validate(False)

        return super().validate(extra_validators=extra_validators)

    def validate_name(self, name: wtforms.StringField) -> None:
        """Validate form input for project name."""
        if name.data is not None:
            name.data = name.data.strip()

        if not model_val.is_legal_project_name(name.data):
            raise ValidationError("Invalid project name")

    def validate_date(self, date: wtforms.DateField) -> None:
        """Validate form input for project implementation date."""
        if not model_val.is_legal_project_implementation_date(date.data):
            raise ValidationError("Invalid project implementation date")

    def validate_description(self, description: wtforms.TextAreaField) -> None:
        """Validate form input for project description."""
        if description.data is not None:
            description.data = description.data.strip()

        if not model_val.is_legal_project_description(description.data):
            raise ValidationError("Invalid project description")

    def validate_category(self, category: wtforms.RadioField) -> None:
        """Validate form input for project category."""
        if category.data not in model_interface.get_project_categories():
            raise ValidationError("Invalid project category")

    def validate_work_folder(self, folder: wtforms.StringField) -> None:
        """Validate form input for project work folder."""
        if not model_val.is_legal_project_work_folder(folder.data):
            raise ValidationError("Invalid project work folder")

    def validate_students(self, students: wtforms.FieldList) -> None:
        """Validate form input for project students."""
        if len(students.data) > model_interface.get_project_max_students():
            raise ValidationError("Too many students for a project")

    def validate_sdgs(self, sdgs: wtforms.FieldList) -> None:
        """Validate form input for project SDGs."""
        # TODO: do this through model interface
        if len(sdgs.data) == 0:
            raise ValidationError("At least one SDG must be selected")
        for sdg in sdgs.data:
            if not sdg.isnumeric():
                ValidationError("Invalid SDG type")
            sdg = int(sdg)
            if sdg < 0 or sdg > 16:
                raise ValidationError("SDG must go from 1 to 17")

    def validate_dashboard(self, dashboard: wtforms.StringField) -> None:
        """Validate form input for project dashboard."""
        if dashboard.data is not None:
            dashboard.data = dashboard.data.strip()

        if (
            self.data_source.source.data is not None
            and len(self.data_source.source.data) != 0
            and not model_val.is_legal_project_dashboard(dashboard.data)
        ):
            raise ValidationError(
                f"Invalid project dashboard: {dashboard.data}"
            )
