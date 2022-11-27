"""This package contains all the code for the Humasol webapp."""

# Python Libraries
from dotenv import load_dotenv

# Local Modules
from .ui.app import HumasolApp

load_dotenv()

app = HumasolApp()
