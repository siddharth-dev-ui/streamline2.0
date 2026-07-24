"""Landing page gate for Streamline (works locally and on Streamlit Cloud)."""

from __future__ import annotations

from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

LANDING_DIR = Path(__file__).resolve().parent.parent / "landing"
ENTERED_KEY = "entered_app"


def should_show_landing() -> bool:
    """Return True when the marketing landing should be shown instead of the app."""
    params = st.query_params
    if params.get("app") == "1":
        st.session_state[ENTERED_KEY] = True
    if params.get("landing") == "1":
        st.session_state[ENTERED_KEY] = False
    return not st.session_state.get(ENTERED_KEY, False)


def enter_app() -> None:
    """Mark the user as having entered the product UI."""
    st.session_state[ENTERED_KEY] = True
    try:
        st.query_params["app"] = "1"
    except Exception:
        pass


def _inline_landing_html() -> str:
    html_path = LANDING_DIR / "index.html"
    css_path = LANDING_DIR / "styles.css"
    js_path = LANDING_DIR / "script.js"

    if not html_path.exists():
        raise FileNotFoundError(f"Landing page not found at {html_path}")

    html = html_path.read_text(encoding="utf-8")
    css = css_path.read_text(encoding="utf-8") if css_path.exists() else ""
    js = js_path.read_text(encoding="utf-8") if js_path.exists() else ""

    # Avoid prematurely closing the injected <style> / <script> blocks.
    css = css.replace("</style>", "<\\/style>")
    js = js.replace("</script>", "<\\/script>")

    html = html.replace(
        '<link rel="stylesheet" href="styles.css" />',
        f"<style>\n{css}\n</style>",
    )
    # Flag must be set BEFORE landing/script.js runs.
    html = html.replace(
        '<script src="script.js"></script>',
        "<script>window.STREAMLIT_EMBED = true;</script>"
        f"<script>\n{js}\n</script>",
    )

    # Normalize all “enter app” targets for Streamlit (Cloud + local).
    for old in ('href="../?app=1"', 'href="../"', 'href="/?app=1"'):
        html = html.replace(old, 'href="?app=1" data-enter-app="1"')

    bridge = """
<script>
window.STREAMLIT_EMBED = true;
(function () {
  try {
    document.documentElement.classList.add("streamlit-embed");
    if (document.body) document.body.classList.add("streamlit-embed");
    document.querySelectorAll(".reveal").forEach(function (el) {
      el.classList.add("visible");
    });
  } catch (e) {}

  function enterApp(event) {
    if (event) event.preventDefault();
    var targets = [];
    try { targets.push(window.top); } catch (e) {}
    try { targets.push(window.parent); } catch (e) {}
    targets.push(window);
    for (var i = 0; i < targets.length; i++) {
      var target = targets[i];
      if (!target || !target.location) continue;
      try {
        var url = new URL(target.location.href);
        url.searchParams.set("app", "1");
        url.searchParams.delete("landing");
        target.location.href = url.toString();
        return;
      } catch (err) {}
    }
    try { window.location.href = "?app=1"; } catch (err2) {}
  }

  document.querySelectorAll("[data-enter-app], a[href*='app=1']").forEach(function (el) {
    el.addEventListener("click", enterApp);
  });

  window.streamlineEnterApp = enterApp;

  // Re-apply after a tick in case the main script runs later.
  setTimeout(function () {
    document.querySelectorAll(".reveal").forEach(function (el) {
      el.classList.add("visible");
    });
  }, 50);
  setTimeout(function () {
    document.querySelectorAll(".reveal").forEach(function (el) {
      el.classList.add("visible");
    });
  }, 400);
})();
</script>
"""
    if "</body>" in html:
        return html.replace("</body>", bridge + "</body>")
    return html + bridge


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
          #MainMenu, footer, .stDeployButton, .stAppDeployButton {
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
          .sl-landing-fallback {
            position: sticky;
            bottom: 0;
            z-index: 20;
            display: flex;
            gap: 0.75rem;
            justify-content: center;
            align-items: center;
            padding: 0.85rem 1rem;
            background: rgba(250, 246, 234, 0.92);
            border-top: 1px solid rgba(28, 25, 20, 0.12);
            backdrop-filter: blur(10px);
          }
        </style>
        """,
        unsafe_allow_html=True,
    )

    try:
        components.html(_inline_landing_html(), height=7200, scrolling=True)
    except Exception as exc:
        st.error("The landing page could not be loaded.")
        st.caption(str(exc))

    # Cloud-safe live demo (Streamlit Cloud cannot reach localhost:8080).
    with st.expander("Live ticker demo (works on Streamlit Cloud)", expanded=False):
        st.caption("Educational only — not financial advice.")
        demo_q = st.text_input("Ticker", placeholder="e.g. MSFT", key="cloud_landing_demo_ticker")
        if st.button("Analyze ticker", key="cloud_landing_demo_go", type="primary"):
            try:
                from landing.demo_recommend import build_demo_recommendation

                with st.spinner("Fetching live market data…"):
                    result = build_demo_recommendation(demo_q)
                st.subheader(f"{result.get('recommendation', '—')} · {result.get('ticker', '')}")
                st.write(
                    f"**{result.get('company', '')}** — confidence {result.get('confidence', '—')}%"
                )
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.markdown("**Technical**")
                    st.write(result.get("technical_label", ""))
                    st.caption(result.get("technical_detail", ""))
                with c2:
                    st.markdown("**Fundamental**")
                    st.write(result.get("fundamental_label", ""))
                    st.caption(result.get("fundamental_detail", ""))
                with c3:
                    st.markdown("**Risk**")
                    st.write(result.get("risk_label", ""))
                    st.caption(result.get("risk_detail", ""))
                if result.get("price") is not None:
                    st.caption(f"Live price ≈ ${float(result['price']):.2f}")
            except ValueError as exc:
                st.warning(str(exc))
            except Exception:
                st.error("Unable to fetch live data right now. Try again in a moment.")

    # Always-visible Cloud-safe entry (iframe links can be blocked by the browser).
    cols = st.columns([2, 1, 2])
    with cols[1]:
        if st.button("Enter Streamline", type="primary", use_container_width=True, key="enter_app_fallback"):
            enter_app()
            st.rerun()
