"""Module project components.

A project object is composed of many smaller parts (project components).
This module defines all these components that are then mapped to a database
schema using the database object from the repository.

Classes
_______
ProjectComponent        -- Abstract base class for elements of a project
EnergyProjectComponent  -- Abstract superclass of all component related to
                            an energy installation.
Source          -- Abstract class for electrical sources
Grid            -- Class representing an electrical grid
PV              -- Class representing a PV installation
Generator       -- Class representing an electrical generator
Storage         -- Abstract class for electrical storage systems
Battery         -- Class representing an electrical battery
ConsumptionComponent    -- Class representing an electrical consumer element
"""

# Python Libraries
from __future__ import annotations

import typing as ty
from abc import abstractmethod
from enum import Enum, unique

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.declarative import declared_attr

# Local modules
# pylint: disable=cyclic-import
from humasol import exceptions, model
from humasol.model.snapshot import Snapshot

# pylint: enable=cyclic-import
from humasol.repository import db


class ProjectComponent(db.Model, model.ProjectElement):
    """Base class for a project component.

    Project components are elements specific to a certain project domain
    that have been used to complete the project. Components with relevant
    states that provide interesting data can be represented as a class
    implementing this interface.
    (E.g., energy components are used to build a project of the energy
    category. Interesting components might be the grid or a battery.)
    These objects can be used during the reporting operations to provide
    meaningful context or comparisons in the analyses.
    """

    __tablename__ = "project_component"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    type = db.Column(db.String)  # Used for internal mapping by SQLAlchemy

    @declared_attr
    def project_id(self) -> SQLAlchemy.Colum:
        """Return project ID foreign key database column."""
        return db.Column(
            db.Integer,
            db.ForeignKey("project.id", ondelete="CASCADE"),
        )

    __mapper_args__ = {
        "polymorphic_identity": __tablename__,
        "with_polymorphic": "*",
        "polymorphic_on": type,
    }

    def __init__(self, *args: ty.Any, **kwargs: ty.Any) -> None:
        """Instantiate project component."""
        super().__init__(*args, **kwargs)

        self.type = self.LABEL

    # Capital case attribute doesn't conform to snake-casing
    # Used here because it represents a class constant that has to be defined
    # pylint: disable=invalid-name
    @property
    @abstractmethod
    def LABEL(self) -> str:
        """Provide identifying label for a component."""

    # pylint: enable=invalid-name

    def as_dict(self) -> dict[str, ty.Any]:
        """Provide the contents of this instance as a dictionary."""
        return self.__dict__ | {"label": self.LABEL}

    @abstractmethod
    @Snapshot.protect
    def update(self, params: dict[str, ty.Any]) -> ProjectComponent:
        """Update this instance with the provided new parameters."""


# -------------------------------------
# ----- Energy project components -----
# -------------------------------------


class EnergyProjectComponent(ProjectComponent):
    """Abstract superclass of all components related to an EnergyProject.

    Attributes
    __________
    power       -- Power rating of the component
    is_primary  -- Whether this is a primary component, opposed to
                    backup or auxiliary
    """

    __tablename__ = "energy_project_component"
    __mapper_args__ = {
        "polymorphic_identity": __tablename__,
        "with_polymorphic": "*",
    }

    id = db.Column(  # Repeat ID at level to split hierarchy in tables
        None,
        db.ForeignKey("project_component.id", ondelete="CASCADE"),
        primary_key=True,
    )
    power = db.Column(db.Float, nullable=False)
    is_primary = db.Column(db.Boolean, nullable=False)

    def __init__(self, power: float, is_primary: bool = True) -> None:
        """Instantiate EnergyProjectComponent.

        Parameters
        __________
        power       -- Power rating of the component
        is_primary  -- Whether this is a primary component, opposed to
                        backup or auxiliary. Default: primary
        """
        if not EnergyProjectComponent.is_legal_power(power):
            raise exceptions.IllegalArgumentException(
                "Parameter 'power' should be a non-negative float"
            )

        if not EnergyProjectComponent.is_legal_is_primary(is_primary):
            raise exceptions.IllegalArgumentException(
                "Parameter 'is_primary' should be of type bool"
            )

        super().__init__()

        self.power = power
        self.is_primary = is_primary

    # pylint: disable=invalid-name
    @property
    @abstractmethod
    def LABEL(self) -> str:
        """Provide identifying label for a component."""

    # pylint: enable=invalid-name

    @staticmethod
    def is_legal_power(power: float) -> bool:
        """Check if the provided power is legal for an energy component."""
        return isinstance(power, (float, int)) and power >= 0

    @staticmethod
    def is_legal_is_primary(flag: bool) -> bool:
        """Check whether this is a legal flag."""
        return isinstance(flag, bool)

    @Snapshot.protect
    def update(self, params: dict[str, ty.Any]) -> EnergyProjectComponent:
        """Update this instance with the provided new parameters.

        Parameters
        __________
        params  -- Parameters with new values. Valid parameters are those
                    passed to the __init__ method

        Returns
        _______
        Return reference to self
        """
        if "power" in params:
            self.power = params["power"]
        if "is_primary" in params:
            self.is_primary = params["is_primary"]

        return self


