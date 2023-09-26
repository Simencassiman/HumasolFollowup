"""Module providing all project forms related to an energy project."""

# Python Libraries
import typing as ty
from abc import abstractmethod

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
from humasol import model
from humasol.model import model_interface
from humasol.model import model_validation as model_val
from humasol.ui import forms
from humasol.ui.forms import base

T = ty.TypeVar("T", bound=model.EnergyProjectComponent)
S = ty.TypeVar("S", bound=model.SourceComponent)
U = ty.TypeVar("U", bound=model.StorageComponent)
V = ty.TypeVar("V", bound=model.ConsumptionComponent)


class EnergyProjectComponentForm(forms.ProjectElementForm[T], ty.Generic[T]):
    """Form linked to an energy project component."""

    power = FloatField("Component power rating [kW]", default=0)
    is_primary = BooleanField("Primary component")

    @property
    @abstractmethod
    def LABEL(self) -> str:
        """Provide identifying label of the project component."""

    def from_object(self, obj: T) -> None:
        """Fill in energy component from object."""
        self.power.data = obj.power
        self.is_primary.data = obj.is_primary

    def get_data(self) -> dict[str, ty.Any]:
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
            error = "Invalid power for a project component."
            self.power.errors.append(error)
            raise ValidationError(error)


class SourceComponentForm(EnergyProjectComponentForm[S], ty.Generic[S]):
    """Form linked to a source project component."""

    price = FloatField("Energy price [€/kWh]", default=0)

    def __init__(self, *args, **kwargs) -> None:
        """Instantiate from object."""
        super().__init__(*args, **kwargs)

    @property
    @abstractmethod
    def LABEL(self) -> str:
        """Provide identifying label of the project component."""

    def from_object(self, obj: S) -> None:
        """Fill in source component from object."""
        super().from_object(obj)
        self.price.data = obj.price

    def get_data(self) -> dict[str, ty.Any]:
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
            error = "Invalid price for source component."
            self.price.errors.append(error)
            raise ValidationError(error)


class GridForm(SourceComponentForm[model.Grid]):
    """Form linked to a grid energy project component."""

    LABEL = model_interface.get_grid_label()

    blackout_threshold = FloatField("Blackout threshold [kW]", default=None)
    injection_price = FloatField("Injection price [€]", default=None)

    def from_object(self, obj: model.Grid) -> None:
        """Fill in grid from object."""
        super().from_object(obj)
        self.blackout_threshold.data = obj.blackout_threshold
        self.injection_price.data = obj.injection_price

    def get_data(self) -> dict[str, ty.Any]:
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
            error = "Invalid blackout threshold for a grid"
            self.blackout_threshold.errors.append(error)
            raise ValidationError(error)

    def validate_injection_price(self, price) -> None:
        """Validate form input for injection price."""
        if not model_val.is_legal_grid_injection_price(price.data):
            error = "Invalid injection price for a grid."
            self.injection_price.errors.append(error)
            raise ValidationError(error)


class PVForm(SourceComponentForm[model.PV]):
    """Form linked to a PV energy project component."""

    LABEL = model_interface.get_pv_label()


class GeneratorForm(SourceComponentForm[model.Generator]):
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

    def from_object(self, obj: model.Generator) -> None:
        """Fill in generator from object."""
        super().from_object(obj)
        self.efficiency.data = obj.efficiency
        self.fuel_cost.data = obj.fuel_cost
        self.overheats.data = obj.overheats
        self.overheating_time.data = obj.overheating_time
        self.cooldown_time.data = obj.cooldown_time

    def get_data(self) -> dict[str, ty.Any]:
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
            error = "Invalid generator efficiency."
            self.efficiency.errors.append(error)
            raise ValidationError(error)

    def validate_fuel_cost(self, cost) -> None:
        """Validate form input for generator fuel cost."""
        if not model_val.is_legal_generator_fuel_cost(cost.data):
            error = "Invalid generator fuel cost."
            self.fuel_cost.errors.append(error)
            raise ValidationError(error)

    def validate_overheating_time(self, time) -> None:
        """Validate form input for generator overheating time."""
        if (
            self.overheats.data
            and not model_val.is_legal_generator_overtheating_time(time.data)
        ):
            error = "Invalid generator overheating time"
            self.overheating_time.errors.append(error)
            raise ValidationError(error)

    def validate_cooldown_time(self, time) -> None:
        """Validate form input for cool-down time."""
        if (
            self.overheats.data
            and not model_val.is_legal_generator_cooldown_time(time.data)
        ):
            error = "Invalid cool-down time for a generator."
            self.cooldown_time.errors.append(error)
            raise ValidationError(error)


