"""Landing page gate for Streamline."""

from __future__ import annotations

from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

LANDING_DIR = Path(__file__).resolve().parent.parent / "landing"
ENTERED_KEY = "entered_app"


def should_show_landing() -> bool:
    """Return True when the marketing landing should be shown instead of the app."""
    if st.query_params.get("app") == "1":
        st.session_state[ENTERED_KEY] = True
    if st.query_params.get("landing") == "1":
        st.session_state[ENTERED_KEY] = False
    return not st.session_state.get(ENTERED_KEY, False)


def _inline_landing_html() -> str:
    html = (LANDING_DIR / "index.html").read_text(encoding="utf-8")
    css = (LANDING_DIR / "styles.css").read_text(encoding="utf-8")
    js = (LANDING_DIR / "script.js").read_text(encoding="utf-8")

    # Avoid prematurely closing the injected <style> / <script> blocks.
    css = css.replace("</style>", "<\\/style>")
    js = js.replace("</script>", "<\\/script>")

    html = html.replace(
        '<link rel="stylesheet" href="styles.css" />',
        f"<style>\n{css}\n</style>",
    )
    html = html.replace('<script src="script.js"></script>', f"<script>\n{js}\n</script>")

    html = html.replace('href="../?app=1"', 'href="?app=1" data-enter-app="1"')
    html = html.replace('href="../"', 'href="?app=1" data-enter-app="1"')

    bridge = """
<script>
document.querySelectorAll('[data-enter-app]').forEach((el) => {
  el.addEventListener('click', (event) => {
    event.preventDefault();
    const target = window.top || window.parent || window;
    try {
      const url = new URL(target.location.href);
      url.searchParams.set('app', '1');
      target.location.href = url.toString();
    } catch (err) {
      window.location.href = '?app=1';
    }
  });
});
</script>
"""
    return html.replace("</body>", bridge + "</body>")


def render_landing() -> None:
    """Render the full marketing landing page inside Streamlit."""
    st.markdown(
        """
        <style>
          [data-testid="stSidebar"],
          [data-testid="stHeader"],
          [data-testid="stToolbar"],
          [data-testid="stDecoration"],
          [data-testid="stStatusWidget"],
          #MainMenu, footer, .stDeployButton {
            display: none !important;
          }
          .block-container {
            padding: 0 !important;
            max-width: 100% !important;
          }
          [data-testid="stAppViewContainer"] > .main {
            padding: 0 !important;
          }
          div[data-testid="stVerticalBlock"] > div:has(iframe) {
            width: 100% !important;
          }
          iframe {
            border: none !important;
            width: 100% !important;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )
    components.html(_inline_landing_html(), height=7800, scrolling=True)
