"""FITPULSE Top Navigation Header Component."""

from datetime import date, datetime
from typing import Optional

import streamlit as st


def render_header(
    current_section: str = "Overview",
    data_mode: str = "Sample data",
    selected_date: Optional[date] = None,
) -> None:
    """Render the active section title, date, and data source.

    Args:
        current_section: The name of the active view.
    """
    clean_title = current_section.partition(" ")[2] or current_section
    current_date_str = (
        selected_date.strftime("%A, %b %d, %Y")
        if selected_date is not None
        else datetime.now().strftime("%A, %b %d, %Y")
    )
    is_overview = clean_title == "Overview"

    overview_welcome = ""
    if is_overview:
        overview_welcome = (
            '<div class="overview-welcome">'
            '<span class="overview-greeting">YOUR ACTIVITY</span>'
            '<strong>Move more. Feel better.</strong>'
            "</div>"
        )

    html_content = f"""<div class="top-header-bar{' top-header-overview' if is_overview else ''}">
    <div class="top-header-left">
        <span class="top-page-badge">FITPULSE</span>
        <span class="top-page-divider">/</span>
        <h2 class="top-page-title">{clean_title}</h2>
        {overview_welcome}
    </div>
    <div class="top-header-right">
        <div class="pill-date">📅 {current_date_str}</div>
        <div class="pill-badge pill-sample">
            <span class="pill-pulse"></span>
            <span>{data_mode}</span>
        </div>
    </div>
</div>"""
    st.html(html_content)
