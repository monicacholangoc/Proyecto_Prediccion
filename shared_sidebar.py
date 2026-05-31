"""
shared_sidebar.py — Sidebar oscuro + nav funcional + logo + equipo + temas.

RESPONSABILIDADES de este archivo:
  - CSS del sidebar (fondo oscuro, siempre, independiente del tema de la app)
  - CSS del fondo del área de contenido (via data-theme en <html>)
  - Logo centrado (detecta assets/Logo.jpg automáticamente)
  - Equipo del proyecto
  - Navegación funcional con st.page_link()
  - Botones de tema (Claro / Oscuro / Sistema)

NO duplica nada de styles.css. Ese archivo maneja los componentes de contenido.
"""

import os
import base64
import streamlit as st

# ── Configuración ────────────────────────────────────────────────────────────

LOGO_URL  = None   # URL pública del logo, o None para usar archivo local
LOGO_CANDIDATES = [
    "assets/Logo.jpg", "assets/Logo.jpeg", "assets/Logo.png",
    "assets/logo.jpg", "assets/logo.jpeg", "assets/logo.png",
    "assets/Logo.JPG", "assets/Logo.PNG",
]
TEAM = ["Arévalo José", "Cholango Mónica", "Torres Byron"]


# ── Logo ─────────────────────────────────────────────────────────────────────

def _find_logo():
    for p in LOGO_CANDIDATES:
        if os.path.exists(p):
            return p
    return None


def _logo_tag() -> str:
    if LOGO_URL:
        return f'<img class="sb-logo" src="{LOGO_URL}" alt="Logo">'
    path = _find_logo()
    if path:
        ext  = path.rsplit(".", 1)[-1].lower()
        mime = {"png":"image/png","jpg":"image/jpeg","jpeg":"image/jpeg"}.get(ext,"image/png")
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        return f'<img class="sb-logo" src="data:{mime};base64,{b64}" alt="Logo">'
    # Respaldo SVG
    return """<svg class="sb-logo" viewBox="0 0 80 80" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect width="80" height="80" rx="14" fill="url(#gfb)"/>
      <path d="M22 58L40 26l18 32Z" fill="rgba(255,255,255,.15)" stroke="rgba(255,255,255,.4)" stroke-width="2"/>
      <path d="M31 58l9-20 9 20Z" fill="rgba(255,255,255,.92)"/>
      <circle cx="40" cy="24" r="5.5" fill="#7dd3fc"/>
      <defs><linearGradient id="gfb" x1="0" y1="0" x2="80" y2="80" gradientUnits="userSpaceOnUse">
        <stop stop-color="#1e3a8a"/><stop offset="1" stop-color="#0f4c5c"/>
      </linearGradient></defs></svg>"""


# ── Iconos ───────────────────────────────────────────────────────────────────

def _ico(d: str) -> str:
    return f'<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="rgba(248,250,252,.85)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{d}</svg>'

ICONS = {
    "home":   _ico('<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>'),
    "file":   _ico('<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>'),
    "search": _ico('<circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>'),
    "chart":  _ico('<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>'),
    "shield": _ico('<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>'),
    "bar":    _ico('<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>'),
}


# ── CSS del sidebar — TODO aquí, nada en styles.css ──────────────────────────
# El sidebar es SIEMPRE oscuro, sin importar el tema de la app.

