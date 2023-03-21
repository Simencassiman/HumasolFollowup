"""Module responsible for the functionality extensions of the app."""

# Python Libraries
import typing as ty

# Local modules
from humasol import model
from humasol.model import model_authorization as ma
from humasol.model import model_ops


class AppAssistant:
    """Class assisting central app in information recollection."""

    def _get_dashboard_admin(self) -> dict[str, ty.Any]:
        """Collect data for an admin's dashboard."""
        return {"users": {"users": model_ops.get_users()}}

    def _get_dashboard_followup(self) -> dict[str, ty.Any]:
        """Collect data for a dashboard of a user from follow-up."""
        return {"users": {"users": model_ops.get_users()}}

    def get_dashboard(self, user: model.User) -> dict[str, ty.Any]:
        """Collect data for user dashboard."""
        # General section
        dashboard = {
            "profile": {
                "user": user,
                "my_projects": model_ops.get_my_projects(user),
                "connected_projects": model_ops.get_my_associated_projects(
                    user
                ),
                "subsciptions": model_ops.get_my_subscriptions(user),
                "tasks": model_ops.get_my_tasks(user),
            }
        }

        # Add role specific dashboard components
        if ma.get_role_humasol_followup() in user.roles:
            dashboard.update(self._get_dashboard_followup())

        if ma.get_role_admin() in user.roles:
            dashboard.update(self._get_dashboard_admin())

        return dashboard