# -----------------------------
# ----- Source components -----
# -----------------------------


class SourceComponent(EnergyProjectComponent):
    """Abstract class representing electrical sources.

    Attributes
    __________
    power       -- Power rating of the component
    is_primary  -- Whether this is a primary component, opposed to
                    back-up or auxiliary
    price   -- Price of electricity from this source (€/kWh)
    """

    __tablename__ = "source_component"
    __mapper_args__ = {
        "polymorphic_identity": __tablename__,
        "with_polymorphic": "*",
    }

    price = db.Column(db.Float)

    def __init__(self, price: float, **kwargs: ty.Any) -> None:
        """Instantiate object of this class.

        Parameters
        __________
        price   -- Price of electricity from this source (€/kWh)
        kwargs  -- Additional parameters for the superclasses
        """
        if not SourceComponent.is_legal_price(price):
            raise exceptions.IllegalArgumentException(
                "Parameter 'price' should be a non-negative float."
            )

        super().__init__(**kwargs)

        self.price = price

    # pylint: disable=invalid-name
    @property
    @abstractmethod
    def LABEL(self) -> str:
        """Provide identifying label for a component."""

    # pylint: enable=invalid-name

    @staticmethod
    def is_legal_price(price: float) -> bool:
        """Check whether the provided price is a legal energy cost."""
        return isinstance(price, (float, int)) and price >= 0

    @Snapshot.protect
    def update(self, params: dict[str, ty.Any]) -> SourceComponent:
        """Update this instance with the provided new parameters.

        Parameters
        __________
        params  -- Parameters with new values. Valid parameters are those
                    passed to the __init__ method

        Returns
        _______
        Return reference to self
        """
        super().update(params)

        if "price" in params:
            self.price = params["price"]

        return self


class Grid(SourceComponent):
    """Class representing an electric grid.

    Class containing certain attributes of an electric grid that can be
    configured for each project.

    Attributes
    __________
    power       -- Power rating of the component
    is_primary  -- Whether this is a primary component, opposed to
                    backup or auxiliary
    price       -- Price of electricity from this source (€/kWh)
    blackout_threshold  -- Power level at which the grid is considered to fail
    injection_price  -- Price (or remuneration if negative) for injecting
                        electricity back into the grid (if available)
    """

    LABEL = "grid"

    __tablename__ = "grid_component"
    __mapper_args__ = {
        "polymorphic_identity": LABEL,
        "with_polymorphic": "*",
    }
    blackout_threshold = db.Column(db.Float)
    injection_price = db.Column(db.Float)

    def __init__(
        self,
        blackout_threshold: ty.Optional[float] = None,
        injection_price: ty.Optional[float] = None,
        **kwargs: ty.Any,
    ):
        """Instantiate grid object.

        Parameters
        __________
        energy_cost     -- Price for buying electricity (€/kWh)
        blackout_threshold  -- Power level at which the grid is considered
                                to fail
        injection_price  -- Price (or remuneration if negative) for injecting
                            electricity back into the grid (if available)
        """
        if not Grid.is_legal_blackout_threshold(blackout_threshold):
            raise exceptions.IllegalArgumentException(
                "Parameter 'blackout_threshold' should be a non-negative "
                "float or None"
            )

        if not Grid.is_lega_injection_price(injection_price):
            raise exceptions.IllegalArgumentException(
                "Parameter 'injection_price' should be of type float or None"
            )

        super().__init__(**kwargs)

        self.blackout_threshold = blackout_threshold
        self.injection_price = injection_price

    @staticmethod
    def is_legal_blackout_threshold(threshold: ty.Optional[float]) -> bool:
        """Check whether the provided threshold is valid for blackouts.

        A blackout threshold should be a non-negative float or integer.
        """
        return threshold is None or (
            isinstance(threshold, (float, int)) and threshold >= 0
        )

    @staticmethod
    def is_lega_injection_price(cost: ty.Optional[float]) -> bool:
        """Check whether the provided cost is a valid injection price.

        An injection price should be a float or integer. Make no assumptions
        on whether it is a cost or remuneration.
        """
        return cost is None or isinstance(cost, (float, int))

    @Snapshot.protect
    def update(self, params: dict[str, ty.Any]) -> Grid:
        """Update this instance with the provided new parameters.

        Parameters
        __________
        params  -- Parameters with new values. Valid parameters are those
                    passed to the __init__ method

        Returns
        _______
        Return reference to self
        """
        super().update(params)

        if "blackout_threshold" in params:
            self.blackout_threshold = params["blackout_threshold"]

        if "injection_price" in params:
            self.injection_price = params["injection_price"]

        return self


