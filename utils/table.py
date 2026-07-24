"""Themed HTML tables that follow Streamline light/dark palettes."""

from __future__ import annotations

from html import escape
from typing import Any

import streamlit as st


def render_themed_table(rows: list[dict[str, Any]], *, max_height: int = 420) -> None:
    """Render a scrollable HTML table styled by the active Streamline theme."""
    if not rows:
        st.caption("No rows to display.")
        return

    columns = list(rows[0].keys())
    header = "".join(f"<th>{escape(str(column))}</th>" for column in columns)
    body_parts: list[str] = []
    for row in rows:
        cells = "".join(f"<td>{escape(str(row.get(column, '—')))}</td>" for column in columns)
        body_parts.append(f"<tr>{cells}</tr>")

    st.markdown(
        f"""
        <div class="sl-table-wrap" style="max-height:{max_height}px">
          <table class="sl-table">
            <thead><tr>{header}</tr></thead>
            <tbody>{"".join(body_parts)}</tbody>
          </table>
        </div>
        """,
        unsafe_allow_html=True,
    )
