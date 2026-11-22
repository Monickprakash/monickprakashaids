"""Unit tests for FITPULSE datasets, centralized data processing, and fitness calculations."""

from datetime import date
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from utils.data_processor import (
    calculate_active_days,
    calculate_average_daily_active_minutes,
    calculate_average_daily_calories,
    calculate_average_daily_distance,
    calculate_average_daily_steps,
    calculate_metric_trend,
    calculate_period_summary,
    calculate_summary_metrics,
    calculate_total_active_minutes,
    calculate_total_calories,
    calculate_total_distance,
    calculate_total_steps,
    clean_fitness_data,
    filter_by_date_range,
    get_daily_activity,
    get_dataset_date_bounds,
    inspect_dataset_columns,
    load_dataset,
)

# Resolve the project root directory dynamically
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_DATA_PATH = PROJECT_ROOT / "data" / "sample_fitness_data.csv"

EXPECTED_COLUMNS = {
    "date",
    "steps",
    "distance_km",
    "active_minutes",
    "calories",
}


# ==============================================================================
# Baseline Phase 3 Dataset Tests (Preserved)
# ==============================================================================


def test_sample_fitness_data_exists():
    """Verify that the sample fitness CSV exists in the data directory."""
    assert SAMPLE_DATA_PATH.exists(), f"Sample data not found at {SAMPLE_DATA_PATH}"


def test_sample_fitness_data_columns():
    """Verify that the sample dataset contains all required fitness tracking columns."""
    df = pd.read_csv(SAMPLE_DATA_PATH)
    missing_columns = EXPECTED_COLUMNS - set(df.columns)
    assert not missing_columns, f"Sample data is missing expected columns: {missing_columns}"


def test_sample_fitness_data_not_empty():
    """Verify that the sample dataset contains at least 7 records."""
    df = pd.read_csv(SAMPLE_DATA_PATH)
    assert len(df) >= 7, f"Expected at least 7 rows in sample data, found {len(df)}"


def test_sample_fitness_data_types():
    """Verify basic data types and ranges of the sample dataset."""
    df = pd.read_csv(SAMPLE_DATA_PATH)
    assert pd.api.types.is_numeric_dtype(df["steps"]), "Steps column must be numeric"
    assert (df["steps"] >= 0).all(), "Steps must not be negative"
    assert (df["distance_km"] >= 0).all(), "Distance must not be negative"
    assert (df["calories"] >= 0).all(), "Calories must not be negative"
    assert (df["active_minutes"] >= 0).all(), "Active minutes must not be negative"


# ==============================================================================
# Phase 4 Centralized Data Processing & Cleaning Tests
# ==============================================================================


def test_clean_fitness_data_handles_duplicates_and_negatives():
    """Verify that clean_fitness_data removes duplicate dates and clamps negative values."""
    raw_data = {
        "Date": ["2024-04-01", "2024-04-01", "2024-04-02", "invalid_date"],
        "Steps": [-500, 8000, 10000, 5000],
        "Distance_km": [-2.5, 5.0, 7.5, 3.0],
        "Active_Minutes": [30, -10, 60, 45],
        "Calories": [1800, 2200, -300, 2000],
    }
    df_raw = pd.DataFrame(raw_data)
    cleaned = clean_fitness_data(df_raw)

    # Invalid date row dropped, duplicate 2024-04-01 resolved to 1 entry
    assert len(cleaned) == 2
    assert list(cleaned["date"]) == ["2024-04-01", "2024-04-02"]

    # All numeric values must be non-negative
    assert (cleaned["steps"] >= 0).all()
    assert (cleaned["distance_km"] >= 0.0).all()
    assert (cleaned["active_minutes"] >= 0).all()
    assert (cleaned["calories"] >= 0).all()


def test_clean_fitness_data_empty_inputs():
    """Verify that clean_fitness_data handles None and empty DataFrames gracefully."""
    empty_df = clean_fitness_data(None)
    assert isinstance(empty_df, pd.DataFrame)
    assert empty_df.empty
    assert set(empty_df.columns) == EXPECTED_COLUMNS

    empty_df2 = clean_fitness_data(pd.DataFrame())
    assert isinstance(empty_df2, pd.DataFrame)
    assert empty_df2.empty


def test_inspect_dataset_columns():
    """Verify column inspection accurately detects present and missing columns."""
    df_valid = pd.DataFrame(columns=list(EXPECTED_COLUMNS))
    report = inspect_dataset_columns(df_valid)
    assert report["is_valid"] is True
    assert len(report["missing_columns"]) == 0

    df_incomplete = pd.DataFrame(columns=["date", "steps"])
    report_inc = inspect_dataset_columns(df_incomplete)
    assert report_inc["is_valid"] is False
    assert "distance_km" in report_inc["missing_columns"]


# ==============================================================================
# Phase 4 Fitness Calculation Engine Tests
# ==============================================================================


