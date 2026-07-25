"""Theme configuration and styling for Streamline."""

import streamlit as st

THEME_KEY = "theme"
DEFAULT_THEME = "dark"
THEME_MIGRATION_KEY = "_theme_dark_default_v2"

FONT_FAMILY = "Montserrat, sans-serif"
DISPLAY_FONT = '"Instrument Serif", Georgia, serif'
LILAC = {
    "50": "#FAF5FF",
    "100": "#F3E8FF",
    "200": "#E9D5FF",
    "300": "#D8B4FE",
    "400": "#C4A1FF",
    "500": "#A855F7",
    "600": "#9333EA",
    "700": "#7E22CE",
}

THEMES = {
    "light": {
        # Match landing cream / jasmine system
        "bg": "#F3EEE0",
        "bg_secondary": "#FAF6EA",
        "bg_soft": "#EBE4D2",
        "text": "#12110F",
        "text_muted": "#5C574C",
        "border": "rgba(28, 25, 20, 0.14)",
        "border_strong": "rgba(28, 25, 20, 0.20)",
        "accent": LILAC["700"],
        "accent_fg": "#FFFFFF",
        "accent_soft": "rgba(126, 34, 206, 0.12)",
        "accent_muted": LILAC["600"],
        "accent_glow": "rgba(126, 34, 206, 0.22)",
        "input_bg": "#FFFDF8",
        "sidebar_bg": "#F7F1E3",
        "nav_hover": "#EFE8D6",
        "nav_active": LILAC["700"],
        "link": LILAC["700"],
        "chart": [LILAC["700"], LILAC["600"], LILAC["500"], LILAC["400"], LILAC["300"], "#6D28D9"],
        "chart_fill": "rgba(126, 34, 206, 0.10)",
        "color_scheme": "light",
        "btn_shadow": "0 1px 2px rgba(28, 25, 20, 0.04), 0 10px 28px rgba(28, 25, 20, 0.06)",
        "btn_shadow_hover": "0 8px 28px rgba(126, 34, 206, 0.18)",
        "icon_bg": "rgba(28, 25, 20, 0.04)",
        "icon_hover": "rgba(126, 34, 206, 0.12)",
        "dropdown_shadow": "0 16px 40px rgba(28, 25, 20, 0.14)",
        "dropdown_bg": "#FAF6EA",
        "glass": "rgba(250, 246, 234, 0.78)",
    },
    "dark": {
        # Match landing charcoal system
        "bg": "#222226",
        "bg_secondary": "#2C2C32",
        "bg_soft": "#33333A",
        "text": "#F3F2EF",
        "text_muted": "#A8A6A0",
        "border": "rgba(255, 255, 255, 0.12)",
        "border_strong": "rgba(255, 255, 255, 0.18)",
        "accent": LILAC["400"],
        "accent_fg": "#1A1520",
        "accent_soft": "rgba(196, 161, 255, 0.14)",
        "accent_muted": "#D4B8FF",
        "accent_glow": "rgba(196, 161, 255, 0.28)",
        "input_bg": "#2A2A30",
        "sidebar_bg": "#1E1E22",
        "nav_hover": "#33333A",
        "nav_active": LILAC["400"],
        "link": LILAC["400"],
        "chart": [LILAC["400"], LILAC["300"], LILAC["500"], LILAC["200"], LILAC["600"], "#DDD6FE"],
        "chart_fill": "rgba(196, 161, 255, 0.14)",
        "color_scheme": "dark",
        "btn_shadow": "0 1px 2px rgba(0, 0, 0, 0.25), 0 14px 36px rgba(0, 0, 0, 0.28)",
        "btn_shadow_hover": "0 10px 28px rgba(196, 161, 255, 0.22)",
        "icon_bg": "rgba(255, 255, 255, 0.06)",
        "icon_hover": "rgba(196, 161, 255, 0.18)",
        "dropdown_shadow": "0 18px 44px rgba(0, 0, 0, 0.45)",
        "dropdown_bg": "#2C2C32",
        "glass": "rgba(44, 44, 50, 0.78)",
    },
}


def init_theme() -> str:
    """Initialize theme in session state."""
    # One-time migration: older sessions defaulted to light.
    if THEME_MIGRATION_KEY not in st.session_state:
        st.session_state[THEME_KEY] = DEFAULT_THEME
        st.session_state[THEME_MIGRATION_KEY] = True
    elif THEME_KEY not in st.session_state:
        st.session_state[THEME_KEY] = DEFAULT_THEME
    return st.session_state[THEME_KEY]


def toggle_theme() -> str:
    """Switch between light and dark mode."""
    current = init_theme()
    st.session_state[THEME_KEY] = "light" if current == "dark" else "dark"
    return st.session_state[THEME_KEY]


def get_theme() -> dict:
    """Return the active theme palette."""
    mode = init_theme()
    return THEMES[mode]


