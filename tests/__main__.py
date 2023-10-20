"""Main test suite to run unit tests for the entire project."""

# Python Libraries
import os
import sys
import unittest

# Add path to main project
project_dir = os.path.dirname(os.path.dirname((os.path.abspath(__file__))))
sys.path.append(project_dir)

# Local modules
from test_model import TestSuiteModel  # noqa


class TestSuitModel(unittest.TestSuite):
    def __init__(self):
        super(TestSuitModel, self).__init__([TestSuiteModel()])


# Run tests
runner = unittest.TextTestRunner()
runner.run(TestSuitModel())