def test_sample_fitness_calculations_accuracy():
    """Verify exact mathematical calculations for total and average metrics on sample data."""
    df = load_dataset(SAMPLE_DATA_PATH)
    assert len(df) == 7

    # Totals: 8420+10250+6300+11840+9120+14300+7650 = 67,880
    assert calculate_total_steps(df) == 67880

    # Distance: 6.2+7.8+4.7+8.9+6.8+10.7+5.6 = 50.7
    assert calculate_total_distance(df) == 50.7

    # Active Minutes: 48+62+35+74+55+92+42 = 408
    assert calculate_total_active_minutes(df) == 408

    # Calories: 2150+2380+1920+2560+2210+2840+2040 = 16,100
    assert calculate_total_calories(df) == 16100

    # Averages:
    # Steps: 67880 / 7 = 9697.14 -> 9697
    assert calculate_average_daily_steps(df) == 9697

    # Distance: 50.7 / 7 = 7.2428 -> 7.24
    assert calculate_average_daily_distance(df) == 7.24

    # Active Minutes: 408 / 7 = 58.28 -> 58
    assert calculate_average_daily_active_minutes(df) == 58

    # Calories: 16100 / 7 = 2300.0 -> 2300
    assert calculate_average_daily_calories(df) == 2300


def test_calculations_with_empty_dataframe():
    """Verify that calculation functions return safe defaults for empty DataFrames."""
    empty_df = pd.DataFrame()

    assert calculate_total_steps(empty_df) == 0
    assert calculate_total_distance(empty_df) == 0.0
    assert calculate_total_active_minutes(empty_df) == 0
    assert calculate_total_calories(empty_df) == 0
    assert calculate_average_daily_steps(empty_df) == 0
    assert calculate_average_daily_distance(empty_df) == 0.0
    assert calculate_average_daily_active_minutes(empty_df) == 0
    assert calculate_average_daily_calories(empty_df) == 0


def test_calculate_active_days_uses_steps_or_active_minutes():
    df = pd.DataFrame(
        {
            "steps": [100, 0, 0, 0],
            "active_minutes": [0, 20, 0, 0],
        }
    )

    assert calculate_active_days(df) == 2
    assert calculate_active_days(pd.DataFrame()) == 0


def test_get_daily_activity_returns_actual_record_or_none():
    df = pd.DataFrame(
        {
            "date": ["2024-04-01", "2024-04-03"],
            "calories": [2150, 1920],
            "steps": [8420, 6300],
            "distance_km": [6.2, 4.7],
            "active_minutes": [48, 35],
        }
    )

    assert get_daily_activity(df, date(2024, 4, 1)) == {
        "calories": 2150,
        "steps": 8420,
        "distance_km": 6.2,
        "active_minutes": 48,
    }
    assert get_daily_activity(df, date(2024, 4, 2)) is None


def test_date_range_filtering():
    """Verify that date range filtering accurately isolates target date records."""
    df = load_dataset(SAMPLE_DATA_PATH)

    # Filter to first 3 days: 2024-04-01 through 2024-04-03
    filtered = filter_by_date_range(df, start_date="2024-04-01", end_date="2024-04-03")
    assert len(filtered) == 3
    assert list(filtered["date"]) == ["2024-04-01", "2024-04-02", "2024-04-03"]

    # Re-calculate metrics on filtered subset:
    # 8420 + 10250 + 6300 = 24,970 steps
    assert calculate_total_steps(filtered) == 24970
    assert calculate_average_daily_steps(filtered) == int(round(24970 / 3))

    # Out-of-bounds filter returns empty DataFrame without errors
    out_of_bounds = filter_by_date_range(df, start_date="2025-01-01", end_date="2025-01-05")
    assert out_of_bounds.empty


def test_calculate_summary_metrics_structure():
    """Verify that calculate_summary_metrics generates comprehensive summary dictionary."""
    df = load_dataset(SAMPLE_DATA_PATH)
    metrics = calculate_summary_metrics(df)

    assert metrics["record_count"] == 7
    assert metrics["total_steps"] == 67880
    assert metrics["peak_steps"] == 14300
    assert metrics["peak_steps_date"] == "2024-04-06"
    assert "trends" in metrics
    assert "steps" in metrics["trends"]
    assert "badge_text" in metrics["trends"]["steps"]


def test_get_dataset_date_bounds():
    """Verify date bounds extraction from dataset."""
    df = load_dataset(SAMPLE_DATA_PATH)
    min_date, max_date = get_dataset_date_bounds(df)

    assert min_date == date(2024, 4, 1)
    assert max_date == date(2024, 4, 7)


def test_period_summaries_aggregate_only_recorded_dates():
    df = pd.DataFrame(
        {
            "date": ["2024-04-01", "2024-04-03"],
            "steps": [1000, 3000],
            "distance_km": [1.0, 3.0],
            "active_minutes": [10, 30],
            "calories": [100, 300],
        }
    )

    daily = calculate_period_summary(df, "daily")
    weekly = calculate_period_summary(df, "weekly")
    monthly = calculate_period_summary(df, "monthly")

    assert len(daily) == 2
    assert daily["recorded_days"].tolist() == [1, 1]
    assert len(weekly) == 1
    assert weekly.iloc[0]["recorded_days"] == 2
    assert weekly.iloc[0]["active_days"] == 2
    assert weekly.iloc[0]["steps"] == 4000
    assert weekly.iloc[0]["calories"] == 400
    assert monthly.iloc[0]["distance_km"] == 4.0
    assert monthly.iloc[0]["active_minutes"] == 40


def test_period_summary_rejects_unknown_period():
    with pytest.raises(ValueError, match="period must be"):
        calculate_period_summary(pd.DataFrame(), "quarterly")
