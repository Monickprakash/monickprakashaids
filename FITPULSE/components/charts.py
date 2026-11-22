"""FITPULSE Interactive Visualizations, Goal Progress, and Analytics Charts."""

from typing import Optional
from datetime import date, timedelta
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from components.theme import get_plotly_layout_defaults
from utils.data_processor import (
    calculate_goal_achievement,
    calculate_weekly_summary,
)


def render_weekly_activity_chart(
    df: Optional[pd.DataFrame],
    selected_date: Optional[date],
) -> None:
    """Render actual daily calories for the selected calendar week."""
    st.markdown("#### Weekly calories")
    if df is None or df.empty or selected_date is None:
        st.info("No activity data is available for this date range.")
        return

    week_start = selected_date - timedelta(days=selected_date.weekday())
    week_dates = [week_start + timedelta(days=offset) for offset in range(7)]
    work_df = df.copy()
    work_df["_activity_date"] = pd.to_datetime(work_df["date"], errors="coerce").dt.date
    week_df = work_df.loc[
        work_df["_activity_date"].between(week_dates[0], week_dates[-1])
    ].drop_duplicates("_activity_date", keep="last")
    calories_by_date = {
        row["_activity_date"]: int(row["calories"])
        for _, row in week_df.iterrows()
    }
    if not calories_by_date:
        st.info("No recorded activity is available for this week.")
        return

    labels = [day.strftime("%a") for day in week_dates]
    values = [calories_by_date.get(day) for day in week_dates]
    colors = [
        "#EA580C" if day == selected_date else "rgba(234, 88, 12, 0.65)"
        for day in week_dates
    ]
    layout_cfg = get_plotly_layout_defaults()
    fig = go.Figure(
        go.Bar(
            x=labels,
            y=values,
            name="Calories burned",
            marker={"color": colors},
            customdata=[
                [
                    day.strftime("%A, %b %d"),
                    "No data available" if value is None else f"{value:,} kcal",
                ]
                for day, value in zip(week_dates, values)
            ],
            marker_line={"color": "#FFFFFF", "width": 1},
            hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]}<extra></extra>",
        )
    )
    layout_cfg.update(
        {
            "height": 270,
            "showlegend": False,
            "bargap": 0.3,
            "transition": {"duration": 450, "easing": "cubic-in-out"},
            "margin": {"l": 8, "r": 8, "t": 8, "b": 12},
            "xaxis": {
                **layout_cfg["xaxis"],
                "title": "",
                "showgrid": False,
                "tickangle": 0,
                "tickfont": {"size": 12},
                "automargin": True,
            },
            "yaxis": {
                **layout_cfg["yaxis"],
                "title": "Calories (kcal)",
                "rangemode": "tozero",
            },
        }
    )
    fig.update_layout(**layout_cfg)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def render_activity_overview_chart(
    df: Optional[pd.DataFrame],
    target_steps: int = 10000,
) -> None:
    """Render interactive Plotly visual analytics including trends, goal achievement, and weekly summaries.

    Args:
        df: DataFrame containing the active or filtered activity records.
        target_steps: User-configurable daily step target benchmark.
    """
    st.html(
        """<div class="section-header-row">
    <h3 class="section-title">
        <span>📈</span> Activity Performance & Goal Analytics
    </h3>
    <span class="section-tag tag-active">Interactive Visualizations</span>
</div>"""
    )

    if df is None or df.empty:
        st.info("No activity records available in the selected range to display charts.")
        return

    # Multi-view tabs for rich interactive analysis
    tab_trend, tab_goal, tab_weekly = st.tabs(
        ["📈 Daily Trend", "🎯 Goal Achievement", "📅 Day-of-Week Summary"]
    )

    layout_cfg = get_plotly_layout_defaults()

    with tab_trend:
        # Metric Selector for Trend Analysis
        col_metric, _ = st.columns([4, 8])
        with col_metric:
            selected_metric = st.selectbox(
                "Metric to plot:",
                options=["Daily Steps", "Distance (km)", "Calories Burned (kcal)", "Active Time (min)"],
                index=0,
                key="chart_metric_selector",
                label_visibility="collapsed",
            )

        fig_trend = go.Figure()

        if selected_metric == "Daily Steps":
            y_col = "steps"
            line_color = "#2563EB"
            y_title = "Steps"
            hover_fmt = "%{y:,.0f} steps"
        elif selected_metric == "Distance (km)":
            y_col = "distance_km"
            line_color = "#0891B2"
            y_title = "Distance (km)"
            hover_fmt = "%{y:.2f} km"
        elif selected_metric == "Calories Burned (kcal)":
            y_col = "calories"
            line_color = "#EA580C"
            y_title = "Calories (kcal)"
            hover_fmt = "%{y:,.0f} kcal"
        else:
            y_col = "active_minutes"
            line_color = "#7C3AED"
            y_title = "Active Minutes"
            hover_fmt = "%{y:,.0f} min"

        # Trace: Metric Spline
        fig_trend.add_trace(
            go.Scatter(
                x=df["date"],
                y=df[y_col],
                mode="lines+markers",
                name=selected_metric,
                line={"color": line_color, "width": 2},
                marker={
                    "size": 6,
                    "color": line_color,
                    "line": {"color": "#FFFFFF", "width": 1},
                },
                hovertemplate=f"<b>Date:</b> %{{x}}<br><b>{selected_metric}:</b> {hover_fmt}<extra></extra>",
            )
        )

        # Dynamic Benchmark Reference line for Steps
        if selected_metric == "Daily Steps" and target_steps > 0:
            fig_trend.add_hline(
                y=target_steps,
                line_dash="dot",
                line_color="rgba(37, 99, 235, 0.55)",
                line_width=1,
                annotation_text=f"Target: {target_steps:,} Steps",
                annotation_position="top left",
                annotation_font={"color": "#2563EB", "size": 10, "family": "Plus Jakarta Sans"},
            )

        max_y = float(df[y_col].max()) if not df[y_col].empty else 100
        upper_bound = max(max_y * 1.18, target_steps * 1.1 if selected_metric == "Daily Steps" else max_y * 1.1)

        cfg_copy = layout_cfg.copy()
        cfg_copy.update(
            {
                "height": 310,
                "showlegend": False,
                "margin": {"l": 10, "r": 10, "t": 20, "b": 10},
                "autosize": True,
                "xaxis": {**cfg_copy["xaxis"], "title": "", "type": "category"},
                "yaxis": {**cfg_copy["yaxis"], "title": y_title, "range": [0, upper_bound]},
            }
        )
        fig_trend.update_layout(**cfg_copy)
        st.plotly_chart(fig_trend, width="stretch", config={"displayModeBar": False})

    with tab_goal:
        # Goal Achievement Distribution Chart
        goal_summary = calculate_goal_achievement(df, target_steps=target_steps)
        rate = goal_summary["achievement_rate_pct"]
        achieved_days = goal_summary["days_achieved"]
        total_days = goal_summary["total_days"]

        st.caption(
            f"🎯 Goal Completion Rate: **{rate}%** ({achieved_days} of {total_days} days met or exceeded target of {target_steps:,} steps)"
        )

        fig_goal = go.Figure()

        # Dynamic bar colors: Neon Lime if met, Amber if not
        bar_colors = [
            "#16A34A" if d["is_achieved"] else "rgba(37, 99, 235, 0.34)"
            for d in goal_summary["days_data"]
        ]

        fig_goal.add_trace(
            go.Bar(
                x=[d["date"] for d in goal_summary["days_data"]],
                y=[d["steps"] for d in goal_summary["days_data"]],
                marker={"color": bar_colors, "line": {"width": 0}},
                hovertemplate="<b>Date:</b> %{x}<br><b>Steps:</b> %{y:,.0f}<br><b>Goal:</b> %{customdata}%<extra></extra>",
                customdata=[d["pct_of_goal"] for d in goal_summary["days_data"]],
            )
        )

        fig_goal.add_hline(
            y=target_steps,
            line_dash="dash",
            line_color="rgba(37, 99, 235, 0.55)",
            line_width=1,
            annotation_text=f"Target: {target_steps:,}",
            annotation_position="top right",
            annotation_font={"color": "#2563EB", "size": 10},
        )

        goal_layout = layout_cfg.copy()
        goal_layout.update(
            {
                "height": 310,
                "showlegend": False,
                "margin": {"l": 10, "r": 10, "t": 20, "b": 10},
                "xaxis": {**goal_layout["xaxis"], "title": "", "type": "category"},
                "yaxis": {
                    **goal_layout["yaxis"],
                    "title": "Steps",
                    "range": [0, max(df["steps"].max() * 1.15, target_steps * 1.15)],
                },
            }
        )
        fig_goal.update_layout(**goal_layout)
        st.plotly_chart(fig_goal, width="stretch", config={"displayModeBar": False})

    with tab_weekly:
        # Day of Week Aggregated Volume
        weekly_df = calculate_weekly_summary(df)

        fig_weekly = go.Figure()
        fig_weekly.add_trace(
            go.Bar(
                x=weekly_df["day_name"],
                y=weekly_df["avg_steps"],
                marker={
                    "color": "#16A34A",
                    "line": {"width": 0},
                },
                hovertemplate="<b>%{x}:</b> Avg %{y:,.0f} steps<extra></extra>",
            )
        )

        weekly_layout = layout_cfg.copy()
        weekly_layout.update(
            {
                "height": 310,
                "showlegend": False,
                "margin": {"l": 10, "r": 10, "t": 20, "b": 10},
                "xaxis": {**weekly_layout["xaxis"], "title": ""},
                "yaxis": {**weekly_layout["yaxis"], "title": "Avg Steps"},
            }
        )
        fig_weekly.update_layout(**weekly_layout)
        st.plotly_chart(fig_weekly, width="stretch", config={"displayModeBar": False})


