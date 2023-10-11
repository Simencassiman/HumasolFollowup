"""Module for the main automation logic.

The Reporter class is responsible for listing all the projects and handling
them. If notifications need to be sent it will also take care of that.
"""


class Reporter:
    """Class responsible for automating the follow-up jobs."""

    # TODO: implement logic

    def __init__(self) -> None:
        """Initialize reporter object.

        Create the required objects to execute the automated follow-up jobs.
        """
        # TODO: Instantiate repo
        self.repo = None

    def _dispatch_project(self) -> None:
        pass

    def _save_to_drive(self, docs: dict[str, tuple[str, str]]) -> None:
        pass

    def _notify_subscribers(self) -> None:
        pass

    def _notify_taskers(self) -> None:
        pass

    def _notify_humasol(self, exception: Exception) -> None:
        pass

    def run(self):
        """Run main automation loop."""
