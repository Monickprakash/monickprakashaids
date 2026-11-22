"""FITPULSE — Fitness Activity Visualization Platform
Main Application Orchestrator

Tagline: Visualize Your Movement. Understand Your Progress.
Phase 4: Smart Fitness Analytics.
"""

from datetime import date
from pathlib import Path
import pandas as pd
import streamlit as st

from components.analytics import render_activity_analytics
from components.charts import render_weekly_activity_chart
from components.goals import render_goals
from components.header import render_header
from components.history import render_activity_history
from components.metrics import render_metric_cards
from components.sidebar import render_sidebar
from components.theme import inject_custom_css
from utils.data_processor import (
    clean_fitness_data,
    get_dataset_date_bounds,
    load_dataset,
)
from utils.storage import load_activity_records, load_goal_settings, merge_activity_records

# Configure page parameters
st.set_page_config(
    page_title="FITPULSE — Fitness Analytics",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="auto",
)

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_PATH = PROJECT_ROOT / "data" / "sample_fitness_data.csv"


@st.cache_data
def get_cached_dataset() -> pd.DataFrame:
    """Load and validate the bundled sample activity dataset.

    Returns:
        pd.DataFrame: Cleaned sample activity data.
    """
    return load_dataset(DATA_PATH)


def main() -> None:
    """Main application orchestrator."""
    # Apply the shared design system
    inject_custom_css()

    try:
        goal_settings = load_goal_settings()
    except (OSError, ValueError) as error:
        st.error(f"Saved goal settings could not be loaded: {error}")
        st.stop()

    pending_goals = st.session_state.pop("pending_goal_settings", None)
    if pending_goals is not None:
        st.session_state["daily_step_target"] = pending_goals["daily_step_goal"]
        st.session_state["goals_step_input"] = pending_goals["daily_step_goal"]
        st.session_state["goals_calorie_input"] = pending_goals["daily_calorie_goal"]
    st.session_state.setdefault("daily_step_target", goal_settings["daily_step_goal"])

    try:
        user_records = load_activity_records()
    except (OSError, ValueError, pd.errors.ParserError) as error:
        st.error(f"Saved activity records could not be loaded: {error}")
        user_records = clean_fitness_data(pd.DataFrame())
    df = merge_activity_records(get_cached_dataset(), user_records)

    selected_page, filtered_df = render_sidebar(df)
    target_steps = goal_settings["daily_step_goal"]
    st.session_state["daily_step_target"] = target_steps

    header_date = None
    if selected_page == "⚡ Overview":
        date_min, date_max = get_dataset_date_bounds(filtered_df)
        candidate_date = st.session_state.get("overview_activity_date")
        if date_min is not None and date_max is not None:
            if (
                not isinstance(candidate_date, date)
                or not date_min <= candidate_date <= date_max
            ):
                candidate_date = date_max
            header_date = candidate_date

    render_header(
        selected_page,
        data_mode="Sample + saved data" if not user_records.empty else "Sample data",
        selected_date=header_date,
    )
    if st.session_state.pop("goal_saved_notice", False):
        st.success("Fitness goals saved.")

    # Render the selected dashboard section
    if selected_page == "⚡ Overview":
        selected_activity_date = render_metric_cards(
            filtered_df,
            target_steps=target_steps,
        )
        render_weekly_activity_chart(filtered_df, selected_activity_date)

    elif selected_page == "📊 Analytics":
        render_activity_analytics(filtered_df, target_steps=target_steps)

    elif selected_page == "🗓️ Activity History":
        render_activity_history(filtered_df, target_steps=target_steps)

    elif selected_page == "🎯 Goals":
        render_goals(
            filtered_df,
            step_goal=target_steps,
            calorie_goal=goal_settings["daily_calorie_goal"],
            selected_date=st.session_state.get("overview_activity_date"),
        )


if __name__ == "__main__":
    main()
