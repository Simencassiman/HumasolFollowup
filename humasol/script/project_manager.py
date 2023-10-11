"""Module for project manager class."""

# Python Libraries

# Local modules
from humasol import model, script


class ProjectManager:
    """Class responsible for managing a project automatic jobs."""

    def __init__(self) -> None:
        """Instantiate project manager object."""
        self.policy = ProjectManagerPolicy(self)

        self.api_manager: script.APIManager
        self.data_manager: script.DataManager
        self.report_manager: script.ReportManager

    def handle_project(self, project: model.Project) -> dict:
        """Handle the jobs to be carried out for the given project."""
        self.policy.configure(project)

        # TODO: implement glue logic (including checking if there should be
        #  updates)

        # Retrieve data
        link = "some-link"
        method = "get"
        data = self.api_manager.get_data(link, method)

        # Process data
        self.data_manager.process_data(data)
        summary = self.data_manager.create_summary()
        # ...

        # Generate report
        report = self.report_manager.generate_report(summary)

        return {"report": report, "recipients": []}


class ProjectManagerPolicy:
    """Policy for configuring the project manager's sub-managers."""

    def __init__(self, manager: ProjectManager) -> None:
        """Bind policy object to the provided manager."""
        self.manager = manager

    def _get_api_manager(self) -> script.APIManager:
        pass

    def _get_data_manager(self) -> script.DataManager:
        pass

    def _get_report_manager(self) -> script.ReportManager:
        pass

    def configure(self, project: model.Project) -> None:
        """Configure the linked manager for the given project."""
