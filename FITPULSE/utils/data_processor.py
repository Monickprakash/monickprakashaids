"""FITPULSE — Centralized Fitness Data Processing Engine.

Phase 4: Smart Fitness Analytics.
This module provides reusable, robust Pandas functions for data ingestion,
cleaning, schema validation, and fitness metrics calculations.
"""

from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union
import numpy as np
import pandas as pd

# Expected schema for FITPULSE datasets
CORE_COLUMNS = {
    "date",
    "steps",
    "distance_km",
    "active_minutes",
    "calories",
}


def inspect_dataset_columns(df: pd.DataFrame) -> Dict[str, Any]:
    """Inspect a DataFrame to identify existing, missing, and extra columns.

    Args:
        df: Input DataFrame to examine.

    Returns:
        Dict containing present_columns, missing_columns, and is_valid flag.
    """
    if df is None or not isinstance(df, pd.DataFrame):
        return {
            "present_columns": [],
            "missing_columns": list(CORE_COLUMNS),
            "is_valid": False,
        }

    present = set(df.columns)
    missing = CORE_COLUMNS - present

    return {
        "present_columns": list(present),
        "missing_columns": list(missing),
        "is_valid": len(missing) == 0,
    }


def clean_fitness_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and validate raw fitness activity records using Pandas.

    Cleaning steps:
    1. Gracefully handle None or empty DataFrames.
    2. Normalize column names (lowercase, stripped whitespace).
    3. Ensure core fitness columns exist with default zeroes if absent.
    4. Parse 'date' to datetime and drop invalid/unparseable dates.
    5. Remove duplicate date entries (keeping the most recently recorded entry).
    6. Convert metrics to numeric types, coercing non-numeric values to zero.
    7. Clamp negative values to zero (steps, distance, calories, active time cannot be negative).
    8. Sort records chronologically by date and reset index.

    Args:
        df: Raw DataFrame loaded from CSV or user input.

    Returns:
        pd.DataFrame: Cleaned, validated, and chronologically sorted DataFrame.
    """
    if df is None or df.empty:
        # Return an empty DataFrame with the expected column types
        empty_df = pd.DataFrame(
            columns=["date", "steps", "distance_km", "active_minutes", "calories"]
        )
        empty_df["steps"] = empty_df["steps"].astype(int)
        empty_df["distance_km"] = empty_df["distance_km"].astype(float)
        empty_df["active_minutes"] = empty_df["active_minutes"].astype(int)
        empty_df["calories"] = empty_df["calories"].astype(int)
        return empty_df

    # Create a working copy
    cleaned = df.copy()

    # 1. Normalize column names
    cleaned.columns = [str(col).strip().lower() for col in cleaned.columns]

    # 2. Check for missing columns and initialize them safely
    if "date" not in cleaned.columns:
        return pd.DataFrame(columns=["date", "steps", "distance_km", "active_minutes", "calories"])

    for col, default_val in [
        ("steps", 0),
        ("distance_km", 0.0),
        ("active_minutes", 0),
        ("calories", 0),
    ]:
        if col not in cleaned.columns:
            cleaned[col] = default_val

    # 3. Clean and parse date column
    cleaned["date_parsed"] = pd.to_datetime(cleaned["date"], errors="coerce")
    # Drop rows where the date is completely invalid or NaN
    cleaned = cleaned.dropna(subset=["date_parsed"]).copy()
    if cleaned.empty:
        return pd.DataFrame(columns=["date", "steps", "distance_km", "active_minutes", "calories"])

    # Standardize string date format (YYYY-MM-DD)
    cleaned["date"] = cleaned["date_parsed"].dt.strftime("%Y-%m-%d")

    # 4. Handle duplicate date entries (keep the latest occurrence)
    cleaned = cleaned.drop_duplicates(subset=["date"], keep="last")

    # 5. Clean and convert numeric columns
    # Steps: Integer, non-negative
    cleaned["steps"] = pd.to_numeric(cleaned["steps"], errors="coerce").fillna(0)
    cleaned["steps"] = cleaned["steps"].clip(lower=0).round().astype(int)

    # Distance: Float (km), non-negative
    cleaned["distance_km"] = pd.to_numeric(cleaned["distance_km"], errors="coerce").fillna(0.0)
    cleaned["distance_km"] = cleaned["distance_km"].clip(lower=0.0).astype(float)

    # Active Minutes: Integer, non-negative (capped at 1440 min/day)
    cleaned["active_minutes"] = pd.to_numeric(cleaned["active_minutes"], errors="coerce").fillna(0)
    cleaned["active_minutes"] = cleaned["active_minutes"].clip(lower=0, upper=1440).round().astype(int)

    # Calories: Integer, non-negative
    cleaned["calories"] = pd.to_numeric(cleaned["calories"], errors="coerce").fillna(0)
    cleaned["calories"] = cleaned["calories"].clip(lower=0).round().astype(int)

    # 6. Sort chronologically by date
    cleaned = cleaned.sort_values(by="date_parsed", ascending=True)

    # Clean up auxiliary columns and reset index
    cleaned = cleaned.drop(columns=["date_parsed"], errors="ignore")
    cleaned = cleaned.reset_index(drop=True)

    return cleaned


def load_dataset(file_path: Union[str, Path]) -> pd.DataFrame:
    """Safely load and clean a fitness dataset from a CSV filepath.

    Args:
        file_path: Absolute or relative path to CSV file.

    Returns:
        pd.DataFrame: Cleaned DataFrame, or empty DataFrame if file is not found.
    """
    path = Path(file_path)
    if not path.exists():
        return clean_fitness_data(pd.DataFrame())

    try:
        raw_df = pd.read_csv(path)
    except (OSError, UnicodeDecodeError, ValueError, pd.errors.ParserError) as error:
        raise ValueError(f"Unable to read fitness dataset '{path}': {error}") from error
    return clean_fitness_data(raw_df)


def filter_by_date_range(
    df: pd.DataFrame,
    start_date: Optional[Union[date, datetime, str]] = None,
    end_date: Optional[Union[date, datetime, str]] = None,
) -> pd.DataFrame:
    """Filter fitness records between start_date and end_date (inclusive).

    Args:
        df: Cleaned fitness DataFrame containing a 'date' column.
        start_date: Earliest date to include.
        end_date: Latest date to include.

    Returns:
        pd.DataFrame: Filtered subset of records.
    """
    if df is None or df.empty or "date" not in df.columns:
        return pd.DataFrame(columns=["date", "steps", "distance_km", "active_minutes", "calories"])

    # Convert date strings to timestamps for comparison
    df_dates = pd.to_datetime(df["date"])
    mask = pd.Series(True, index=df.index)

    if start_date is not None:
        start_ts = pd.to_datetime(start_date)
        mask = mask & (df_dates >= start_ts)

    if end_date is not None:
        end_ts = pd.to_datetime(end_date)
        mask = mask & (df_dates <= end_ts)

    filtered = df.loc[mask].copy().reset_index(drop=True)
    return filtered


def get_dataset_date_bounds(df: pd.DataFrame) -> Tuple[Optional[date], Optional[date]]:
    """Determine the minimum and maximum calendar dates present in the dataset.

    Args:
        df: Cleaned fitness DataFrame.

    Returns:
        Tuple of (min_date, max_date) as datetime.date objects, or (None, None).
    """
    if df is None or df.empty or "date" not in df.columns:
        return None, None

    date_series = pd.to_datetime(df["date"], errors="coerce").dropna()
    if date_series.empty:
        return None, None

    min_date = date_series.min().date()
    max_date = date_series.max().date()
    return min_date, max_date


# ==============================================================================
# Reusable Fitness Calculation Functions
# ==============================================================================


def calculate_total_steps(df: pd.DataFrame) -> int:
    """Calculate the cumulative total steps across all records in the dataset.

    Args:
        df: Cleaned fitness DataFrame.

    Returns:
        int: Total steps taken, or 0 if dataset is empty.
    """
    if df is None or df.empty or "steps" not in df.columns:
        return 0
    return int(df["steps"].sum())


def calculate_total_distance(df: pd.DataFrame) -> float:
    """Calculate the cumulative total distance in kilometers.

    Args:
        df: Cleaned fitness DataFrame.

    Returns:
        float: Total distance in km rounded to 2 decimal places, or 0.0.
    """
    if df is None or df.empty or "distance_km" not in df.columns:
        return 0.0
    return round(float(df["distance_km"].sum()), 2)


def calculate_total_active_minutes(df: pd.DataFrame) -> int:
    """Calculate the cumulative total active minutes.

    Args:
        df: Cleaned fitness DataFrame.

    Returns:
        int: Total active minutes, or 0.
    """
    if df is None or df.empty or "active_minutes" not in df.columns:
        return 0
    return int(df["active_minutes"].sum())


def calculate_total_calories(df: pd.DataFrame) -> int:
    """Calculate the cumulative total calories burned in kilocalories (kcal).

    Args:
        df: Cleaned fitness DataFrame.

    Returns:
        int: Total calories burned, or 0.
    """
    if df is None or df.empty or "calories" not in df.columns:
        return 0
    return int(df["calories"].sum())


def get_daily_activity(df: pd.DataFrame, selected_date: date) -> Optional[Dict[str, Any]]:
    """Return recorded activity metrics for one date, or None when no record exists."""
    required_columns = {"date", "calories", "steps", "distance_km", "active_minutes"}
    if df is None or df.empty or not required_columns.issubset(df.columns):
        return None

    record_dates = pd.to_datetime(df["date"], errors="coerce").dt.date
    matching_rows = df.loc[record_dates == selected_date]
    if matching_rows.empty:
        return None

    row = matching_rows.iloc[0]
    return {
        "calories": int(row["calories"]),
        "steps": int(row["steps"]),
        "distance_km": float(row["distance_km"]),
        "active_minutes": int(row["active_minutes"]),
    }


def calculate_active_days(df: pd.DataFrame) -> int:
    """Count recorded days with steps or active minutes greater than zero."""
    if df is None or df.empty:
        return 0

    active_mask = pd.Series(False, index=df.index)
    if "steps" in df.columns:
        active_mask |= df["steps"].fillna(0).gt(0)
    if "active_minutes" in df.columns:
        active_mask |= df["active_minutes"].fillna(0).gt(0)
    return int(active_mask.sum())


def calculate_average_daily_steps(df: pd.DataFrame) -> int:
    """Calculate the arithmetic mean of daily steps.

    Args:
        df: Cleaned fitness DataFrame.

    Returns:
        int: Average daily steps rounded to nearest integer, or 0.
    """
    if df is None or df.empty or "steps" not in df.columns:
        return 0
    return int(round(df["steps"].mean()))


def calculate_average_daily_distance(df: pd.DataFrame) -> float:
    """Calculate the arithmetic mean of daily distance in kilometers.

    Args:
        df: Cleaned fitness DataFrame.

    Returns:
        float: Average daily distance in km rounded to 2 decimal places, or 0.0.
    """
    if df is None or df.empty or "distance_km" not in df.columns:
        return 0.0
    return round(float(df["distance_km"].mean()), 2)


def calculate_average_daily_active_minutes(df: pd.DataFrame) -> int:
    """Calculate the arithmetic mean of daily active minutes.

    Args:
        df: Cleaned fitness DataFrame.

    Returns:
        int: Average active minutes rounded to nearest integer, or 0.
    """
    if df is None or df.empty or "active_minutes" not in df.columns:
        return 0
    return int(round(df["active_minutes"].mean()))


def calculate_average_daily_calories(df: pd.DataFrame) -> int:
    """Calculate the arithmetic mean of daily calories burned.

    Args:
        df: Cleaned fitness DataFrame.

    Returns:
        int: Average calories burned rounded to nearest integer, or 0.
    """
    if df is None or df.empty or "calories" not in df.columns:
        return 0
    return int(round(df["calories"].mean()))


def calculate_metric_trend(
    df: pd.DataFrame,
    column: str,
    comparison_mode: str = "vs_average",
) -> Dict[str, Any]:
    """Calculate the factual trend or variation for a given numeric column.

    This avoids fabricated percentages by strictly calculating the mathematical
    delta between the most recent recorded day and the period average.

    Args:
        df: Cleaned fitness DataFrame.
        column: Column name to evaluate ('steps', 'distance_km', etc.).
        comparison_mode: 'vs_average' (latest vs mean) or 'day_over_day'.

    Returns:
        Dict containing:
            - pct_change: float (e.g. 14.2)
            - direction: 'up', 'down', or 'neutral'
            - badge_text: e.g. "▲ +14.2% vs avg" or "▼ -5.1% vs avg"
            - is_available: bool (False if insufficient data)
    """
    if df is None or df.empty or column not in df.columns or len(df) == 0:
        return {
            "pct_change": 0.0,
            "direction": "neutral",
            "badge_text": "No data",
            "is_available": False,
        }

    # If only 1 record exists, cannot calculate a meaningful comparison
    if len(df) == 1:
        return {
            "pct_change": 0.0,
            "direction": "neutral",
            "badge_text": "Single record",
            "is_available": True,
        }

    series = df[column].astype(float)
    latest_val = series.iloc[-1]

    if comparison_mode == "day_over_day":
        prev_val = series.iloc[-2]
        if prev_val == 0:
            pct_change = 0.0
        else:
            pct_change = ((latest_val - prev_val) / prev_val) * 100.0
        comparison_label = "vs prev day"
    else:  # vs_average
        avg_val = series.mean()
        if avg_val == 0:
            pct_change = 0.0
        else:
            pct_change = ((latest_val - avg_val) / avg_val) * 100.0
        comparison_label = "vs period avg"

    if pct_change > 0.05:
        direction = "up"
        badge_text = f"▲ +{pct_change:.1f}% {comparison_label}"
    elif pct_change < -0.05:
        direction = "down"
        badge_text = f"▼ {pct_change:.1f}% {comparison_label}"
    else:
        direction = "neutral"
        badge_text = f"— 0.0% {comparison_label}"

    return {
        "pct_change": round(pct_change, 2),
        "direction": direction,
        "badge_text": badge_text,
        "is_available": True,
    }


def calculate_summary_metrics(df: pd.DataFrame, target_steps: int = 10000) -> Dict[str, Any]:
    """Compute comprehensive fitness metrics dictionary for dashboard cards and analytics.

    Calculates all metrics strictly from actual dataset records with safe fallbacks
    for empty datasets.

    Args:
        df: Cleaned fitness DataFrame.
        target_steps: Daily step target (default 10,000).

    Returns:
        Dict with totals, averages, day counts, date bounds, peak records, and trends.
    """
    record_count = len(df) if df is not None else 0
    min_date, max_date = get_dataset_date_bounds(df)

    if df is None or df.empty:
        return {
            "record_count": 0,
            "target_steps": target_steps,
            "start_date": None,
            "end_date": None,
            "total_steps": 0,
            "total_distance_km": 0.0,
            "total_active_minutes": 0,
            "total_calories": 0,
            "avg_daily_steps": 0,
            "avg_daily_distance_km": 0.0,
            "avg_daily_active_minutes": 0,
            "avg_daily_calories": 0,
            "peak_steps": 0,
            "peak_steps_date": None,
            "latest_steps": 0,
            "latest_date": None,
            "step_goal_completion_pct": 0.0,
            "trends": {
                "steps": {"badge_text": "No data", "direction": "neutral"},
                "distance_km": {"badge_text": "No data", "direction": "neutral"},
                "active_minutes": {"badge_text": "No data", "direction": "neutral"},
                "calories": {"badge_text": "No data", "direction": "neutral"},
            },
        }

    total_steps = calculate_total_steps(df)
    total_dist = calculate_total_distance(df)
    total_active = calculate_total_active_minutes(df)
    total_cals = calculate_total_calories(df)

    avg_steps = calculate_average_daily_steps(df)
    avg_dist = calculate_average_daily_distance(df)
    avg_active = calculate_average_daily_active_minutes(df)
    avg_cals = calculate_average_daily_calories(df)

    # Peak performance day
    max_steps_idx = df["steps"].idxmax()
    peak_steps = int(df.loc[max_steps_idx, "steps"])
    peak_date = str(df.loc[max_steps_idx, "date"])

    # Latest recorded day
    latest_row = df.iloc[-1]
    latest_steps = int(latest_row["steps"])
    latest_date = str(latest_row["date"])

    # Dynamic steps goal completion rate
    days_meeting_goal = int((df["steps"] >= target_steps).sum()) if target_steps > 0 else 0
    goal_completion_pct = round((days_meeting_goal / record_count) * 100.0, 1)

    return {
        "record_count": record_count,
        "target_steps": target_steps,
        "start_date": min_date.strftime("%Y-%m-%d") if min_date else None,
        "end_date": max_date.strftime("%Y-%m-%d") if max_date else None,
        "total_steps": total_steps,
        "total_distance_km": total_dist,
        "total_active_minutes": total_active,
        "total_calories": total_cals,
        "avg_daily_steps": avg_steps,
        "avg_daily_distance_km": avg_dist,
        "avg_daily_active_minutes": avg_active,
        "avg_daily_calories": avg_cals,
        "peak_steps": peak_steps,
        "peak_steps_date": peak_date,
        "latest_steps": latest_steps,
        "latest_date": latest_date,
        "step_goal_completion_pct": goal_completion_pct,
        "trends": {
            "steps": calculate_metric_trend(df, "steps"),
            "distance_km": calculate_metric_trend(df, "distance_km"),
            "active_minutes": calculate_metric_trend(df, "active_minutes"),
            "calories": calculate_metric_trend(df, "calories"),
        },
    }


def safe_percentage_change(val1: float, val2: float) -> float:
    """Calculate percentage change between val1 and baseline val2 with safe zero handling.

    Args:
        val1: Current or Period 1 value.
        val2: Baseline or Period 2 value.

    Returns:
        float: Percentage change, handling division-by-zero safely.
    """
    if val2 == 0.0:
        if val1 == 0.0:
            return 0.0
        return 100.0  # Positive surge from zero baseline
    return round(((val1 - val2) / abs(val2)) * 100.0, 2)


def compare_fitness_periods(
    df_period1: pd.DataFrame,
    df_period2: pd.DataFrame,
) -> Dict[str, Any]:
    """Compare fitness performance between two distinct date periods.

    Safely calculates absolute and percentage changes with zero-handling across
    all core metrics.

    Args:
        df_period1: Current / primary period DataFrame.
        df_period2: Comparison / baseline period DataFrame.

    Returns:
        Dict: Structured comparison metrics and delta badges.
    """
    m1 = calculate_summary_metrics(df_period1)
    m2 = calculate_summary_metrics(df_period2)

    def build_metric_comparison(val1: float, val2: float, is_int: bool = False) -> Dict[str, Any]:
        abs_diff = round(val1 - val2, 2) if not is_int else int(round(val1 - val2))
        pct_diff = safe_percentage_change(float(val1), float(val2))

        if abs_diff > 0:
            direction = "up"
            badge = f"▲ +{pct_diff:.1f}%"
        elif abs_diff < 0:
            direction = "down"
            badge = f"▼ {pct_diff:.1f}%"
        else:
            direction = "neutral"
            badge = "— 0.0%"

        return {
            "period1_val": int(val1) if is_int else round(float(val1), 2),
            "period2_val": int(val2) if is_int else round(float(val2), 2),
            "abs_diff": abs_diff,
            "pct_diff": pct_diff,
            "direction": direction,
            "badge": badge,
        }

    return {
        "period1_count": m1["record_count"],
        "period2_count": m2["record_count"],
        "period1_dates": (m1["start_date"], m1["end_date"]),
        "period2_dates": (m2["start_date"], m2["end_date"]),
        "metrics": {
            "total_steps": build_metric_comparison(m1["total_steps"], m2["total_steps"], is_int=True),
            "total_distance_km": build_metric_comparison(m1["total_distance_km"], m2["total_distance_km"]),
            "total_active_minutes": build_metric_comparison(m1["total_active_minutes"], m2["total_active_minutes"], is_int=True),
            "total_calories": build_metric_comparison(m1["total_calories"], m2["total_calories"], is_int=True),
            "avg_daily_steps": build_metric_comparison(m1["avg_daily_steps"], m2["avg_daily_steps"], is_int=True),
            "avg_daily_distance_km": build_metric_comparison(m1["avg_daily_distance_km"], m2["avg_daily_distance_km"]),
        },
    }


def calculate_weekly_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate activity statistics grouped by Day of the Week.

    Args:
        df: Cleaned fitness DataFrame.

    Returns:
        pd.DataFrame: Aggregated Day of Week summary sorted Monday through Sunday.
    """
    days_order = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]

    if df is None or df.empty or "date" not in df.columns:
        empty_weekly = pd.DataFrame(
            {
                "day_name": days_order,
                "avg_steps": 0,
                "avg_distance_km": 0.0,
                "avg_calories": 0,
                "avg_active_minutes": 0,
                "record_count": 0,
            }
        )
        return empty_weekly

    work_df = df.copy()
    work_df["day_name"] = pd.to_datetime(work_df["date"]).dt.day_name()

    agg_df = (
        work_df.groupby("day_name", as_index=False)
        .agg(
            avg_steps=("steps", "mean"),
            avg_distance_km=("distance_km", "mean"),
            avg_calories=("calories", "mean"),
            avg_active_minutes=("active_minutes", "mean"),
            record_count=("steps", "count"),
        )
    )

    agg_df["avg_steps"] = agg_df["avg_steps"].round().astype(int)
    agg_df["avg_distance_km"] = agg_df["avg_distance_km"].round(2)
    agg_df["avg_calories"] = agg_df["avg_calories"].round().astype(int)
    agg_df["avg_active_minutes"] = agg_df["avg_active_minutes"].round().astype(int)

    # Sort in standard calendar order (Mon-Sun)
    agg_df["day_name"] = pd.Categorical(agg_df["day_name"], categories=days_order, ordered=True)
    agg_df = agg_df.sort_values("day_name").reset_index(drop=True)
    agg_df["day_name"] = agg_df["day_name"].astype(str)

    return agg_df


