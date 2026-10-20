"""Deterministic daily reading targets, generated one ISO week at a time.

The plan is pseudo-random but stable for an ISO calendar week.  Stability is
important for retries: rerunning a workflow on the same day must not silently
change that day's target.
"""

from datetime import date
import hashlib
import random


AUTOMATIC_RESUME_DATE = date(2026, 10, 19)
MIN_DAILY_MINUTES = 120
MAX_DAILY_MINUTES = 180
MIN_WEEKLY_MINUTES = 7 * MIN_DAILY_MINUTES
MAX_WEEKLY_MINUTES = 7 * MAX_DAILY_MINUTES
PLAN_STEP_MINUTES = 5


def weekly_plan(plan_date):
    """Return ``(weekly_total, monday_to_sunday_minutes)`` for *plan_date*."""
    iso_year, iso_week, _ = plan_date.isocalendar()
    seed_text = f"wxread-daily-v2:{iso_year}-W{iso_week:02d}"
    seed = int.from_bytes(hashlib.sha256(seed_text.encode()).digest()[:8], "big")
    rng = random.Random(seed)

    plan = tuple(
        rng.randrange(
            MIN_DAILY_MINUTES,
            MAX_DAILY_MINUTES + PLAN_STEP_MINUTES,
            PLAN_STEP_MINUTES,
        )
        for _ in range(7)
    )
    return sum(plan), plan


def minutes_for_date(plan_date):
    """Return the scheduled minutes for one local calendar date."""
    _, plan = weekly_plan(plan_date)
    return plan[plan_date.weekday()]


def automatic_reading_enabled(plan_date):
    """Return whether automatic reading has reached its requested resume date."""
    return plan_date >= AUTOMATIC_RESUME_DATE
