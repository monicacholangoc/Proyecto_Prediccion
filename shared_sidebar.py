"""
Helper de sidebar: logo + navegación funcional con st.page_link().
Las rutas deben coincidir exactamente con los nombres de archivo en pages/.
"""

import os
import base64
import streamlit as st

# ── Logo ───────────────────────────────────────────────────────────────────────
_LOGO_CANDIDATES = [
    "assets/Logo.jpg", "assets/Logo.jpeg", "assets/Logo.png",
    "assets/logo.jpg", "assets/logo.jpeg", "assets/logo.png",
    "assets/Logo.JPG", "assets/Logo.PNG",
]
LOGO_URL = None  # Alternativa: URL pública "https://..."


def _find_logo() -> str | None:
    for path in _LOGO_CANDIDATES:
        if os.path.exists(path):
            return path
    return None


def _logo_html() -> str:
    if LOGO_URL:
        return f'<img src="{LOGO_URL}" style="width:44px;height:44px;border-radius:10px;object-fit:contain;background:#fff;padding:2px;" alt="Logo">'
    path = _find_logo()
    if path:
        ext  = path.rsplit(".", 1)[-1].lower()
        mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg"}.get(ext, "image/png")
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        return f'<img src="data:{mime};base64,{b64}" style="width:44px;height:44px;border-radius:10px;object-fit:contain;background:#fff;padding:2px;" alt="Logo">'
    return """<svg width="44" height="44" viewBox="0 0 44 44" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect width="44" height="44" rx="10" fill="url(#lgfb2)"/>
      <path d="M12 30 L22 14 L32 30 Z" fill="rgba(255,255,255,0.15)" stroke="rgba(255,255,255,0.45)" stroke-width="1.2"/>
      <path d="M17 30 L22 20 L27 30 Z" fill="rgba(255,255,255,0.92)"/>
      <circle cx="22" cy="13" r="3" fill="#7dd3fc"/>
      <defs><linearGradient id="lgfb2" x1="0" y1="0" x2="44" y2="44" gradientUnits="userSpaceOnUse">
        <stop offset="0%" stop-color="#1e3a8a"/><stop offset="100%" stop-color="#0f4c5c"/>
      </linearGradient></defs>
    </svg>"""


# ── Iconos SVG ─────────────────────────────────────────────────────────────────
_I_HOME   = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>'
_I_FILE   = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>'
_I_SEARCH = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>'
_I_CHART  = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>'
_I_SHIELD = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>'
_I_BAR    = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>'


def _detect_page_files() -> dict:
    """
    Detecta los nombres reales de los archivos en pages/.
    Devuelve un dict con la ruta correcta para cada sección.
    Soporta nombres con mayúsculas o minúsculas.
    """
    pages_dir = "pages"
    mapping = {
        "resumen":    None,
        "exploracion": None,
        "modelos":    None,
        "auditoria":  None,
        "ranking":    None,
    }

    if not os.path.isdir(pages_dir):
        return mapping

    for fname in os.listdir(pages_dir):
        lower = fname.lower()
        fpath = os.path.join(pages_dir, fname)
        if "resumen" in lower:
            mapping["resumen"] = fpath
        elif "explor" in lower:
            mapping["exploracion"] = fpath
        elif "model" in lower:
            mapping["modelos"] = fpath
        elif "audit" in lower:
            mapping["auditoria"] = fpath
        elif "rank" in lower:
            mapping["ranking"] = fpath

    return mapping


def render_sidebar() -> None:
    """Renderiza logo + nav funcional en el sidebar."""
    pages = _detect_page_files()

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
            """,
            unsafe_allow_html=True,
        )

        _nav_item("main.py",                   _I_HOME,   "Inicio")
        _nav_item(pages["resumen"],             _I_FILE,   "Resumen Ejecutivo")
        _nav_item(pages["exploracion"],         _I_SEARCH, "Exploración de Datos")
        _nav_item(pages["modelos"],             _I_CHART,  "Modelos y Evaluación")
        _nav_item(pages["auditoria"],           _I_SHIELD, "Auditoría en Tiempo Real")
        _nav_item(pages["ranking"],             _I_BAR,    "Ranking y Benchmark")


def _nav_item(page: str | None, icon_svg: str, label: str) -> None:
    """Un ítem de nav: icono SVG + st.page_link funcional."""
    if page is None:
        # Página no encontrada — muestra solo el label como texto
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:0.5rem;padding:0.3rem 0.5rem;'
            f'color:rgba(248,250,252,0.4);font-size:0.82rem">'
            f'<div class="snav-link-icon">{icon_svg}</div>{label}</div>',
            unsafe_allow_html=True,
        )
        return

    col_icon, col_link = st.columns([0.18, 0.82], gap="small")
    with col_icon:
        st.markdown(
            f'<div class="snav-link-icon">{icon_svg}</div>',
            unsafe_allow_html=True,
        )
    with col_link:
        st.page_link(page, label=label)