_SB_CSS = """
<style>
/* ══ SIDEBAR — siempre oscuro ══════════════════════════════════════════════ */
[data-testid="stSidebar"],
[data-testid="stSidebar"] > div,
[data-testid="stSidebar"] > div > div,
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg,#18253f 0%,#111b31 100%) !important;
    border-right: 1px solid rgba(255,255,255,.06) !important;
}
/* Todo el texto del sidebar blanco */
[data-testid="stSidebar"],
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] div,
[data-testid="stSidebar"] label { color: #f8fafc !important; }

/* Ocultar nav automático */
[data-testid="stSidebarNav"] { display: none !important; }

/* ══ Logo centrado ══════════════════════════════════════════════════════════ */
.sb-logo-wrap {
    display: flex; flex-direction: column; align-items: center;
    padding: 1.1rem 0.5rem 0.8rem;
    border-bottom: 1px solid rgba(255,255,255,.1);
    margin-bottom: 0.4rem; gap: 0.45rem;
}
.sb-logo {
    width: 80px; height: 80px; border-radius: 12px;
    object-fit: contain; background: #fff;
    padding: 4px; box-shadow: 0 4px 14px rgba(0,0,0,.3);
    display: block;
}
.sb-name { color:#f8fafc!important; font-size:.88rem; font-weight:700; text-align:center; line-height:1.2; }
.sb-sub  { color:rgba(248,250,252,.48)!important; font-size:.68rem; text-align:center; }

/* ══ Equipo ════════════════════════════════════════════════════════════════ */
.sb-team {
    padding: .45rem .6rem .55rem;
    border-bottom: 1px solid rgba(255,255,255,.07);
    margin-bottom: .4rem;
}
.sb-team-t { color:rgba(248,250,252,.42)!important; font-size:.63rem; font-weight:700; text-transform:uppercase; letter-spacing:.07em; margin-bottom:.25rem; }
.sb-member { color:rgba(248,250,252,.78)!important; font-size:.77rem; padding:.1rem 0; display:flex; align-items:center; gap:.35rem; }
.sb-member::before { content:""; width:5px; height:5px; border-radius:50%; background:rgba(125,211,252,.7); flex-shrink:0; }

/* ══ Nav icono ═════════════════════════════════════════════════════════════ */
.sb-ico {
    display:flex; align-items:center; justify-content:center;
    width:26px; height:26px; border-radius:6px;
    background:rgba(255,255,255,.1); flex-shrink:0; margin-top:.2rem;
}

/* ══ page_link styling ═════════════════════════════════════════════════════ */
[data-testid="stSidebar"] [data-testid="stPageLink"] {
    background:transparent!important; border:none!important; padding:0!important; margin:0!important;
}
[data-testid="stSidebar"] [data-testid="stPageLink"] a,
[data-testid="stSidebar"] [data-testid="stPageLink"] p {
    color:rgba(248,250,252,.82)!important; font-size:.81rem!important; font-weight:500!important;
    text-decoration:none!important; padding:.28rem .4rem!important; border-radius:8px!important;
    display:block!important; transition:background .15s!important; line-height:1.25!important;
}
[data-testid="stSidebar"] [data-testid="stPageLink"] a:hover,
[data-testid="stSidebar"] [data-testid="stPageLink"] p:hover {
    background:rgba(255,255,255,.09)!important; color:#fff!important;
}
[data-testid="stSidebar"] [data-testid="stPageLink"][aria-current="page"] a,
[data-testid="stSidebar"] [data-testid="stPageLink"][aria-current="page"] p {
    background:rgba(255,255,255,.15)!important; color:#fff!important;
}
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] {
    gap:.1rem!important; align-items:center!important; margin-bottom:.04rem!important;
}
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] > div {
    padding:0!important; min-width:0!important;
}

/* ══ Botones de tema ════════════════════════════════════════════════════════ */
.sb-theme-t {
    color:rgba(248,250,252,.4)!important; font-size:.63rem; font-weight:700;
    text-transform:uppercase; letter-spacing:.07em;
    padding: .45rem .6rem .1rem; display:block;
}

/* ══ Fondo del área de contenido — tema claro (default) ════════════════════ */
html, html[data-theme="light"], html[data-theme="system"] {
    --bg-from:#f8fbff; --bg-to:#eef3f9;
    --ov1:rgba(23,70,162,.08); --ov2:rgba(15,76,92,.08);
}
html[data-theme="dark"] {
    --bg-from:#0d1117; --bg-to:#161b22;
    --ov1:rgba(77,142,240,.06); --ov2:rgba(86,212,196,.05);
}

.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] > section.main,
[data-testid="stAppViewContainer"] > section.main > div,
[data-testid="stMain"],
[data-testid="stMain"] > div,
[data-testid="block-container"] {
    background:
        radial-gradient(circle at top right, var(--ov1), transparent 22%),
        radial-gradient(circle at top left,  var(--ov2), transparent 18%),
        linear-gradient(180deg, var(--bg-from) 0%, var(--bg-to) 100%) !important;
}
</style>
"""


