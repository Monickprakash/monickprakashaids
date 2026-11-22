"""FITPULSE sidebar branding and core navigation."""

from typing import Optional, Tuple

import pandas as pd
import streamlit as st


NAV_OPTIONS = [
    "⚡ Overview",
    "📊 Analytics",
    "🗓️ Activity History",
    "🎯 Goals",
]


def render_sidebar(
    df: Optional[pd.DataFrame] = None,
) -> Tuple[str, pd.DataFrame]:
    """Render the core navigation and return the selected page and activity data."""
    activity = df.copy() if df is not None else pd.DataFrame()
    current_page = st.session_state.get("current_page")
    if current_page not in NAV_OPTIONS:
        current_page = NAV_OPTIONS[0]
        st.session_state["current_page"] = current_page

    with st.sidebar:
        st.html(
            """<div class="sidebar-brand-container">
    <div class="brand-icon-badge">⚡</div>
    <div>
        <div class="brand-text-title">FITPULSE</div>
        <div class="brand-text-tagline">Visualize Your Progress</div>
    </div>
</div>"""
        )
        st.html('<div class="nav-section-title">Navigation</div>')
        selected_page = st.radio(
            "Navigation Menu",
            options=NAV_OPTIONS,
            index=NAV_OPTIONS.index(current_page),
            label_visibility="collapsed",
            key="nav_radio_selection",
        )
        st.session_state["current_page"] = selected_page

    return selected_page, activity
