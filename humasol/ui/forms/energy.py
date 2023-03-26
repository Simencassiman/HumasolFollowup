"""Module providing all project forms related to an energy project."""

# Python Libraries
from abc import abstractmethod
from typing import Any

from wtforms import (
    BooleanField,
    DecimalRangeField,
    FieldList,
    FloatField,
    FormField,
    SelectField,
    ValidationError,
)

# Local Modules
from humasol.model import model_interface
from humasol.model import model_validation as model_val
from humasol.ui import forms
from humasol.ui.forms import base


class EnergyProjectComponentForm(forms.ProjectElementForm):
    """Form linked to an energy project component."""

    power = FloatField("Component power rating [kW]", default=0)
    is_primary = BooleanField("Primary component")

    @property
    @abstractmethod
    def LABEL(self) -> str:
        """Provide identifying label of the project component."""

    def get_data(self) -> dict[str, Any]:
        """Return the data in the form fields.

        Returns
        _______
        Dictionary mapping attributes from the corresponding models to the data
        in the form fields.
        """
        return {"power": self.power.data, "is_primary": self.is_primary.data}

    def validate_power(self, power) -> None:
        """Validate form input for component power."""
        if not model_val.is_legal_energy_project_component_power(power.data):
            raise ValidationError("Invalid power for a project component.")


class SourceComponentForm(EnergyProjectComponentForm):
    """Form linked to a source project component."""

    price = FloatField("Energy price [€/kWh]", default=0)

    def __init__(self, *args, **kwargs) -> None:
        """Instantiate from object."""
        super().__init__(*args, **kwargs)

    @property
    @abstractmethod
    def LABEL(self) -> str:
        """Provide identifying label of the project component."""

    def get_data(self) -> dict[str, Any]:
        """Return the data in the form fields.

        Returns
        _______
        Dictionary mapping attributes from the corresponding models to the data
        in the form fields.
        """
        return {"price": self.price.data, **super().get_data()}

    def validate_price(self, price) -> None:
        """Validate form input for source energy price."""
        if not model_val.is_legal_source_component_price(price.data):
            raise ValidationError("Invalid price for source component.")


class GridForm(SourceComponentForm):
    """Form linked to a grid energy project component."""

    LABEL = model_interface.get_grid_label()

    blackout_threshold = FloatField("Blackout threshold [kW]", default=None)
    injection_price = FloatField("Injection price [€]", default=None)

    def get_data(self) -> dict[str, Any]:
        """Return the data in the form fields.

        Returns
        _______
        Dictionary mapping attributes from the corresponding models to the data
        in the form fields.
        """
        return {
            "blackout_threshold": self.blackout_threshold.data,
            "injection_price": self.injection_price.data,
            **super().get_data(),
        }

    def validate_blackout_threshold(self, threshold) -> None:
        """Validate form input for blackout threshold."""
        if not model_val.is_legal_grid_blackout_threshold(threshold.data):
            raise ValidationError("Invalid blackout threshold for a grid")

    def validate_injection_price(self, price) -> None:
        """Validate form input for injection price."""
        if not model_val.is_legal_grid_injection_price(price.data):
            raise ValidationError("Invalid injection price for a grid.")


class PVForm(SourceComponentForm):
    """Form linked to a PV energy project component."""

    LABEL = model_interface.get_pv_label()


class GeneratorForm(SourceComponentForm):
    """Form linked to a generator energy project component."""

    LABEL = model_interface.get_generator_label()

    EFFICIENCY_MAX = 100
    EFFICIENCY_MIN = 0

    # TODO: add label with exact value of the slider
    efficiency = DecimalRangeField("Efficiency (%)", default=50)
    fuel_cost = FloatField("Fuel cost [€/L]", default=0)
    overheats = BooleanField("The generator overheats")
    # TODO: Deactivate cool-down time if overheating is not selected
    overheating_time = FloatField("Overheating time", default=0)
    cooldown_time = FloatField("Cool-down time", default=0)

    def get_data(self) -> dict[str, Any]:
        """Return the data in the form fields.

        Returns
        _______
        Dictionary mapping attributes from the corresponding models to the data
        in the form fields.
        """
        return {
            **super().get_data(),
            "efficiency": float(self.efficiency.data) / 100,
            "fuel_cost": self.fuel_cost.data,
            "overheats": self.overheats.data,
            "overheating_time": self.overheating_time.data,
            "cooldown_time": self.cooldown_time.data,
        }

    def validate_efficiency(self, efficiency) -> None:
        """Validate form input for generator efficiency."""
        eff = float(efficiency.data) / 100
        if not model_val.is_legal_generator_efficiency(eff):
            raise ValidationError("Invalid generator efficiency.")

    def validate_fuel_cost(self, cost) -> None:
        """Validate form input for generator fuel cost."""
        if not model_val.is_legal_generator_fuel_cost(cost.data):
            raise ValidationError("Invalid generator fuel cost.")

    def validate_overheating_time(self, time) -> None:
        """Validate form input for generator overheating time."""
        if (
            self.overheats.data
            and not model_val.is_legal_generator_overtheating_time(time.data)
        ):
            raise ValidationError("Invalid generator overheating time")

    def validate_cooldown_time(self, time) -> None:
        """Validate form input for cool-down time."""
        if (
            self.overheats.data
            and not model_val.is_legal_generator_cooldown_time(time.data)
        ):
            raise ValidationError("Invalid cool-down time for a generator.")


