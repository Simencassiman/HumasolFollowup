"""Provide interface to model class data."""

# Python Libraries

# Local modules
from humasol import model


def get_battery_label() -> str:
    """Provide label of the Battery class."""
    return model.Battery.LABEL


def get_battery_type_values() -> tuple[tuple[str, str], ...]:
    """Provide pairs of battery type with its value.

    Returns
    _______
    Tuple of tuples containing two strings. The first string indicates the
    name of the battery type and the second is the value.
    """
    return tuple(
        (k, str(v)) for k, v in model.Battery.BatteryType.__members__.items()
    )


def get_belgian_partner_label() -> str:
    """Provide label of the BelgianPartner class."""
    return model.BelgianPartner.LABEL


def get_generator_label() -> str:
    """Provide label of the Generator class."""
    return model.Generator.LABEL


def get_grid_label() -> str:
    """Provide label of the Grid class."""
    return model.Grid.LABEL


def get_partner_label() -> str:
    """Provide label of the Partner class."""
    return model.Partner.LABEL


def get_project_categories() -> tuple[tuple[str, str], ...]:
    """Provide project categories and values.

    Returns
    _______
    Tuple of tuples containing two strings. The first one indicates the name
    of the project category and the second is the value.
    """
    return tuple(
        (p_cat.name, p_cat.category_name)
        for p_cat in model.ProjectCategory.categories()
    )


def get_project_max_students() -> int:
    """Provide the maximum number of students per project."""
    return model.Project.MAX_STUDENTS


def get_sdgs() -> tuple[tuple[str, str], ...]:
    """Provide SDGs and values.

    Returns
    _______
    Tuple of tuples containing two strings. The first string indicates the
    name of the SDG and the second is its value.
    """
    return tuple((k, v.goal_name) for k, v in model.SDG.__members__.items())


def get_southern_partner_label() -> str:
    """Provide label of the SouthernPartner class."""
    return model.SouthernPartner.LABEL


def get_student_label() -> str:
    """Provide label of the Student class."""
    return model.Student.LABEL


def get_supervisor_label() -> str:
    """Provide label of the Supervisor class."""
    return model.Supervisor.LABEL


def get_time_unit_items() -> tuple[tuple[str, str], ...]:
    """Provide period time unit elements.

    Returns
    _______
    Tuple of tuples containing two strings. The first one is the name of the
    time unit and the second one is its value.
    """
    return tuple(
        (k, str(v)) for k, v in model.Period.TimeUnit.__members__.items()
    )


if __name__ == "__main__":
    print(get_project_categories()[0])
