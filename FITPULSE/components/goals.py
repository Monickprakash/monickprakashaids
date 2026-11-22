"""Persistent personal daily step and calorie goals."""

from datetime import date
from typing import Optional

import pandas as pd
import streamlit as st

from utils.data_processor import get_daily_activity, get_dataset_date_bounds
from utils.storage import save_goal_settings


def _render_goal_bar(label: str, current: int, target: int, tone: str) -> None:
    progress = min(100.0, current / target * 100) if target > 0 else 0
    status = "Goal complete" if current >= target else f"{target - current:,} remaining"
    completion_class = " goal-progress-complete" if current >= target else ""
    st.markdown(f"**{label}:** {current:,} of {target:,} ({progress:.0f}%)")
    st.html(
        f"""<div class="goal-progress-track" role="progressbar"
             aria-label="{label} goal progress" aria-valuemin="0"
             aria-valuemax="{target}" aria-valuenow="{min(current, target)}"
             aria-valuetext="{current:,} of {target:,}">
            <div class="goal-progress-fill goal-progress-{tone}{completion_class}"
                 style="width: {progress:.2f}%;"></div>
        </div>"""
    )
    st.caption(status)


def render_goals(
    df: Optional[pd.DataFrame],
    step_goal: int,
    calorie_goal: int,
    selected_date: Optional[date] = None,
) -> None:
    """Display actual selected-day goal progress and allow persistent goal updates."""
    st.markdown("### Personal fitness goals")
    st.caption("Update your daily targets here. A calorie goal of 0 disables calorie tracking.")
    st.session_state.setdefault("goals_step_input", int(step_goal))
    st.session_state.setdefault("goals_calorie_input", int(calorie_goal))

    with st.form("fitness_goals_form"):
        new_step_goal = st.number_input(
            "Daily step goal",
            min_value=1000,
            max_value=50000,
            step=500,
            key="goals_step_input",
        )
        new_calorie_goal = st.number_input(
            "Daily calorie goal (kcal)",
            min_value=0,
            max_value=50000,
            step=100,
            key="goals_calorie_input",
            help="Set to 0 if you do not want to track a calorie goal.",
        )
        submitted = st.form_submit_button("Save goals")

    if submitted:
        try:
            save_goal_settings(int(new_step_goal), int(new_calorie_goal))
        except (OSError, ValueError) as error:
            st.error(f"Goals could not be saved: {error}")
        else:
            st.session_state["pending_goal_settings"] = {
                "daily_step_goal": int(new_step_goal),
                "daily_calorie_goal": int(new_calorie_goal),
            }
            st.session_state["goal_saved_notice"] = True
            st.rerun()

    if df is None or df.empty:
        st.info("No activity records are available to show goal progress.")
        return

    min_date, max_date = get_dataset_date_bounds(df)
    if min_date is None or max_date is None:
        st.info("No valid activity dates are available for goal tracking.")
        return
    selected_date = selected_date or max_date
    if not min_date <= selected_date <= max_date:
        selected_date = max_date
    date_key = "goals_activity_date"
    if st.session_state.get(date_key) != selected_date and (
        st.session_state.get(date_key) is None
        or not min_date <= st.session_state[date_key] <= max_date
    ):
        st.session_state[date_key] = selected_date
    selected_date = st.date_input(
        "Progress date",
        min_value=min_date,
        max_value=max_date,
        key=date_key,
        help="Choose a recorded date; missing dates have no goal progress.",
    )
    activity = get_daily_activity(df, selected_date)
    if activity is None:
        st.info(f"No activity record is available for {selected_date:%B %d, %Y}.")
        return

    st.markdown(f"#### Progress for {selected_date:%A, %B %d, %Y}")
    _render_goal_bar("Steps", activity["steps"], step_goal, "steps")

    if calorie_goal > 0:
        _render_goal_bar("Calories (kcal)", activity["calories"], calorie_goal, "calories")
    else:
        st.caption("No daily calorie goal is configured.")
