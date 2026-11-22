"""FITPULSE Recent Activity History Component."""

import pandas as pd
import streamlit as st


def render_recent_activity(df: pd.DataFrame, target_steps: int = 10000) -> None:
    """Render a table of recent activity records labeled as sample data.

    Args:
        df: DataFrame containing the 7-day fitness records.
    """
    if df is None or df.empty:
        st.info("No activity records available to display.")
        return

    # Sort descending by date so most recent comes first
    sorted_df = df.sort_values(by="date", ascending=False).copy()

    # Build HTML table with progress indicators
    rows_html = []
    for _, row in sorted_df.iterrows():
        steps = int(row["steps"])
        pct = min(100, int((steps / target_steps) * 100)) if target_steps > 0 else 0
        dist = f"{row['distance_km']:.1f}"
        cal = int(row["calories"])
        mins = int(row["active_minutes"])
        date_str = str(row["date"])

        row_str = f"""<tr class="activity-feed-row">
            <td data-label="Date">{date_str}</td>
            <td data-label="Steps" style="font-weight: 700; color: #FFFFFF;">{steps:,}</td>
            <td data-label="Progress">
        <div class="mini-progress-track">
            <div class="mini-progress-fill" style="width: {pct}%;"></div>
        </div>
    </td>
            <td data-label="Target">{pct}%</td>
            <td data-label="Distance">{dist} km</td>
            <td data-label="Calories">{cal:,} kcal</td>
            <td data-label="Active Time">{mins} min</td>
</tr>"""
        rows_html.append(row_str)

    table_body = "\n".join(rows_html)

    html_content = f"""<div class="section-header-row">
    <h3 class="section-title">
        <span>🗓️</span> Recent Activity Log
    </h3>
    <span class="section-tag tag-placeholder">{len(sorted_df)} Records • Filtered Window</span>
</div>
<div class="glass-panel" style="padding: 14px 18px;">
    <div class="table-responsive-wrap">
        <table class="activity-feed-table">
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Steps</th>
                    <th>Progress</th>
                    <th>Target</th>
                    <th>Distance</th>
                    <th>Calories</th>
                    <th>Active Time</th>
                </tr>
            </thead>
            <tbody>
                {table_body}
            </tbody>
        </table>
    </div>
</div>"""

    st.html(html_content)
