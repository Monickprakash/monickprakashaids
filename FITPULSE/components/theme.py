"""FITPULSE UI Theme and Plotly Template Utilities."""

from pathlib import Path
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CSS_FILE_PATH = PROJECT_ROOT / "assets" / "styles.css"


def inject_custom_css() -> None:
    """Inject the external CSS design system into the Streamlit session."""
    if CSS_FILE_PATH.exists():
        with open(CSS_FILE_PATH, "r", encoding="utf-8") as f:
            css_content = f.read()
        st.html(f"<style>{css_content}</style>")
    else:
        st.warning("Custom CSS file not found at assets/styles.css")


def get_plotly_layout_defaults() -> dict:
    """Return common Plotly layout properties matching the light dashboard theme."""
    return {
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {
            "family": "Plus Jakarta Sans, sans-serif",
            "color": "#344054",
            "size": 12,
        },
        "hovermode": "x unified",
        "margin": {"l": 16, "r": 16, "t": 20, "b": 16},
        "xaxis": {
            "showgrid": True,
            "gridcolor": "#E8EDF4",
            "zeroline": False,
            "linecolor": "#D7DEE8",
            "tickfont": {"color": "#667085"},
        },
        "yaxis": {
            "showgrid": True,
            "gridcolor": "#E8EDF4",
            "zeroline": False,
            "linecolor": "#D7DEE8",
            "tickfont": {"color": "#667085"},
        },
        "hoverlabel": {
            "bgcolor": "#FFFFFF",
            "bordercolor": "#2563EB",
            "font": {"family": "Plus Jakarta Sans, sans-serif", "color": "#172B4D", "size": 12},
        },
    }
