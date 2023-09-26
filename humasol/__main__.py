"""This module will run the main code."""

from humasol import app

with app.app_context():
    app.run()