class PV(SourceComponent):
    """Class representing a PV installation.

    Attributes
    __________
    power       -- Power rating of the component
    is_primary  -- Whether this is a primary component, opposed to
                    backup or auxiliary
    price       -- Price of electricity from this source (€/kWh)
    """

    LABEL = "pv"

    __tablename__ = "pv_component"
    __mapper_args__ = {
        "polymorphic_identity": LABEL,
        "with_polymorphic": "*",
    }

    # This is indeed useless delegation, but needed to satisfy mypy
    # pylint: disable=useless-parent-delegation
    def __init__(self, **kwargs: ty.Any) -> None:
        """Instantiate PV object."""
        super().__init__(**kwargs)

    # pylint: enable=useless-parent-delegation


class Generator(SourceComponent):
    """Class representing an electricity generator.

    Class containing certain attributes of an electric generator that can be
    configured for each project.

    Attributes
    __________
    power       -- Power rating of the component
    is_primary  -- Whether this is a primary component, opposed to
                    backup or auxiliary
    price       -- Price of electricity from this source (€/kWh)
    efficiency  -- Fuel conversion factor (kWh/L)
    fuel_cost        -- Price for fuel (€/L)
    overheats        -- Flag indicating whether the generator overheats during
                        operation
    overheating_time -- Operation time before the generator overheats
                        (in seconds)
    cooldown_time    -- Time required by to cool down and restart working after
                         it has overheated (in seconds)
    """

    LABEL = "generator"

    __tablename__ = "generator_component"
    __mapper_args__ = {
        "polymorphic_identity": LABEL,
        "with_polymorphic": "*",
    }

    efficiency = db.Column(db.Float)
    fuel_cost = db.Column(db.Float)
    overheats = db.Column(db.Boolean)
    overheating_time = db.Column(db.Float)
    cooldown_time = db.Column(db.Float)

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        efficiency: float,
        fuel_cost: float,
        overheats: bool = False,
        overheating_time: ty.Optional[float] = None,
        cooldown_time: ty.Optional[float] = None,
        **kwargs: ty.Any,
    ):
        """Instantiate an object of this class.

        Parameters
        __________
        efficiency       -- Fuel conversion factor (kWh/L)
        fuel_cost        -- Price for fuel (€/L)
        overheats        -- Flag indicating whether the generator overheats
                            during operation
        overheating_time -- Operation time before the generator overheats
                            (in seconds)
        cooldown_time    -- Time required by to cool down and restart working
                            after it has overheated (in seconds)
        kwargs           -- Parameters for superclasses
        """
        if not Generator.is_legal_efficiency(efficiency):
            raise exceptions.IllegalArgumentException(
                "Parameter 'efficiency' should be a positive float"
            )

        if not Generator.is_legal_fuel_cost(fuel_cost):
            raise exceptions.IllegalArgumentException(
                "Parameter 'fuel_cost' should be a non-negative float"
            )

        if not Generator.is_legal_overheats(overheats):
            raise exceptions.IllegalArgumentException(
                "Parameter 'overheats' should be of type bool"
            )

        if not Generator.is_legal_overheating_time(overheating_time):
            raise exceptions.IllegalArgumentException(
                "Parameter 'overheating_time' should be a non-negative float "
                "or None"
            )

        if not Generator.is_legal_cooldown_time(cooldown_time):
            raise exceptions.IllegalArgumentException(
                "Parameter 'cooldown_time' should be a non-negative float "
                "or None"
            )

        if overheats and (overheating_time is None or cooldown_time is None):
            raise exceptions.IllegalArgumentException(
                "A generator that overheats must have an operation and "
                "cooldown time"
            )

        if not overheats and (overheating_time or cooldown_time):
            raise exceptions.IllegalArgumentException(
                "A generator that does not overheat cannot have an "
                "'overheating_time' nor a 'cooldown_time'"
            )

        super().__init__(**kwargs)

        self.efficiency = efficiency
        self.fuel_cost = fuel_cost
        self.overheats = overheats
        self.overheating_time = overheating_time
        self.cooldown_time = cooldown_time

    # pylint: enable=too-many-arguments

    @staticmethod
    def is_legal_cooldown_time(time: ty.Optional[float]) -> bool:
        """Check whether the provided cooldown time is a legal duration."""
        return time is None or (isinstance(time, (float, int)) and time >= 0)

    @staticmethod
    def is_legal_efficiency(factor: float) -> bool:
        """Check whether the provided efficiency is a legal fuel efficiency."""
        return isinstance(factor, (float, int)) and factor > 0

    @staticmethod
    def is_legal_fuel_cost(cost: float) -> bool:
        """Check whether the provided cost is legal."""
        return isinstance(cost, (float, int)) and cost >= 0

    @staticmethod
    def is_legal_overheating_time(time: ty.Optional[float]) -> bool:
        """Check whether the provided time is a legal duration."""
        return time is None or (isinstance(time, (float, int)) and time >= 0)

    @staticmethod
    def is_legal_overheats(flag: bool) -> bool:
        """Check whether the provide flag is a legal flag."""
        return isinstance(flag, bool)

    def is_valid_overheats(self, flag: bool) -> bool:
        """Check weather the flag is valid for the generator object.

        If the generator can overheat, the times have to be specified before.
        The flag should control all the logic, so if it is false, then the
        times don't matter. If it is true, then the times do matter, and so
        they must already be specified to avoid an inconsistent state.
        """
        return (
            not flag
            or self.cooldown_time is not None
            and self.overheating_time is not None
        )

    @Snapshot.protect
    def update(self, params: dict[str, ty.Any]) -> Generator:
        """Update this instance with the provided new parameters.

        Parameters
        __________
        params  -- Parameters with new values. Valid parameters are those
                    passed to the __init__ method

        Returns
        _______
        Return reference to self
        """
        super().update(params)

        if "efficiency" in params:
            self.efficiency = params["efficiency"]

        if "fuel_cost" in params:
            self.fuel_cost = params["fuel_cost"]

        if "overheating_time" in params:
            self.overheating_time = params["overheating_time"]

        if "cooldown_time" in params:
            self.cooldown_time = params["cooldown_time"]

        if "overheats" in params:
            self.overheats = params["overheats"]

            if not self.overheats:
                self.cooldown_time = None
                self.overheating_time = None

        return self