def calculate_period_summary(df: pd.DataFrame, period: str = "weekly") -> pd.DataFrame:
    """Aggregate recorded metrics by calendar day, Monday-based week, or month."""
    period = period.lower()
    if period not in {"daily", "weekly", "monthly"}:
        raise ValueError("period must be 'daily', 'weekly', or 'monthly'")

    columns = [
        "period_start",
        "period_end",
        "label",
        "recorded_days",
        "active_days",
        "steps",
        "distance_km",
        "active_minutes",
        "calories",
    ]
    if df is None or df.empty or "date" not in df.columns:
        return pd.DataFrame(columns=columns)

    work_df = df.copy()
    parsed_dates = pd.to_datetime(work_df["date"], errors="coerce")
    work_df = work_df.loc[parsed_dates.notna()].copy()
    if work_df.empty:
        return pd.DataFrame(columns=columns)

    parsed_dates = parsed_dates.loc[work_df.index]
    normalized_dates = parsed_dates.dt.normalize()
    if period == "daily":
        work_df["_period_start"] = normalized_dates
    elif period == "weekly":
        work_df["_period_start"] = (
            normalized_dates - pd.to_timedelta(normalized_dates.dt.day_of_week, unit="D")
        )
    else:
        work_df["_period_start"] = normalized_dates.dt.to_period("M").dt.start_time

    work_df["_is_active"] = (
        work_df.get("steps", pd.Series(0, index=work_df.index)).fillna(0).gt(0)
        | work_df.get("active_minutes", pd.Series(0, index=work_df.index)).fillna(0).gt(0)
    )
    for metric in ("steps", "distance_km", "active_minutes", "calories"):
        if metric not in work_df.columns:
            work_df[metric] = 0

    summary = (
        work_df.groupby("_period_start", as_index=False)
        .agg(
            recorded_days=("date", "size"),
            active_days=("_is_active", "sum"),
            steps=("steps", "sum"),
            distance_km=("distance_km", "sum"),
            active_minutes=("active_minutes", "sum"),
            calories=("calories", "sum"),
        )
        .rename(columns={"_period_start": "period_start"})
    )
    summary["period_start"] = pd.to_datetime(summary["period_start"]).dt.date

    if period == "daily":
        summary["period_end"] = summary["period_start"]
        summary["label"] = summary["period_start"].map(lambda value: value.strftime("%a, %b %d"))
    elif period == "weekly":
        summary["period_end"] = summary["period_start"].map(lambda value: value + pd.Timedelta(days=6))
        summary["label"] = summary["period_start"].map(lambda value: f"Week of {value:%b %d}")
    else:
        summary["period_end"] = summary["period_start"].map(
            lambda value: (pd.Timestamp(value) + pd.offsets.MonthEnd(0)).date()
        )
        summary["label"] = summary["period_start"].map(lambda value: value.strftime("%B %Y"))

    summary["distance_km"] = summary["distance_km"].astype(float).round(2)
    summary["active_days"] = summary["active_days"].astype(int)
    summary["recorded_days"] = summary["recorded_days"].astype(int)
    return summary[columns].sort_values("period_start").reset_index(drop=True)