def _build_css(t: dict) -> str:
    """Build landing-aligned Streamline stylesheet (cream/charcoal + lilac)."""
    return f"""
<style id="streamline-theme">
    @import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Montserrat:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap');

    @keyframes streamline-fade-up {{
        from {{ opacity: 0; transform: translateY(10px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}

    @keyframes streamline-nav-in {{
        from {{ opacity: 0.55; transform: translateX(-6px) scale(0.98); }}
        to {{ opacity: 1; transform: translateX(0) scale(1); }}
    }}

    @keyframes streamline-soft-pulse {{
        0%, 100% {{ box-shadow: 0 4px 14px {t["accent_glow"]}; }}
        50% {{ box-shadow: 0 6px 22px {t["accent_glow"]}; }}
    }}

    :root {{
        --primary-color: {t["accent"]} !important;
        --background-color: {t["bg"]} !important;
        --secondary-background-color: {t["bg_secondary"]} !important;
        --text-color: {t["text"]} !important;
        --border-color: {t["border"]} !important;
        --accent: {t["accent"]};
        --accent-soft: {t["accent_soft"]};
        --accent-glow: {t["accent_glow"]};
        --sl-dropdown-bg: {t["dropdown_bg"]};
        --sl-glass: {t["glass"]};
        color-scheme: {t["color_scheme"]} !important;
    }}

    html, body, .stApp {{
        color-scheme: {t["color_scheme"]} !important;
    }}

    /* One atmospheric layer — nested scroll panes must stay transparent
       or you get “gradient sidebars” while the center content scrolls. */
    html, body, .stApp {{
        background-color: {t["bg"]} !important;
        background-image:
            radial-gradient(900px 480px at 12% -8%, {t["accent_soft"]}, transparent 55%),
            radial-gradient(700px 420px at 92% 8%, {t["accent_glow"]}, transparent 50%),
            linear-gradient(180deg, {t["bg"]} 0%, {t["bg"]} 100%) !important;
        background-attachment: fixed !important;
        background-repeat: no-repeat !important;
        color: {t["text"]} !important;
        font-family: {FONT_FAMILY} !important;
    }}

    [data-testid="stAppViewContainer"],
    [data-testid="stAppViewBlockContainer"], section.main,
    [data-testid="stMain"], [data-testid="stMainBlockContainer"],
    [data-testid="stBottomBlockContainer"], .block-container,
    [data-testid="stVerticalBlock"],
    [data-testid="stHorizontalBlock"] {{
        background: transparent !important;
        background-image: none !important;
        background-color: transparent !important;
        color: {t["text"]} !important;
        font-family: {FONT_FAMILY} !important;
    }}

    /* Transparent header — no opaque strip */
    header[data-testid="stHeader"],
    [data-testid="stHeader"],
    [data-testid="stHeader"] > div,
    [data-testid="stToolbar"],
    .stApp > header,
    .stApp header {{
        background: transparent !important;
        background-color: transparent !important;
        background-image: none !important;
        backdrop-filter: none !important;
        -webkit-backdrop-filter: none !important;
        box-shadow: none !important;
        border: none !important;
        border-bottom: none !important;
    }}

    /* Keep toolbar (holds sidebar expand). Only strip Deploy / chrome. */
    [data-testid="stToolbar"] {{
        display: flex !important;
        visibility: visible !important;
        opacity: 1 !important;
        height: auto !important;
        min-height: 0 !important;
        pointer-events: auto !important;
    }}

    [data-testid="stDecoration"],
    [data-testid="stStatusWidget"],
    [data-testid="stAppDeployButton"],
    [data-testid="stToolbarActions"],
    .stDeployButton,
    .stAppDeployButton,
    #MainMenu,
    footer {{
        display: none !important;
        visibility: hidden !important;
        pointer-events: none !important;
    }}

    /* Sidebar open/close controls — always visible, slightly larger */
    [data-testid="stSidebarCollapseButton"],
    [data-testid="stExpandSidebarButton"],
    [data-testid="collapsedControl"],
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="stHeader"] [data-testid="stBaseButton-headerNoPadding"],
    [data-testid="stToolbar"] [data-testid="stExpandSidebarButton"],
    [data-testid="stToolbar"] [data-testid="stBaseButton-headerNoPadding"] {{
        display: flex !important;
        visibility: visible !important;
        opacity: 1 !important;
        pointer-events: auto !important;
        height: auto !important;
        width: auto !important;
        min-width: 3.1rem !important;
        min-height: 3.1rem !important;
        max-height: none !important;
    }}

    [data-testid="stSidebarCollapseButton"] button,
    [data-testid="stExpandSidebarButton"],
    [data-testid="stSidebarCollapseButton"] [data-testid="stBaseButton-headerNoPadding"],
    [data-testid="stToolbar"] [data-testid="stExpandSidebarButton"],
    [data-testid="collapsedControl"] button {{
        min-width: 3.1rem !important;
        min-height: 3.1rem !important;
        width: 3.1rem !important;
        height: 3.1rem !important;
        border-radius: 12px !important;
        padding: 0 !important;
    }}

    [data-testid="stSidebarCollapseButton"] span[data-testid="stIconMaterial"],
    [data-testid="stExpandSidebarButton"] span[data-testid="stIconMaterial"],
    [data-testid="stSidebarCollapseButton"] svg,
    [data-testid="stExpandSidebarButton"] svg,
    [data-testid="collapsedControl"] span[data-testid="stIconMaterial"] {{
        font-size: 1.65rem !important;
        width: 1.65rem !important;
        height: 1.65rem !important;
    }}

    /* Un-hide Streamlit wrappers around the expand control */
    [data-testid="stToolbar"] > div,
    [data-testid="stToolbar"] > div > div,
    [data-testid="stToolbar"] > div > div > div {{
        display: flex !important;
        visibility: visible !important;
        opacity: 1 !important;
        height: auto !important;
        width: auto !important;
        pointer-events: auto !important;
    }}

    [data-testid="stSidebar"],
    [data-testid="stSidebarContent"], [data-testid="stSidebarUserContent"] {{
        background:
            linear-gradient(180deg, {t["sidebar_bg"]} 0%, {t["bg_secondary"]} 100%) !important;
        color: {t["text"]} !important;
    }}

    [data-testid="stSidebar"] {{
        border-right: 1px solid {t["border"]} !important;
        box-shadow: 8px 0 32px rgba(28, 25, 20, 0.04);
    }}

    .stApp *, .stApp *::before, .stApp *::after {{
        --primary-color: {t["accent"]} !important;
        --background-color: {t["bg"]} !important;
        --secondary-background-color: {t["bg_secondary"]} !important;
        --text-color: {t["text"]} !important;
        --border-color: {t["border"]} !important;
    }}

    .stApp p, .stApp label, .stApp h1, .stApp h2, .stApp h3,
    .stApp h4, .stApp h5, .stApp h6, .stApp li, .stApp small,
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] span:not([data-testid="stIconMaterial"]):not([class*="material"]),
    [data-testid="stWidgetLabel"] p,
    [data-testid="stWidgetLabel"] label,
    label[data-testid="stWidgetLabel"],
    .stApp span:not([data-testid="stIconMaterial"]):not([class*="material"]) {{
        color: {t["text"]} !important;
        font-family: {FONT_FAMILY} !important;
    }}

    /* —— Icons: keep Material ligatures, tone them to the theme —— */
    .stApp [data-testid="stIconMaterial"],
    .stApp span[class*="material"],
    .stApp i[class*="material"],
    [data-testid="stSidebarCollapseButton"] span,
    [data-testid="stBaseButton-headerNoPadding"] span,
    [data-testid="collapsedControl"] span,
    [data-testid="stExpanderToggleIcon"] span,
    [data-testid="stSelectbox"] svg,
    [data-testid="stMultiSelect"] svg,
    [data-testid="stNumberInput"] button svg,
    [data-testid="stToolbar"] svg,
    [data-testid="stHeader"] svg {{
        font-family: "Material Symbols Rounded", "Material Symbols Outlined",
            "Material Icons", "Material Icons Outlined", sans-serif !important;
        font-style: normal !important;
        font-weight: normal !important;
        letter-spacing: normal !important;
        text-transform: none !important;
        -webkit-font-smoothing: antialiased !important;
        color: {t["text_muted"]} !important;
        fill: {t["text_muted"]} !important;
        opacity: 0.92;
        transition: color 0.18s ease, fill 0.18s ease, opacity 0.18s ease !important;
    }}

    .stApp [data-testid="stIconMaterial"]:hover,
    [data-testid="stSidebarCollapseButton"]:hover span,
    [data-testid="stBaseButton-headerNoPadding"]:hover span,
    [data-testid="collapsedControl"]:hover span,
    [data-testid="stNumberInput"] button:hover svg,
    [data-testid="stSelectbox"]:hover svg {{
        color: {t["accent"]} !important;
        fill: {t["accent"]} !important;
        opacity: 1;
    }}

    /* Header / collapse icon chips */
    [data-testid="stSidebarCollapseButton"] button,
    [data-testid="stBaseButton-headerNoPadding"],
    [data-testid="collapsedControl"] button,
    [data-testid="stHeader"] button,
    [data-testid="stToolbar"] button {{
        background: {t["icon_bg"]} !important;
        border: 1px solid transparent !important;
        border-radius: 12px !important;
        box-shadow: none !important;
        min-width: 3.1rem !important;
        min-height: 3.1rem !important;
        transition: background 0.18s ease, border-color 0.18s ease, transform 0.15s ease !important;
    }}

    [data-testid="stSidebarCollapseButton"] button:hover,
    [data-testid="stBaseButton-headerNoPadding"]:hover,
    [data-testid="collapsedControl"] button:hover,
    [data-testid="stHeader"] button:hover,
    [data-testid="stToolbar"] button:hover {{
        background: {t["icon_hover"]} !important;
        border-color: {t["border"]} !important;
        transform: translateY(-1px);
    }}

    .tagline, .page-subtitle, .section-subtitle, .placeholder-sub,
    .sidebar-section, .form-section-label, .search-label, .theme-toggle-label {{
        color: {t["text_muted"]} !important;
    }}

    a, a:visited {{
        color: {t["link"]} !important;
    }}

    a:hover {{
        color: {t["accent_muted"]} !important;
    }}

    .block-container {{
        padding-top: 1.5rem;
        max-width: 860px;
        animation: streamline-fade-up 0.4s ease-out;
    }}

    .home-hero, .onboarding-hero, .page-header {{
        text-align: center;
        padding: 3.5rem 0.75rem 1.25rem;
        position: relative;
        animation: streamline-fade-up 0.5s ease-out;
    }}

    .home-hero::before {{
        content: "";
        position: absolute;
        top: 2rem;
        left: 50%;
        transform: translateX(-50%);
        width: min(520px, 90vw);
        height: 180px;
        background: radial-gradient(ellipse at center, {t["accent_glow"]} 0%, transparent 70%);
        pointer-events: none;
        z-index: 0;
    }}

    .home-hero > *, .onboarding-hero > *, .page-header > * {{
        position: relative;
        z-index: 1;
    }}

    .onboarding-hero, .page-header {{ padding: 2rem 0.75rem 1rem; }}

    .logo-text, .page-title, .sidebar-brand {{
        font-weight: 500;
        letter-spacing: -0.02em;
        color: {t["text"]} !important;
        text-transform: lowercase;
        font-family: {DISPLAY_FONT} !important;
    }}

    .section-title, .placeholder-title {{
        font-weight: 600;
        letter-spacing: -0.03em;
        color: {t["text"]} !important;
        text-transform: lowercase;
        font-family: {FONT_FAMILY} !important;
    }}

    .logo-text {{
        font-size: 3.35rem;
        font-style: italic;
        background: linear-gradient(135deg, {t["text"]} 18%, {t["accent"]} 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }}

    .page-title {{ font-size: 1.95rem; font-style: italic; }}

    .sidebar-brand {{
        font-size: 1.15rem;
        font-style: italic;
        padding: 0.05rem 0 0.45rem;
        border-bottom: 1px solid {t["border"]};
        margin-bottom: 0.45rem;
        line-height: 1.1;
        background: linear-gradient(135deg, {t["text"]} 20%, {t["accent"]} 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }}

    .sidebar-section {{
        font-size: 0.65rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin: 0.15rem 0 0.2rem;
        line-height: 1.2;
    }}

    .theme-toggle-label {{
        font-size: 0.78rem !important;
        margin: 0 0 0.2rem !important;
        line-height: 1.25;
    }}

    .search-label {{
        text-align: center;
        font-size: 1.05rem;
        margin: 0 0 0.85rem;
    }}

    section.main div[data-testid="stForm"] {{
        background: {t["glass"]} !important;
        backdrop-filter: blur(12px) saturate(1.1);
        -webkit-backdrop-filter: blur(12px) saturate(1.1);
        border: 1px solid {t["border"]} !important;
        border-radius: 18px !important;
        padding: 0.9rem 1rem 0.8rem !important;
        box-shadow: {t["btn_shadow"]} !important;
    }}

    section.main div[data-testid="stTextArea"] textarea,
    section.main div[data-testid="stTextAreaRootElement"] textarea,
    section.main textarea[aria-label="Research query"] {{
        min-height: 75px !important;
        height: 75px !important;
    }}

    [data-testid="column"]:has([data-testid="stTextInput"]),
    [data-testid="stVerticalBlockBorderWrapper"] {{
        background: {t["bg_secondary"]} !important;
        border: 1px solid {t["border"]} !important;
        border-radius: 14px !important;
        box-shadow: {t["btn_shadow"]} !important;
    }}

    /* —— Buttons: unified modern system —— */
    .stButton > button,
    button[kind="secondary"],
    [data-testid="stBaseButton-secondary"],
    [data-testid="stBaseButton-secondaryFormSubmit"] {{
        background: {t["bg_secondary"]} !important;
        color: {t["text"]} !important;
        -webkit-text-fill-color: {t["text"]} !important;
        border: 1px solid {t["border"]} !important;
        border-radius: 12px !important;
        box-shadow: {t["btn_shadow"]} !important;
        font-family: {FONT_FAMILY} !important;
        font-weight: 500 !important;
        font-size: 0.92rem !important;
        letter-spacing: 0.01em !important;
        min-height: 2.55rem !important;
        padding: 0.55rem 1.05rem !important;
        transition:
            background 0.18s ease,
            border-color 0.18s ease,
            box-shadow 0.18s ease,
            transform 0.15s ease,
            color 0.15s ease !important;
    }}

    .stButton > button:hover,
    button[kind="secondary"]:hover,
    [data-testid="stBaseButton-secondary"]:hover,
    [data-testid="stBaseButton-secondaryFormSubmit"]:hover {{
        background: {t["accent_soft"]} !important;
        border-color: {t["accent_muted"]} !important;
        color: {t["accent"]} !important;
        -webkit-text-fill-color: {t["accent"]} !important;
        box-shadow: {t["btn_shadow_hover"]} !important;
        transform: translateY(-1px);
    }}

    .stButton > button:active,
    button[kind="secondary"]:active,
    [data-testid="stBaseButton-secondary"]:active {{
        transform: translateY(0);
        box-shadow: {t["btn_shadow"]} !important;
    }}

    .stButton > button p,
    .stButton > button span:not([data-testid="stIconMaterial"]):not([class*="material"]),
    button[kind="secondary"] p,
    [data-testid="stBaseButton-secondary"] p {{
        color: inherit !important;
        -webkit-text-fill-color: inherit !important;
        font-family: {FONT_FAMILY} !important;
    }}

    button[kind="primary"],
    button[kind="primaryFormSubmit"],
    [data-testid="stBaseButton-primary"],
    [data-testid="stBaseButton-primaryFormSubmit"],
    [data-testid="stFormSubmitButton"] > button {{
        background: linear-gradient(180deg, {t["accent_muted"]} 0%, {t["accent"]} 100%) !important;
        color: {t["accent_fg"]} !important;
        -webkit-text-fill-color: {t["accent_fg"]} !important;
        border: 1px solid {t["accent"]} !important;
        border-radius: 12px !important;
        box-shadow: 0 2px 8px {t["accent_glow"]}, {t["btn_shadow"]} !important;
        font-family: {FONT_FAMILY} !important;
        font-weight: 600 !important;
        font-size: 0.94rem !important;
        letter-spacing: 0.015em !important;
        min-height: 2.65rem !important;
        padding: 0.55rem 1.15rem !important;
        transition:
            filter 0.18s ease,
            box-shadow 0.18s ease,
            transform 0.15s ease !important;
    }}

    button[kind="primary"] p,
    button[kind="primary"] span:not([data-testid="stIconMaterial"]):not([class*="material"]),
    button[kind="primaryFormSubmit"] p,
    [data-testid="stBaseButton-primary"] p,
    [data-testid="stFormSubmitButton"] > button p {{
        color: {t["accent_fg"]} !important;
        -webkit-text-fill-color: {t["accent_fg"]} !important;
        font-family: {FONT_FAMILY} !important;
        font-weight: 600 !important;
    }}

    button[kind="primary"]:hover,
    button[kind="primaryFormSubmit"]:hover,
    [data-testid="stBaseButton-primary"]:hover,
    [data-testid="stBaseButton-primaryFormSubmit"]:hover,
    [data-testid="stFormSubmitButton"] > button:hover {{
        filter: brightness(1.06) saturate(1.05);
        box-shadow: 0 6px 20px {t["accent_glow"]} !important;
        transform: translateY(-1px);
    }}

    button[kind="primary"]:active,
    [data-testid="stBaseButton-primary"]:active,
    [data-testid="stFormSubmitButton"] > button:active {{
        transform: translateY(0);
        filter: brightness(0.97);
    }}

    /* Sidebar — compact so nav + theme + account fit without scrolling */
    [data-testid="stSidebar"] > div:first-child,
    [data-testid="stSidebarContent"],
    [data-testid="stSidebarUserContent"] {{
        padding-top: 0.55rem !important;
        padding-bottom: 0.55rem !important;
    }}

    [data-testid="stSidebarUserContent"] {{
        overflow: hidden !important;
    }}

    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {{
        gap: 0.2rem !important;
    }}

    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {{
        margin-bottom: 0 !important;
    }}

    [data-testid="stSidebar"] hr {{
        margin: 0.35rem 0 !important;
    }}

    [data-testid="stSidebar"] .stCaption,
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {{
        margin: 0.1rem 0 0.15rem !important;
        font-size: 0.72rem !important;
        line-height: 1.25 !important;
    }}

    [data-testid="stSidebar"] .stCaption p,
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {{
        font-size: 0.72rem !important;
        line-height: 1.25 !important;
    }}

    /* Sidebar nav — high-contrast active pill */
    [data-testid="stSidebar"] .stButton {{
        margin-bottom: 0.08rem !important;
    }}

    [data-testid="stSidebar"] .stButton > button,
    [data-testid="stSidebar"] [data-testid="stBaseButton-secondary"],
    [data-testid="stSidebar"] [data-testid="stBaseButton-primary"] {{
        border-radius: 10px !important;
        min-height: 1.95rem !important;
        height: 1.95rem !important;
        justify-content: flex-start !important;
        text-align: left !important;
        padding: 0.2rem 0.7rem !important;
        box-shadow: none !important;
        border: 1px solid transparent !important;
        background: transparent !important;
        color: {t["text_muted"]} !important;
        -webkit-text-fill-color: {t["text_muted"]} !important;
        font-weight: 500 !important;
        font-size: 0.84rem !important;
        letter-spacing: 0.01em !important;
        transition:
            background 0.2s ease,
            color 0.2s ease,
            border-color 0.2s ease,
            box-shadow 0.2s ease,
            transform 0.18s ease !important;
    }}

    [data-testid="stSidebar"] .stButton > button:hover,
    [data-testid="stSidebar"] [data-testid="stBaseButton-secondary"]:hover {{
        background: {t["nav_hover"]} !important;
        color: {t["text"]} !important;
        -webkit-text-fill-color: {t["text"]} !important;
        border-color: {t["border"]} !important;
        box-shadow: none !important;
        transform: translateX(2px);
        filter: none !important;
    }}

    [data-testid="stSidebar"] .stButton > button[kind="primary"],
    [data-testid="stSidebar"] [data-testid="stBaseButton-primary"] {{
        background: linear-gradient(135deg, {t["accent_muted"]} 0%, {t["accent"]} 100%) !important;
        color: {t["accent_fg"]} !important;
        -webkit-text-fill-color: {t["accent_fg"]} !important;
        border: 1px solid {t["accent"]} !important;
        box-shadow: 0 4px 16px {t["accent_glow"]} !important;
        font-weight: 600 !important;
        filter: none !important;
        animation: streamline-nav-in 0.28s ease-out;
    }}

    [data-testid="stSidebar"] .stButton > button[kind="primary"]:hover,
    [data-testid="stSidebar"] [data-testid="stBaseButton-primary"]:hover {{
        background: linear-gradient(135deg, {t["accent"]} 0%, {t["accent_muted"]} 100%) !important;
        color: {t["accent_fg"]} !important;
        -webkit-text-fill-color: {t["accent_fg"]} !important;
        border-color: {t["accent"]} !important;
        box-shadow: 0 6px 20px {t["accent_glow"]} !important;
        filter: brightness(1.04) !important;
        transform: translateX(0);
    }}

    [data-testid="stSidebar"] .stButton > button p,
    [data-testid="stSidebar"] [data-testid="stBaseButton-primary"] p,
    [data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] p,
    [data-testid="stSidebar"] .stButton > button span:not([data-testid="stIconMaterial"]):not([class*="material"]) {{
        color: inherit !important;
        -webkit-text-fill-color: inherit !important;
        font-weight: inherit !important;
    }}

    /* Number stepper / download / link-style buttons */
    [data-testid="stNumberInput"],
    [data-testid="stNumberInput"] > div,
    [data-testid="stNumberInput"] [data-baseweb="input"],
    [data-testid="stNumberInput"] [data-baseweb="base-input"] {{
        background: {t["input_bg"]} !important;
        background-color: {t["input_bg"]} !important;
        color: {t["text"]} !important;
        border-color: {t["border"]} !important;
    }}

    [data-testid="stNumberInput"] button,
    [data-testid="stNumberInput"] button[kind],
    [data-testid="stNumberInput"] [data-testid="stNumberInputStepUp"],
    [data-testid="stNumberInput"] [data-testid="stNumberInputStepDown"] {{
        background: {t["bg_secondary"]} !important;
        background-color: {t["bg_secondary"]} !important;
        background-image: none !important;
        border: 1px solid {t["border"]} !important;
        border-radius: 8px !important;
        color: {t["text"]} !important;
        -webkit-text-fill-color: {t["text"]} !important;
        box-shadow: none !important;
        transition: background 0.15s ease, border-color 0.15s ease !important;
    }}

    [data-testid="stNumberInput"] button *,
    [data-testid="stNumberInput"] button svg,
    [data-testid="stNumberInput"] button span,
    [data-testid="stNumberInput"] [data-testid="stNumberInputStepUp"] svg,
    [data-testid="stNumberInput"] [data-testid="stNumberInputStepDown"] svg {{
        color: {t["text"]} !important;
        fill: {t["text"]} !important;
        -webkit-text-fill-color: {t["text"]} !important;
    }}

    [data-testid="stNumberInput"] button:hover {{
        background: {t["icon_hover"]} !important;
        border-color: {t["accent_muted"]} !important;
    }}

    [data-testid="stDownloadButton"] > button {{
        background: {t["bg_secondary"]} !important;
        color: {t["accent"]} !important;
        border: 1px solid {t["border"]} !important;
        border-radius: 12px !important;
        box-shadow: {t["btn_shadow"]} !important;
        font-weight: 600 !important;
    }}

    [data-testid="stDownloadButton"] > button:hover {{
        background: {t["accent_soft"]} !important;
        border-color: {t["accent_muted"]} !important;
        box-shadow: {t["btn_shadow_hover"]} !important;
    }}

    div[data-testid="stTextInput"] input,
    div[data-testid="stTextArea"] textarea,
    div[data-testid="stTextAreaRootElement"] textarea,
    div[data-testid="stNumberInput"] input,
    section.main textarea,
    section.main input[type="text"],
    section.main input[type="number"],
    section.main input[type="search"],
    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] textarea,
    .stApp textarea,
    .stApp input:not([type="checkbox"]):not([type="radio"]) {{
        background-color: {t["input_bg"]} !important;
        border: 1px solid {t["border"]} !important;
        color: {t["text"]} !important;
        -webkit-text-fill-color: {t["text"]} !important;
        caret-color: {t["accent"]} !important;
        border-radius: 12px !important;
        box-shadow: {t["btn_shadow"]} !important;
        transition: border-color 0.18s ease, box-shadow 0.18s ease !important;
    }}

    div[data-testid="stTextInput"] input:focus,
    div[data-testid="stTextArea"] textarea:focus,
    div[data-testid="stTextAreaRootElement"] textarea:focus,
    div[data-testid="stNumberInput"] input:focus,
    .stApp textarea:focus,
    .stApp input:focus {{
        border-color: {t["accent"]} !important;
        box-shadow: 0 0 0 3px {t["accent_glow"]} !important;
        color: {t["text"]} !important;
        -webkit-text-fill-color: {t["text"]} !important;
    }}

    div[data-testid="stTextInput"] input::placeholder,
    div[data-testid="stTextArea"] textarea::placeholder,
    div[data-testid="stTextAreaRootElement"] textarea::placeholder,
    .stApp textarea::placeholder,
    .stApp input::placeholder {{
        color: {t["text_muted"]} !important;
        -webkit-text-fill-color: {t["text_muted"]} !important;
        opacity: 1 !important;
    }}

    /* —— Select / multiselect (React Aria ComboBox — not BaseWeb) —— */
    [data-testid="stSelectbox"],
    [data-testid="stMultiSelect"],
    .stSelectbox,
    .stMultiSelect {{
        color: {t["text"]} !important;
    }}

    [data-testid="stSelectbox"] .react-aria-ComboBox,
    [data-testid="stMultiSelect"] .react-aria-ComboBox,
    [data-testid="stSelectbox"] [role="group"],
    [data-testid="stMultiSelect"] [role="group"],
    .stSelectbox [role="group"],
    .stMultiSelect [role="group"],
    [data-testid="stSelectbox"] [data-rac][role="group"],
    [data-testid="stMultiSelect"] [data-rac][role="group"] {{
        background: {t["input_bg"]} !important;
        background-color: {t["input_bg"]} !important;
        background-image: none !important;
        border: 1px solid {t["border"]} !important;
        border-radius: 12px !important;
        box-shadow: {t["btn_shadow"]} !important;
        color: {t["text"]} !important;
        min-height: 2.55rem !important;
        transition: border-color 0.18s ease, box-shadow 0.18s ease !important;
    }}

    [data-testid="stSelectbox"] [role="group"]:hover,
    [data-testid="stMultiSelect"] [role="group"]:hover,
    .stSelectbox [role="group"]:hover {{
        border-color: {t["accent_muted"]} !important;
    }}

    [data-testid="stSelectbox"] [role="group"]:focus-within,
    [data-testid="stMultiSelect"] [role="group"]:focus-within,
    [data-testid="stSelectbox"] [role="group"]:has([aria-expanded="true"]),
    .stSelectbox [role="group"]:has([aria-expanded="true"]) {{
        border-color: {t["accent"]} !important;
        box-shadow: 0 0 0 3px {t["accent_glow"]} !important;
    }}

    [data-testid="stSelectbox"] input[role="combobox"],
    [data-testid="stMultiSelect"] input[role="combobox"],
    [data-testid="stSelectbox"] input,
    [data-testid="stMultiSelect"] input,
    .stSelectbox input,
    .stMultiSelect input {{
        background: transparent !important;
        background-color: transparent !important;
        background-image: none !important;
        border: none !important;
        box-shadow: none !important;
        color: {t["text"]} !important;
        -webkit-text-fill-color: {t["text"]} !important;
        caret-color: {t["accent"]} !important;
        font-family: {FONT_FAMILY} !important;
    }}

    [data-testid="stSelectbox"] button[aria-label="Open"],
    [data-testid="stSelectbox"] button[aria-haspopup="listbox"],
    [data-testid="stMultiSelect"] button[aria-haspopup="listbox"],
    .stSelectbox button[aria-haspopup="listbox"],
    .stMultiSelect button[aria-haspopup="listbox"] {{
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        color: {t["text_muted"]} !important;
    }}

    [data-testid="stSelectbox"] button[aria-haspopup="listbox"] svg,
    [data-testid="stMultiSelect"] button[aria-haspopup="listbox"] svg,
    .stSelectbox svg,
    .stMultiSelect svg {{
        fill: {t["text_muted"]} !important;
        color: {t["text_muted"]} !important;
    }}

    /* Legacy BaseWeb selects (older Streamlit) */
    [data-testid="stSelectbox"] [data-baseweb="select"] > div,
    [data-testid="stMultiSelect"] [data-baseweb="select"] > div,
    [data-testid="stSelectbox"] [data-baseweb="select"] div,
    [data-testid="stMultiSelect"] [data-baseweb="select"] div {{
        background: {t["input_bg"]} !important;
        background-color: {t["input_bg"]} !important;
        background-image: none !important;
        color: {t["text"]} !important;
        -webkit-text-fill-color: {t["text"]} !important;
    }}

    /* Opened list / popover menus (React Aria + BaseWeb) */
    [data-testid="stSelectboxVirtualDropdown"],
    .react-aria-Popover,
    .react-aria-ListBox,
    [class*="react-aria-Popover"],
    [class*="react-aria-ListBox"],
    div[data-baseweb="popover"],
    div[data-baseweb="popover"] > div,
    div[data-baseweb="popover"] > div > div,
    div[data-baseweb="popover"] [data-baseweb="menu"],
    div[data-baseweb="popover"] ul,
    ul[data-baseweb="menu"],
    ul[role="listbox"],
    div[role="listbox"],
    [role="listbox"],
    [data-baseweb="menu"] {{
        background: {t["dropdown_bg"]} !important;
        background-color: {t["dropdown_bg"]} !important;
        background-image: none !important;
        color: {t["text"]} !important;
        border: 1px solid {t["border"]} !important;
        border-radius: 14px !important;
        box-shadow: {t["dropdown_shadow"]} !important;
    }}

    [role="option"],
    [role="listbox"] [role="option"],
    .react-aria-ListBoxItem,
    li[role="option"],
    ul[data-baseweb="menu"] li,
    [data-baseweb="menu"] li,
    ul[role="listbox"] li,
    div[role="option"] {{
        color: {t["text"]} !important;
        -webkit-text-fill-color: {t["text"]} !important;
        background: transparent !important;
        background-color: transparent !important;
        border-radius: 10px !important;
        font-family: {FONT_FAMILY} !important;
    }}

    [role="option"]:hover,
    [role="option"][aria-selected="true"],
    [role="option"][data-focused],
    [role="option"][data-hovered],
    .react-aria-ListBoxItem:hover,
    .react-aria-ListBoxItem[data-focused],
    li[role="option"]:hover,
    li[role="option"][aria-selected="true"],
    ul[role="listbox"] li:hover,
    div[role="option"]:hover {{
        background: {t["accent_soft"]} !important;
        background-color: {t["accent_soft"]} !important;
        color: {t["accent"]} !important;
        -webkit-text-fill-color: {t["accent"]} !important;
    }}

    /* Dataframes / tables — match active Streamline theme */
    [data-testid="stDataFrame"],
    [data-testid="stDataFrameResizable"],
    [data-testid="stTable"],
    .stDataFrame,
    .stTable {{
        background: {t["bg_secondary"]} !important;
        border: 1px solid {t["border"]} !important;
        border-radius: 14px !important;
        overflow: hidden !important;
        box-shadow: {t["btn_shadow"]} !important;
    }}

    [data-testid="stDataFrame"] *,
    [data-testid="stTable"] *,
    .stDataFrame *,
    .stTable th,
    .stTable td {{
        color: {t["text"]} !important;
        border-color: {t["border"]} !important;
    }}

    [data-testid="stDataFrame"] canvas {{
        border-radius: 0 0 14px 14px !important;
    }}

    .sl-table-wrap {{
        overflow: auto;
        border: 1px solid {t["border"]};
        border-radius: 14px;
        background: {t["bg_secondary"]};
        box-shadow: {t["btn_shadow"]};
        animation: streamline-fade-up 0.35s ease-out;
    }}

    .sl-table {{
        width: 100%;
        border-collapse: collapse;
        font-family: {FONT_FAMILY};
        font-size: 0.92rem;
    }}

    .sl-table thead th {{
        position: sticky;
        top: 0;
        z-index: 1;
        background: {t["input_bg"]};
        color: {t["text_muted"]} !important;
        font-weight: 600;
        letter-spacing: 0.03em;
        text-transform: uppercase;
        font-size: 0.72rem;
        text-align: left;
        padding: 0.75rem 0.9rem;
        border-bottom: 1px solid {t["border"]};
    }}

    .sl-table tbody td {{
        color: {t["text"]} !important;
        padding: 0.7rem 0.9rem;
        border-bottom: 1px solid {t["border"]};
        white-space: nowrap;
    }}

    .sl-table tbody tr {{
        transition: background 0.15s ease;
    }}

    .sl-table tbody tr:hover td {{
        background: {t["accent_soft"]};
    }}

    .sl-table tbody tr:last-child td {{
        border-bottom: none;
    }}

    span[data-baseweb="tag"] {{
        background-color: {t["accent_soft"]} !important;
        color: {t["accent"]} !important;
        -webkit-text-fill-color: {t["accent"]} !important;
        border: 1px solid {t["accent_muted"]} !important;
        border-radius: 999px !important;
        font-weight: 500 !important;
    }}

    span[data-baseweb="tag"] span,
    span[data-baseweb="tag"] svg {{
        color: {t["accent"]} !important;
        fill: {t["accent"]} !important;
        -webkit-text-fill-color: {t["accent"]} !important;
    }}

    [data-testid="stCaptionContainer"],
    [data-testid="stCaptionContainer"] p,
    [data-testid="stCaptionContainer"] span,
    .stCaption, small {{
        color: {t["text_muted"]} !important;
    }}

    div[data-testid="stRadio"] label {{
        color: {t["text"]} !important;
        background: transparent !important;
        border: none !important;
    }}

    div[data-testid="stRadio"] div[role="radiogroup"] > label > div:first-child {{
        background-color: {t["input_bg"]} !important;
        border-color: {t["border"]} !important;
    }}

    div[data-testid="stRadio"] div[role="radiogroup"] > label[data-baseweb="radio"] > div:first-child > div {{
        background-color: {t["accent"]} !important;
    }}

    [data-testid="stTabs"] button {{
        color: {t["text_muted"]} !important;
        border-radius: 10px 10px 0 0 !important;
        font-weight: 500 !important;
        transition: color 0.15s ease, border-color 0.15s ease !important;
    }}

    [data-testid="stTabs"] button:hover {{
        color: {t["text"]} !important;
    }}

    [data-testid="stTabs"] button[aria-selected="true"] {{
        color: {t["accent"]} !important;
        border-bottom-color: {t["accent"]} !important;
        font-weight: 600 !important;
    }}

    [data-testid="stMetricValue"] {{
        color: {t["text"]} !important;
        font-weight: 600 !important;
    }}

    [data-testid="stMetricDelta"] svg {{
        fill: {t["accent"]} !important;
    }}

    [data-testid="stMetricDelta"] {{
        color: {t["accent"]} !important;
    }}

    .stProgress > div > div {{
        background-color: {t["accent"]} !important;
    }}

    .stProgress > div {{
        background-color: {t["border"]} !important;
    }}

    [data-testid="stAlert"],
    [data-testid="stAlert"] > div,
    [data-testid="stNotification"],
    .stSuccess, .stInfo, .stWarning, .stError,
    div[role="alert"] {{
        background: {t["bg_secondary"]} !important;
        background-color: {t["bg_secondary"]} !important;
        background-image: none !important;
        color: {t["text"]} !important;
        -webkit-text-fill-color: {t["text"]} !important;
        border: 1px solid {t["border"]} !important;
        border-radius: 12px !important;
        box-shadow: {t["btn_shadow"]} !important;
    }}

    [data-testid="stAlert"] *,
    [data-testid="stAlert"] p,
    [data-testid="stAlert"] span:not([data-testid="stIconMaterial"]),
    .stInfo *,
    .stSuccess *,
    div[role="alert"] * {{
        color: {t["text"]} !important;
        -webkit-text-fill-color: {t["text"]} !important;
    }}

    [data-testid="stExpander"],
    [data-testid="stExpander"] details,
    [data-testid="stExpander"] > details,
    [data-testid="stExpander"] [data-testid="stExpanderDetails"],
    .streamlit-expanderContent,
    .streamlit-expanderHeader {{
        background: {t["bg_secondary"]} !important;
        background-color: {t["bg_secondary"]} !important;
        background-image: none !important;
        color: {t["text"]} !important;
        border-color: {t["border"]} !important;
    }}

    [data-testid="stExpander"] {{
        border: 1px solid {t["border"]} !important;
        border-radius: 14px !important;
        box-shadow: {t["btn_shadow"]} !important;
        overflow: hidden !important;
    }}

    [data-testid="stExpander"] summary,
    [data-testid="stExpander"] summary:hover,
    [data-testid="stExpander"] [data-testid="stExpanderIcon"],
    .streamlit-expanderHeader {{
        background: {t["bg_secondary"]} !important;
        background-color: {t["bg_secondary"]} !important;
        color: {t["text"]} !important;
        -webkit-text-fill-color: {t["text"]} !important;
        border-radius: 0 !important;
    }}

    [data-testid="stExpander"] summary *,
    [data-testid="stExpander"] summary p,
    [data-testid="stExpander"] summary span:not([data-testid="stIconMaterial"]),
    .streamlit-expanderHeader * {{
        color: {t["text"]} !important;
        -webkit-text-fill-color: {t["text"]} !important;
    }}

    [data-testid="stExpander"] svg {{
        fill: {t["text_muted"]} !important;
        color: {t["text_muted"]} !important;
    }}

    hr {{ border-color: {t["border"]} !important; }}

    [data-testid="stMarkdownContainer"] strong {{
        color: {t["text"]} !important;
    }}

    /* Prevent Streamlit LaTeX ($…$) from rendering as green “math” in news copy */
    .stApp code.language-math,
    .stApp .katex,
    .stApp .katex * {{
        color: {t["text"]} !important;
        -webkit-text-fill-color: {t["text"]} !important;
        font-family: {FONT_FAMILY} !important;
        font-style: normal !important;
        background: transparent !important;
    }}

    iframe[title="streamlit_plotly_events.st_plotly_chart"] {{
        border-radius: 12px;
    }}

    .watch-empty {{
        text-align: center;
        padding: 3.5rem 1rem 1.5rem;
        border: 1px dashed {t["border"]};
        border-radius: 16px;
        background: {t["bg_secondary"]};
        margin: 0.5rem 0 1.25rem;
    }}

    .watch-empty-title {{
        font-size: 1.25rem;
        font-weight: 600;
        color: {t["text"]} !important;
        margin-bottom: 0.4rem;
    }}

    .watch-empty-sub {{
        color: {t["text_muted"]} !important;
        font-size: 0.95rem;
    }}

    [data-testid="stVerticalBlockBorderWrapper"] {{
        transition: border-color 0.15s ease, transform 0.15s ease, box-shadow 0.15s ease;
    }}

    [data-testid="stVerticalBlockBorderWrapper"]:hover {{
        border-color: {t["accent_muted"]} !important;
        transform: translateY(-1px);
        box-shadow: 0 8px 24px {t["accent_glow"]} !important;
    }}
</style>
"""