# ------------------------------
# ----- Storage components -----
# ------------------------------


class StorageComponent(EnergyProjectComponent):
    """Class representing project elements for electrical storage.

    Attributes
    __________
    power       -- Power rating of the component
    is_primary  -- Whether this is a primary component, opposed to
                    backup or auxiliary
    capacity    -- Electrical storage capacity (kWh)
    """

    __tablename__ = "storage_component"
    __mapper_args__ = {
        "polymorphic_identity": __tablename__,
        "with_polymorphic": "*",
    }

    capacity = db.Column(db.Float)

    def __init__(self, capacity: float, **kwargs: ty.Any) -> None:
        """Instantiate object of this class.

        Parameters
        __________
        capacity    -- Storage capacity (kWh)
        kwargs      --  Parameters for the superclasses
        """
        if not StorageComponent.is_legal_capacity(capacity):
            raise exceptions.IllegalArgumentException(
                "Parameter 'capacity' should be a non-negative float"
            )

        super().__init__(**kwargs)

        self.capacity = capacity

    # pylint: disable=invalid-name
    @property
    @abstractmethod
    def LABEL(self) -> str:
        """Provide identifying label for a component."""

    # pylint: enable=invalid-name

    @staticmethod
    def is_legal_capacity(capacity: float) -> bool:
        """Check whether the provided amount is a legal capacity."""
        return isinstance(capacity, (float, int)) and capacity >= 0

    @Snapshot.protect
    def update(self, params: dict[str, ty.Any]) -> StorageComponent:
        """Update this instance with the provided new parameters.

        Parameters
        __________
        params  -- Parameters with new values. Valid parameters are those
                    passed to the __init__ method

        Returns
        _______
        Return reference to self
        """
        super().update(params)

        if "capacity" in params:
            self.capacity = params["capacity"]

        return self


