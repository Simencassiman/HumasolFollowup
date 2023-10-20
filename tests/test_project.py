"""Test suite for the project module."""

# Python Libraries
import datetime
import unittest

# Local modules
if __name__ == "__main__":
    # Add path to main project
    import os
    import sys

    project_dir = os.path.dirname(os.path.dirname((os.path.abspath(__file__))))
    sys.path.append(project_dir)
import humasol.exceptions as exc
from humasol.model import followup_work as fw
from humasol.model import person as pers
from humasol.model import project as proj
from humasol.model import project_elements as pe

###################
# Helper functions
###################


def check_project_attributes(tester, project):
    tester.assertEqual(tester.name, project.name)
    tester.assertEqual(tester.implementation_date, project.date)
    tester.assertEqual(tester.data_source, project.data_source.source)
    tester.assertEqual(tester.api_manager, project.data_source.api_manager)
    tester.assertEqual(tester.description, project.description)
    tester.assertIs(tester.location, project.location)
    tester.assertEqual(tester.work_folder, project.work_folder)
    tester.assertEqual(tester.students, project.students)
    tester.assertEqual(tester.supervisors, project.supervisors)
    tester.assertEqual(tester.contact_person, project.contact_person)
    tester.assertEqual(tester.code, project.code)
    tester.assertEqual(tester.partners, project.partners)
    tester.assertEqual(tester.dashboard, project.dashboard)
    tester.assertEqual(tester.save_data, project.save_data)
    tester.assertEqual(tester.project_data, project.project_data)
    tester.assertEqual(tester.extra_data, project.extra_data)
    tester.assertEqual(tester.sdgs, project.sdgs)
    tester.assertEqual(tester.subscriptions, project.subscriptions)
    tester.assertEqual(tester.tasks, project.tasks)
    creds = project.data_source.get_credentials()
    tester.assertEqual(tester.user, creds["user"])
    tester.assertEqual(tester.password, creds["password"])
    tester.assertEqual(tester.token, creds["token"])


def check_energy_project_attributes(tester, project):
    tester.assertEqual(
        "EnergyReportManager", project.data_source.report_manager
    )
    tester.assertEqual(tester.power, project.power)


###################
# Mock classes
###################


class MockProject(proj.Project):
    def __init__(self, **kwargs):
        if "data_source" not in kwargs:
            pass
        elif kwargs["data_source"] is None:
            pass
        elif isinstance(kwargs["data_source"], str):
            kwargs["data_source"] = pe.DataSource(
                kwargs["data_source"],
                "VictronAPI",
                "BatteryDataManager",
                "EnergyReportManager",
            )
        else:
            raise TypeError("Invalid 'data_source'")
        super(MockProject, self).__init__(
            category=proj.ProjectCategory.ENERGY, **kwargs
        )

    @classmethod
    def get_project(cls, **kwargs):
        pass


###################
# Test Cases
###################