# ── Detección de páginas ──────────────────────────────────────────────────────

def _find_pages() -> dict:
    m = {"resumen":None,"exploracion":None,"modelos":None,"auditoria":None,"ranking":None}
    if not os.path.isdir("pages"):
        return m
    for f in sorted(os.listdir("pages")):
        if not f.endswith(".py"):
            continue
        l = f.lower()
        p = os.path.join("pages", f)
        if   "resumen"  in l: m["resumen"]     = p
        elif "explor"   in l: m["exploracion"] = p
        elif "model"    in l: m["modelos"]     = p
        elif "audit"    in l: m["auditoria"]   = p
        elif "rank"     in l: m["ranking"]     = p
    return m


# ── Render principal ──────────────────────────────────────────────────────────

def render_sidebar() -> None:
    """Inyecta CSS y renderiza sidebar completo."""

    # 1. CSS — fuera del sidebar para que llegue al <head>
    st.markdown(_SB_CSS, unsafe_allow_html=True)

    # 2. JS — aplica data-theme al <html> según session_state
    theme = st.session_state.get("app_theme", "light")
    st.markdown(
        f'<script>document.documentElement.setAttribute("data-theme","{theme}");</script>',
        unsafe_allow_html=True,
    )

    pages = _find_pages()
    members_html = "".join(f'<div class="sb-member">{m}</div>' for m in TEAM)

    with st.sidebar:
        # Logo + branding
        st.markdown(
            f"""
            <div class="sb-logo-wrap">
                {_logo_tag()}
                <div class="sb-name">Seminario Predictivo</div>
                <div class="sb-sub">Caso 06 · Amazon Reviews</div>
            </div>
            <div class="sb-team">
                <div class="sb-team-t">Equipo</div>
                {members_html}
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Nav
        _nav("main.py",            ICONS["home"],   "Inicio")
        _nav(pages["resumen"],     ICONS["file"],   "Resumen Ejecutivo")
        _nav(pages["exploracion"], ICONS["search"], "Exploración de Datos")
        _nav(pages["modelos"],     ICONS["chart"],  "Modelos y Evaluación")
        _nav(pages["auditoria"],   ICONS["shield"], "Auditoría en Tiempo Real")
        _nav(pages["ranking"],     ICONS["bar"],    "Ranking y Benchmark")

        # Selector de tema
        st.markdown('<span class="sb-theme-t">Tema</span>', unsafe_allow_html=True)
        tc1, tc2, tc3 = st.columns(3, gap="small")
        with tc1:
            if st.button("☀ Claro",   key="th_l", use_container_width=True):
                st.session_state["app_theme"] = "light";  st.rerun()
        with tc2:
            if st.button("◑ Oscuro",  key="th_d", use_container_width=True):
                st.session_state["app_theme"] = "dark";   st.rerun()
        with tc3:
            if st.button("⊙ Sistema", key="th_s", use_container_width=True):
                st.session_state["app_theme"] = "system"; st.rerun()


def _nav(page, icon, label):
    if page is None:
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:.5rem;padding:.28rem .5rem;'
            f'color:rgba(248,250,252,.3);font-size:.8rem">'
            f'<div class="sb-ico">{icon}</div>{label}</div>',
            unsafe_allow_html=True,
        )
        return
    ci, cl = st.columns([0.18, 0.82], gap="small")
    with ci: st.markdown(f'<div class="sb-ico">{icon}</div>', unsafe_allow_html=True)
    with cl: st.page_link(page, label=label)