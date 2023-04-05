"""Interface for validating model parameters."""

# Python Libraries
import datetime
from typing import Optional

# Local modules
import humasol
import humasol.model.followup_work as fw
import humasol.model.person as pn
import humasol.model.project_components as pc
import humasol.model.project_elements as pe
from humasol import model


def are_legal_datasource_managers(
    api_manager: str, data_manager: str, report_manager: str
) -> bool:
    """Check whether the provided managers are legal for a data source."""
    return pe.DataSource.are_legal_managers(
        api_manager, data_manager, report_manager
    )


def are_legal_period_dates(
    start: datetime.date, end: Optional[datetime.date]
) -> bool:
    """Check whether the combination of dates is legal for a period."""
    return fw.Period.are_legal_dates(start, end)


def are_legal_project_extra_data(data: dict[str, str]) -> bool:
    """Check whether the provided extra data are legal for a project."""
    return model.Project.are_legal_extra_data(data)


def is_legal_address_country(country: str) -> bool:
    """Check whether the provided country is legal for an address."""
    return pe.Address.is_legal_country(country)


def is_legal_address_number(number: Optional[int]) -> bool:
    """Check whether the provided number is a legal address street number."""
    return pe.Address.is_legal_number(number)


def is_legal_address_place(place: str) -> bool:
    """Check whether the provided place is legal for an address."""
    return pe.Address.is_legal_place(place)


def is_legal_address_street(street: Optional[str]) -> bool:
    """Check whether the provided street is legal for an address."""
    return pe.Address.is_legal_street(street)


def is_legal_api_manager(api_manager: str, category: str) -> bool:
    """Check whether the given API manager is legal for the given category."""
    return humasol.script.api_manager_exists(
        api_manager, model.ProjectCategory.from_string(category)
    )


def is_legal_battery_base_soc(soc: float) -> bool:
    """Check whether the provided SOC is legal for a battery base SOC."""
    return pc.Battery.is_legal_base_soc(soc)


def is_legal_battery_max_soc(soc: float) -> bool:
    """Check whether the provided SOC is a legal maximum battery SOC."""
    return pc.Battery.is_legal_max_soc(soc)


def is_legal_battery_min_soc(soc: float) -> bool:
    """Check whether the provided SOC is a legal minimum battery SOC."""
    return pc.Battery.is_legal_min_soc(soc)


def is_legal_battery_type(b_type: str) -> bool:
    """Check whether the provided type is a legal battery type."""
    return pc.Battery.is_legal_battery_type(
        pc.Battery.BatteryType.from_str(b_type)
    )


def is_legal_consumption_component_critical_flag(flag: bool) -> bool:
    """Check whether the provided flag is a legal critical flag."""
    return pc.ConsumptionComponent.is_legal_is_critical(flag)


def is_legal_coordinates_latitude(latitude: float) -> bool:
    """Check whether the provided latitude is legal for coordinates."""
    return pe.Coordinates.is_legal_latitude(latitude)


def is_legal_coordinates_longitude(longitude: float) -> bool:
    """Check whether the provided longitude is legal for coordinates."""
    return pe.Coordinates.is_legal_longitude(longitude)


def is_legal_datasource_password(password: Optional[str]) -> bool:
    """Check whether the provided password is legal for a data source."""
    return pe.DataSource.is_legal_password(password)


def is_legal_datasource_source(source: str) -> bool:
    """Check whether the provided source is legal for a project data source."""
    return pe.DataSource.is_legal_source(source)


def is_legal_datasource_token(token: Optional[str]) -> bool:
    """Check whether the provided token is legal for a data source."""
    return pe.DataSource.is_legal_token(token)


def is_legal_datasource_user(user: Optional[str]) -> bool:
    """Check whether the provided user is legal for a data source."""
    return pe.DataSource.is_legal_user(user)


def is_legal_energy_project_component_power(power: float) -> bool:
    """Check if the provided power is legal for an energy project component."""
    return pc.EnergyProjectComponent.is_legal_power(power)


def is_legal_energy_project_component_primary_flag(flag: bool) -> bool:
    """Check whether the provide flag is legal as a primary."""
    return pc.EnergyProjectComponent.is_legal_is_primary(flag)


def is_legal_energy_project_power(power: float) -> bool:
    """Check whether the provided power is legal for an energy project."""
    return model.EnergyProject.is_legal_power(power)


def is_legal_followup_last_notification(
    notification: Optional[datetime.date],
) -> bool:
    """Check if the notification date is legal for FollowupWork.

    Parameters
    __________
    notification    -- Date of last notification of the job's subscriber
    """
    return fw.FollowupJob.is_legal_last_notification(notification)


def is_legal_generator_cooldown_time(time: Optional[float]) -> bool:
    """Check if the provided time is a legal generator cooldown duration."""
    return pc.Generator.is_legal_cooldown_time(time)


def is_legal_generator_efficiency(factor: float) -> bool:
    """Check whether the provided factor is a legal generator efficiency."""
    return pc.Generator.is_legal_efficiency(factor)


