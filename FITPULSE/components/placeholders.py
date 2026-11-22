"""FITPULSE Unfinished Section Placeholders."""

import streamlit as st


def render_placeholder(title: str, icon: str, phase_label: str, description: str) -> None:
    """Render a styled placeholder card for navigation sections scheduled for future phases.

    Args:
        title: Title of the view.
        icon: Display emoji or icon.
        phase_label: Development phase that will introduce this feature.
        description: Description of the intended functionality.
    """
    html_content = f"""<div class="placeholder-container">
    <div class="placeholder-icon">{icon}</div>
    <div class="placeholder-title">{title}</div>
    <div class="placeholder-desc">{description}</div>
    <div class="placeholder-badge">
        <span>⚡ Scheduled Implementation: {phase_label}</span>
    </div>
</div>"""
    st.html(html_content)
