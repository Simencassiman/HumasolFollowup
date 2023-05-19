"""Module responsible for the webapp business logic."""

# Python libraries
import datetime
import typing as ty

from flask import Flask, after_this_request, request, session
from flask.sessions import SessionMixin
from flask_login import COOKIE_NAME, current_user
from flask_migrate import Migrate
from flask_security import (
    Security,
    SQLAlchemyUserDatastore,
    core,
    login_user,
    logout_user,
)
from flask_security import utils as sec_util
from flask_sqlalchemy.session import Session
from werkzeug.local import LocalProxy

# Local modules
from humasol import exceptions, model
from humasol.config import config as cf
from humasol.model import model_authorization as ma
from humasol.model import model_ops
from humasol.repository import db
from humasol.ui.app_assistant import AppAssistant
from humasol.ui.view import GUI


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
        super().__init__(__name__, *args, **kwargs)

        # TODO: create objects it depends on
        self.assistant = AppAssistant()
        self._migrate = None
        self._current_user = current_user
        self._session: LocalProxy[SessionMixin] = LocalProxy(lambda: session)

        self._setup()
        self._setup_db()
        # Setup Flask-Security
        self._setup_security()

        self._gui = GUI(self)

    def _create_admin(self, user_datastore: SQLAlchemyUserDatastore) -> None:
        """Create admin user if none exists."""
        # TODO: do this through model_ops
        with self.app_context():
            if db.engine.execute(
                db.text(
                    """
                    SELECT user_id
                    FROM users_role
                    WHERE user_role_id in (
                                    SELECT id
                                    FROM user_role
                                    WHERE name = :role_name
                                    )
                    """
                ),
                {"role_name": ma.get_role_admin().name},
            ).first():
                return

            user_datastore.create_role(name=ma.get_role_admin())
            user_datastore.create_user(
                email=cf.ADMIN_EMAIL,
                password=sec_util.hash_password(cf.ADMIN_PWD),
                roles=[ma.get_role_admin()],
                active=True,
                confirmed_at=datetime.datetime.now(),
            )

            # Pylint says the session has no commit member...
            # pylint: disable=no-member
            db.session.commit()
            # pylint: enable=no-member

    def _setup(self) -> None:
        """Configure this application instance."""
        self.config["DEBUG"] = True

        self.config["SECRET_KEY"] = cf.SECRET_KEY
        self.config["SECURITY_PASSWORD_SALT"] = cf.SECURITY_PASSWORD_SALT
        self.config["SECURITY_REGISTERABLE"] = True

        self.config["SQLALCHEMY_DATABASE_URI"] = cf.DATABASE_URL

    def _setup_db(self) -> None:
        """Set up the database connection."""
        db.init_app(self)
        self._migrate = Migrate(self, db)

        # Create tables if they do not exist
        with self.app_context():
            if not model_ops.tables_exist():
                model_ops.create_db_tables()

    def _setup_security(self) -> None:
        """Set up required security for this app."""
        self.user_datastore = SQLAlchemyUserDatastore(
            db, model.User, model.UserRole
        )
        self.security = Security(
            self, self.user_datastore, register_blueprint=False
        )
        # See if this is necessary or not for this use case
        # pylint: disable=protected-access
        self.context_processor(core._context_processor)
        # pylint: enable=protected-access

        self._create_admin(self.user_datastore)

    def archive_project(self, project_id: int) -> None:
        """Mark an existing project as archived.

        Projects can be archived when their follow-up is no longer needed and
        are only kept for their information.

        Parameters
        __________
        project_id  -- Identifier of the project to archive
        """

    def change_user_password(self, user: model.User, password: str) -> bool:
        """Change the specified user's password.

        MIT License

        Copyright (C) 2012-2021 by Matthew Wright
        Copyright (C) 2019-2021 by Chris Wagner

        Parameters
        __________
        user        -- User whose password to change
        password    -- The unhashed new password
        notify      -- if True send notification (if configured) to user
        """
        if not password:
            return False

        after_this_request(sec_util.view_commit)
        user.password = sec_util.hash_password(password)
        # Change uniquifier - this will cause ALL sessions to be invalidated.
        self.user_datastore.set_uniquifier(user)
        self.user_datastore.put(user)

        # re-login user - this will update session, optional remember etc.
        remember_cookie_name = self.config.get(
            "REMEMBER_COOKIE_NAME", COOKIE_NAME
        )
        has_remember_cookie = (
            remember_cookie_name in request.cookies
            and session.get("remember") != "clear"
        )

        login_user(user, remember=has_remember_cookie, authn_via=["change"])

        return True

    def create_project(self, parameters: dict[str, ty.Any]) -> int:
        """Create a new project in the system.

        Parameters
        __________
        parameters  -- All the parameters required to create the project

        Returns
        _______
        Return the newly assigned project identifier. If the process fails,
        returns -1.
        """
        if (
            parameters["location"]["coordinates"]["latitude"] is None
            or parameters["location"]["coordinates"]["longitude"] is None
        ):
            # TODO: get actual coordinates
            parameters["location"]["coordinates"] = {
                "latitude": 0.0,
                "longitude": 0.0,
            }

        parameters["creator"] = self.get_user()
        parameters["creation_date"] = datetime.date.today()

        success = False
        try:
            project = model_ops.create_project(parameters)
            success, _ = model_ops.save_project(project)

        except (
            exceptions.IllegalArgumentException,
            exceptions.MissingArgumentException,
        ) as exc:
            raise exceptions.FormError(str(exc)) from exc
        except exceptions.ModelException as exc:
            raise exceptions.Error500(
                "An internal error occurred while parsing the data"
            ) from exc
        except exceptions.IntegrityException as exc:
            raise exceptions.FormError(
                "Some provided elements violate database integrity."
            ) from exc
        except exceptions.RepositoryException as exc:
            raise exceptions.Error500(
                "An internal error occurred while saving the data."
            ) from exc

        return project.id if success else -1

    def edit_project(
        self, project_id: int, parameters: dict[str, ty.Any]
    ) -> None:
        """Edit an existing project in the system.

        Parameters
        __________
        parameters  -- Parameters and values to update. Contains the project
                        identifier as 'id'
        """
        project = model_ops.get_project(project_id, eager=True)
        if project is None:
            raise exceptions.Error404("Project not found")

        if not (
            self.get_user() == project.creator
            or set(self.get_user().roles).intersection(
                {ma.get_role_admin(), ma.get_role_humasol_followup()}
            )
        ):
            raise exceptions.Error404("Unauthorized request.")

        if (
            parameters["location"]["coordinates"]["latitude"] is None
            or parameters["location"]["coordinates"]["longitude"] is None
        ):
            # TODO: get actual coordinates
            parameters["location"]["coordinates"] = {
                "latitude": 0.0,
                "longitude": 0.0,
            }

        model_ops.edit_project(project, parameters)  # type: ignore

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

    def get_dashboard(self) -> ty.Optional[dict[str, ty.Any]]:
        """Retrieve dashboard information for the specified user.

        Is applied for the user currently logged in.

        Returns
        _______
        Return dictionary containing all relevant information.
        """
        if not self.get_user():
            return None

        return self.assistant.get_dashboard(self.get_user())

    def get_project(self, project_id: int, editable=False) -> model.Project:
        """Retrieve the project matching the project identifier.

        Retrieve the complete project object from storage.

        Parameters
        __________
        project_id  -- Identifier of the project to be retrieved

        Returns
        _______
        Return complete project object.
        """
        project = model_ops.get_project(project_id)

        if editable and not (
            self.get_user() == project.creator
            or set(self.get_user().roles).intersection(
                {ma.get_role_admin(), ma.get_role_humasol_followup()}
            )
        ):
            raise exceptions.InvalidRequestException("Insufficient rights")

        return project

    def get_projects(self) -> list[model.Project]:
        """Retrieve a list of all projects in the system.

        Returns
        _______
        Return a list of project objects.
        """
        # TODO: catch errors and solve or wrap
        return model_ops.get_projects()

    # pylint: disable=protected-access

    def get_session(self) -> Session:
        """Return this app's current session."""
        return self._session._get_current_object()

    def get_user(self) -> model.User:
        """Return currently logged in user."""
        return self._current_user._get_current_object()

    # pylint: enable=protected-access

    def login(self, form) -> bool:
        """Authenticate the user with provided credentials.

        Parameters
        __________
        username    -- Username of the user in this system
        password    -- Matching password for this system
        """
        # TODO: remove dependence on forms
        # TODO: Catch any errors
        assert form.user is not None
        remember_me = form.remember.data if "remember" in form else None
        after_this_request(sec_util.view_commit)
        login_user(form.user, remember=remember_me, authn_via=["password"])

        return True

    def logout(self) -> bool:
        """End the provided user's session."""
        # TODO: catch potential errors
        if self._current_user.is_authenticated:
            logout_user()

        return True

    def register_user(
        self, email: str, password: str, roles: list[str]
    ) -> model.User:
        """Register a new user in the system.

        Parameters
        __________
        password    -- New password for the user
        email       -- Email of the person behind the user
        roles       -- Role name of the user w.r.t. the system and Humasol
        """
        after_this_request(sec_util.view_commit)
        password = sec_util.hash_password(password)
        user_kwargs = {
            "email": email,
            "password": password,
            "roles": [
                self.user_datastore.create_role(name=ma.get_role(r))
                for r in roles
            ],
            "active": True,
            "confirmed_at": datetime.datetime.now(),
        }

        user = self.user_datastore.create_user(**user_kwargs)

        return user

    def remove_project(self, project_id: int) -> bool:
        """Remove the project from the database.

        Parameters
        __________
        project_id  -- ID of the project to be deleted
        """
        project = self.get_project(project_id)

        if not project:
            return False

        can_edit = (
            set((user := self.get_user()).roles).intersection(
                {ma.get_role_admin(), ma.get_role_humasol_followup()}
            )
            or user.id == project.creator.id
        )
        if not can_edit:
            return False

        try:
            model_ops.delete_project(project)
        except exceptions.ModelException:
            return False

        return True

    def search(self, value: str) -> list[model.Project]:
        """Search the projects database for attributes matching the value.

        Parameters
        __________
        value   -- Search string for which to find matching attributes

        Returns
        _______
        Return list of project objects matching the value. If no such project
        were found, return an empty list.
        """
