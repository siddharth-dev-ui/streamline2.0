"""Branded loading screen for Streamline — always auto-dismisses."""

from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components

from utils.theme import DISPLAY_FONT, FONT_FAMILY, get_theme


def show_boot_loader(message: str = "Loading Streamline…") -> None:
    """
    Show a full-viewport branded loader in the parent document.

    Uses a components.html bridge so the overlay lives on the real page
    (not trapped in a zero-height iframe). Auto-removes after max 4s even
    if dismiss_boot_loader() never runs.
    """
    t = get_theme()
    message_js = message.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")

    components.html(
        f"""
<!DOCTYPE html>
<html><head><meta charset="utf-8" /></head>
<body>
<script>
(function () {{
  const message = `{message_js}`;
  const docs = [];
  try {{ docs.push(document); }} catch (e) {{}}
  try {{ if (window.parent && window.parent.document) docs.push(window.parent.document); }} catch (e) {{}}

  const css = `
    #sl-boot-loader {{
      position: fixed;
      inset: 0;
      z-index: 2147483646;
      display: grid;
      place-items: center;
      background:
        radial-gradient(900px 480px at 12% -8%, {t["accent_soft"]}, transparent 55%),
        radial-gradient(700px 420px at 92% 8%, {t["accent_glow"]}, transparent 50%),
        {t["bg"]};
      font-family: {FONT_FAMILY};
      color: {t["text"]};
      transition: opacity 0.35s ease, visibility 0.35s ease;
    }}
    #sl-boot-loader.sl-hide {{
      opacity: 0;
      visibility: hidden;
      pointer-events: none;
    }}
    #sl-boot-loader .sl-card {{ text-align: center; padding: 1.5rem; }}
    #sl-boot-loader .sl-brand {{
      font-family: {DISPLAY_FONT};
      font-style: italic;
      font-size: 2.4rem;
      letter-spacing: -0.02em;
      text-transform: lowercase;
      margin-bottom: 1.25rem;
      background: linear-gradient(135deg, {t["text"]} 18%, {t["accent"]} 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }}
    #sl-boot-loader .sl-ring {{
      width: 42px; height: 42px; margin: 0 auto 1rem;
      border-radius: 50%;
      border: 2.5px solid {t["border"]};
      border-top-color: {t["accent"]};
      animation: sl-spin 0.75s linear infinite;
    }}
    #sl-boot-loader .sl-msg {{
      color: {t["text_muted"]};
      font-size: 0.95rem;
      font-weight: 500;
    }}
    @keyframes sl-spin {{ to {{ transform: rotate(360deg); }} }}
  `;

  function ensure(doc) {{
    try {{
      let style = doc.getElementById("sl-boot-loader-style");
      if (!style) {{
        style = doc.createElement("style");
        style.id = "sl-boot-loader-style";
        (doc.head || doc.documentElement).appendChild(style);
      }}
      style.textContent = css;

      let el = doc.getElementById("sl-boot-loader");
      if (!el) {{
        el = doc.createElement("div");
        el.id = "sl-boot-loader";
        el.innerHTML = '<div class="sl-card"><div class="sl-brand">streamline</div><div class="sl-ring" aria-hidden="true"></div><div class="sl-msg"></div></div>';
        (doc.body || doc.documentElement).appendChild(el);
      }}
      el.classList.remove("sl-hide");
      const msg = el.querySelector(".sl-msg");
      if (msg) msg.textContent = message;

      // Hard failsafe — never leave the overlay up forever.
      if (!doc.documentElement.dataset.slBootTimer) {{
        doc.documentElement.dataset.slBootTimer = "1";
        setTimeout(() => {{
          const node = doc.getElementById("sl-boot-loader");
          if (node) {{
            node.classList.add("sl-hide");
            setTimeout(() => node.remove(), 400);
          }}
        }}, 4000);
      }}
    }} catch (err) {{}}
  }}

  docs.forEach(ensure);
}})();
</script>
</body></html>
""",
        height=0,
        width=0,
    )


def dismiss_boot_loader() -> None:
    """Fade out and remove the boot loader as soon as the app is ready."""
    components.html(
        """
<!DOCTYPE html>
<html><body>
<script>
(function () {
  function dismiss(doc) {
    try {
      const el = doc.getElementById("sl-boot-loader");
      if (!el) return;
      el.classList.add("sl-hide");
      setTimeout(() => { try { el.remove(); } catch (e) {} }, 400);
    } catch (err) {}
  }
  const docs = [];
  try { docs.push(document); } catch (e) {}
  try { if (window.parent && window.parent.document) docs.push(window.parent.document); } catch (e) {}
  docs.forEach(dismiss);
  setTimeout(() => docs.forEach(dismiss), 100);
  setTimeout(() => docs.forEach(dismiss), 500);
})();
</script>
</body></html>
""",
        height=0,
        width=0,
    )


def render_skeleton(message: str = "Loading…") -> None:
    """Inline skeleton block for section-level loading states."""
    t = get_theme()
    st.markdown(
        f"""
        <div role="status" aria-live="polite"
             style="border:1px solid {t["border"]};border-radius:16px;background:{t["bg_secondary"]};
                    padding:1.1rem 1.2rem;margin:0.75rem 0 1.25rem;font-family:{FONT_FAMILY};
                    box-shadow:{t["btn_shadow"]};color:{t["text_muted"]};">
          <div style="margin-bottom:0.85rem;font-weight:500;">{message}</div>
          <div style="height:12px;width:62%;border-radius:999px;background:{t["bg_soft"]};margin:0.55rem 0;"></div>
          <div style="height:12px;width:88%;border-radius:999px;background:{t["bg_soft"]};margin:0.55rem 0;"></div>
          <div style="height:12px;width:74%;border-radius:999px;background:{t["bg_soft"]};margin:0.55rem 0;"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
