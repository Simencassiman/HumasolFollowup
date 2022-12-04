"""This package contains all the code for the Humasol webapp."""

# Local Modules
from . import model  # noqa
from . import repository  # noqa
from . import script  # noqa
from . import ui

app = ui.app.HumasolApp()
