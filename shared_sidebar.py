"""
Helper de sidebar: logo + navegación funcional con st.page_link() + iconos SVG.

El nav usa st.page_link() nativo de Streamlit para que la navegación funcione.
Los iconos SVG se inyectan via CSS sobre cada link generado por Streamlit.

Uso:
    from shared_sidebar import render_sidebar
    render_sidebar()
"""

import os
import base64
import streamlit as st

# ── Logo ───────────────────────────────────────────────────────────────────────
# Busca automáticamente Logo.jpg, Logo.png, logo.jpg, logo.png en assets/
_LOGO_CANDIDATES = [
    "assets/Logo.jpg", "assets/Logo.jpeg", "assets/Logo.png",
    "assets/logo.jpg", "assets/logo.jpeg", "assets/logo.png",
    "assets/Logo.JPG", "assets/Logo.PNG",
]
LOGO_URL = None  # Alternativa: URL pública "https://..."


def _find_logo() -> str | None:
    """Devuelve la primera ruta de logo que existe."""
    for path in _LOGO_CANDIDATES:
        if os.path.exists(path):
            return path
    return None


def _logo_html() -> str:
    """HTML del logo: imagen real si existe, SVG geométrico si no."""
    if LOGO_URL:
        return f'<img src="{LOGO_URL}" style="width:44px;height:44px;border-radius:10px;object-fit:contain;background:#fff;padding:2px;" alt="Logo">'

    path = _find_logo()
    if path:
        ext  = path.rsplit(".", 1)[-1].lower()
        mime = {"png": "image/png", "jpg": "image/jpeg",
                "jpeg": "image/jpeg"}.get(ext, "image/png")
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        return f'<img src="data:{mime};base64,{b64}" style="width:44px;height:44px;border-radius:10px;object-fit:contain;background:#fff;padding:2px;" alt="Logo">'

    # SVG de respaldo
    return """<svg width="44" height="44" viewBox="0 0 44 44" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect width="44" height="44" rx="10" fill="url(#lgfb2)"/>
      <path d="M12 30 L22 14 L32 30 Z" fill="rgba(255,255,255,0.15)" stroke="rgba(255,255,255,0.45)" stroke-width="1.2"/>
      <path d="M17 30 L22 20 L27 30 Z" fill="rgba(255,255,255,0.92)"/>
      <circle cx="22" cy="13" r="3" fill="#7dd3fc"/>
      <defs><linearGradient id="lgfb2" x1="0" y1="0" x2="44" y2="44" gradientUnits="userSpaceOnUse">
        <stop offset="0%" stop-color="#1e3a8a"/><stop offset="100%" stop-color="#0f4c5c"/>
      </linearGradient></defs>
    </svg>"""


# ── Iconos SVG para cada página ─────────────────────────────────────────────
_ICON_HOME    = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>'
_ICON_FILE    = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>'
_ICON_SEARCH  = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>'
_ICON_CHART   = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>'
_ICON_SHIELD  = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>'
_ICON_BAR     = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>'

# CSS que estiliza los page_link de Streamlit y agrega los iconos SVG inline
_NAV_CSS = """
<style>
/* Ocultar nav automático */
[data-testid="stSidebarNav"] { display: none !important; }

/* Contenedor del nav personalizado */
.snav-section { margin-top: 0.5rem; }

/* Estilizar cada page_link como ítem de nav */
[data-testid="stSidebarNav"] + div { display: none; }

.snav-link-row {
    display: flex;
    align-items: center;
    gap: 0.55rem;
    padding: 0.38rem 0.55rem;
    border-radius: 9px;
    margin-bottom: 0.08rem;
    transition: background 0.15s;
}
.snav-link-row:hover { background: rgba(255,255,255,0.09); }

.snav-link-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 26px;
    height: 26px;
    border-radius: 6px;
    background: rgba(255,255,255,0.11);
    flex-shrink: 0;
    color: rgba(248,250,252,0.85);
}

/* Override de Streamlit page_link dentro del sidebar */
[data-testid="stSidebar"] [data-testid="stPageLink"] {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
    margin: 0 !important;
    border-radius: 0 !important;
}
[data-testid="stSidebar"] [data-testid="stPageLink"] a,
[data-testid="stSidebar"] [data-testid="stPageLink"] p {
    color: rgba(248,250,252,0.82) !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    text-decoration: none !important;
    padding: 0.38rem 0 0.38rem 0.55rem !important;
    border-radius: 9px !important;
    display: block !important;
    transition: background 0.15s !important;
}
[data-testid="stSidebar"] [data-testid="stPageLink"] a:hover,
[data-testid="stSidebar"] [data-testid="stPageLink"] p:hover {
    background: rgba(255,255,255,0.09) !important;
    color: #fff !important;
}
[data-testid="stSidebar"] [data-testid="stPageLink"][aria-current="page"] a,
[data-testid="stSidebar"] [data-testid="stPageLink"][aria-current="page"] p {
    background: rgba(255,255,255,0.14) !important;
    color: #fff !important;
}
</style>
"""


def render_sidebar() -> None:
    """Renderiza logo + nav funcional con st.page_link() en el sidebar."""
    with st.sidebar:
        # Logo + branding
        st.markdown(
            f"""
            <div class="sidebar-logo-wrap">
                {_logo_html()}
                <div>
                    <div class="sidebar-logo-text-main">Seminario<br>Predictivo</div>
                    <div class="sidebar-logo-text-sub">Caso 06 · Amazon Reviews</div>
                </div>
            </div>
            {_NAV_CSS}
            """,
            unsafe_allow_html=True,
        )

        # Nav funcional: icon + page_link lado a lado
        _nav_item("main.py",                          _ICON_HOME,   "Inicio")
        _nav_item("pages/01_Resumen_Ejecutivo.py",    _ICON_FILE,   "Resumen Ejecutivo")
        _nav_item("pages/02_Exploracion_de_Datos.py", _ICON_SEARCH, "Exploración de Datos")
        _nav_item("pages/03_Modelos_y_Evaluacion.py", _ICON_CHART,  "Modelos y Evaluación")
        _nav_item("pages/04_Auditoria_en_Tiempo_Real.py", _ICON_SHIELD, "Auditoría en Tiempo Real")
        _nav_item("pages/05_Ranking_y_Benchmark.py",  _ICON_BAR,    "Ranking y Benchmark")


def _nav_item(page: str, icon_svg: str, label: str) -> None:
    """Renderiza un ítem de nav con icono SVG + st.page_link funcional."""
    col_icon, col_link = st.columns([0.18, 0.82], gap="small")
    with col_icon:
        st.markdown(
            f'<div class="snav-link-icon">{icon_svg}</div>',
            unsafe_allow_html=True,
        )
    with col_link:
        st.page_link(page, label=label)