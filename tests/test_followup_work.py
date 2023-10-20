"""Test suite for the followup_work module."""

# Python Libraries
import datetime
import os.path
import unittest

import mock
from dateutil.relativedelta import relativedelta

# Local modules
if __name__ == "__main__":
    # Add path to main project
    import sys

    project_dir = os.path.dirname(os.path.dirname((os.path.abspath(__file__))))
    sys.path.append(project_dir)
from humasol import exceptions as exc
from humasol import model
from humasol.model import followup_work as fw
from humasol.model import person as pers

student = pers.Student(
    "Test", "test@student.be", "KU Leuven", "Engineering Sciences"
)


class TestFollowupJob(unittest.TestCase):
    def test_invalid_instantiation(self):
        period = fw.Period(
            2,
            fw.Period.TimeUnit.MONTH,
            start=datetime.date.today() + relativedelta(months=-2),
            end=datetime.date.today() + relativedelta(months=+5),
        )
        self.assertRaises(
            exc.AbstractClassException,
            lambda: fw.FollowupJob(student, [period], datetime.date.today()),
        )


class TestSubscriptionInit(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.person = student
        cls.period = fw.Period(
            2,
            fw.Period.TimeUnit.MONTH,
            start=datetime.date.today() + relativedelta(months=-2),
            end=datetime.date.today() + relativedelta(months=+5),
        )
        cls.another_period = fw.Period(
            5,
            fw.Period.TimeUnit.MONTH,
            start=datetime.date.today() + relativedelta(months=+10),
            end=datetime.date.today() + relativedelta(months=+20),
        )
        cls.passed_period = fw.Period(
            2,
            fw.Period.TimeUnit.MONTH,
            start=datetime.date.today() + relativedelta(months=-10),
            end=datetime.date.today() + relativedelta(months=-2),
        )
        cls.date = datetime.date.today()

    def test_valid_arguments(self):
        sub = fw.Subscription(self.person, [self.period], self.date)

        self.assertIs(sub.subscriber, self.person)
        self.assertIn(self.period, sub.periods)
        self.assertEqual(1, len(sub.periods))
        self.assertEqual(self.date, sub.last_notification)

    def test_valid_none_last_notification(self):
        sub = fw.Subscription(self.person, [self.period], None)

        self.assertIsNone(sub.last_notification)

        sub = fw.Subscription(self.person, [self.period])

        self.assertIsNone(sub.last_notification)

    def test_valid_unordered_periods(self):
        first_period = self.period
        second_period = self.another_period

        sub = fw.Subscription(self.person, [first_period, second_period], None)

        self.assertIn(first_period, sub.periods)
        self.assertIn(second_period, sub.periods)
        self.assertEqual(2, len(sub.periods))

        sub = fw.Subscription(self.person, [second_period, first_period], None)

        self.assertIn(first_period, sub.periods)
        self.assertIn(second_period, sub.periods)
        self.assertEqual(2, len(sub.periods))

    def test_invalid_subscriber(self):
        # None
        self.assertRaises(
            exc.IllegalArgumentException,
            lambda: fw.Subscription(None, [self.period], self.date),
        )
        # Not a Person
        self.assertRaises(
            exc.IllegalArgumentException,
            lambda: fw.Subscription(pers.Humasol(), [self.period], self.date),
        )

    def test_invalid_periods(self):
        # For not a list
        self.assertRaises(
            exc.IllegalArgumentException,
            lambda: fw.Subscription(self.person, self.period, self.date),
        )

        # For an empty list
        self.assertRaises(
            exc.IllegalArgumentException,
            lambda: fw.Subscription(self.person, [], self.date),
        )

        # For a list containing non-period objects
        self.assertRaises(
            exc.IllegalArgumentException,
            lambda: fw.Subscription(
                self.person, [self.period, None], self.date
            ),
        )

        # For past period
        self.assertRaises(
            exc.IllegalArgumentException,
            lambda: fw.Subscription(
                self.person, [self.passed_period], self.date
            ),
        )

        # For overlapping periods
        first_period = fw.Period(
            1,
            fw.Period.TimeUnit.MONTH,
            start=datetime.datetime.strptime("01/08/2021", "%d/%m/%Y").date(),
            end=datetime.datetime.strptime("01/08/2022", "%d/%m/%Y").date(),
        )
        second_period = fw.Period(
            1,
            fw.Period.TimeUnit.MONTH,
            start=datetime.datetime.strptime("01/02/2022", "%d/%m/%Y").date(),
            end=datetime.datetime.strptime("01/08/2023", "%d/%m/%Y").date(),
        )
        self.assertRaises(
            exc.IllegalArgumentException,
            lambda: fw.Subscription(
                self.person, [first_period, second_period], None
            ),
        )
        self.assertRaises(
            exc.IllegalArgumentException,
            lambda: fw.Subscription(
                self.person, [second_period, first_period], None
            ),
        )

    def test_invalid_last_notification(self):
        # For not a date
        self.assertRaises(
            exc.IllegalArgumentException,
            lambda: fw.Subscription(self.person, [self.period], "03/05/2021"),
        )

        # For a date in the future
        future = datetime.date.today() + relativedelta(months=+1)
        self.assertRaises(
            exc.IllegalArgumentException,
            lambda: fw.Subscription(self.person, [self.period], future),
        )


class TestSubscriptionMethods(unittest.TestCase):
    # Relative to today
    base_period_periodicity = 2  # months
    base_period_start = -2  # months
    base_period_end = +5  # months

    @classmethod
    def setUpClass(cls) -> None:
        cls.person = student
        cls.period = fw.Period(
            cls.base_period_periodicity,
            fw.Period.TimeUnit.MONTH,
            start=(
                datetime.date.today()
                + relativedelta(months=cls.base_period_start)
            ),
            end=(
                datetime.date.today()
                + relativedelta(months=cls.base_period_end)
            ),
        )
        cls.date = datetime.date.today()

    def setUp(self) -> None:
        self.subscription = fw.Subscription(
            self.person, [self.period], self.date
        )

    def test_invalid_set_earlier_last_notification(self):
        def invalid_assign(sub):
            sub.last_notification = datetime.date.today() + relativedelta(
                days=-1
            )

        self.assertRaises(
            exc.IllegalStateException,
            lambda: invalid_assign(self.subscription),
        )
        self.assertIs(self.date, self.subscription.last_notification)

    def test_should_notify_inactive_period(self):
        future_period = fw.Period(
            1,
            fw.Period.TimeUnit.MONTH,
            start=datetime.date.today() + relativedelta(months=+1),
        )
        sub = fw.Subscription(self.person, [future_period], None)

        self.assertFalse(
            sub.should_notify(),
            msg=(
                "A subscription with a period in the future should not "
                "be notified"
            ),
        )
        self.assertIsNotNone(sub.should_notify())

    def test_should_notify_active_period(self):
        # Test notify
        sub = fw.Subscription(
            self.person,
            [self.period],
            last_notification=(
                datetime.date.today()
                + relativedelta(months=-self.base_period_periodicity)
            ),
        )

        self.assertTrue(
            sub.should_notify(), msg="The subscriber should be notified"
        )

        # Test don't notify
        months = int(self.base_period_periodicity / 2)
        sub = fw.Subscription(
            self.person,
            [self.period],
            last_notification=(
                datetime.date.today() + relativedelta(months=-months)
            ),
        )

        self.assertFalse(sub.should_notify())

    @mock.patch.object(model.followup_work.Period, "is_legal_end")
    @mock.patch.object(model.followup_work.Period, "is_legal_start")
    @mock.patch("humasol.model.followup_work.date")
    def test_should_notify_none_last_notification(
        self, mock_date, mock_start, mock_end
    ):
        mock_start.return_value = True
        mock_end.return_value = True

        # TimeUnit.WEEK
        period = fw.Period(
            1, fw.Period.TimeUnit.WEEK, start=datetime.date.today()
        )
        sub = fw.Subscription(self.person, [period])

        not_monday = datetime.date.today()
        if not_monday.isoweekday() == 1:
            not_monday += relativedelta(days=+1)

        monday = datetime.date.today()
        if monday.isoweekday() != 1:
            monday += relativedelta(days=+(8 - monday.isoweekday()))

        # Shouldn't send if not monday
        mock_date.today.return_value = not_monday
        self.assertFalse(sub.should_notify())

        # Should send if monday
        mock_date.today.return_value = monday
        self.assertTrue(sub.should_notify())

        # TimeUnit.MONTH
        period = fw.Period(
            3,
            fw.Period.TimeUnit.MONTH,
            start=datetime.date.today() + relativedelta(months=-1),
        )
        sub = fw.Subscription(self.person, [period])

        not_first_day = datetime.date.today()
        if not_first_day.day == 1:
            not_first_day += relativedelta(days=+1)

        today = datetime.date.today()
        first_day = datetime.datetime.strptime(
            f"01/{today.month}/{today.year}", "%d/%m/%Y"
        )

        # Shouldn't send if not the first day of the month
        mock_date.today.return_value = not_first_day
        self.assertFalse(sub.should_notify())

        # Should send if the first day
        mock_date.today.return_value = first_day
        self.assertTrue(sub.should_notify())

    @mock.patch.object(model.followup_work.Period, "is_legal_end")
    @mock.patch.object(model.followup_work.Period, "is_legal_start")
    @mock.patch("humasol.model.followup_work.date")
    def test_clean_periods(self, mock_date, mock_start, mock_end):
        mock_start.return_value = True
        mock_end.return_value = True

        mock_date.today.return_value = datetime.datetime.strptime(
            "01/01/2021", "%d/%m/%Y"
        ).date()
        past_period = fw.Period(
            1,
            fw.Period.TimeUnit.WEEK,
            start=datetime.datetime.strptime("01/02/2021", "%d/%m/%Y").date(),
            end=datetime.datetime.strptime("01/04/2021", "%d/%m/%Y").date(),
        )
        sub = fw.Subscription(
            self.person, [past_period, self.period], last_notification=None
        )

        self.assertIn(past_period, sub.periods)
        self.assertIn(self.period, sub.periods)

        mock_date.today.return_value = datetime.datetime.strptime(
            "01/05/2021", "%d/%m/%Y"
        ).date()
        sub.clean_periods()

        self.assertNotIn(
            past_period,
            sub.periods,
            msg="A period that has passed should no longer be in the periods "
            "list of a subscription",
        )
        self.assertIn(
            self.period,
            sub.periods,
            msg="Valid periods should not be removed by clean_periods",
        )


class TestTaskInit(unittest.TestCase):

    # Relative to today
    base_period_periodicity = 2  # months
    base_period_start = -2  # months
    base_period_end = +5  # months

    @classmethod
    def setUpClass(cls) -> None:
        cls.person = student
        cls.period = fw.Period(
            2,
            fw.Period.TimeUnit.MONTH,
            start=datetime.date.today() + relativedelta(months=-2),
            end=datetime.date.today() + relativedelta(months=+5),
        )
        cls.another_period = fw.Period(
            5,
            fw.Period.TimeUnit.MONTH,
            start=datetime.date.today() + relativedelta(months=+10),
            end=datetime.date.today() + relativedelta(months=+20),
        )
        cls.date = datetime.date.today()
        cls.name = "Test check"
        cls.function = "Check tests"

    def test_valid_arguments(self):
        person = pers.Supervisor(
            "Testron", "testron@humasol.be", "Tester", "+32333444555"
        )
        period = fw.Period(
            3, fw.Period.TimeUnit.WEEK, start=datetime.date.today()
        )
        name = "Test code"
        function = "Rerun unit tests"
        date = datetime.date.today()
        task = fw.Task(person, [period], name, function, date)

        self.assertIs(task.subscriber, person)
        self.assertIn(period, task.periods)
        self.assertEqual(1, len(task.periods))
        self.assertEqual(name, task.name)
        self.assertEqual(function, task.function)
        self.assertEqual(date, task.last_notification)

    def test_valid_none_last_notification(self):
        task = fw.Task(
            self.person, [self.period], self.name, self.function, None
        )

        self.assertIsNone(task.last_notification)

    def test_valid_unordered_periods(self):
        first_period = self.period
        second_period = self.another_period

        sub = fw.Subscription(self.person, [first_period, second_period], None)

        self.assertIn(first_period, sub.periods)
        self.assertIn(second_period, sub.periods)
        self.assertEqual(2, len(sub.periods))

        sub = fw.Subscription(self.person, [second_period, first_period], None)

        self.assertIn(first_period, sub.periods)
        self.assertIn(second_period, sub.periods)
        self.assertEqual(2, len(sub.periods))

    def test_invalid_subscriber(self):
        # For is none
        self.assertRaises(
            exc.IllegalArgumentException,
            lambda: fw.Task(None, [self.period], self.name, self.function),
        )

        # For not a person
        self.assertRaises(
            exc.IllegalArgumentException,
            lambda: fw.Task(
                "Lincoln", [self.period], self.name, self.function
            ),
        )

    def test_invalid_periods(self):
        # Not a list
        self.assertRaises(
            exc.IllegalArgumentException,
            lambda: fw.Task(
                self.person, self.period, self.name, self.function, self.date
            ),
        )

        # Empty list
        self.assertRaises(
            exc.IllegalArgumentException,
            lambda: fw.Task(
                self.person, [], self.name, self.function, self.date
            ),
        )

        # List with not only periods
        self.assertRaises(
            exc.IllegalArgumentException,
            lambda: fw.Task(
                self.person,
                [self.period, "Mondays"],
                self.name,
                self.function,
                self.date,
            ),
        )

        # Past period
        passed_period = fw.Period(
            2,
            fw.Period.TimeUnit.YEAR,
            start=datetime.date.today() + relativedelta(months=-10),
            end=datetime.date.today() + relativedelta(months=-2),
        )
        self.assertRaises(
            exc.IllegalArgumentException,
            lambda: fw.Task(
                self.person,
                [passed_period],
                self.name,
                self.function,
                self.date,
            ),
        )

        # Overlapping period
        end_first_period = +5
        first_period = fw.Period(
            3,
            fw.Period.TimeUnit.WEEK,
            start=datetime.date.today(),
            end=datetime.date.today() + relativedelta(months=end_first_period),
        )
        second_period = fw.Period(
            2,
            fw.Period.TimeUnit.MONTH,
            start=(
                datetime.date.today()
                + relativedelta(months=end_first_period - 1)
            ),
        )
        self.assertRaises(
            exc.IllegalArgumentException,
            lambda: fw.Task(
                self.person,
                [first_period, second_period],
                self.name,
                self.function,
                self.date,
            ),
        )
        self.assertRaises(
            exc.IllegalArgumentException,
            lambda: fw.Subscription(
                self.person, [second_period, first_period], None
            ),
        )

    def test_invalid_name(self):
        # For None
        self.assertRaises(
            exc.IllegalArgumentException,
            lambda: fw.Task(
                self.person, [self.period], None, self.function, self.date
            ),
        )

        # For not a String
        self.assertRaises(
            exc.IllegalArgumentException,
            lambda: fw.Task(
                self.person, [self.period], self.person, self.function
            ),
        )

        # For no letters
        self.assertRaises(
            exc.IllegalArgumentException,
            lambda: fw.Task(
                self.person,
                [self.period],
                "12.#@,;?",
                self.function,
                self.date,
            ),
        )

    def test_invalid_function(self):
        # For None
        self.assertRaises(
            exc.IllegalArgumentException,
            lambda: fw.Task(
                self.person, [self.period], self.name, None, self.date
            ),
        )

        # For not a string
        self.assertRaises(
            exc.IllegalArgumentException,
            lambda: fw.Task(
                self.person, [self.period], self.name, self.period, self.date
            ),
        )

        # For no letters
        self.assertRaises(
            exc.IllegalArgumentException,
            lambda: fw.Task(
                self.person, [self.period], self.name, "12#@;?", self.date
            ),
        )

    def test_invalid_last_notification(self):
        # Not a date
        self.assertRaises(
            exc.IllegalArgumentException,
            lambda: fw.Task(
                self.person, [self.period], self.name, self.function, 12342341
            ),
        )

        # Future
        future = datetime.date.today() + relativedelta(months=+10)
        self.assertRaises(
            exc.IllegalArgumentException,
            lambda: fw.Task(
                self.person, [self.period], self.name, self.function, future
            ),
        )


class TestTaskMethods(unittest.TestCase):

    # Relative to today
    base_period_periodicity = 2  # months
    base_period_start = -2  # months
    base_period_end = +5  # months

    @classmethod
    def setUpClass(cls) -> None:
        cls.person = student
        cls.period = fw.Period(
            cls.base_period_periodicity,
            fw.Period.TimeUnit.MONTH,
            start=(
                datetime.date.today()
                + relativedelta(months=cls.base_period_start)
            ),
            end=(
                datetime.date.today()
                + relativedelta(months=cls.base_period_end)
            ),
        )
        cls.date = datetime.date.today()
        cls.name = "Testing"
        cls.function = "More testing"

    def setUp(self) -> None:
        self.task = fw.Task(
            self.person, [self.period], self.name, self.function, self.date
        )

    def test_invalid_set_earlier_last_notification(self):
        def invalid_assign(t):
            t.last_notification = datetime.date.today() + relativedelta(
                days=-1
            )

        self.assertRaises(
            exc.IllegalStateException, lambda: invalid_assign(self.task)
        )
        self.assertIs(self.date, self.task.last_notification)

    def test_should_notify_inactive_period(self):
        period = fw.Period(
            1,
            fw.Period.TimeUnit.MONTH,
            start=datetime.date.today() + relativedelta(months=+1),
        )
        task = fw.Task(self.person, [period], self.name, self.function)

        self.assertFalse(task.should_notify())
        self.assertIsNotNone(task.should_notify())

    def test_should_notify_active_period(self):
        period = fw.Period(
            3,
            fw.Period.TimeUnit.WEEK,
            start=datetime.date.today() + relativedelta(months=-2),
        )

        # Active but not on interval (shouldn't send)
        task = fw.Task(
            self.person,
            [period],
            self.name,
            self.function,
            last_notification=datetime.date.today() + relativedelta(weeks=-2),
        )
        self.assertFalse(task.should_notify())

        # Active and on interval (should send)
        task = fw.Task(
            self.person,
            [period],
            self.name,
            self.function,
            last_notification=datetime.date.today() + relativedelta(weeks=-3),
        )
        self.assertTrue(task.should_notify())

    @mock.patch.object(model.followup_work.Period, "is_legal_end")
    @mock.patch.object(model.followup_work.Period, "is_legal_start")
    @mock.patch("humasol.model.followup_work.date")
    def test_should_notify_none_last_notification(
        self, mock_date, mock_start, mock_end
    ):
        mock_start.return_value = True
        mock_end.return_value = True

        # TimeUnit.WEEK
        period = fw.Period(
            1, fw.Period.TimeUnit.WEEK, start=datetime.date.today()
        )
        task = fw.Task(self.person, [period], self.name, self.function)

        not_monday = datetime.date.today()
        if not_monday.isoweekday() == 1:
            not_monday += relativedelta(days=+1)

        monday = datetime.date.today()
        if monday.isoweekday() != 1:
            monday += relativedelta(days=+(8 - monday.isoweekday()))

        # Shouldn't send if not monday
        mock_date.today.return_value = not_monday
        self.assertFalse(task.should_notify())

        # Should send if monday
        mock_date.today.return_value = monday
        self.assertTrue(task.should_notify())

        # TimeUnit.MONTH
        period = fw.Period(
            3,
            fw.Period.TimeUnit.MONTH,
            start=datetime.date.today() + relativedelta(months=-1),
        )
        task = fw.Task(self.person, [period], self.name, self.function)

        not_first_day = datetime.date.today()
        if not_first_day.day == 1:
            not_first_day += relativedelta(days=+1)

        today = datetime.date.today()
        first_day = datetime.datetime.strptime(
            f"01/{today.month}/{today.year}", "%d/%m/%Y"
        )

        # Shouldn't send if not the first day of the month
        mock_date.today.return_value = not_first_day
        self.assertFalse(task.should_notify())

        # Should send if the first day
        mock_date.today.return_value = first_day
        self.assertTrue(task.should_notify())

    @mock.patch.object(model.followup_work.Period, "is_legal_end")
    @mock.patch.object(model.followup_work.Period, "is_legal_start")
    @mock.patch("humasol.model.followup_work.date")
    def test_clean_periods(self, mock_date, mock_start, mock_end):
        mock_start.return_value = True
        mock_end.return_value = True

        mock_date.today.return_value = datetime.datetime.strptime(
            "01/08/2021", "%d/%m/%Y"
        ).date()
        first_period = fw.Period(
            1,
            fw.Period.TimeUnit.WEEK,
            start=datetime.datetime.strptime("01/08/2021", "%d/%m/%Y").date(),
            end=datetime.datetime.strptime("01/09/2021", "%d/%m/%Y").date(),
        )
        second_period = fw.Period(
            1,
            fw.Period.TimeUnit.MONTH,
            start=datetime.datetime.strptime("02/09/2021", "%d/%m/%Y").date(),
        )
        task = fw.Task(
            self.person,
            [first_period, second_period],
            self.name,
            self.function,
        )

        self.assertIn(first_period, task.periods)
        self.assertEqual(2, len(task.periods))

        mock_date.today.return_value = datetime.datetime.strptime(
            "10/09/2021", "%d/%m/%Y"
        ).date()
        task.clean_periods()

        self.assertNotIn(first_period, task.periods)
        self.assertEqual(1, len(task.periods))


class TestPeriodInit(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.periodicity = 5
        cls.unit = fw.Period.TimeUnit.MONTH
        cls.start = datetime.date.today()
        cls.end = datetime.date.today() + relativedelta(months=+10)

    def test_valid_arguments(self):
        period = fw.Period(
            self.periodicity, self.unit, start=self.start, end=self.end
        )

        self.assertEqual(self.periodicity, period.interval)
        self.assertIs(self.unit, period.unit)
        self.assertIs(self.start, period.start)
        self.assertIs(self.end, period.end)

    def test_valid_none_end(self):
        period = fw.Period(
            self.periodicity, self.unit, start=self.start, end=None
        )

        self.assertIsNone(period.end)

        period = fw.Period(self.periodicity, self.unit, start=self.start)

        self.assertIsNone(period.end)

    def test_invalid_period(self):
        # None
        self.assertRaises(
            exc.IllegalArgumentException,
            lambda: fw.Period(None, self.unit, start=self.start, end=self.end),
        )

        # Not integer
        self.assertRaises(
            exc.IllegalArgumentException,
            lambda: fw.Period(1.5, self.unit, start=self.start, end=self.end),
        )

        # Non-positive
        self.assertRaises(
            exc.IllegalArgumentException,
            lambda: fw.Period(-2, self.unit, start=self.start, end=self.end),
        )
        self.assertRaises(
            exc.IllegalArgumentException,
            lambda: fw.Period(0, self.unit, start=self.start, end=self.end),
        )

    def test_invalid_unit(self):
        # None
        self.assertRaises(
            exc.IllegalArgumentException,
            lambda: fw.Period(self.periodicity, None, start=self.start),
        )

        # Not TimeUnit
        self.assertRaises(
            exc.IllegalArgumentException,
            lambda: fw.Period(self.periodicity, "Month", start=self.start),
        )

    def test_invalid_start(self):
        # None
        self.assertRaises(
            exc.IllegalArgumentException,
            lambda: fw.Period(self.periodicity, self.unit, start=None),
        )

        # Not a date
        self.assertRaises(
            exc.IllegalArgumentException,
            lambda: fw.Period(self.periodicity, self.unit, start="01/08/2021"),
        )

    def test_invalid_end(self):
        # Not a date
        self.assertRaises(
            exc.IllegalArgumentException,
            lambda: fw.Period(
                self.periodicity, self.unit, start=self.start, end="01/08/2021"
            ),
        )

    def test_invalid_start_end_combo(self):
        # End before start
        start = datetime.datetime.strptime("01/09/2021", "%d/%m/%Y").date()
        end = datetime.datetime.strptime("31/08/2021", "%d/%m/%Y").date()

        self.assertRaises(
            exc.IllegalArgumentException,
            lambda: fw.Period(
                self.periodicity, self.unit, start=start, end=end
            ),
        )


class TestPeriodMethods(unittest.TestCase):

    period_end = +10

    @classmethod
    def setUpClass(cls) -> None:
        cls.periodicity = 5
        cls.unit = fw.Period.TimeUnit.MONTH
        cls.start_date = datetime.date.today()
        cls.end_date = datetime.date.today() + relativedelta(
            months=cls.period_end
        )

    def setUp(self) -> None:
        self.period_end = fw.Period(
            self.periodicity,
            self.unit,
            start=self.start_date,
            end=self.end_date,
        )
        self.period_no_end = fw.Period(
            self.periodicity, self.unit, start=self.start_date
        )

    def test_is_applicable_true(self):
        self.assertTrue(self.period_end.is_applicable(self.start_date))
        self.assertTrue(
            self.period_end.is_applicable(
                self.start_date + relativedelta(days=+10)
            )
        )
        self.assertTrue(self.period_end.is_applicable(self.end_date))

        self.assertTrue(
            self.period_no_end.is_applicable(
                self.end_date + relativedelta(months=+2)
            )
        )

    def test_is_applicable_false(self):
        self.assertFalse(
            self.period_end.is_applicable(
                self.start_date + relativedelta(days=-1)
            )
        )
        self.assertFalse(
            self.period_end.is_applicable(
                self.end_date + relativedelta(days=+1)
            )
        )
        self.assertIsNotNone(
            self.period_end.is_applicable(
                self.end_date + relativedelta(days=+1)
            )
        )

    @mock.patch.object(model.followup_work.Period, "is_legal_end")
    @mock.patch.object(model.followup_work.Period, "is_legal_start")
    @mock.patch("humasol.model.followup_work.date")
    def test_should_update_true(
        self, mock_date, mock_start_date, mock_end_date
    ):
        check_date = datetime.datetime.strptime(
            "01/08/2021", "%d/%m/%Y"
        ).date()
        mock_date.today.return_value = check_date
        mock_start_date.return_value = True
        mock_end_date.return_value = True

        period = fw.Period(
            self.periodicity,
            fw.Period.TimeUnit.WEEK,
            start=datetime.datetime.strptime("01/01/2021", "%d/%m/%Y").date(),
        )

        self.assertTrue(
            period.should_update(
                check_date + relativedelta(weeks=-self.periodicity)
            )
        )

    @mock.patch.object(model.followup_work.Period, "is_legal_end")
    @mock.patch.object(model.followup_work.Period, "is_legal_start")
    @mock.patch("humasol.model.followup_work.date")
    def test_should_update_false(
        self, mock_date, mock_start_date, mock_end_date
    ):
        check_date = datetime.datetime.strptime(
            "01/08/2021", "%d/%m/%Y"
        ).date()
        mock_date.today.return_value = check_date
        mock_start_date.return_value = True
        mock_end_date.return_value = True

        period = fw.Period(
            self.periodicity,
            fw.Period.TimeUnit.WEEK,
            start=datetime.datetime.strptime("01/01/2021", "%d/%m/%Y").date(),
        )

        self.assertFalse(
            period.should_update(
                check_date + relativedelta(weeks=-(self.periodicity - 1))
            )
        )
        self.assertIsNotNone(
            period.should_update(
                check_date + relativedelta(weeks=-(self.periodicity - 1))
            )
        )

    @mock.patch.object(model.followup_work.Period, "is_legal_end")
    @mock.patch.object(model.followup_work.Period, "is_legal_start")
    @mock.patch("humasol.model.followup_work.date")
    def test_should_update_last_notification_from_past_period(
        self, mock_date, mock_start_date, mock_end_date
    ):
        start_date = datetime.date.today()
        last_notify_date = start_date + relativedelta(weeks=-self.periodicity)
        mock_start_date.return_value = True
        mock_end_date.return_value = True

        period = fw.Period(
            self.periodicity, fw.Period.TimeUnit.WEEK, start=start_date
        )

        # For weeks, send on monday
        not_monday = (
            start_date
            if start_date.isoweekday() != 1
            else start_date + relativedelta(days=+1)
        )
        monday = (
            start_date
            if start_date.isoweekday() == 1
            else start_date
            + relativedelta(days=+(8 - start_date.isoweekday()))
        )

        mock_date.today.return_value = not_monday
        self.assertFalse(period.should_update(last_notify_date))

        mock_date.today.return_value = monday
        self.assertTrue(period.should_update(last_notify_date))

        # For months, send on 1st of the month
        not_first = (
            start_date
            if start_date.day != 1
            else start_date + relativedelta(days=+1)
        )
        first = (
            start_date
            if start_date.day == 1
            else datetime.datetime.strptime(
                f"01/{start_date.month + 1}/{start_date.year}"
                if start_date.month < 12
                else f"01/01/{start_date.year + 1}",
                "%d/%m/%Y",
            ).date()
        )
        period.unit = fw.Period.TimeUnit.MONTH

        mock_date.today.return_value = not_first
        self.assertFalse(period.should_update(last_notify_date))

        mock_date.today.return_value = first
        self.assertTrue(period.should_update(last_notify_date))

    @mock.patch.object(model.followup_work.Period, "is_legal_end")
    @mock.patch.object(model.followup_work.Period, "is_legal_start")
    @mock.patch("humasol.model.followup_work.date")
    def test_should_update_none_last_notification(
        self, mock_date, mock_start_date, mock_end_date
    ):
        start_date = datetime.date.today()
        mock_start_date.return_value = True
        mock_end_date.return_value = True

        period = fw.Period(1, fw.Period.TimeUnit.WEEK, start=start_date)

        # For weeks, send on monday
        not_monday = (
            start_date
            if start_date.isoweekday() != 1
            else start_date + relativedelta(days=+1)
        )
        monday = (
            start_date
            if start_date.isoweekday() == 1
            else start_date
            + relativedelta(days=+(8 - start_date.isoweekday()))
        )

        mock_date.today.return_value = not_monday
        self.assertFalse(period.should_update(None))

        mock_date.today.return_value = monday
        self.assertTrue(period.should_update(None))

        # For months, send on 1st of the month
        not_first = (
            start_date
            if start_date.day != 1
            else start_date + relativedelta(days=+1)
        )
        first = (
            start_date
            if start_date.day == 1
            else datetime.datetime.strptime(
                f"01/{start_date.month + 1}/{start_date.year}"
                if start_date.month < 12
                else f"01/01/{start_date.year + 1}",
                "%d/%m/%Y",
            ).date()
        )
        period.unit = fw.Period.TimeUnit.MONTH

        mock_date.today.return_value = not_first
        self.assertFalse(period.should_update(None))

        mock_date.today.return_value = first
        self.assertTrue(period.should_update(None))

    def test_has_passed_true(self):
        self.assertTrue(
            self.period_end.has_past(self.end_date + relativedelta(days=+1))
        )

    def test_has_passed_false(self):
        self.assertFalse(self.period_end.has_past(self.end_date))
        self.assertFalse(
            self.period_no_end.has_past(
                self.end_date + relativedelta(months=+2)
            )
        )
        self.assertFalse(
            self.period_no_end.has_past(
                self.start_date + relativedelta(days=-1)
            )
        )
        self.assertIsNotNone(self.period_end.has_past(self.end_date))


class TestSuiteFollowupWork(unittest.TestSuite):
    def __init__(self):
        super().__init__(
            [
                unittest.TestLoader().loadTestsFromTestCase(TestFollowupJob),
                unittest.TestLoader().loadTestsFromTestCase(
                    TestSubscriptionInit
                ),
                unittest.TestLoader().loadTestsFromTestCase(
                    TestSubscriptionMethods
                ),
                unittest.TestLoader().loadTestsFromTestCase(TestTaskInit),
                unittest.TestLoader().loadTestsFromTestCase(TestTaskMethods),
                unittest.TestLoader().loadTestsFromTestCase(TestPeriodInit),
                unittest.TestLoader().loadTestsFromTestCase(TestPeriodMethods),
            ]
        )


if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    runner.run(TestSuiteFollowupWork())