class Battery(StorageComponent):
    """Class representing an electric battery.

    Class containing certain attributes of an electric battery that can be
    configured for each project.

    Attributes
    __________
    power       -- Power rating of the component
    is_primary  -- Whether this is a primary component, opposed to
                    backup or auxiliary
    capacity    -- Electrical storage capacity (kWh)
    battery_type  -- Type of electrical battery (e.g., Lithium Ion)
    base_soc    -- Base state of charge
    min_soc     -- Minimally allowed state of charge
    max_soc     -- Maximally allowed state of charge
    """

    LABEL = "battery"

    __tablename__ = "battery_component"
    __mapper_args__ = {
        "polymorphic_identity": LABEL,
        "with_polymorphic": "*",
    }

    @unique
    class BatteryType(Enum):
        """Enum class for battery types."""

        LITHIUM_ION = "Lithium ion"
        LEAD_ACID = "Lead acid"

        @staticmethod
        def from_str(label: str) -> Battery.BatteryType:
            """Provide enum element from the provided label string."""
            try:
                return Battery.BatteryType.__members__[label.upper()]
            except KeyError as exc:
                raise exceptions.IllegalArgumentException(
                    f"Unknown battery type: {label}"
                ) from exc

        def __repr__(self) -> str:
            """Provide a string representation of the element."""
            return self.value

        def __str__(self) -> str:
            """Provide a string version of the element."""
            return self.value

    battery_type = db.Column(db.Enum(BatteryType))
    base_soc = db.Column(db.Float)
    min_soc = db.Column(db.Float)
    max_soc = db.Column(db.Float)

    def __init__(
        self,
        battery_type: BatteryType,
        base_soc: float,
        min_soc: float = 50,
        max_soc: float = 90,
        **kwargs: ty.Any,
    ) -> None:
        """Instantiate a battery object.

        Parameters
        __________
        battery_type      -- Type of electrical battery (e.g., Lithium Ion).
                        Value should be from Battery.BatteryType enum
        base_soc    -- Base state of charge
        min_soc     -- Minimally allowed state of charge
        max_soc     -- Maximally allowed state of charge
        kwargs      -- Parameters for the superclasses
        """
        if not Battery.is_legal_battery_type(battery_type):
            raise exceptions.IllegalArgumentException(
                "Parameter 'battery_type' should not be None and of "
                "type BatteryType"
            )

        if not Battery.is_legal_base_soc(base_soc):
            raise exceptions.IllegalArgumentException(
                "Parameter 'base_soc' should be a float in the range [0,100]"
            )

        if not Battery.is_legal_min_soc(min_soc):
            raise exceptions.IllegalArgumentException(
                "Parameter 'min_soc' should be a float in the range [0,100]"
            )

        if not Battery.is_legal_max_soc(max_soc):
            raise exceptions.IllegalArgumentException(
                "Parameter 'max_soc' should be a float in the range [0,100]"
            )

        if max_soc < min_soc:
            raise exceptions.IllegalArgumentException(
                "Parameter 'max_soc' cannot be below 'min_soc'"
            )

        if not min_soc <= base_soc <= max_soc:
            raise exceptions.IllegalArgumentException(
                "Parameter 'base_soc' should be in the range "
                "[min_soc, max_soc]"
            )

        super().__init__(**kwargs)

        self.battery_type = battery_type
        self.base_soc = base_soc
        self.min_soc = min_soc
        self.max_soc = max_soc

    @staticmethod
    def _is_legal_soc(soc: float) -> bool:
        """Check whether the provided state of charge is legal."""
        return isinstance(soc, (float, int)) and 0 <= soc <= 100

    @staticmethod
    def from_form(**kwargs: ty.Any) -> Battery:
        """Create a battery from form input."""
        if "battery_type" in kwargs:
            kwargs["battery_type"] = Battery.BatteryType.from_str(
                kwargs["battery_type"]
            )

        return Battery(**kwargs)

    @staticmethod
    def is_legal_base_soc(soc: float) -> bool:
        """Check whether the provided soc is a legal base state of charge."""
        return Battery._is_legal_soc(soc)

    @staticmethod
    def is_legal_battery_type(battery_type: BatteryType) -> bool:
        """Check whether the provided type is a legal battery type."""
        return isinstance(battery_type, Battery.BatteryType)

    @staticmethod
    def is_legal_max_soc(soc: float) -> bool:
        """Check if the provided soc is a legal maximal state of charge."""
        return Battery._is_legal_soc(soc)

    @staticmethod
    def is_legal_min_soc(soc: float) -> bool:
        """Check if the provided soc is a legal minimal state of charge."""
        return Battery._is_legal_soc(soc)

    def is_valid_base_soc(self, soc: bool) -> bool:
        """Check that the base SOC is between the min and max SOC."""
        return (
            self.is_legal_base_soc(soc) and self.min_soc <= soc <= self.max_soc
        )

    def is_valid_max_soc(self, soc: float) -> bool:
        """Check that the max SOC is above both the min and base SOC."""
        return (
            self.is_legal_max_soc(soc)
            and soc >= self.min_soc
            and soc >= self.base_soc
        )

    def is_valid_min_soc(self, soc: float) -> bool:
        """Check that the min SOC is below both the base and max SOC."""
        return (
            self.is_legal_min_soc(soc)
            and soc <= self.base_soc
            and soc <= self.max_soc
        )

    @Snapshot.protect
    def update(self, params: dict[str, ty.Any]) -> Battery:
        """Update this instance with the provided new parameters.

        Parameters
        __________
        params  -- Parameters with new values. Valid parameters are those
                    passed to the __init__ method

        Returns
        _______
        Return reference to self.
        """
        super().update(params)

        base_present = "base_soc" in params
        min_present = "min_soc" in params
        max_present = "max_soc" in params
        base_soc = params["base_soc"] if base_present else self.base_soc
        min_soc = params["min_soc"] if min_present else self.min_soc
        max_soc = params["max_soc"] if max_present else self.max_soc

        if base_present or min_present or max_present:
            # Allow to lower minimal state of charge before lowering base
            # state of charge below the previous minimal level, otherwise it
            # might be impossible to change to new values.
            # Consider: change from (base, min) = (80,70) to (50, 20)
            #     is impossible when always setting the base first,
            #     the setter won't allow going under the minimal state of
            #     charge.
            # Consider: change from (50, 20) to (80, 70) is impossible when
            #     always setting minimal state of charge first, the setter
            #     won't allow to go above the base state of charge.
            if min_soc < self.min_soc:
                self.min_soc = min_soc
                self.base_soc = base_soc
                self.max_soc = max_soc
            elif max_soc > self.max_soc:
                self.max_soc = max_soc
                self.base_soc = base_soc
                self.min_soc = min_soc
            else:
                self.base_soc = base_soc
                self.min_soc = min_soc
                self.max_soc = max_soc

        if "battery_type" in params:
            self.battery_type = params["battery_type"]

        return self


