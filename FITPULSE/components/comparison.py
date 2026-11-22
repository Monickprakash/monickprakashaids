"""FITPULSE Date Range Comparison Component.

Phase 4: Smart Fitness Analytics.
Renders comparative analysis between two selected timeframes,
displaying absolute differences and percentage deltas with safe zero handling.
"""

from typing import Optional
import pandas as pd
import streamlit as st
from utils.data_processor import compare_fitness_periods


def render_comparison_panel(
    df_period1: Optional[pd.DataFrame],
    df_period2: Optional[pd.DataFrame],
    period1_name: str = "Active Window",
    period2_name: str = "Comparison Window",
) -> None:
    """Render an interactive side-by-side comparison between two dataset periods.

    Args:
        df_period1: Primary / current timeframe DataFrame.
        df_period2: Baseline / comparison timeframe DataFrame.
        period1_name: Display label for primary window.
        period2_name: Display label for comparison window.
    """
    comp = compare_fitness_periods(df_period1, df_period2)
    p1_count = comp["period1_count"]
    p2_count = comp["period2_count"]
    p1_start, p1_end = comp["period1_dates"]
    p2_start, p2_end = comp["period2_dates"]

    p1_label = f"{p1_start} to {p1_end} ({p1_count} days)" if p1_count > 0 else "Empty (0 days)"
    p2_label = f"{p2_start} to {p2_end} ({p2_count} days)" if p2_count > 0 else "Empty (0 days)"

    st.html(
        f"""<div class="section-header-row" style="margin-top: 10px;">
    <h3 class="section-title">
        <span>🔄</span> Period-over-Period Performance Comparison
    </h3>
    <span class="section-tag tag-active">Comparative Analytics</span>
</div>
<div class="glass-panel" style="padding: 18px 22px; margin-bottom: 22px;">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; margin-bottom: 16px; border-bottom: 1px solid var(--border-subtle); padding-bottom: 12px;">
        <div style="display: flex; align-items: center; gap: 10px;">
            <span style="font-size: 0.85rem; font-weight: 700; color: #2563EB;">Window A: {period1_name}</span>
            <span style="font-size: 0.76rem; color: #526176; background: rgba(37, 99, 235, 0.08); padding: 3px 8px; border-radius: 9999px;">{p1_label}</span>
        </div>
        <div style="display: flex; align-items: center; gap: 8px; color: #64748B; font-size: 0.8rem;">VS</div>
        <div style="display: flex; align-items: center; gap: 10px;">
            <span style="font-size: 0.85rem; font-weight: 700; color: #2563EB;">Window B: {period2_name}</span>
            <span style="font-size: 0.76rem; color: #526176; background: rgba(37, 99, 235, 0.08); padding: 3px 8px; border-radius: 9999px;">{p2_label}</span>
        </div>
    </div>"""
    )

    if p1_count == 0 and p2_count == 0:
        st.info("Both selected date ranges are empty. Choose a range with recorded activity to view comparison metrics.")
        st.html("</div>")
        return

    m = comp["metrics"]

    def badge_html(metric_info: dict) -> str:
        d = metric_info["direction"]
        cls = "trend-up" if d == "up" else ("trend-down" if d == "down" else "trend-neutral")
        return f'<span class="metric-trend-badge {cls}">{metric_info["badge"]}</span>'

    comparison_grid = f"""<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 14px;">
        <!-- Steps Comparison -->
        <div style="background: #FFFFFF; border: 1px solid var(--border-subtle); border-radius: 12px; padding: 14px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="font-size: 0.76rem; text-transform: uppercase; color: #526176; font-weight: 600;">Total Steps</span>
                {badge_html(m['total_steps'])}
            </div>
            <div style="display: flex; align-items: baseline; gap: 8px; margin-bottom: 6px;">
                <span style="font-size: 1.3rem; font-weight: 800; color: #172B4D;">{m['total_steps']['period1_val']:,}</span>
                <span style="font-size: 0.8rem; color: #64748B;">vs {m['total_steps']['period2_val']:,}</span>
            </div>
            <div style="font-size: 0.72rem; color: #526176;">
                Delta: <strong style="color: {'#2563EB' if m['total_steps']['abs_diff'] >= 0 else '#DC2626'};">{'+' if m['total_steps']['abs_diff'] > 0 else ''}{m['total_steps']['abs_diff']:,}</strong> steps
            </div>
        </div>

        <!-- Distance Comparison -->
        <div style="background: #FFFFFF; border: 1px solid var(--border-subtle); border-radius: 12px; padding: 14px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="font-size: 0.76rem; text-transform: uppercase; color: #526176; font-weight: 600;">Total Distance</span>
                {badge_html(m['total_distance_km'])}
            </div>
            <div style="display: flex; align-items: baseline; gap: 8px; margin-bottom: 6px;">
                <span style="font-size: 1.3rem; font-weight: 800; color: #172B4D;">{m['total_distance_km']['period1_val']:.1f}</span>
                <span style="font-size: 0.8rem; color: #64748B;">vs {m['total_distance_km']['period2_val']:.1f} km</span>
            </div>
            <div style="font-size: 0.72rem; color: #526176;">
                Delta: <strong style="color: {'#0891B2' if m['total_distance_km']['abs_diff'] >= 0 else '#DC2626'};">{'+' if m['total_distance_km']['abs_diff'] > 0 else ''}{m['total_distance_km']['abs_diff']:.1f}</strong> km
            </div>
        </div>

        <!-- Active Minutes Comparison -->
        <div style="background: #FFFFFF; border: 1px solid var(--border-subtle); border-radius: 12px; padding: 14px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="font-size: 0.76rem; text-transform: uppercase; color: #526176; font-weight: 600;">Active Time</span>
                {badge_html(m['total_active_minutes'])}
            </div>
            <div style="display: flex; align-items: baseline; gap: 8px; margin-bottom: 6px;">
                <span style="font-size: 1.3rem; font-weight: 800; color: #172B4D;">{m['total_active_minutes']['period1_val']:,}</span>
                <span style="font-size: 0.8rem; color: #64748B;">vs {m['total_active_minutes']['period2_val']:,} min</span>
            </div>
            <div style="font-size: 0.72rem; color: #526176;">
                Delta: <strong style="color: {'#7C3AED' if m['total_active_minutes']['abs_diff'] >= 0 else '#DC2626'};">{'+' if m['total_active_minutes']['abs_diff'] > 0 else ''}{m['total_active_minutes']['abs_diff']:,}</strong> min
            </div>
        </div>

        <!-- Calories Comparison -->
        <div style="background: #FFFFFF; border: 1px solid var(--border-subtle); border-radius: 12px; padding: 14px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="font-size: 0.76rem; text-transform: uppercase; color: #526176; font-weight: 600;">Calories Burned</span>
                {badge_html(m['total_calories'])}
            </div>
            <div style="display: flex; align-items: baseline; gap: 8px; margin-bottom: 6px;">
                <span style="font-size: 1.3rem; font-weight: 800; color: #172B4D;">{m['total_calories']['period1_val']:,}</span>
                <span style="font-size: 0.8rem; color: #64748B;">vs {m['total_calories']['period2_val']:,} kcal</span>
            </div>
            <div style="font-size: 0.72rem; color: #526176;">
                Delta: <strong style="color: {'#EA580C' if m['total_calories']['abs_diff'] >= 0 else '#DC2626'};">{'+' if m['total_calories']['abs_diff'] > 0 else ''}{m['total_calories']['abs_diff']:,}</strong> kcal
            </div>
        </div>

        <!-- Daily Average Steps Comparison -->
        <div style="background: #FFFFFF; border: 1px solid var(--border-subtle); border-radius: 12px; padding: 14px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="font-size: 0.76rem; text-transform: uppercase; color: #526176; font-weight: 600;">Daily Avg Steps</span>
                {badge_html(m['avg_daily_steps'])}
            </div>
            <div style="display: flex; align-items: baseline; gap: 8px; margin-bottom: 6px;">
                <span style="font-size: 1.3rem; font-weight: 800; color: #172B4D;">{m['avg_daily_steps']['period1_val']:,}</span>
                <span style="font-size: 0.8rem; color: #64748B;">vs {m['avg_daily_steps']['period2_val']:,} /day</span>
            </div>
            <div style="font-size: 0.72rem; color: #526176;">
                Delta: <strong style="color: {'#2563EB' if m['avg_daily_steps']['abs_diff'] >= 0 else '#DC2626'};">{'+' if m['avg_daily_steps']['abs_diff'] > 0 else ''}{m['avg_daily_steps']['abs_diff']:,}</strong> steps/day
            </div>
        </div>
    </div>
</div>"""

    st.html(comparison_grid)
