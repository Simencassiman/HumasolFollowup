"""Module responsible for the GUI and the incoming user requests."""

# Python modules
from __future__ import annotations

import abc
import os
import typing as ty

import flask_security.forms as sec_forms
from flask import (
    Blueprint,
    Response,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_security import login_required, roles_accepted
from flask_security import utils as sec_util
from flask_security.forms import form_errors_munge

# Local modules
from werkzeug.datastructures import MultiDict

from humasol import exceptions
from humasol.model import model_authorization as ma
from humasol.ui import forms, utils

if ty.TYPE_CHECKING:
    # This is necessary for type checking and to avoid cyclic
    # imports at runtime
    from humasol.ui.app import HumasolApp


# Type alias for clarity
HtmlPage = str  # A full HTML page with head and body
HtmlContent = str  # Portion of HTML formatted content


class HumasolBlueprint(Blueprint):
    """Interface for all blueprints."""

    def __init__(
        self,
        name: str,
        app: HumasolApp,
        *args,
        template_prefix: str = None,
        template_folder: str = None,
        **kwargs,
    ) -> None:
        """Initialize Humasol blueprint.

        Binds blueprint routes specified in the _bind_routs method.

        Parameters
        __________
        name: name of the blueprint
        app: reference to the connected application
        template_prefix: prefix for the blueprint's template folder. Can be
                used from the main GUI to provide a nested template directory
                structure. Default None
        template_folder: name of the template folder for the blueprint. If None
                is given, the top level template folder will be used.
                Default None
        """
        super().__init__(
            name,
            __name__,
            *args,
            template_folder=(
                template_folder
                if not template_prefix or not template_folder
                else os.path.join(template_prefix, template_folder)
            ),
            **kwargs,
        )
        self.app = app
        self._bind_routes()

    @abc.abstractmethod
    def _bind_routes(self) -> None:
        """Bind route endpoints of the GUI."""


class GUI(HumasolBlueprint):
    """Class containing the GUI functionality related to projects."""

    # TODO: add 404 error page
    # TODO: add error handler
    # TODO: add logging

    TEMPLATES_FOLDER = "templates"

    def __init__(self, app: HumasolApp, **kwargs) -> None:
        """Instantiate GUI object.

        Parameters
        __________
        kwargs  -- Arguments for the flask Blueprint superclass
        """
        super().__init__(
            "gui",
            app,
            template_folder=self.TEMPLATES_FOLDER,
            **kwargs,
        )

        self.context_processor(self._set_context)

        self._bind_blueprints()
        self._bind_app()

    def _bind_app(self) -> None:
        """Bind this instance to an app and vice versa.

        Register this gui's endpoints to the app and keep a reference for
        directing the backend calls.
        """
        self.register(self.app, {})

    def _bind_blueprints(self) -> None:
        """Bind sub-gui elements."""
        security = SecurityGUI(self.app, template_prefix=self.TEMPLATES_FOLDER)
        self.register_blueprint(security, url_prefix="/security")

        projects = ProjectGUI(self.app, template_prefix=self.TEMPLATES_FOLDER)
        self.register_blueprint(projects, url_prefix="/projects")

        dashboard = DashboardGUI(
            self.app, template_prefix=self.TEMPLATES_FOLDER
        )
        self.register_blueprint(dashboard, url_prefix="/dashboard")

    def _bind_routes(self) -> None:
        """Bind the URL routes to the interface functions."""
        self.add_url_rule("/", "index", self.index)
        self.add_url_rule("/favicon.ico", "favicon", self.favicon)

    def _set_context(self) -> dict[str, bool]:
        """Set the context to render a template.

        Set the context of user rights to correctly render a template.
        """
        return dict(
            user_authenticated=self.app.get_user().is_authenticated,
            can_add_project=len(
                set(self.app.get_user().roles).intersection(
                    ProjectGUI.ROLES_ADD_PROJECT
                )
            )
            > 0,
        )

    def favicon(self) -> Response:
        """Provide icon for web browser tab.

        Web browsers try to retrieve an icon to display on the tab next to the
        page title.
        """
        return redirect("static/img/favicon.ico")

    def index(self) -> Response:
        """Provide index page."""
        return redirect(url_for("gui.projects.view_projects"))


class DashboardGUI(HumasolBlueprint):
    """User interface for dashboard endpoints."""

    NAME = "dashboard"

    # Roles access permissions
    ROLES_VIEW_DASHBOARD = {*ma.get_roles_all()}

    def __init__(self, app: HumasolApp, **kwargs: ty.Any) -> None:
        """Initialize dashboard blueprint."""
        super().__init__(self.NAME, app, template_folder=self.NAME, **kwargs)

    def _bind_routes(self) -> None:
        """Bind the URL routes to the interface functions."""
        self.add_url_rule("/", "view_dashboard", self.view_dashboard)
        self.add_url_rule(
            "/dashboard-content", "get_dashboard", self.get_dashboard
        )

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
        info = self.app.get_dashboard()

        if not info:
            return redirect(url_for("gui.security.login"))

        if "profile" in info:
            info["profile"][
                "change_password_form"
            ] = sec_forms.ChangePasswordForm(prefix="profile")
        if "users" in info:
            info["users"]["register_user_form"] = forms.security.RegisterForm(
                prefix="users"
            )

        # Render each panel
        dashboard_templates = {
            "profile": "profile.html",
            "users": "users.html",
        }
        tabs = {
            k: render_template(dashboard_templates[k], **v)
            for k, v in info.items()
        }

        return render_template("dashboard_content.html", tabs=tabs)

    @login_required
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
        return render_template("dashboard.html")


class ProjectGUI(HumasolBlueprint):
    """User interface for project related endpoints."""

    NAME = "projects"

    # Roles access permissions
    ROLES_ADD_PROJECT = {ma.get_role_admin(), *ma.get_roles_humasol()}
    ROLES_ARCHIVE_PROJECT = {ma.get_role_admin(), *ma.get_roles_humasol()}
    ROLES_SEARCH_PROJECT = {*ma.get_roles_all()}
    ROLES_VIEW_PROJECT = {*ma.get_roles_all()}

    def __init__(self, app: HumasolApp, **kwargs: ty.Any) -> None:
        """Initialize projects blueprint."""
        super().__init__(self.NAME, app, template_folder=self.NAME, **kwargs)

        self._forms = {
            n: {f.__name__: f() for f in fs}
            for n, fs in forms.get_subforms().items()
        }

    def _bind_routes(self) -> None:
        """Bind the URL routes to the interface functions."""
        self.add_url_rule("/", "view_projects", self.view_projects)
        self.add_url_rule("/projects-list", "get_projects", self.get_projects)

        self.add_url_rule("/project", "view_project", self.view_project)
        self.add_url_rule("/project-content", "get_project", self.get_project)

        self.add_url_rule(
            "/add-project", "view_add_project", self.view_add_project
        )
        self.add_url_rule(
            "/edit-project", "view_edit_project", self.view_edit_project
        )

        self.add_url_rule(
            "/save-project", "add_project", self.add_project, methods=["POST"]
        )

        self.add_url_rule(
            "/remove-project",
            "remove_project",
            self.remove_project,
            methods=["GET"],
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

        Parse the completed project form to construct a project and save it
        to the database.

        Parameters
        __________
        form    -- Completed project form
        """
        if p_id := request.args.get("id", None):
            # The project is being edited
            return self.edit_project(int(p_id))

        form = forms.ProjectForm(request.form)

        # TODO: improve flash messages
        if form.validate_on_submit():
            try:

                project_id = self.app.create_project(form.get_data())

                if project_id is not None and project_id >= 0:  # Success
                    self.app.get_session()["id"] = project_id

                    return redirect(url_for(f"gui.{self.NAME}.view_project"))

                # Saving failed
                flash("Some of the fields violate the uniqueness constraint.")

            except exceptions.FormError as exc:
                flash(str(exc))

        else:
            for key, err in form.errors.items():
                flash(f"{key}: {err}")

        self.app.get_session()["project_form"] = request.form

        return redirect(url_for(f"gui.{self.NAME}.view_add_project"))

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
    def edit_project(self, p_id: int) -> Response:
        """Update the referenced project with the provided input.

        Parameters
        __________
        project_id  -- Identifier of the project to update
        form        -- New inputs with which to update the project.
                        As a requests argument
        """
        form = forms.ProjectForm(request.form)

        # TODO: improve flash messages
        if form.validate_on_submit():
            try:

                self.app.edit_project(p_id, form.get_data())
                self.app.get_session()["id"] = p_id

                return redirect(url_for(f"gui.{self.NAME}.view_project"))

            except exceptions.FormError as exc:
                flash(str(exc))

        else:
            for key, err in form.errors.items():
                flash(f"{key}: {err}")

        self.app.get_session()["id"] = p_id
        self.app.get_session()["project_form"] = request.form

        return redirect(url_for(f"gui.{self.NAME}.view_edit_project"))

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
            return redirect(url_for(f"gui.{self.NAME}.view_projects"))

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
            return redirect(url_for(f"gui.{self.NAME}.view_projects"))

        return render_template(
            "project_content.html",
            project=project,
            editable=can_edit,
            has_followup=(
                len(project.tasks) > 0 or len(project.subscriptions) > 0
            ),
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
            "projects_list.html",
            projects=projects,
            no_projects=len(ul_ps) == 0,
        )

    @roles_accepted(*ROLES_ADD_PROJECT)
    def remove_project(self) -> HtmlPage | Response:
        """Remove a project.

        Parameters
        __________
        id  -- ID of the project to remove
        """
        if not (p_id := request.args.get("id", None)):
            # TODO: raise 403
            return redirect(url_for(f"gui.{self.NAME}.view_projects"))

        success = self.app.remove_project(int(p_id))

        if success:
            flash("Deletion was successful")
        else:
            flash("Deletion was unsuccessful")

        return redirect(url_for(f"gui.{self.NAME}.view_projects"))

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
        if form_data := self.app.get_session().get("project_form", None):
            self.app.get_session().pop("project_form")
            form = forms.ProjectForm(MultiDict(form_data))
            show_followup = form.has_followup
        else:
            form = forms.ProjectForm()
            show_followup = False

        # TODO: reload category JS if one is selected already

        return render_template(
            "form_add_project.html",
            form=form,
            id=None,
            show_followup=show_followup,
            _forms=self._forms,
            unwrap=forms.utils.unwrap,
            general_errors=False,
            team_errors=False,
            specifics_errors=False,
            followup_errors=True,
        )

    @roles_accepted(*ROLES_ADD_PROJECT)
    def view_edit_project(self) -> HtmlPage:
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
        if not (
            p_id := (
                request.args.get("id", None)
                or self.app.get_session().get("id", None)
            )
        ):
            # TODO: raise exception instead
            print("Redirecting")
            return redirect(url_for(f"gui.{self.NAME}.view_projects"))

        project = self.app.get_project(int(p_id), editable=True)
        has_followup = (
            project.tasks or project.subscriptions or project.data_source
        )

        if form_data := self.app.get_session().get("project_form", None):
            self.app.get_session().pop("project_form")
            form = forms.ProjectForm(MultiDict(form_data))
        else:
            form = forms.ProjectForm()
            form.from_object(project)

        return render_template(
            "form_add_project.html",
            form=form,
            id=project.id,
            show_followup=has_followup,
            _forms=self._forms,
            unwrap=forms.utils.unwrap,
            general_errors=False,
            team_errors=False,
            specifics_errors=False,
            followup_errors=True,
        )

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
        if not (
            p_id := (
                request.args.get("id", None)
                or self.app.get_session().get("id", None)
            )
        ):
            # TODO: raise exception instead
            print("Redirecting")
            return redirect(url_for(f"gui.{self.NAME}.view_projects"))

        project_id = int(p_id)

        return render_template("project.html", project_id=project_id)

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
            "projects.html",
            logged_in=user is not None,
            add_permissions=permission,
        )


class SecurityGUI(HumasolBlueprint):
    """User interface for security endpoints."""

    NAME = "security"

    ROLES_REGISTER_USER = {ma.get_role_admin(), ma.get_role_humasol_followup()}

    def __init__(self, app: HumasolApp, **kwargs: ty.Any) -> None:
        """Initialize security blueprint."""
        super().__init__(self.NAME, app, template_folder=self.NAME, **kwargs)

    def _bind_routes(self) -> None:
        """Bind the URL routes to the interface functions."""
        self.add_url_rule("/login", "view_login", self.view_login)
        self.add_url_rule("/login-user", "login", self.login, methods=["POST"])
        self.add_url_rule("/logout", "logout", self.logout)

        self.add_url_rule(
            "/change-password",
            "change_password",
            self.change_password,
            methods=["POST"],
        )
        self.add_url_rule(
            "/register-user",
            "register_user",
            self.register_user,
            methods=["POST"],
        )

    @roles_accepted(*ma.get_roles_all())
    def change_password(self) -> dict:
        """Reset a user's password."""
        form = sec_forms.ChangePasswordForm(request.form, prefix="profile")

        success = False
        if form.validate_on_submit():
            success = self.app.change_user_password(
                self.app.get_user(), form.new_password.data
            )

        return {
            "success": success,
            "msg": (
                "Password has been changed"
                if success
                else "Something went wrong while changing the password"
            ),
        }

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

        return redirect(url_for(f"gui.{self.NAME}.view_login"))

    def logout(self) -> Response:
        """End the session of an authenticated user."""
        self.app.logout()

        return redirect("/")

    @roles_accepted(*ROLES_REGISTER_USER)
    def register_user(self) -> dict:
        """Register a new user of the system.

        Parameters
        __________
        username    -- String to be used for login
        password    -- String to be used for login
        role        -- UserRole of the user with respect to Humasol and the
                        webapp
        email       -- Email of the person behind the user
        """
        _form = request.form.copy()
        for role in request.form.getlist("users-roles[]"):
            _form.add("users-roles", role)
        form = forms.security.RegisterForm(_form, prefix="users")

        success = False
        if form.validate_on_submit():
            success = self.app.register_user(**form.get_data()) is not None

        return {
            "success": success,
            "msg": f"Registration "
            f'{"successful" if success else "unsuccessful"}',
        }

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
            "login_user.html",
            login_user_form=form,
            identity_attributes=[[*f][0] for f in iattrs] if iattrs else [],
            **security_app._run_ctx_processor("login"),
        )
        # pylint: enable=protected-access
