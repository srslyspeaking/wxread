"""Deterministic weekly reading-plan generation.

The plan is pseudo-random but stable for an ISO calendar week.  Stability is
important for retries: rerunning a workflow on the same day must not silently
change that day's target.
"""

from datetime import date
import hashlib
import random


AUTOMATIC_RESUME_DATE = date(2026, 10, 19)
MIN_WEEKLY_MINUTES = 600
MAX_WEEKLY_MINUTES = 900
MIN_DAILY_MINUTES = 60
MAX_DAILY_MINUTES = 150
PLAN_STEP_MINUTES = 5


def weekly_plan(plan_date):
    """Return ``(weekly_total, monday_to_sunday_minutes)`` for *plan_date*."""
    iso_year, iso_week, _ = plan_date.isocalendar()
    seed_text = f"wxread-weekly-v1:{iso_year}-W{iso_week:02d}"
    seed = int.from_bytes(hashlib.sha256(seed_text.encode()).digest()[:8], "big")
    rng = random.Random(seed)

    weekly_total = rng.randrange(
        MIN_WEEKLY_MINUTES,
        MAX_WEEKLY_MINUTES + PLAN_STEP_MINUTES,
        PLAN_STEP_MINUTES,
    )
    plan = [MIN_DAILY_MINUTES] * 7
    extra_blocks = (
        weekly_total - 7 * MIN_DAILY_MINUTES
    ) // PLAN_STEP_MINUTES
    blocks_per_day = (
        MAX_DAILY_MINUTES - MIN_DAILY_MINUTES
    ) // PLAN_STEP_MINUTES

    # Choosing from a shuffled pool keeps the allocation reasonably balanced
    # while preserving the exact weekly total and the per-day ceiling.
    available_blocks = [
        weekday
        for weekday in range(7)
        for _ in range(blocks_per_day)
    ]
    rng.shuffle(available_blocks)
    for weekday in available_blocks[:extra_blocks]:
        plan[weekday] += PLAN_STEP_MINUTES

    return weekly_total, tuple(plan)


def minutes_for_date(plan_date):
    """Return the scheduled minutes for one local calendar date."""
    _, plan = weekly_plan(plan_date)
    return plan[plan_date.weekday()]


def automatic_reading_enabled(plan_date):
    """Return whether automatic reading has reached its requested resume date."""
    return plan_date >= AUTOMATIC_RESUME_DATE
