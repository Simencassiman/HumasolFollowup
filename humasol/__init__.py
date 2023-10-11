"""This package contains all the code for the Humasol webapp."""

# Local Modules
from . import exceptions  # noqa
from . import utils  # noqa
from . import repository  # noqa
from . import model  # noqa
from . import script  # noqa
from . import ui

app = ui.app.HumasolApp()
