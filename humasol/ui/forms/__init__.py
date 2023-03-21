"""Package providing all forms."""

import re

# pylint: disable=wrong-import-order
# pylint: disable=cyclic-import

from . import base  # noqa
from . import utils  # noqa

from .base import (  # noqa
    IHumasolForm,
    HumasolBaseForm,
    HumasolSubform,
    ProjectElementForm,
    ProjectElementWrapper,
)

from . import security  # noqa
from . import energy  # noqa
from . import general  # noqa

from .general import ProjectForm  # noqa

# pylint: enable=cyclic-import
# pylint: enable=wrong-import-order


def get_subforms() -> dict[str, list[type[HumasolSubform]]]:
    """Return all defined concrete form classes extending HumasolSubform.

    Returns
    _______
    Dictionary containing names of modules as keys which are mapped to lists
    of classes.
    """
    modules = [general, energy]

    forms = {
        match.groups()[0]: utils.get_subclasses(
            HumasolSubform, module  # type: ignore
        )
        for module in modules
        if (match := re.match(r".*\.forms\.([a-z_]*)", module.__name__))
    }

    return forms
