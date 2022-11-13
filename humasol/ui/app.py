"""Module responsible for the webapp business logic."""

# Python libraries
from typing import Any

from flask import Flask
from flask_security import Security, SQLAlchemyUserDatastore

# Local modules
from .. import config as cf
from ..model.project import Project
from ..model.user import Role, User
from ..repository import db


class HumasolApp(Flask):
    """Class containing main app logic and central control module.

    Inherits all the app logic from the Flask app component. It is responsible
    for servicing all requests from web clients. It uses the GUI to present a
    web interface to the users and is the entry point to the backend for all
    requests.
    """

    def __init__(self, *args, **kwargs) -> None:
        """Instantiate HumasolApp object.

        Parameters
        __________
        kwargs  -- Arguments for the flask App superclass
        """
        super().__init__(*args, **kwargs)

        # TODO: create objects it depends on
        self._configure()

    def _configure(self) -> None:
        self.config["DEBUG"] = True

        self.config["SECRET_KEY"] = cf.SECRET_KEY
        self.config["SECURITY_PASSWORD_SALT"] = cf.SECURITY_PASSWORD_SALT
        self.config["SECURITY_REGISTERABLE"] = True

        # TODO: do this through repo
        self.config["SQLALCHEMY_DATABASE_URI"] = cf.DB_URI

        # Setup Flask-Security
        user_datastore = SQLAlchemyUserDatastore(db, User, Role)
        self.security = Security(self, user_datastore)

    def archive_project(self, project_id: int) -> None:
        """Mark an existing project as archived.

        Projects can be archived when their follow-up is no longer needed and
        are only kept for their information.

        Parameters
        __________
        project_id  -- Identifier of the project to archive
        """

    def create_project(self, parameters: dict[str, Any]) -> int:
        """Create a new project in the system.

        Parameters
        __________
        parameters  -- All the parameters required to create the project

        Returns
        _______
        Return the newly assigned project identifier.
        """

    def edit_project(self, parameters: dict[str, Any]) -> None:
        """Edit an existing project in the system.

        Parameters
        __________
        parameters  -- Parameters and values to update. Contains the project
                        identifier as 'id'
        """

    def get_api_token(
        self, username: str, password: str, api_interface: str
    ) -> str:
        """Retrieve a token for automatic authentication.

        Data services often offer the option of using a token for
        authentication between processes. Retrieve such a token using the
        provided credentials and the specified API interface.

        Parameters
        __________
        username    -- Username for the third party service
        password    -- Matching password for the third party service
        api_interface   -- Name of the class capable of interacting with this
                            specific third party API

        Returns
        _______
        Return the retrieved token as a string.
        """

    def get_dashboard(self, user: User) -> dict[str, Any]:
        """Retrieve dashboard information for the specified user.

        Parameters
        __________
        user    -- User currently in session

        Returns
        _______
        Return dictionary containing all relevant information.
        """

    def get_project(self, project_id: int) -> Project:
        """Retrieve the project matching the project identifier.

        Retrieve the complete project object from storage.

        Parameters
        __________
        project_id  -- Identifier of the project to be retrieved

        Returns
        _______
        Return complete project object.
        """

    def get_projects(self) -> list[Project]:
        """Retrieve a list of all projects in the system.

        Returns
        _______
        Return a list of project objects.
        """

    def login(self, username: str, password: str) -> bool:
        """Authenticate the user with provided credentials.

        Parameters
        __________
        username    -- Username of the user in this system
        password    -- Matching password for this system
        """

    def logout(self, user: User) -> bool:
        """En the provided user's session."""

    def register_user(
        self, username: str, password: str, email: str, role: str
    ) -> None:
        """Register a new user in the system.

        Parameters
        __________
        username    -- Unique username for the new user
        password    -- New password for the user
        email       -- Email of the person behind the user
        role        -- UserRole of the user w.r.t. the system and Humasol
        """

    def search(self, value: str) -> list[Project]:
        """Search the projects database for attributes matching the value.

        Parameters
        __________
        value   -- Search string for which to find matching attributes

        Returns
        _______
        Return list of project objects matching the value. If no such project
        were found, return an empty list.
        """


# Run #
if __name__ == "__main__":
    print("Running app")
