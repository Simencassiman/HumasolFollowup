"""This module will run the main code."""

from humasol import app

if __name__ == "__main__":
    with app.app_context():
        app.run()