# ----------------------------------
# ----- Consumption components -----
# ----------------------------------


class ConsumptionComponent(EnergyProjectComponent):
    """Class representing an electrical consumption element.

    Attributes
    __________
    power       -- Power rating of the component
    is_primary  -- Whether this is a primary component, opposed to
                    backup or auxiliary
    is_critical -- Whether it should be ensured that this component is
                    always powered
    """

    LABEL = "consumer"

    __tablename__ = "consumption_component"
    __mapper_args__ = {
        "polymorphic_identity": LABEL,
        "with_polymorphic": "*",
    }

    is_critical = db.Column(db.Boolean)

    def __init__(self, is_critical: bool, **kwargs: ty.Any) -> None:
        """Instantiate object of this class.

        Parameters
        __________
        is_critical -- Flag indicating whether this element's power should be
                        prioritized
        """
        if not ConsumptionComponent.is_legal_is_critical(is_critical):
            raise exceptions.IllegalArgumentException(
                "Parameter 'is_critical' should be of type bool"
            )

        super().__init__(**kwargs)

        self.is_critical = is_critical

    @staticmethod
    def is_legal_is_critical(flag: bool) -> bool:
        """Check whether the provided flag is a legal flag."""
        return isinstance(flag, bool)

    @Snapshot.protect
    def update(self, params: dict[str, ty.Any]) -> ConsumptionComponent:
        """Update this instance with the provided new parameters.

        Parameters
        __________
        params  -- Parameters with new values. Valid parameters are those
                    passed to the __init__ method

        Returns
        _______
        Return reference to self.
        """
        super().update(params)

        if "is_critical" in params:
            self.is_critical = params["is_critical"]

        return self