def is_legal_generator_fuel_cost(cost: float) -> bool:
    """Check whether the provided cost is a legal generator fuel cost."""
    return pc.Generator.is_legal_fuel_cost(cost)


def is_legal_generator_overtheating_time(time: float) -> bool:
    """Check if the provided time is a legal generator overheating duration."""
    return pc.Generator.is_legal_overheating_time(time)


def is_legal_generator_overheats_flag(flag: bool) -> bool:
    """Check whether the provided flag is a legal generator overheats flag."""
    return pc.Generator.is_legal_overheats(flag)


def is_legal_grid_blackout_threshold(threshold: Optional[float]) -> bool:
    """Check whether the provided threshold is legal for a grid blackout."""
    return pc.Grid.is_legal_blackout_threshold(threshold)


def is_legal_grid_injection_price(price: Optional[float]) -> bool:
    """Check whether the provided price is a legal grid injection price."""
    return pc.Grid.is_lega_injection_price(price)


def is_legal_organization_logo(logo: str) -> bool:
    """Check whether the provided logo URI is legal for an organization."""
    return pn.Organization.is_legal_logo(logo)


def is_legal_organization_name(name: str) -> bool:
    """Check whether the provided name is legal for an organization."""
    return pn.Organization.is_legal_name(name)


def is_legal_partner_function(function: str) -> bool:
    """Check whether the provided function is legal for a partner."""
    return pn.Partner.is_legal_function(function)


def is_legal_period_end(end: datetime.date) -> bool:
    """Check whether the provide end is a legal period end date."""
    return fw.Period.is_legal_end(end)


def is_legal_period_interval(interval: int) -> bool:
    """Check whether the provided interval is a legal period interval."""
    return fw.Period.is_legal_interval(interval)


def is_legal_period_start(start: datetime.date) -> bool:
    """Check whether the provided start is a legal start date for a period."""
    return fw.Period.is_legal_start(start)


def is_legal_period_unit(unit: str) -> bool:
    """Check whether the provided unit is a known and legal unit."""
    return fw.Period.is_legal_unit(fw.Period.TimeUnit.get_unit(unit))


def is_legal_person_email(email: str) -> bool:
    """Check whether the provided email is legal for a person."""
    return pn.Person.is_legal_email(email)


def is_legal_person_name(name: str) -> bool:
    """Check whether the provided name is legal for a person."""
    return pn.Person.is_legal_name(name)


def is_legal_person_phone(phone: str) -> bool:
    """Check if the provided phone is a legal phone number for a person."""
    return pn.Person.is_legal_phone(phone)


def is_legal_project_category(category: str) -> bool:
    """Check whether the provided project category is a defined category."""
    return category in model.ProjectCategory.__members__


def is_legal_project_dashboard(dashboard: str) -> bool:
    """Check whether the provided dashboard is a legal dashboard address."""
    return model.Project.is_legal_dashboard(dashboard)


def is_legal_project_data_folder(folder: str) -> bool:
    """Check whether the provided folder is a legal folder URL."""
    return model.Project.is_legal_data_folder(folder)


def is_legal_project_description(description: str) -> bool:
    """Check whether the provided description is legal for a project."""
    return model.Project.is_legal_description(description)


def is_legal_project_implementation_date(date: datetime.date) -> bool:
    """Check if the provided date is a legal project implementation date."""
    return model.Project.is_legal_implementation_date(date)


def is_legal_project_name(name: str) -> bool:
    """Check whether the provided name is legal for a project."""
    return model.Project.is_legal_name(name)


def is_legal_project_data_flag(flag: bool) -> bool:
    """Check whether the provided flag is a legal project save data flag."""
    return model.Project.is_legal_save_data_flag(flag)


def is_legal_project_work_folder(folder: str) -> bool:
    """Check whether the provided folder is a legal work folder URL."""
    return model.Project.is_legal_work_folder(folder)


def is_legal_source_component_price(price: float) -> bool:
    """Check whether the provided price is legal for a source component."""
    return pc.SourceComponent.is_legal_price(price)


def is_legal_southern_partner_country(country: str) -> bool:
    """Check whether the provided country is legal for a southern partner."""
    return pn.SouthernPartner.is_legal_country(country)


def is_legal_storage_component_capacity(capacity: float) -> bool:
    """Check whether the provided capacity is legal for a storage component."""
    return pc.StorageComponent.is_legal_capacity(capacity)


def is_legal_student_field_of_study(field: str) -> bool:
    """Check whether the provided field is a legal field of study."""
    return pn.Student.is_legal_field_of_study(field)


def is_legal_student_university(uni: str) -> bool:
    """Check whether the provided university is a legal university."""
    return pn.Student.is_legal_university(uni)


def is_legal_supervisor_function(function: str) -> bool:
    """Check whether the provided function is legal for a supervisor."""
    return pn.Supervisor.is_legal_function(function)


def is_legal_task_function(function: str) -> bool:
    """Check whether the provided function is a legal task function."""
    return fw.Task.is_legal_function(function)


def is_legal_task_name(name: str) -> bool:
    """Check whether the provided name is a legal task name."""
    return fw.Task.is_legal_name(name)
