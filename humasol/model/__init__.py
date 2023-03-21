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
from .project_elements import (  # noqa
    Address,
    Coordinates,
    SDG,
    DataSource,
    Location,
)

from .project_components import (  # noqa
    ConsumptionComponent,
    Battery,
    EnergyProjectComponent,
    Generator,
    Grid,
    ProjectComponent,
    PV,
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

# pylint: disable=wrong-import-order
from humasol import script  # noqa

# pylint: enable=wrong-import-order

Model = ProjectElement | Project