def render_goal_progress_ring(
    current_steps: int = 0,
    target_steps: int = 10000,
    title: str = "Daily Step Goal",
    tag_label: str = "Active Target",
) -> None:
    """Render an animated SVG circular progress ring showing daily goal completion.

    Args:
        current_steps: Steps taken so far today or period average.
        target_steps: Daily step objective.
        title: Title of the progress ring card.
        tag_label: Status tag displayed in the card header.
    """
    percentage = min(100.0, (current_steps / target_steps) * 100) if target_steps > 0 else 0
    # Circumference for radius r=66: 2 * pi * 66 ~= 414.7
    circumference = 414.7
    offset = circumference - (percentage / 100.0) * circumference
    remaining = max(0, target_steps - current_steps)
    completion_class = " ring-progress-complete" if remaining == 0 else ""

    html_content = f"""<div class="glass-panel goal-ring-card">
    <div style="display: flex; justify-content: space-between; width: 100%; align-items: center;">
        <div style="font-weight: 700; font-size: 1rem; color: #172B4D; display: flex; align-items: center; gap: 8px;">
            <span>🎯</span> {title}
        </div>
        <span class="metric-sample-tag">{tag_label}</span>
    </div>

    <!-- SVG Animated Circular Progress Ring -->
    <div class="progress-ring-wrap">
        <svg class="progress-ring-svg" viewBox="0 0 160 160">
            <circle class="ring-bg" cx="80" cy="80" r="66" />
            <circle 
                class="ring-progress{completion_class}" 
                cx="80" 
                cy="80" 
                r="66" 
                stroke-dasharray="{circumference:.1f}" 
                stroke-dashoffset="{offset:.1f}" 
            />
        </svg>
        <div class="ring-center-content">
            <span class="ring-percentage">{percentage:.0f}%</span>
            <span class="ring-label">Completed</span>
        </div>
    </div>

    <!-- Goal Breakdown Subtext -->
    <div class="goal-details-row">
        <div class="goal-detail-item">
            <span class="goal-detail-val">{current_steps:,}</span>
            <span class="goal-detail-lbl">Current</span>
        </div>
        <div class="goal-detail-item">
            <span class="goal-detail-val">{target_steps:,}</span>
            <span class="goal-detail-lbl">Target</span>
        </div>
        <div class="goal-detail-item">
            <span class="goal-detail-val" style="color: {'#16A34A' if remaining == 0 else '#EA580C'};">
                {f"{remaining:,}" if remaining > 0 else "Achieved! 🏆"}
            </span>
            <span class="goal-detail-lbl">Remaining</span>
        </div>
    </div>
</div>"""

    st.html(html_content)