def calculate_goal_achievement(
    df: pd.DataFrame,
    target_steps: int = 10000,
) -> Dict[str, Any]:
    """Calculate daily target achievement metrics and breakdown.

    Args:
        df: Cleaned fitness DataFrame.
        target_steps: User-configurable daily step goal.

    Returns:
        Dict: Summary containing achievement rate, days achieved, and per-day statuses.
    """
    if df is None or df.empty or "steps" not in df.columns:
        return {
            "target_steps": target_steps,
            "days_achieved": 0,
            "total_days": 0,
            "achievement_rate_pct": 0.0,
            "days_data": [],
        }

    total_days = len(df)
    achieved_mask = df["steps"] >= target_steps
    days_achieved = int(achieved_mask.sum())
    rate_pct = round((days_achieved / total_days) * 100.0, 1) if total_days > 0 else 0.0

    days_data = []
    for _, row in df.iterrows():
        steps = int(row["steps"])
        is_achieved = steps >= target_steps
        pct = round((steps / target_steps) * 100.0, 1) if target_steps > 0 else 0.0
        days_data.append(
            {
                "date": str(row["date"]),
                "steps": steps,
                "target": target_steps,
                "is_achieved": is_achieved,
                "delta": steps - target_steps,
                "pct_of_goal": pct,
            }
        )

    return {
        "target_steps": target_steps,
        "days_achieved": days_achieved,
        "total_days": total_days,
        "achievement_rate_pct": rate_pct,
        "days_data": days_data,
    }
