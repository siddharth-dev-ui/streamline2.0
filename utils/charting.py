"""Shared Plotly chart helpers."""

from __future__ import annotations

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from utils.theme import FONT_FAMILY, get_theme


def themed_layout(fig: go.Figure, *, height: int = 420) -> go.Figure:
    """Apply the active Streamline theme to a Plotly figure."""
    theme = get_theme()
    fig.update_layout(
        height=height,
        margin=dict(l=0, r=0, t=24, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=theme["text"], family=FONT_FAMILY),
        legend=dict(font=dict(color=theme["text_muted"])),
        hovermode="x unified",
    )
    fig.update_xaxes(
        gridcolor=theme["border"],
        linecolor=theme["border"],
        tickfont=dict(color=theme["text_muted"]),
    )
    fig.update_yaxes(
        gridcolor=theme["border"],
        linecolor=theme["border"],
        tickfont=dict(color=theme["text_muted"]),
    )
    return fig


def make_subplot_figure(rows: int, row_heights: list[float], titles: list[str]) -> go.Figure:
    """Create a themed subplot figure."""
    theme = get_theme()
    fig = make_subplots(
        rows=rows,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.06,
        row_heights=row_heights,
        subplot_titles=titles,
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=theme["text"], family=FONT_FAMILY),
        legend=dict(font=dict(color=theme["text_muted"])),
        hovermode="x unified",
        margin=dict(l=0, r=0, t=40, b=0),
    )
    for i in range(1, rows + 1):
        fig.update_xaxes(gridcolor=theme["border"], linecolor=theme["border"], row=i, col=1)
        fig.update_yaxes(gridcolor=theme["border"], linecolor=theme["border"], row=i, col=1)
    return fig