def _escape_js(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace("`", "\\`")
        .replace("${", "\\${")
    )


def _parent_theme_css(t: dict) -> str:
    """CSS that must live on the parent document (BaseWeb popovers / portals)."""
    return f"""
:root {{
  color-scheme: {t["color_scheme"]} !important;
  --primary-color: {t["accent"]} !important;
  --background-color: {t["bg"]} !important;
  --secondary-background-color: {t["bg_secondary"]} !important;
  --text-color: {t["text"]} !important;
  --border-color: {t["border"]} !important;
  --sl-dropdown-bg: {t["dropdown_bg"]} !important;
}}
html, body {{
  color-scheme: {t["color_scheme"]} !important;
}}
header[data-testid="stHeader"],
[data-testid="stHeader"],
[data-testid="stHeader"] > div,
[data-testid="stToolbar"],
.stApp > header,
.stApp header {{
  background: transparent !important;
  background-color: transparent !important;
  background-image: none !important;
  box-shadow: none !important;
  border: none !important;
}}
[data-testid="stToolbar"] {{
  display: flex !important;
  visibility: visible !important;
  opacity: 1 !important;
  pointer-events: auto !important;
}}
[data-testid="stDecoration"],
[data-testid="stAppDeployButton"],
[data-testid="stToolbarActions"],
.stDeployButton,
.stAppDeployButton {{
  display: none !important;
  visibility: hidden !important;
  pointer-events: none !important;
}}
[data-testid="stSidebarCollapseButton"],
[data-testid="stExpandSidebarButton"],
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"],
[data-testid="stToolbar"] [data-testid="stExpandSidebarButton"],
[data-testid="stToolbar"] > div,
[data-testid="stToolbar"] > div > div,
[data-testid="stToolbar"] > div > div > div {{
  display: flex !important;
  visibility: visible !important;
  opacity: 1 !important;
  pointer-events: auto !important;
  height: auto !important;
  width: auto !important;
}}
div[data-baseweb="popover"],
div[data-baseweb="popover"] > div,
div[data-baseweb="popover"] > div > div,
div[data-baseweb="popover"] [data-baseweb="menu"],
div[data-baseweb="popover"] ul,
ul[data-baseweb="menu"],
ul[role="listbox"],
div[role="listbox"],
[data-baseweb="menu"],
[data-baseweb="popover"] [class*="st-"] {{
  background: {t["dropdown_bg"]} !important;
  background-color: {t["dropdown_bg"]} !important;
  background-image: none !important;
  color: {t["text"]} !important;
  border-color: {t["border"]} !important;
}}
div[data-baseweb="popover"],
div[data-baseweb="popover"] > div,
ul[data-baseweb="menu"],
ul[role="listbox"] {{
  border: 1px solid {t["border"]} !important;
  border-radius: 14px !important;
  box-shadow: {t["dropdown_shadow"]} !important;
  padding: 0.4rem !important;
  overflow: auto !important;
}}
li[role="option"],
ul[data-baseweb="menu"] li,
[data-baseweb="menu"] li,
ul[role="listbox"] li,
div[role="option"] {{
  color: {t["text"]} !important;
  -webkit-text-fill-color: {t["text"]} !important;
  background: transparent !important;
  background-color: transparent !important;
  border-radius: 10px !important;
  padding: 0.6rem 0.85rem !important;
  font-family: {FONT_FAMILY} !important;
}}
li[role="option"] *,
ul[role="listbox"] li *,
div[role="option"] * {{
  color: {t["text"]} !important;
  -webkit-text-fill-color: {t["text"]} !important;
  background: transparent !important;
}}
li[role="option"]:hover,
li[role="option"][aria-selected="true"],
ul[role="listbox"] li:hover,
div[role="option"]:hover {{
  background: {t["accent_soft"]} !important;
  background-color: {t["accent_soft"]} !important;
  color: {t["accent"]} !important;
  -webkit-text-fill-color: {t["accent"]} !important;
}}
li[role="option"]:hover *,
li[role="option"][aria-selected="true"] * {{
  color: inherit !important;
  -webkit-text-fill-color: inherit !important;
  background: transparent !important;
}}
/* Select controls — React Aria ComboBox + legacy BaseWeb */
[data-testid="stSelectbox"] [role="group"],
[data-testid="stMultiSelect"] [role="group"],
.stSelectbox [role="group"],
.stMultiSelect [role="group"],
[data-testid="stSelectbox"] [data-rac][role="group"],
[data-testid="stSelectbox"] [data-baseweb="select"] div,
[data-testid="stMultiSelect"] [data-baseweb="select"] div {{
  background: {t["input_bg"]} !important;
  background-color: {t["input_bg"]} !important;
  background-image: none !important;
  color: {t["text"]} !important;
  -webkit-text-fill-color: {t["text"]} !important;
  border-color: {t["border"]} !important;
}}
[data-testid="stSelectbox"] input[role="combobox"],
[data-testid="stMultiSelect"] input[role="combobox"],
[data-testid="stSelectbox"] input,
.stSelectbox input {{
  background: transparent !important;
  color: {t["text"]} !important;
  -webkit-text-fill-color: {t["text"]} !important;
}}
[data-testid="stSelectbox"] button[aria-haspopup="listbox"],
.stSelectbox button[aria-haspopup="listbox"] {{
  background: transparent !important;
  color: {t["text_muted"]} !important;
}}
[data-testid="stSelectboxVirtualDropdown"],
.react-aria-Popover,
.react-aria-ListBox,
[role="listbox"] {{
  background: {t["dropdown_bg"]} !important;
  background-color: {t["dropdown_bg"]} !important;
  color: {t["text"]} !important;
  border: 1px solid {t["border"]} !important;
}}
"""


