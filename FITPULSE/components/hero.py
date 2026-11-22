"""FITPULSE Hero Welcome Banner Component.

Phase 4: Smart Fitness Analytics.
Displays welcoming hero banner with dynamic dataset statistics.
"""

from typing import Optional
import pandas as pd
import streamlit as st
from utils.data_processor import (
    calculate_average_daily_steps,
    get_dataset_date_bounds,
)


def render_hero(df: Optional[pd.DataFrame] = None, target_steps: int = 10000) -> None:
    """Render the hero welcome panel with gradient lighting, title, and dynamic metadata.

    Args:
        df: Optional DataFrame with fitness records to display real date window and status.
        target_steps: User-adjustable daily step objective.
    """
    if df is not None and not df.empty:
        min_date, max_date = get_dataset_date_bounds(df)
        if min_date and max_date:
            window_text = f"{min_date.strftime('%b %d')} – {max_date.strftime('%b %d, %Y')} ({len(df)} Days)"
        else:
            window_text = f"{len(df)} Days Recorded"

        avg_steps = calculate_average_daily_steps(df)
        if avg_steps >= target_steps:
            status_text = "Target Exceeded"
            status_color = "#38BDF8"
        elif avg_steps >= int(target_steps * 0.75):
            status_text = "Optimal Cadence"
            status_color = "#38BDF8"
        else:
            status_text = "Active Tracking"
            status_color = "#38BDF8"
        tracking_tag = "Live Analytics Active"
    else:
        window_text = "No Filtered Records"
        status_text = "Awaiting Data"
        status_color = "#D9B56B"
        tracking_tag = "Dataset Inactive"

    html_content = f"""<div class="hero-container">
    <div class="hero-content">
        <div class="hero-status-tag">
            <span style="display: inline-block; width: 6px; height: 6px; border-radius: 50%; background: #38BDF8;"></span>
            {tracking_tag}
        </div>
        <h1 class="hero-title">Welcome back, athlete. <span>Keep moving.</span></h1>
        <p class="hero-subtitle">
            Turn everyday movement into meaningful insights. Explore physical activity patterns, 
            track progress toward personal wellness targets, and celebrate consistency milestones.
        </p>
        <div class="hero-meta-row">
            <div class="hero-meta-item">
                <span>🎯 Daily Step Goal:</span>
                <strong>{target_steps:,} steps</strong>
            </div>
            <div class="hero-meta-item">
                <span>📅 Window:</span>
                <strong>{window_text}</strong>
            </div>
            <div class="hero-meta-item">
                <span>⚡ Status:</span>
                <strong style="color: {status_color};">{status_text}</strong>
            </div>
        </div>
    </div>
</div>"""
    st.html(html_content)
