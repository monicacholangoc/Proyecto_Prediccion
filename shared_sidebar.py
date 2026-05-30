"""
Helper de sidebar compartido.
Solo renderiza logo + nav con iconos.
Todo el CSS ya está en styles/styles.css.

Uso en cada página:
    from shared_sidebar import render_sidebar
    render_sidebar()
"""

import os
import base64
import streamlit as st

LOGO_PATH = "assets/logo.png"   # Pon tu logo aquí (png o jpg)
LOGO_URL  = None                 # O URL pública: "https://..."

# ── Iconos SVG (Feather outline, 16x16) ────────────────────────────────────
_ICONS = {
    "home":       '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="rgba(248,250,252,0.85)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>',
    "file":       '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="rgba(248,250,252,0.85)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>',
    "search":     '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="rgba(248,250,252,0.85)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>',
    "activity":   '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="rgba(248,250,252,0.85)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>',
    "shield":     '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="rgba(248,250,252,0.85)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
    "bar-chart":  '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="rgba(248,250,252,0.85)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>',
}

_NAV = [
    (_ICONS["home"],      "Inicio"),
    (_ICONS["file"],      "Resumen Ejecutivo"),
    (_ICONS["search"],    "Exploración de Datos"),
    (_ICONS["activity"],  "Modelos y Evaluación"),
    (_ICONS["shield"],    "Auditoría en Tiempo Real"),
    (_ICONS["bar-chart"], "Ranking y Benchmark"),
]


def _logo_html() -> str:
    """Imagen real si existe, SVG de respaldo si no."""
    if LOGO_URL:
        return f'<img src="{LOGO_URL}" style="width:40px;height:40px;border-radius:10px;object-fit:cover;" alt="Logo">'
    if os.path.exists(LOGO_PATH):
        ext  = LOGO_PATH.rsplit(".", 1)[-1].lower()
        mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
                "svg": "image/svg+xml"}.get(ext, "image/png")
        with open(LOGO_PATH, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        return f'<img src="data:{mime};base64,{b64}" style="width:40px;height:40px;border-radius:10px;object-fit:cover;" alt="Logo">'
    # SVG de respaldo
    return """<svg width="40" height="40" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect width="40" height="40" rx="10" fill="url(#lgfb)"/>
      <path d="M11 27 L20 13 L29 27 Z" fill="rgba(255,255,255,0.15)" stroke="rgba(255,255,255,0.45)" stroke-width="1.2"/>
      <path d="M15 27 L20 18 L25 27 Z" fill="rgba(255,255,255,0.92)"/>
      <circle cx="20" cy="12" r="2.8" fill="#7dd3fc"/>
      <defs><linearGradient id="lgfb" x1="0" y1="0" x2="40" y2="40" gradientUnits="userSpaceOnUse">
        <stop offset="0%" stop-color="#1e3a8a"/><stop offset="100%" stop-color="#0f4c5c"/>
      </linearGradient></defs>
    </svg>"""


def render_sidebar() -> None:
    """Renderiza logo + nav con iconos en el sidebar."""
    nav_items = "".join(
        f'<div class="snav-item"><span class="snav-icon">{icon}</span>'
        f'<span class="snav-label">{label}</span></div>'
        for icon, label in _NAV
    )
    with st.sidebar:
        st.markdown(
            f"""
            <div class="sidebar-logo-wrap">
                {_logo_html()}
                <div>
                    <div class="sidebar-logo-text-main">Seminario<br>Predictivo</div>
                    <div class="sidebar-logo-text-sub">Caso 06 · Amazon Reviews</div>
                </div>
            </div>
            <div class="snav-panel">{nav_items}</div>
            """,
            unsafe_allow_html=True,
        )