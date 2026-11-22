"""Tests for persisted FITPULSE goals and user records."""

from datetime import date

import pandas as pd
import pytest

from utils.storage import (
    load_activity_records,
    load_goal_settings,
    merge_activity_records,
    save_activity_records,
    save_goal_settings,
    validate_activity_records,
)


def record(day: date, steps: int, calories: int = 2000) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "date": day,
                "steps": steps,
                "distance_km": 5.0,
                "active_minutes": 40,
                "calories": calories,
            }
        ]
    )


def test_activity_records_persist_and_upsert_by_date(tmp_path):
    path = tmp_path / "activity.csv"
    save_activity_records(record(date(2024, 4, 1), 8000), path)
    saved = save_activity_records(record(date(2024, 4, 1), 9500, 2200), path)

    assert len(saved) == 1
    assert len(load_activity_records(path)) == 1
    assert int(load_activity_records(path).iloc[0]["steps"]) == 9500
    assert int(load_activity_records(path).iloc[0]["calories"]) == 2200


def test_user_records_override_same_sample_date():
    sample = record(date(2024, 4, 1), 8000)
    user = record(date(2024, 4, 1), 10000)

    merged = merge_activity_records(sample, user)

    assert len(merged) == 1
    assert int(merged.iloc[0]["steps"]) == 10000


def test_activity_validation_rejects_negative_or_missing_metrics():
    with pytest.raises(ValueError, match="cannot be negative"):
        validate_activity_records(record(date(2024, 4, 1), -1))

    with pytest.raises(ValueError, match="Missing required"):
        validate_activity_records(pd.DataFrame({"date": ["2024-04-01"]}))


@pytest.mark.parametrize("column", ["steps", "active_minutes", "calories"])
def test_activity_validation_rejects_fractional_count_metrics(column):
    activity = record(date(2024, 4, 1), 8000)
    activity[column] = 12.5

    with pytest.raises(ValueError, match="whole numbers"):
        validate_activity_records(activity)


def test_goal_settings_persist_and_validate(tmp_path):
    path = tmp_path / "goals.json"
    assert load_goal_settings(path) == {
        "daily_step_goal": 10000,
        "daily_calorie_goal": 0,
    }

    save_goal_settings(12000, 2400, path)
    assert load_goal_settings(path) == {
        "daily_step_goal": 12000,
        "daily_calorie_goal": 2400,
    }

    with pytest.raises(ValueError, match="between 1,000 and 50,000"):
        save_goal_settings(500, 2400, path)
