import unittest
from datetime import date, timedelta

import weekly_schedule


class WeeklyScheduleTests(unittest.TestCase):
    def test_plan_is_stable_and_respects_all_limits(self):
        monday = date(2026, 1, 5)
        for week_offset in range(520):
            plan_date = monday + timedelta(weeks=week_offset)
            first = weekly_schedule.weekly_plan(plan_date)
            second = weekly_schedule.weekly_plan(plan_date)
            self.assertEqual(first, second)

            weekly_total, plan = first
            self.assertEqual(len(plan), 7)
            self.assertEqual(sum(plan), weekly_total)
            self.assertGreaterEqual(
                weekly_total, weekly_schedule.MIN_WEEKLY_MINUTES
            )
            self.assertLessEqual(
                weekly_total, weekly_schedule.MAX_WEEKLY_MINUTES
            )
            for minutes in plan:
                self.assertGreaterEqual(
                    minutes, weekly_schedule.MIN_DAILY_MINUTES
                )
                self.assertLessEqual(
                    minutes, weekly_schedule.MAX_DAILY_MINUTES
                )
                self.assertEqual(minutes % weekly_schedule.PLAN_STEP_MINUTES, 0)

    def test_each_day_uses_its_weekday_slot(self):
        monday = date(2026, 10, 19)
        _, plan = weekly_schedule.weekly_plan(monday)
        for day_offset, expected in enumerate(plan):
            self.assertEqual(
                weekly_schedule.minutes_for_date(
                    monday + timedelta(days=day_offset)
                ),
                expected,
            )

    def test_resume_date(self):
        self.assertFalse(
            weekly_schedule.automatic_reading_enabled(date(2026, 10, 18))
        )
        self.assertTrue(
            weekly_schedule.automatic_reading_enabled(date(2026, 10, 19))
        )


if __name__ == "__main__":
    unittest.main()