class StorageComponentForm(EnergyProjectComponentForm[U], ty.Generic[U]):
    """Form linked to an energy storage component."""

    capacity = FloatField("Capacity", default=0)

    @property
    @abstractmethod
    def LABEL(self) -> str:
        """Provide identifying label of the project component."""

    def from_object(self, obj: U) -> None:
        """Fill in storage component from object."""
        super().from_object(obj)
        self.capacity.data = obj.capacity

    def get_data(self) -> dict[str, ty.Any]:
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
            error = "Invalid capacity for a storage component."
            self.capacity.errors.append(error)
            raise ValidationError(error)


class BatteryForm(StorageComponentForm[model.Battery]):
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

    def from_object(self, obj: model.Battery) -> None:
        """Fill in battery component from object."""
        super().from_object(obj)
        self.battery_type.data = obj.battery_type.name
        self.battery_base_soc.data = obj.base_soc
        self.battery_min_soc.data = obj.min_soc
        self.battery_max_soc.data = obj.max_soc

    def get_data(self) -> dict[str, ty.Any]:
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
            error = "Invalid battery type"
            self.battery_type.errors.append(error)
            raise ValidationError(error)

    def validate_battery_base_soc(self, soc) -> None:
        """Validate form input for the battery base SOC."""
        if not model_val.is_legal_battery_base_soc(float(soc.data)):
            error = "Invalid battery base state of charge"
            self.battery_base_soc.errors.append(error)
            raise ValidationError(error)

    def validate_battery_min_soc(self, soc) -> None:
        """Validate form input for the battery minimal SOC."""
        error = None

        if not model_val.is_legal_battery_min_soc(float(soc.data)):
            error = "Invalid battery minimum SOC"
            self.battery_min_soc.errors.append(error)

        if soc.data > self.battery_base_soc.data:
            error = (
                "Invalid minimum battery state of charge. "
                "Minimum must be below base SOC"
            )
            self.battery_min_soc.errors.append(error)

        if error:
            raise ValidationError(error)

    def validate_battery_max_soc(self, soc) -> None:
        """Validate form input for the battery maximal SOC."""
        error = None

        if not model_val.is_legal_battery_max_soc(float(soc.data)):
            error = "Invalid battery maximum SOC"
            self.battery_max_soc.errors.append(error)

        if soc.data < self.battery_base_soc.data:
            error = (
                "Invalid maximum battery state of charge. "
                "Maximum must be above base SOC"
            )
            self.battery_max_soc.errors.append(error)

        if error:
            raise ValidationError(error)


class ConsumptionComponentForm(
    EnergyProjectComponentForm[model.ConsumptionComponent]
):
    """Form linked to the energy consumption component form."""

    LABEL = model_interface.get_consumption_component_label()

    is_critical = BooleanField("Is critical load")

    def from_object(self, obj: model.ConsumptionComponent) -> None:
        """Fill in consumption component from object."""
        super().from_object(obj)
        self.is_critical.data = obj.is_critical

    def get_data(self) -> dict[str, ty.Any]:
        """Return the data in the form fields.

        Returns
        _______
        Dictionary mapping attributes from the corresponding models to the data
        in the form fields.
        """
        return {"is_critical": self.is_critical.data, **super().get_data()}


class EnergyProjectForm(forms.HumasolSubform[model.EnergyProject]):
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

    def from_object(self, obj: model.EnergyProject) -> None:
        """Fill in energy project specifics from object."""
        for component in obj.project_components:
            if isinstance(component, model.SourceComponent):
                self.sources.append_entry()
                self.sources[-1].from_object(component)
            elif isinstance(component, model.StorageComponent):
                self.storage.append_entry()
                self.storage[-1].from_object(component)
            elif isinstance(component, model.ConsumptionComponent):
                self.loads.append_entry()
                self.loads[-1].from_object(component)

    def get_data(self) -> dict[str, ty.Any]:
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
