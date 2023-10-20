"""Test suite for the module package."""

# Python Libraries
import unittest

# Local modules
if __name__ == "__main__":
    # Add path to main project
    import os
    import sys

    project_dir = os.path.dirname(os.path.dirname((os.path.abspath(__file__))))
    sys.path.append(project_dir)

from test_followup_work import TestSuiteFollowupWork
from test_person import TestSuitePerson
from test_project import TestSuiteProject


class TestSuiteModel(unittest.TestSuite):
    def __init__(self):
        super().__init__(
            [
                TestSuitePerson(),
                TestSuiteFollowupWork(),
                TestSuiteProject(),
            ]
        )


if __name__ == "__main__":
    # Run tests
    runner = unittest.TextTestRunner()
    runner.run(TestSuiteModel())
