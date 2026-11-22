"""Calendar-selected activity history and adjacent-period comparisons."""

import calendar
from datetime import date, timedelta
from typing import Optional, Tuple

import pandas as pd
import streamlit as st

from components.comparison import render_comparison_panel
from components.metrics import render_daily_activity_cards
from utils.data_processor import (
    calculate_period_summary,
    filter_by_date_range,
    get_daily_activity,
    get_dataset_date_bounds,
)


def _comparison_windows(selected_date: date, period: str) -> Tuple[date, date, date, date]:
    if period == "Weekly":
        current_start = selected_date - timedelta(days=selected_date.weekday())
        current_end = current_start + timedelta(days=6)
        previous_start = current_start - timedelta(days=7)
        previous_end = current_start - timedelta(days=1)
        return current_start, current_end, previous_start, previous_end

    current_start = selected_date.replace(day=1)
    previous_month_end = current_start - timedelta(days=1)
    previous_start = previous_month_end.replace(day=1)
    previous_end = previous_start + timedelta(
        days=min(selected_date.day, previous_month_end.day) - 1
    )
    return current_start, selected_date, previous_start, previous_end


def render_activity_history(
    df: Optional[pd.DataFrame],
    target_steps: int = 10000,
) -> None:
    """Render a date picker, exact daily record, period comparisons, and saved history."""
    st.markdown("### Activity history")
    if df is None or df.empty:
        st.info("No activity records are available.")
        return

    min_date, max_date = get_dataset_date_bounds(df)
    if min_date is None or max_date is None:
        st.info("No valid activity dates are available.")
        return

    date_key = "history_activity_date"
    selected_date = st.session_state.get(date_key)
    if not isinstance(selected_date, date) or not min_date <= selected_date <= max_date:
        selected_date = max_date
        st.session_state[date_key] = selected_date

    month_starts = []
    month_start = min_date.replace(day=1)
    final_month = max_date.replace(day=1)
    while month_start <= final_month:
        month_starts.append(month_start)
        month_start = (
            month_start.replace(year=month_start.year + 1, month=1)
            if month_start.month == 12
            else month_start.replace(month=month_start.month + 1)
        )

    calendar_month_key = "history_calendar_month"
    selected_month = selected_date.replace(day=1)
    if st.session_state.get(calendar_month_key) not in month_starts:
        st.session_state[calendar_month_key] = selected_month
    displayed_month = st.selectbox(
        "Activity calendar",
        options=month_starts,
        format_func=lambda value: value.strftime("%B %Y"),
        key=calendar_month_key,
    )
    if selected_date.replace(day=1) != displayed_month:
        selected_date = min(max(displayed_month, min_date), max_date)
        st.session_state[date_key] = selected_date

    recorded_dates = set(pd.to_datetime(df["date"], errors="coerce").dt.date.dropna())
    st.caption("● = recorded activity")
    weekday_columns = st.columns(7, gap="small")
    for column, weekday in zip(weekday_columns, calendar.day_abbr):
        column.markdown(f'<div class="history-weekday">{weekday}</div>', unsafe_allow_html=True)

    month_days = calendar.monthrange(displayed_month.year, displayed_month.month)[1]
    calendar_cells = [None] * displayed_month.weekday()
    calendar_cells.extend(
        date(displayed_month.year, displayed_month.month, day)
        for day in range(1, month_days + 1)
    )
    calendar_cells.extend([None] * ((-len(calendar_cells)) % 7))
    for week_start in range(0, len(calendar_cells), 7):
        week_columns = st.columns(7, gap="small")
        for column, calendar_day in zip(week_columns, calendar_cells[week_start:week_start + 7]):
            with column:
                if calendar_day is None:
                    st.markdown('<div class="history-calendar-empty"></div>', unsafe_allow_html=True)
                    continue
                in_range = min_date <= calendar_day <= max_date
                has_record = calendar_day in recorded_dates
                button_label = f"● {calendar_day.day}" if has_record else str(calendar_day.day)
                if st.button(
                    button_label,
                    key=f"history_day_{calendar_day:%Y%m%d}",
                    type="primary" if calendar_day == selected_date else "secondary",
                    disabled=not in_range,
                    use_container_width=True,
                    help=(
                        f"{calendar_day:%A, %B %d, %Y}: activity recorded"
                        if has_record
                        else f"{calendar_day:%A, %B %d, %Y}: no data available"
                    ),
                ):
                    selected_date = calendar_day
                    st.session_state[date_key] = calendar_day

    render_daily_activity_cards(get_daily_activity(df, selected_date), target_steps)

    comparison_period = st.radio(
        "Compare activity by",
        options=["Weekly", "Monthly"],
        horizontal=True,
        key="history_comparison_period",
    )
    current_start, current_end, previous_start, previous_end = _comparison_windows(
        selected_date,
        comparison_period,
    )
    current_period = filter_by_date_range(df, current_start, current_end)
    previous_period = filter_by_date_range(df, previous_start, previous_end)

    render_comparison_panel(
        current_period,
        previous_period,
        period1_name=f"Selected {comparison_period.lower()}",
        period2_name=f"Previous {comparison_period.lower()}",
    )

    summary_period = "weekly" if comparison_period == "Weekly" else "monthly"
    period_summary = calculate_period_summary(df, summary_period)
    if not period_summary.empty:
        st.markdown(f"#### Recorded {comparison_period.lower()} summaries")
        st.dataframe(
            period_summary[
                [
                    "label",
                    "recorded_days",
                    "active_days",
                    "steps",
                    "calories",
                    "distance_km",
                    "active_minutes",
                ]
            ],
            hide_index=True,
            width="stretch",
        )

    st.markdown("#### Previous activity records")
    history = df.sort_values("date", ascending=False).reset_index(drop=True)
    history["date"] = pd.to_datetime(history["date"]).dt.date
    st.dataframe(
        history,
        hide_index=True,
        width="stretch",
        column_config={
            "date": st.column_config.DateColumn("Date", format="YYYY-MM-DD"),
            "steps": st.column_config.NumberColumn("Steps", format="%d"),
            "calories": st.column_config.NumberColumn("Calories (kcal)", format="%d"),
            "distance_km": st.column_config.NumberColumn("Distance (km)", format="%.2f"),
            "active_minutes": st.column_config.NumberColumn("Active minutes", format="%d"),
        },
    )
