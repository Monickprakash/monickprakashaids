"""Local, atomic persistence for FITPULSE goals and user activity records."""

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional, Union

import numpy as np
import pandas as pd

from utils.data_processor import clean_fitness_data

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
USER_RECORDS_PATH = DATA_DIR / "user_activity_records.csv"
GOALS_PATH = DATA_DIR / "user_goals.json"
DEFAULT_GOALS = {"daily_step_goal": 10000, "daily_calorie_goal": 0}
RECORD_COLUMNS = ["date", "steps", "distance_km", "active_minutes", "calories"]
PathLike = Union[str, Path]


def validate_activity_records(records: pd.DataFrame) -> pd.DataFrame:
    """Validate all required fields before storing user-supplied activity."""
    if not isinstance(records, pd.DataFrame):
        raise TypeError("Activity records must be provided as a table.")
    if records.empty:
        raise ValueError("No activity records were provided.")

    normalized = records.copy()
    normalized.columns = [str(column).strip().lower() for column in normalized.columns]
    missing = set(RECORD_COLUMNS).difference(normalized.columns)
    if missing:
        raise ValueError(f"Missing required activity columns: {', '.join(sorted(missing))}.")

    parsed_dates = pd.to_datetime(normalized["date"], errors="coerce")
    if parsed_dates.isna().any():
        raise ValueError("Every activity record must have a valid date.")
    normalized["date"] = parsed_dates.dt.strftime("%Y-%m-%d")

    integer_columns = ("steps", "active_minutes", "calories")
    for column in ("steps", "distance_km", "active_minutes", "calories"):
        values = pd.to_numeric(normalized[column], errors="coerce")
        if values.isna().any() or not np.isfinite(values.to_numpy(dtype=float)).all():
            raise ValueError(f"{column} must contain finite numeric values.")
        if values.lt(0).any():
            raise ValueError(f"{column} cannot be negative.")
        if column in integer_columns:
            if values.mod(1).ne(0).any():
                raise ValueError(f"{column} must contain whole numbers.")
            if values.ge(float(np.iinfo(np.int64).max)).any():
                raise ValueError(f"{column} exceeds the supported integer range.")
            values = values.astype("int64")
        normalized[column] = values

    if normalized["active_minutes"].gt(1440).any():
        raise ValueError("Active minutes cannot exceed 1,440 in a day.")
    return clean_fitness_data(normalized[RECORD_COLUMNS])


def load_activity_records(path: Optional[PathLike] = None) -> pd.DataFrame:
    """Load persisted user records, returning a typed empty table when none exist."""
    records_path = Path(path) if path is not None else USER_RECORDS_PATH
    if not records_path.exists():
        return clean_fitness_data(pd.DataFrame())
    return validate_activity_records(pd.read_csv(records_path))


def merge_activity_records(
    base_records: pd.DataFrame,
    user_records: pd.DataFrame,
) -> pd.DataFrame:
    """Merge records by date, giving explicit user records precedence over sample data."""
    combined = pd.concat([base_records, user_records], ignore_index=True)
    return clean_fitness_data(combined)


def save_activity_records(
    records: pd.DataFrame,
    path: Optional[PathLike] = None,
) -> pd.DataFrame:
    """Upsert validated records by date and atomically persist the result."""
    records_path = Path(path) if path is not None else USER_RECORDS_PATH
    incoming = validate_activity_records(records)
    existing = load_activity_records(records_path)
    combined = clean_fitness_data(pd.concat([existing, incoming], ignore_index=True))
    records_path.parent.mkdir(parents=True, exist_ok=True)

    temp_path: Optional[Path] = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            suffix=".tmp",
            prefix=f"{records_path.stem}_",
            dir=records_path.parent,
            delete=False,
        ) as temp_file:
            temp_path = Path(temp_file.name)
        combined.to_csv(temp_path, index=False)
        os.replace(temp_path, records_path)
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()
    return combined


def load_goal_settings(path: Optional[PathLike] = None) -> Dict[str, int]:
    """Load validated persisted daily goals, using defaults only when not configured."""
    goals_path = Path(path) if path is not None else GOALS_PATH
    if not goals_path.exists():
        return DEFAULT_GOALS.copy()

    try:
        raw: Any = json.loads(goals_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"Saved goal settings are not valid JSON: {error}") from error
    if not isinstance(raw, dict):
        raise ValueError("Saved goal settings must be a JSON object.")

    goals = {
        "daily_step_goal": raw.get("daily_step_goal", DEFAULT_GOALS["daily_step_goal"]),
        "daily_calorie_goal": raw.get(
            "daily_calorie_goal",
            DEFAULT_GOALS["daily_calorie_goal"],
        ),
    }
    validate_goal_settings(goals["daily_step_goal"], goals["daily_calorie_goal"])
    return {key: int(value) for key, value in goals.items()}


def validate_goal_settings(step_goal: Any, calorie_goal: Any) -> None:
    """Validate goal values used by both the UI and persistence layer."""
    if isinstance(step_goal, bool) or not isinstance(step_goal, (int, np.integer)):
        raise ValueError("The daily step goal must be a whole number.")
    if not 1000 <= int(step_goal) <= 50000:
        raise ValueError("The daily step goal must be between 1,000 and 50,000.")
    if isinstance(calorie_goal, bool) or not isinstance(calorie_goal, (int, np.integer)):
        raise ValueError("The daily calorie goal must be a whole number.")
    if not 0 <= int(calorie_goal) <= 50000:
        raise ValueError("The daily calorie goal must be between 0 and 50,000.")


def save_goal_settings(
    step_goal: int,
    calorie_goal: int,
    path: Optional[PathLike] = None,
) -> Dict[str, int]:
    """Validate and atomically save daily goals; zero calories means no calorie goal."""
    validate_goal_settings(step_goal, calorie_goal)
    goals = {
        "daily_step_goal": int(step_goal),
        "daily_calorie_goal": int(calorie_goal),
    }
    goals_path = Path(path) if path is not None else GOALS_PATH
    goals_path.parent.mkdir(parents=True, exist_ok=True)

    temp_path: Optional[Path] = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".tmp",
            prefix=f"{goals_path.stem}_",
            dir=goals_path.parent,
            delete=False,
        ) as temp_file:
            temp_path = Path(temp_file.name)
            json.dump(goals, temp_file, indent=2)
            temp_file.write("\n")
        os.replace(temp_path, goals_path)
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()
    return goals


def get_activity_storage_version(path: Optional[PathLike] = None) -> int:
    """Return a cache key that changes when persisted records change."""
    records_path = Path(path) if path is not None else USER_RECORDS_PATH
    try:
        return records_path.stat().st_mtime_ns
    except FileNotFoundError:
        return 0