def inject_parent_theme_css() -> None:
    """Push dropdown/popover styles into the parent document where portals render."""
    css = _escape_js(_parent_theme_css(get_theme()))
    st.html(
        f"""
<script>
(function () {{
  const css = `{css}`;
  const targets = [document];
  try {{
    if (window.parent && window.parent.document) targets.push(window.parent.document);
  }} catch (err) {{}}
  targets.forEach((doc) => {{
    try {{
      let style = doc.getElementById("streamline-theme-parent");
      if (!style) {{
        style = doc.createElement("style");
        style.id = "streamline-theme-parent";
        (doc.head || doc.documentElement).appendChild(style);
      }}
      style.textContent = css;
    }} catch (err) {{}}
  }});
}})();
</script>
"""
    )


def ensure_sidebar_expanded() -> None:
    """Force the Streamlit sidebar open (overrides a remembered collapsed state)."""
    st.html(
        """
<script>
(function () {
  function expandSidebar() {
    const doc = window.parent.document;
    const selectors = [
      '[data-testid="stExpandSidebarButton"]',
      '[data-testid="collapsedControl"]',
      '[data-testid="stSidebarCollapsedControl"]',
      'button[kind="headerNoPadding"]',
    ];
    for (const selector of selectors) {
      const button = doc.querySelector(selector);
      if (button) {
        button.click();
        return;
      }
    }
  }
  expandSidebar();
  setTimeout(expandSidebar, 50);
  setTimeout(expandSidebar, 250);
})();
</script>
"""
    )


@st.cache_resource
def _cached_theme_css(mode: str, revision: str = "2026-07-23-portfolio") -> str:
    """Build theme CSS once per mode/revision for the process lifetime."""
    return _build_css(THEMES[mode])


def apply_theme(*, expand_sidebar: bool = False) -> None:
    """Inject global CSS last so it wins over Streamlit defaults."""
    # Always rebuild so stylesheet edits apply without a server restart.
    st.html(_build_css(get_theme()))
    inject_parent_theme_css()
    if expand_sidebar:
        ensure_sidebar_expanded()