class StorageComponentForm(EnergyProjectComponentForm):
    """Form linked to an energy storage component."""

    capacity = FloatField("Capacity", default=0)

    @property
    @abstractmethod
    def LABEL(self) -> str:
        """Provide identifying label of the project component."""

    def get_data(self) -> dict[str, Any]:
        """Return the data in the form fields.

        Returns
        _______
        Dictionary mapping attributes from the corresponding models to the data
        in the form fields.
        """
        return {"capacity": self.capacity.data, **super().get_data()}

    def validate_capacity(self, capacity) -> None:
        """Validate form input for capacity."""
        if not model_val.is_legal_storage_component_capacity(capacity.data):
            raise ValidationError("Invalid capacity for a storage component.")


class BatteryForm(StorageComponentForm):
    """Form linked to a battery energy project component."""

    LABEL = model_interface.get_battery_label()

    SOC_MAX = 100
    SOC_MIN = 0

    battery_type = SelectField(
        "Type", choices=model_interface.get_battery_type_values()
    )
    # TODO: set slider markers and/or show value
    battery_base_soc = DecimalRangeField(
        "Base State of Charge (%): 50", default=50
    )
    battery_min_soc = DecimalRangeField(
        "Minimum State of Charge (%): 20", default=20
    )
    battery_max_soc = DecimalRangeField(
        "Maximum State of Charge (%): 80", default=80
    )

    def get_data(self) -> dict[str, Any]:
        """Return the data in the form fields.

        Returns
        _______
        Dictionary mapping attributes from the corresponding models to the data
        in the form fields.
        """
        return {
            "battery_type": self.battery_type.data,
            "base_soc": float(self.battery_base_soc.data),
            "min_soc": float(self.battery_min_soc.data),
            "max_soc": float(self.battery_max_soc.data),
            **super().get_data(),
        }

    def validate_battery_type(self, btype) -> None:
        """Validate form input for the battery type."""
        if not model_val.is_legal_battery_type(btype.data):
            raise ValidationError("Invalid battery type")

    def validate_battery_base_soc(self, soc) -> None:
        """Validate form input for the battery base SOC."""
        if not model_val.is_legal_battery_base_soc(float(soc.data)):
            raise ValidationError("Invalid battery base state of charge")

    def validate_battery_min_soc(self, soc) -> None:
        """Validate form input for the battery minimal SOC."""
        if not model_val.is_legal_battery_min_soc(float(soc.data)):
            raise ValidationError("Invalid battery minimum SOC")

        if soc.data > self.battery_base_soc.data:
            raise ValidationError(
                "Invalid minimum battery state of charge. "
                "Minimum must be below base SOC"
            )

    def validate_battery_max_soc(self, soc) -> None:
        """Validate form input for the battery maximal SOC."""
        if not model_val.is_legal_battery_min_soc(float(soc.data)):
            raise ValidationError("Invalid battery maximum SOC")

        if soc.data < self.battery_base_soc.data:
            raise ValidationError(
                "Invalid maximum battery state of charge. "
                "Maximum must be above base SOC"
            )


class ConsumptionComponentForm(EnergyProjectComponentForm):
    """Form linked to the energy consumption component form."""

    LABEL = model_interface.get_consumption_component_label()

    is_critical = BooleanField("Is critical load")

    def get_data(self) -> dict[str, Any]:
        """Return the data in the form fields.

        Returns
        _______
        Dictionary mapping attributes from the corresponding models to the data
        in the form fields.
        """
        return {"is_critical": self.is_critical.data, **super().get_data()}


class EnergyProjectForm(forms.HumasolSubform):
    """Class for en energy project's specific section form.

    The form contains all the inputs for details specific to an energy form.
    """

    sources = FieldList(
        FormField(
            base.ProjectElementWrapper[SourceComponentForm](
                SourceComponentForm
            )
        ),
    )
    storage = FieldList(
        FormField(
            base.ProjectElementWrapper[StorageComponentForm](
                StorageComponentForm
            )
        )
    )
    loads = FieldList(
        FormField(
            base.ProjectElementWrapper[ConsumptionComponentForm](
                ConsumptionComponentForm
            )
        )
    )

    def get_data(self) -> dict[str, Any]:
        """Return the data in the form fields.

        Returns
        _______
        Dictionary mapping attributes from the corresponding models to the data
        in the form fields.
        """
        sources = [s.get_data() for s in self.sources]
        storage = [s.get_data() for s in self.storage]
        loads = [load.get_data() for load in self.loads]
        power = sum(map(lambda l: l["power"], loads))

        return {"power": power, "components": sources + storage + loads}


if __name__ == "__main__":
    e = EnergyProjectForm()

    subforms = forms.get_subforms()

    print(
        {
            n: {
                (f.LABEL if hasattr(f, "LABEL") else f.__name__): f()
                for f in fs
            }
            for n, fs in forms.get_subforms().items()
        }
    )
