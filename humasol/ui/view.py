"""Module responsible for the GUI and the incoming user requests."""

# Python modules
from __future__ import annotations

from typing import TYPE_CHECKING

from flask import (
    Blueprint,
    Response,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_security import roles_accepted
from flask_security import utils as sec_util
from flask_security.forms import form_errors_munge

# Local modules
from humasol.model import model_authorization as ma

from . import utils
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

    ROLES_ADD_PROJECT = {ma.get_role_admin(), *ma.get_roles_humasol()}
    ROLES_ARCHIVE_PROJECT = {ma.get_role_admin(), *ma.get_roles_humasol()}
    ROLES_REGISTER_USER = {ma.get_role_admin(), ma.get_role_humasol_followup()}
    ROLES_SEARCH_PROJECT = {*ma.get_roles_all()}
    ROLES_VIEW_DASHBOARD = {*ma.get_roles_all()}
    ROLES_VIEW_PROJECT = {*ma.get_roles_all()}

    def __init__(self, app: HumasolApp, **kwargs) -> None:
        """Instantiate GUI object.

        Parameters
        __________
        kwargs  -- Arguments for the flask Blueprint superclass
        """
        super().__init__("gui", __name__, **kwargs)

        self.app = app

        self.context_processor(self._set_context)

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
        self.add_url_rule("/favicon.ico", "favicon", self.favicon)

        self.add_url_rule("/login", "view_login", self.view_login)
        self.add_url_rule("/login-user", "login", self.login, methods=["POST"])
        self.add_url_rule("/logout", "logout", self.logout)

        self.add_url_rule("/", "view_projects", self.view_projects)
        self.add_url_rule("/projects-list", "get_projects", self.get_projects)

        self.add_url_rule("/project", "view_project", self.view_project)
        self.add_url_rule("/project-content", "get_project", self.get_project)

        self.add_url_rule(
            "/add-project", "view_add_project", self.view_add_project
        )
        self.add_url_rule(
            "/save-project", "add_project", self.add_project, methods=["POST"]
        )

    def _set_context(self) -> dict[str, bool]:
        """Set the context to render a template.

        Set the context of user rights to correctly render a template.
        """
        user = self.app.get_user()
        return dict(
            user_authenticated=user.is_authenticated,
            can_add_project=len(
                set(user.roles).intersection(self.ROLES_ADD_PROJECT)
            )
            > 0,
        )

    def accept_task(self, task_id: int, accepted: bool) -> None:
        """Accept or reject a task.

        Endpoint to accept or reject the responsibility of being a task
        responsible.

        Parameters
        __________
        task_id     -- Identification number of the task
        accepted    -- Whether the responsibility has been accepted or not
        """

    @roles_accepted(*ROLES_ADD_PROJECT)
    def add_project(self) -> Response:
        """Add a new project to the system.

        Parse the completed project form to contruct a project and save it
        to the database.

        Parameters
        __________
        form    -- Completed project form
        """
        return redirect(url_for("gui.view_projects"))

    @roles_accepted(*ROLES_ARCHIVE_PROJECT)
    def archive_project(self, project_id: int) -> None:
        """Mark an existing project as archived.

        Projects can be archived when their follow-up is no longer needed and
        are only kept for their information.

        Parameters
        __________
        project_id  -- Identifier of the project to archive
        """

    @roles_accepted(*ROLES_ADD_PROJECT)
    def edit_project(self, project_id: int, form: ProjectForm) -> None:
        """Update the referenced project with the provided input.

        Parameters
        __________
        project_id  -- Identifier of the project to update
        form        -- New inputs with which to update the project
        """

    def favicon(self) -> Response:
        """Provide icon for web browser tab.

        Web browsers try to retrieve an icon to display on the tab next to the
        page title.
        """
        return redirect("static/img/favicon.ico")

    @roles_accepted(*ROLES_ADD_PROJECT)
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

    @roles_accepted(*ROLES_VIEW_DASHBOARD)
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
    def get_project(self) -> HtmlContent | Response:
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
        if not (p_id := request.args.get("id", None)):
            # TODO: raise 403
            return redirect(url_for("gui.view_projects"))

        project_id = int(p_id)
        project = self.app.get_project(project_id)
        can_edit = (
            set((user := self.app.get_user()).roles).intersection(
                {ma.get_role_admin(), ma.get_role_humasol_followup()}
            )
            or user.id == project.creator.id
        )

        if not project:
            # TODO: raise 403
            return redirect(url_for("gui.view_projects"))

        return render_template(
            "project/project_content.html", project=project, editable=can_edit
        )

    def get_projects(self) -> HtmlContent:
        """List all projects in the system.

        Retrieve and render a list of all project in the system. Group
        projects by their category.

        Returns
        _______
        Return HTML code (not a full page) listing all the projects.
        """
        ul_ps = self.app.get_projects()
        projects = utils.categorize_projects(ul_ps)

        return render_template(
            "project/projects_list.html",
            projects=projects,
            no_projects=len(ul_ps) == 0,
        )

    def login(self) -> Response | HtmlPage:
        """Authenticate a user.

        Authentication parameters are passed through the request.
        """
        security_app = self.app.extensions["security"]
        form_class = security_app.login_form

        form = form_class(request.form, meta=sec_util.suppress_form_csrf())

        if form.validate_on_submit():
            login_success = self.app.login(form)
            if login_success:
                return redirect("/")

        # Validation failed - make sure all error messages are generic
        if (
            request.method == "POST"
            and self.app.config.get("SECURITY_RETURN_GENERIC_RESPONSES", None)
            and not form.user_authenticated
        ):
            fields_to_squash = dict(
                email=dict(replace_msg="GENERIC_AUTHN_FAILED"),
                password=dict(replace_msg="GENERIC_AUTHN_FAILED"),
            )
            if hasattr(form, "username"):
                fields_to_squash["username"] = dict(
                    replace_msg="GENERIC_AUTHN_FAILED"
                )
            form_errors_munge(form, fields_to_squash)

        if form.is_submitted() and not form.validate():
            self.app.get_session()["formdata"] = request.form

        return redirect(url_for("gui.view_login"))

    def logout(self) -> Response:
        """End the session of an authenticated user."""
        self.app.logout()

        return redirect("/")

    @roles_accepted(*ROLES_REGISTER_USER)
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

    @roles_accepted(*ROLES_SEARCH_PROJECT)
    def search_project(self, value: str) -> HtmlPage:
        """Search the database for a project with attribute matching the value.

        Parameters
        __________
        value   -- Search string for which to find a match

        Returns
        _______
        Return HTML code (not a full page) listing all matching projects.
        """

    @roles_accepted(*ROLES_ADD_PROJECT)
    def view_add_project(self) -> HtmlPage:
        """Retrieve new project form.

        Retrieve the view to fill out a new project form. This form can then
        be submitted to create a new project.

        Returns
        _______
        Return a HTML project form page.
        """
        form = ProjectForm()

        return render_template(
            "project/form_add_project.html", form=form, show_followup=False
        )

    @roles_accepted(*ROLES_VIEW_DASHBOARD)
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

    @roles_accepted(*ROLES_ADD_PROJECT)
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
        security_app = self.app.extensions["security"]
        iattrs = self.app.config["SECURITY_USER_IDENTITY_ATTRIBUTES"]

        form_class = security_app.login_form
        formdata = self.app.get_session().get("formdata", None)
        if formdata:
            form = form_class(request.form, meta=sec_util.suppress_form_csrf())
            form.validate()
            self.app.get_session().pop("formdata")
        else:
            form = form_class()

        # pylint: disable=protected-access
        return render_template(
            "security/login_user.html",
            login_user_form=form,
            identity_attributes=[[*f][0] for f in iattrs] if iattrs else [],
            **security_app._run_ctx_processor("login"),
        )
        # pylint: enable=protected-access

    @roles_accepted(*ROLES_VIEW_PROJECT)
    def view_project(self) -> HtmlPage | Response:
        """Retrieve the page to contain the project info.

        Retrieve the page which will contain the project details. It does not
        contain the information immediately. Rather, it fetches the data while
        showing a loading sign.

        Returns
        _______
        Return an empty HTML project page that will fetch the data while
        loading.
        """
        if not (p_id := request.args.get("id", None)):
            # TODO: raise exception instead
            return redirect(url_for("gui.view_projects"))

        project_id = int(p_id)

        return render_template("project/project.html", project_id=project_id)

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
        user = self.app.get_user()
        permission = user and any(
            map(lambda role: role in ma.get_roles_humasol(), user.roles)
        )

        return render_template(
            "project/projects.html",
            logged_in=user is not None,
            add_permissions=permission,
        )
