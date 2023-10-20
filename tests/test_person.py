"""Test suite for the person module."""

# Python Libraries
import unittest

# Local modules
if __name__ == "__main__":
    # Add path to main project
    import os
    import sys

    project_dir = os.path.dirname(os.path.dirname((os.path.abspath(__file__))))
    sys.path.append(project_dir)
import humasol.exceptions as exc
import humasol.model.person as pers


class TestPerson(unittest.TestCase):
    def test_invalid_instantiation(self):
        self.assertRaises(
            exc.AbstractClassException,
            lambda: pers.Person(
                "Test", "test@email.com", None, pers.Humasol()
            ),
        )


class TestStudent(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.name = "Test"
        cls.email = "test@student.kuleuven.com"
        cls.phone = "+34030430440"
        cls.university = "KU Leuven"
        cls.field_of_study = "Engineering Sciences"


class TestSupervisor(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.name = "Test"
        cls.email = "test@student.kuleuven.com"
        cls.phone = "+34030430440"
        cls.function = "Project Leader"


class TestPartner(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.name = "Test"
        cls.email = "test@projects.company.com"
        cls.phone = "+34030430440"
        cls.function = "Technician"
        cls.organization = pers.BelgianPartner("org", "path/uri.png")


class TestOrganization(unittest.TestCase):
    def test_invalid_instantiation(self):
        self.assertRaises(
            exc.AbstractClassException,
            lambda: pers.Organization("TestOrg", "path/uri.png"),
        )


class TestHumasol(unittest.TestCase):
    def test_correct_arguments(self):
        org = pers.Humasol()

        self.assertEqual("Humasol", org.name, "Humasol name should be Humasol")
        # TODO: Make sure this points to the correct path
        #   (maybe shouldn't test)
        self.assertEqual("logo.png", org.logo)


class TestBelgianPartner(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.name = "Tests belgian"
        cls.logo = "path/test_belgian.png"


class TestSouthernPartner(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.name = "Tests southern"
        cls.logo = "path/test_southern.png"
        cls.country = "Tuvalu"


class TestSuitePerson(unittest.TestSuite):
    def __init__(self):
        super().__init__(
            [
                unittest.TestLoader().loadTestsFromTestCase(TestPerson),
                unittest.TestLoader().loadTestsFromTestCase(TestStudent),
                unittest.TestLoader().loadTestsFromTestCase(TestSupervisor),
                unittest.TestLoader().loadTestsFromTestCase(TestPartner),
                unittest.TestLoader().loadTestsFromTestCase(TestOrganization),
                unittest.TestLoader().loadTestsFromTestCase(TestHumasol),
                unittest.TestLoader().loadTestsFromTestCase(
                    TestBelgianPartner
                ),
                unittest.TestLoader().loadTestsFromTestCase(
                    TestSouthernPartner
                ),
            ]
        )


if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    runner.run(TestSuitePerson())