class TestProjectInit(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.name = "Test project"
        cls.implementation_date = datetime.datetime.strptime(
            "01/08/2021", "%d/%m/%Y"
        ).date()
        cls.description = "Project for testing purposes"
        # cls.location = pe.Location(60, 50, "Belgium", "Leuven")
        cls.work_folder = "url/workfolder"
        cls.students = [
            pers.Student("S1", "s1@gmail.com", "KUL", "CS"),
            pers.Student("S2", "s2@gmail.com", "KUL", "Elec"),
            pers.Student("S3", "s3@gmail.com", "KUL", "Mech"),
        ]
        sup = pers.Supervisor("Test super", "ts@humasol.be", "Test oversight")
        cls.supervisors = [sup]
        cls.partners = [
            pers.Partner(
                "Part",
                "part@email.com",
                "Project oversight",
                pers.BelgianPartner("Test Partner", "path/logo.png"),
            )
        ]
        cls.contact_person = sup
        cls.code = "TP"
        cls.dashboard = "dash"
        cls.save_data = True
        cls.project_data = "folder"
        cls.extra_data = {"tags": [1, 2]}
        cls.sdgs = [pe.SDG.GOAL_1, pe.SDG.GOAL_4]
        period = fw.Period(
            1,
            fw.Period.TimeUnit.MONTH,
            start=datetime.datetime.strptime("01/09/2021", "%d/%m/%Y"),
        )
        cls.subscriptions = [fw.Subscription(sup, [period])]
        cls.tasks = [fw.Task(sup, [period], "Something", "Something more")]
        cls.api_manager = "VictronAPI"
        cls.data_source = "url/data_source"
        cls.power = 10
        cls.user = "user1"
        cls.password = "password1"
        cls.token = "andsn123nsd29fn9"

    def setUp(self) -> None:
        self.params = {
            "name": self.name,
            "implementation_date": self.implementation_date,
            "description": self.description,
            # "location": self.location,
            "work_folder": self.work_folder,
            "students": self.students,
            "supervisors": self.supervisors,
            "partners": self.partners,
            "contact_person": self.contact_person,
            "code": self.code,
            "dashboard": self.dashboard,
            "project_data": self.project_data,
            "extra_data": self.extra_data,
            "sdgs": self.sdgs,
            "subscriptions": self.subscriptions,
            "tasks": self.tasks,
            "data_source": self.data_source,
            "api_manager": self.api_manager,
            "save_data": self.save_data,
            "power": self.power,
            "user": self.user,
            "password": self.password,
            "token": self.token,
        }

    def test_illegal_superclass_instantiation(self):
        self.assertRaises(
            exc.AbstractClassException, lambda: proj.Project(**self.params)
        )

    def test_valid_project_init(self):
        pass


class TestEnergyProject(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.name = "Test project"
        cls.implementation_date = datetime.datetime.strptime(
            "01/08/2021", "%d/%m/%Y"
        ).date()
        cls.description = "Project for testing purposes"
        # cls.location = pe.Location(60, 50, "Belgium", "Leuven")
        cls.work_folder = "url"
        cls.students = [
            pers.Student("S1", "s1@gmail.com", "KUL", "CS"),
            pers.Student("S2", "s2@gmail.com", "KUL", "Elec"),
            pers.Student("S3", "s3@gmail.com", "KUL", "Mech"),
        ]
        sup = pers.Supervisor("Test super", "ts@humasol.be", "Test oversight")
        cls.supervisors = [sup]
        cls.partners = [
            pers.Partner(
                "Part",
                "part@email.com",
                "Project oversight",
                pers.BelgianPartner("Test Partner", "path/logo.png"),
            )
        ]
        cls.contact_person = sup
        cls.code = "TP"
        cls.dashboard = "dash"
        cls.save_data = True
        cls.project_data = "folder"
        cls.extra_data = {"tags": [1, 2]}
        cls.sdgs = [pe.SDG.GOAL_1, pe.SDG.GOAL_4]
        period = fw.Period(
            1,
            fw.Period.TimeUnit.MONTH,
            start=datetime.datetime.strptime("01/09/2021", "%d/%m/%Y"),
        )
        cls.subscriptions = [fw.Subscription(sup, [period])]
        cls.tasks = [fw.Task(sup, [period], "Something", "Something more")]
        cls.api_manager = "VictronAPI"
        cls.data_source = "url"
        cls.power = 10
        cls.user = "user1"
        cls.password = "password1"
        cls.token = "andsn123nsd29fn9"

    def setUp(self) -> None:
        self.params = {
            "name": self.name,
            "implementation_date": self.implementation_date,
            "description": self.description,
            # "location": self.location,
            "work_folder": self.work_folder,
            "students": self.students,
            "supervisors": self.supervisors,
            "partners": self.partners,
            "contact_person": self.contact_person,
            "code": self.code,
            "dashboard": self.dashboard,
            "project_data": self.project_data,
            "extra_data": self.extra_data,
            "sdgs": self.sdgs,
            "subscriptions": self.subscriptions,
            "tasks": self.tasks,
            "data_source": self.data_source,
            "api_manager": self.api_manager,
            "save_data": self.save_data,
            "power": self.power,
            "user": self.user,
            "password": self.password,
            "token": self.token,
        }

    def test_invalid_power(self):
        pass

    def test_invalid_project_components(self):
        pass


class TestSuiteProject(unittest.TestSuite):
    def __init__(self):
        super().__init__(
            [
                unittest.TestLoader().loadTestsFromTestCase(TestProjectInit),
                unittest.TestLoader().loadTestsFromTestCase(TestEnergyProject),
            ]
        )


# saving and loading from storage to be tested


if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    runner.run(TestSuiteProject())
