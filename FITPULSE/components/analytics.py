"""Interactive daily, weekly, and monthly activity analysis."""

from datetime import timedelta
from typing import Optional

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from components.metrics import render_daily_activity_cards
from components.theme import get_plotly_layout_defaults
from utils.data_processor import (
    calculate_period_summary,
    get_daily_activity,
    get_dataset_date_bounds,
)

METRICS = {
    "Steps": ("steps", "steps", "#2563EB"),
    "Calories burned": ("calories", "kcal", "#EA580C"),
    "Distance": ("distance_km", "km", "#0891B2"),
    "Active minutes": ("active_minutes", "min", "#7C3AED"),
}


def render_activity_analytics(
    df: Optional[pd.DataFrame],
    target_steps: int = 10000,
) -> None:
    """Render actual daily records or calendar-period totals with an interactive chart."""
    st.markdown("### Activity analytics")
    if df is None or df.empty:
        st.info("No activity records are available for this date range.")
        return

    period_label = st.radio(
        "View activity by",
        options=["Daily", "Weekly", "Monthly"],
        horizontal=True,
        key="analytics_period",
    )
    period = period_label.lower()
    metric_label = st.selectbox(
        "Metric",
        options=list(METRICS),
        key="analytics_metric",
    )
    metric, unit, color = METRICS[metric_label]
    summary = calculate_period_summary(df, period)
    if summary.empty:
        st.info("No valid activity dates are available to summarize.")
        return

    if period == "daily":
        min_date, max_date = get_dataset_date_bounds(df)
        if min_date is None or max_date is None:
            st.info("No valid activity dates are available to select.")
            return
        available_dates = [
            min_date + timedelta(days=offset)
            for offset in range((max_date - min_date).days + 1)
        ]
        date_key = "analytics_activity_date"
        if st.session_state.get(date_key) not in available_dates:
            st.session_state[date_key] = max_date
        selected_date = st.selectbox(
            "Activity date",
            options=available_dates,
            format_func=lambda value: value.strftime("%A, %b %d, %Y"),
            key=date_key,
        )
        render_daily_activity_cards(get_daily_activity(df, selected_date), target_steps)
        chart_title = f"Daily {metric_label.lower()}"
        chart_x = summary["label"]
        chart_y = summary[metric]
        trace = go.Scatter(
            x=chart_x,
            y=chart_y,
            mode="lines+markers",
            name=metric_label,
            line={"color": color, "width": 3, "shape": "spline"},
            marker={
                "color": color,
                "size": 8,
                "line": {"color": "#FFFFFF", "width": 2},
            },
            fill="tozeroy",
            fillcolor=f"rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.10)",
            customdata=summary["period_start"].astype(str),
            hovertemplate=(
                "<b>%{customdata}</b><br>"
                f"{metric_label}: %{{y:,.1f}} {unit}<extra></extra>"
            ),
        )
        chart_height = 320
    else:
        chart_title = f"{period_label} {metric_label.lower()} totals"
        chart_x = summary["label"]
        chart_y = summary[metric]
        trace = go.Bar(
            x=chart_x,
            y=chart_y,
            name=metric_label,
            marker={"color": color},
            customdata=summary[["recorded_days", "active_days"]].to_numpy(),
            hovertemplate=(
                "<b>%{x}</b><br>"
                f"{metric_label}: %{{y:,.1f}} {unit}<br>"
                "Recorded days: %{customdata[0]}<br>"
                "Active days: %{customdata[1]}<extra></extra>"
            ),
        )
        chart_height = 360

    st.markdown(f"#### {chart_title}")
    layout = get_plotly_layout_defaults()
    layout.update(
        {
            "height": chart_height,
            "showlegend": False,
            "transition": {"duration": 450, "easing": "cubic-in-out"},
            "margin": {"l": 12, "r": 12, "t": 18, "b": 12},
            "xaxis": {
                **layout["xaxis"],
                "title": "",
                "showgrid": False,
                "type": "category",
            },
            "yaxis": {
                **layout["yaxis"],
                "title": f"{metric_label} ({unit})",
                "rangemode": "tozero",
            },
        }
    )
    figure = go.Figure(trace)
    figure.update_layout(**layout)
    st.plotly_chart(figure, width="stretch", config={"displayModeBar": False})

    display_columns = [
        "label",
        "recorded_days",
        "active_days",
        "steps",
        "calories",
        "distance_km",
        "active_minutes",
    ]
    st.markdown(f"#### {period_label} activity summary")
    st.dataframe(
        summary[display_columns],
        hide_index=True,
        width="stretch",
        column_config={
            "label": st.column_config.TextColumn("Period"),
            "recorded_days": st.column_config.NumberColumn("Recorded days"),
            "active_days": st.column_config.NumberColumn("Active days"),
            "steps": st.column_config.NumberColumn("Steps", format="%d"),
            "calories": st.column_config.NumberColumn("Calories", format="%d kcal"),
            "distance_km": st.column_config.NumberColumn("Distance", format="%.2f km"),
            "active_minutes": st.column_config.NumberColumn("Active minutes", format="%d min"),
        },
    )
