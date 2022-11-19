"""Module responsible for the GUI and the incoming user requests."""

# Python modules
from __future__ import annotations

from typing import TYPE_CHECKING

import flask_login
import flask_security.views as sv
from flask import Blueprint, render_template
from flask_security import roles_accepted

# Local modules
from humasol.model import model_authorization as ma

from .forms import ProjectForm

if TYPE_CHECKING:
    # This is necessary for type checking and to avoid cyclic
    # imports at runtime
    from .app import HumasolApp


# Type alias for clarity
HtmlPage = str  # A full HTML page with head and body
HtmlContent = str  # Portion of HTML formatted content


class GUI(Blueprint):
    """Class containing the GUI functionality related to projects."""

    # TODO: add 404 error page
    # TODO: add error handler
    # TODO: add logging

    def __init__(self, app: HumasolApp, **kwargs) -> None:
        """Instantiate GUI object.

        Parameters
        __________
        kwargs  -- Arguments for the flask Blueprint superclass
        """
        super().__init__("gui", __name__, **kwargs)

        self.app = app

        self._bind_routes()
        self._bind_app()

    def _bind_app(self) -> None:
        """Bind this instance to an app and vice versa.

        Register this gui's endpoints to the app and keep a reference for
        directing the backend calls.
        """
        self.register(self.app, {})

    def _bind_routes(self) -> None:
        """Bind the URL routes to the interface functions."""
        self.add_url_rule("/", "view_projects", self.view_projects)
        # self.add_url_rule("/projects-list", "get_projects",
        # self.get_projects)
        self.add_url_rule("/login", "view_login", self.view_login)
        self.add_url_rule("/login-user", "login", self.login)
        self.add_url_rule("/logout", "logout", self.logout)

    def accept_task(self, task_id: int, accepted: bool) -> None:
        """Accept or reject a task.

        Endpoint to accept or reject the responsibility of being a task
        responsible.

        Parameters
        __________
        task_id     -- Identification number of the task
        accepted    -- Whether the responsibility has been accepted or not
        """

    @roles_accepted(*ma.get_roles_humasol())
    def add_project(self, form: ProjectForm) -> None:
        """Add a new project to the system.

        Parse the completed project form to contruct a project and save it
        to the database.

        Parameters
        __________
        form    -- Completed project form
        """

    @roles_accepted(*ma.get_roles_humasol())
    def archive_project(self, project_id: int) -> None:
        """Mark an existing project as archived.

        Projects can be archived when their follow-up is no longer needed and
        are only kept for their information.

        Parameters
        __________
        project_id  -- Identifier of the project to archive
        """

    @roles_accepted(*ma.get_roles_humasol())
    def edit_project(self, project_id: int, form: ProjectForm) -> None:
        """Update the referenced project with the provided input.

        Parameters
        __________
        project_id  -- Identifier of the project to update
        form        -- New inputs with which to update the project
        """

    @roles_accepted(*ma.get_roles_humasol())
    def get_api_token(
        self, username: str, password: str, api_interface: str
    ) -> str:
        """Retrieve a data source API token.

        Retrieve a token for automatic authentication when composing periodic
        project updates. Use the provided API interface to interact with the
        third party service.

        Parameters
        __________
        username    -- Username for authentication with the third party API
        password    -- Password for authentication with the third party API
        api_interface -- Name of the class capable of interfacing with the
                        required third party API

        Returns
        _______
        Return the requested API token as a string.
        """

    @roles_accepted(*ma.get_roles_all())
    def get_dashboard(self) -> HtmlContent:
        """Retrieve the dashboard content for the current user.

        Retrieve and render the information to display on the dashboard of
        the user currently in session. If no user is in session, redirect to
        the login page.

        Returns
        _______
        Return HTML code (not a full page) containing all the requested
        information.
        """

    @roles_accepted(*ma.get_roles_all())
    def get_project(self, project_id: int) -> HtmlContent:
        """Retrieve project information.

        Retrieve and render the details of the requested project.

        Parameters
        __________
        project_id  -- Identifier of the project of interest

        Returns
        _______
        Return HTML code (not a full page) containing all the authorised
        information of the project. The role of the user defines the amount
        of authorised information.
        """

    def get_projects(self) -> HtmlContent:
        """List all projects in the system.

        Retrieve and render a list of all project in the system. Group
        projects by their category.

        Returns
        _______
        Return HTML code (not a full page) listing all the projects.
        """

    def login(self) -> HtmlPage:
        """Authenticate a user.

        Authentication parameters are passed through the request.

        Parameters
        __________
        username    -- Username of a registered user
        password    -- Corresponding password
        """
        return sv.login()

    def logout(self) -> HtmlPage:
        """End the session of an authenticated user."""
        return sv.logout()

    @roles_accepted(ma.get_role_admin(), ma.get_role_humasol_followup())
    def register_user(
        self, username: str, password: str, role: str, email: str
    ) -> None:
        """Register a new user of the system.

        Parameters
        __________
        username    -- String to be used for login
        password    -- String to be used for login
        role        -- UserRole of the user with respect to Humasol and the
                        webapp
        email       -- Email of the person behind the user
        """

    @roles_accepted(*ma.get_roles_all())
    def search_project(self, value: str) -> HtmlPage:
        """Search the database for a project with attribute matching the value.

        Parameters
        __________
        value   -- Search string for which to find a match

        Returns
        _______
        Return HTML code (not a full page) listing all matching projects.
        """

    @roles_accepted(*ma.get_roles_humasol())
    def view_add_project(self) -> HtmlPage:
        """Retrieve new project form.

        Retrieve the view to fill out a new project form. This form can then
        be submitted to create a new project.

        Returns
        _______
        Return a HTML project form page.
        """

    @roles_accepted(*ma.get_roles_all())
    def view_dashboard(self) -> HtmlPage:
        """Retrieve the page for the dashboard view.

        Retrieve the page that will contain the dashboard information for the
        user currently in session. The view does not actually contain the
        information. It shows a loading sign while fetching further details.

        Returns
        _______
        Return an empty HTML dashboard page that will fetch the data while
        loading.
        """

    @roles_accepted(*ma.get_roles_humasol())
    def view_edit_project(self, project_id: int) -> HtmlPage:
        """Retrieve the requested project in editable form.

        Retrieve a filled out form with the project information that can be
        edited and resubmitted with the changes.

        Parameters
        __________
        project_id  -- Identification of the project that should be edited

        Returns
        _______
        Return an empty HTML edit page that will fetch the data while
        loading.
        """

    def view_login(self) -> HtmlPage:
        """Retrieve the login page."""
        return sv.login()

    @roles_accepted(*ma.get_roles_all())
    def view_project(self, project_id: int) -> HtmlPage:
        """Retrieve the page to contain the project info.

        Retrieve the page which will contain the project details. It does not
        contain the information immediately. Rather, it fetches the data while
        showing a loading sign.

        Returns
        _______
        Return an empty HTML project page that will fetch the data while
        loading.
        """

    def view_projects(self) -> HtmlPage:
        """Retrieve the page to display the projects list.

        Retrieve the page that will contain a list of all the projects
        registered in the system. The page does not initially contain this
        information. Rather, it retrieves it while showing a loading screen.

        Returns
        _______
        Return an empty HTML projects page that will fetch the data while
        loading.
        """
        user = flask_login.current_user
        permission = user and any(
            map(lambda role: role in ma.get_roles_humasol(), user.roles)
        )

        return render_template(
            "project/projects.html",
            logged_in=user is not None,
            add_permissions=permission,
        )
