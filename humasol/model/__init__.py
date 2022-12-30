"""
Data models.

Package containing all code regarding models used to store and pass
information.
"""

from .base import ProjectElement, BaseModel  # noqa

from .followup_work import FollowupJob, Period, Subscription, Task  # noqa
from .person import (  # noqa
    BelgianPartner,
    Organization,
    Partner,
    Person,
    SouthernPartner,
    Student,
    Supervisor,
)
from .project_components import (  # noqa
    Address,
    Coordinates,
    ConsumptionComponent,
    SDG,
    Battery,
    DataSource,
    EnergyProjectComponent,
    Generator,
    Grid,
    Location,
    ProjectComponent,
)

# pylint: disable=cyclic-import
from .user import Role, User, UserRole  # noqa

# pylint: enable=cyclic-import


# Must be last import to avoid problems with cyclic imports
from .project import (  # noqa
    EnergyProject,
    Project,
    ProjectCategory,
    ProjectFactory,
)

Model = ProjectElement | Project
