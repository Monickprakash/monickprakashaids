"""FITPULSE selected-day activity summary."""

from datetime import date, timedelta
from typing import Any, Dict, Optional

import pandas as pd
import streamlit as st

from utils.data_processor import get_daily_activity, get_dataset_date_bounds


def render_metric_cards(
    df: Optional[pd.DataFrame] = None,
    target_steps: Optional[int] = None,
) -> Optional[date]:
    """Select a calendar day and render its actual recorded activity."""
    selected_date: Optional[date] = None
    daily_activity = None

    if df is not None and not df.empty:
        min_date, max_date = get_dataset_date_bounds(df)
        if min_date and max_date:
            available_dates = [
                min_date + timedelta(days=offset)
                for offset in range((max_date - min_date).days + 1)
            ]
            selector_key = "overview_activity_date"
            if st.session_state.get(selector_key) not in available_dates:
                st.session_state[selector_key] = max_date

            selected_date = st.selectbox(
                "Activity date",
                options=available_dates,
                format_func=lambda value: value.strftime("%A, %b %d, %Y"),
                key=selector_key,
            )
            daily_activity = get_daily_activity(df, selected_date)

    render_daily_activity_cards(daily_activity, target_steps)
    return selected_date


def render_daily_activity_cards(
    daily_activity: Optional[Dict[str, Any]],
    target_steps: Optional[int] = None,
) -> None:
    """Render actual recorded metrics for one date, including its configured step goal."""
    if daily_activity is None:
        st.info("No data available for the selected date.")
        values = {
            "Calories burned": ("No data available", "", "calories", ""),
            "Steps completed": ("No data available", "", "steps", ""),
            "Distance covered": ("No data available", "", "distance", ""),
            "Active minutes": ("No data available", "", "minutes", ""),
        }
    else:
        steps = daily_activity["steps"]
        goal_html = ""
        if target_steps is not None and target_steps > 0:
            progress_pct = min(100.0, steps / target_steps * 100)
            completion_class = " step-goal-complete" if steps >= target_steps else ""
            goal_html = f"""
        <div class="step-goal-caption">
            <span>{progress_pct:.0f}% of daily goal</span>
            <span>{target_steps:,} steps</span>
        </div>
        <div class="step-goal-track" role="progressbar"
             aria-label="Daily step goal progress" aria-valuemin="0"
             aria-valuemax="{target_steps}"
             aria-valuenow="{min(steps, target_steps)}"
             aria-valuetext="{steps:,} of {target_steps:,} steps">
            <div class="step-goal-fill{completion_class}" style="width: {progress_pct:.2f}%;"></div>
        </div>"""
        values = {
            "Calories burned": (f"{daily_activity['calories']:,}", "kcal", "calories", ""),
            "Daily steps": (f"{steps:,}", "steps", "steps", goal_html),
            "Distance covered": (f"{daily_activity['distance_km']:.1f}", "km", "distance", ""),
            "Active minutes": (f"{daily_activity['active_minutes']:,}", "min", "minutes", ""),
        }

    icons = {
        "calories": "🔥",
        "steps": "👣",
        "distance": "↗",
        "minutes": "◷",
    }

    html_content = """<div class="key-metrics-grid daily-metrics-grid">"""
    for label, (value, unit, metric, goal_html) in values.items():
        featured_class = (
            " key-metric-featured key-metric-calories"
            if metric == "calories"
            else " key-metric-featured key-metric-steps"
            if metric == "steps"
            else " key-metric-distance"
            if metric == "distance"
            else " key-metric-minutes"
            if metric == "minutes"
            else ""
        )
        unit_html = f'<span class="key-metric-unit">{unit}</span>' if unit else ""
        html_content += f"""
    <div class="key-metric-card{featured_class}">
        <div class="key-metric-heading">
            <span class="key-metric-icon" aria-hidden="true">{icons[metric]}</span>
            <span class="key-metric-label">{label}</span>
        </div>
        <div class="key-metric-value">{value}{unit_html}</div>
        {goal_html}
    </div>"""
    html_content += "\n</div>"
    st.html(html_content)
