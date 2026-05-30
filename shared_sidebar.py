"""
Helper de sidebar: logo centrado + navegación funcional con st.page_link().
El CSS del sidebar se inyecta aquí mismo para garantizar que se aplique
antes de que se renderice cualquier elemento del sidebar.
"""

import os
import base64
import streamlit as st

# ── Logo ────────────────────────────────────────────────────────────────────
_LOGO_CANDIDATES = [
    "assets/Logo.jpg", "assets/Logo.jpeg", "assets/Logo.png",
    "assets/logo.jpg", "assets/logo.jpeg", "assets/logo.png",
    "assets/Logo.JPG", "assets/Logo.PNG",
]
LOGO_URL = None


def _find_logo() -> str | None:
    for path in _LOGO_CANDIDATES:
        if os.path.exists(path):
            return path
    return None


def _logo_b64() -> tuple[str, str] | None:
    """Devuelve (base64, mime) si el logo existe, None si no."""
    if LOGO_URL:
        return None
    path = _find_logo()
    if not path:
        return None
    ext  = path.rsplit(".", 1)[-1].lower()
    mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg"}.get(ext, "image/png")
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode(), mime


# ── Iconos SVG ──────────────────────────────────────────────────────────────
_I_HOME   = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="rgba(248,250,252,0.85)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>'
_I_FILE   = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="rgba(248,250,252,0.85)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>'
_I_SEARCH = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="rgba(248,250,252,0.85)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>'
_I_CHART  = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="rgba(248,250,252,0.85)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>'
_I_SHIELD = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="rgba(248,250,252,0.85)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>'
_I_BAR    = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="rgba(248,250,252,0.85)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>'


# ── CSS del sidebar — se inyecta en <head> para que aplique siempre ─────────
_SIDEBAR_CSS = """
<style>
/* ── Fondo oscuro del sidebar ─────────────────────────────────────────────── */
[data-testid="stSidebar"],
[data-testid="stSidebar"] > div,
[data-testid="stSidebar"] > div > div,
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #18253f 0%, #111b31 100%) !important;
    border-right: 1px solid rgba(255,255,255,0.06) !important;
}
[data-testid="stSidebar"] * { color: #f8fafc; }

/* ── Ocultar nav automático de Streamlit ──────────────────────────────────── */
[data-testid="stSidebarNav"] { display: none !important; }

/* ── Logo centrado ───────────────────────────────────────────────────────── */
.sb-logo-wrap {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 1.2rem 0.5rem 0.9rem;
    border-bottom: 1px solid rgba(255,255,255,0.1);
    margin-bottom: 0.7rem;
    gap: 0.55rem;
}
.sb-logo-img {
    width: 80px;
    height: 80px;
    border-radius: 14px;
    object-fit: contain;
    background: #ffffff;
    padding: 5px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.25);
}
.sb-logo-svg {
    width: 80px;
    height: 80px;
    border-radius: 14px;
    display: block;
}
.sb-brand-name {
    color: #f8fafc !important;
    font-size: 0.9rem;
    font-weight: 700;
    text-align: center;
    line-height: 1.2;
    letter-spacing: -0.01em;
}
.sb-brand-sub {
    color: rgba(248,250,252,0.5) !important;
    font-size: 0.7rem;
    text-align: center;
    margin-top: 0.1rem;
}

/* ── Items de nav ─────────────────────────────────────────────────────────── */
.sb-nav-item {
    display: flex;
    align-items: center;
    gap: 0.55rem;
    padding: 0.4rem 0.6rem;
    border-radius: 9px;
    margin-bottom: 0.06rem;
    transition: background 0.15s;
}
.sb-nav-item:hover { background: rgba(255,255,255,0.08); }
.sb-nav-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    border-radius: 7px;
    background: rgba(255,255,255,0.1);
    flex-shrink: 0;
}

/* ── Estilizar page_link ──────────────────────────────────────────────────── */
[data-testid="stSidebar"] [data-testid="stPageLink"] {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
    margin: 0 !important;
}
[data-testid="stSidebar"] [data-testid="stPageLink"] a,
[data-testid="stSidebar"] [data-testid="stPageLink"] p {
    color: rgba(248,250,252,0.82) !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    text-decoration: none !important;
    padding: 0.3rem 0.5rem !important;
    border-radius: 8px !important;
    display: block !important;
    transition: background 0.15s !important;
    line-height: 1.25 !important;
}
[data-testid="stSidebar"] [data-testid="stPageLink"] a:hover,
[data-testid="stSidebar"] [data-testid="stPageLink"] p:hover {
    background: rgba(255,255,255,0.09) !important;
    color: #fff !important;
}
[data-testid="stSidebar"] [data-testid="stPageLink"][aria-current="page"] a,
[data-testid="stSidebar"] [data-testid="stPageLink"][aria-current="page"] p {
    background: rgba(255,255,255,0.15) !important;
    color: #fff !important;
}

/* ── Columnas del nav en sidebar (quitar gaps) ───────────────────────────── */
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] {
    gap: 0.15rem !important;
    align-items: center !important;
    margin-bottom: 0.04rem !important;
}
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] > div {
    padding: 0 !important;
    min-width: 0 !important;
}

/* ── Fondo del contenido principal (todas las páginas) ───────────────────── */
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] > section.main,
[data-testid="stAppViewContainer"] > section.main > div {
    background:
        radial-gradient(circle at top right, rgba(23,70,162,0.08), transparent 22%),
        radial-gradient(circle at top left,  rgba(15,76,92,0.08),  transparent 18%),
        linear-gradient(180deg, #f8fbff 0%, #eef3f9 100%) !important;
}
</style>
"""


def _detect_pages() -> dict:
    """Detecta los nombres reales de archivos en pages/."""
    mapping = {"resumen": None, "exploracion": None,
               "modelos": None, "auditoria": None, "ranking": None}
    pages_dir = "pages"
    if not os.path.isdir(pages_dir):
        return mapping
    for fname in sorted(os.listdir(pages_dir)):
        lower = fname.lower()
        fpath = os.path.join(pages_dir, fname)
        if not fname.endswith(".py"):
            continue
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


_THEME_JS = """
<script>
(function() {
    // Lee el tema guardado o usa 'light' por defecto
    var saved = localStorage.getItem('app_theme') || 'light';
    document.documentElement.setAttribute('data-theme', saved);

    // Aplica fondo CSS directo para cubrir páginas secundarias de Streamlit
    function applyBg(theme) {
        var isDark = theme === 'dark' || (theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);
        var bg = isDark
            ? 'linear-gradient(180deg,#0d1117 0%,#161b22 100%)'
            : 'radial-gradient(circle at top right,rgba(23,70,162,.08),transparent 22%),radial-gradient(circle at top left,rgba(15,76,92,.08),transparent 18%),linear-gradient(180deg,#f8fbff 0%,#eef3f9 100%)';
        // Fuerza fondo en todos los contenedores de Streamlit
        var selectors = [
            '.stApp','[data-testid="stAppViewContainer"]',
            '[data-testid="stAppViewContainer"] > section',
            '[data-testid="stMain"]','[data-testid="block-container"]',
            '.main','.block-container'
        ];
        selectors.forEach(function(sel) {
            document.querySelectorAll(sel).forEach(function(el) {
                el.style.setProperty('background', bg, 'important');
                el.style.setProperty('background-attachment', 'fixed', 'important');
            });
        });
    }

    applyBg(saved);

    // Observa cambios en el DOM (Streamlit re-renderiza)
    var obs = new MutationObserver(function() {
        var t = localStorage.getItem('app_theme') || 'light';
        document.documentElement.setAttribute('data-theme', t);
        applyBg(t);
    });
    obs.observe(document.body, { childList: true, subtree: true });

    // Escucha mensajes del botón del sidebar
    window.addEventListener('message', function(e) {
        if (e.data && e.data.type === 'SET_THEME') {
            localStorage.setItem('app_theme', e.data.theme);
            document.documentElement.setAttribute('data-theme', e.data.theme);
            applyBg(e.data.theme);
        }
    });

    // Escucha cambio de preferencia del sistema
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function() {
        var t = localStorage.getItem('app_theme') || 'light';
        if (t === 'system') applyBg('system');
    });
})();
</script>
"""

_THEME_BUTTONS_HTML = """
<div class="theme-switcher" id="theme-switcher-wrap">
    <button class="theme-btn" id="tb-light" onclick="setTheme('light')" title="Modo claro">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>
        Claro
    </button>
    <button class="theme-btn" id="tb-dark" onclick="setTheme('dark')" title="Modo oscuro">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3a7 7 0 0 0 9.79 9.79z"/></svg>
        Oscuro
    </button>
    <button class="theme-btn" id="tb-system" onclick="setTheme('system')" title="Tema del sistema">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>
        Sistema
    </button>
</div>
<script>
function setTheme(t) {
    localStorage.setItem('app_theme', t);
    document.documentElement.setAttribute('data-theme', t);
    // Marca botón activo
    ['light','dark','system'].forEach(function(id) {
        var b = document.getElementById('tb-'+id);
        if (b) b.classList.toggle('active', id === t);
    });
    // Aplica fondo inmediatamente
    var isDark = t === 'dark' || (t === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);
    var bg = isDark
        ? 'linear-gradient(180deg,#0d1117 0%,#161b22 100%)'
        : 'radial-gradient(circle at top right,rgba(23,70,162,.08),transparent 22%),radial-gradient(circle at top left,rgba(15,76,92,.08),transparent 18%),linear-gradient(180deg,#f8fbff 0%,#eef3f9 100%)';
    ['.stApp','[data-testid="stAppViewContainer"]','[data-testid="stAppViewContainer"] > section',
     '[data-testid="stMain"]','[data-testid="block-container"]','.main','.block-container'
    ].forEach(function(sel) {
        document.querySelectorAll(sel).forEach(function(el) {
            el.style.setProperty('background', bg, 'important');
        });
    });
}
// Marca el botón activo al cargar
(function() {
    var cur = localStorage.getItem('app_theme') || 'light';
    var b = document.getElementById('tb-'+cur);
    if (b) b.classList.add('active');
})();
</script>
"""


def render_sidebar() -> None:
    """Inyecta CSS y renderiza logo + nav funcional en el sidebar."""
    # Inyectar CSS SIEMPRE — fuera del sidebar para que llegue al <head>
    st.markdown(_SIDEBAR_CSS, unsafe_allow_html=True)
    # Inyectar JS de tema (aplica fondo en todas las páginas)
    st.markdown(_THEME_JS, unsafe_allow_html=True)

    pages = _detect_pages()

    # Construir HTML del logo
    logo_result = _logo_b64()
    if LOGO_URL:
        logo_html = f'<img class="sb-logo-img" src="{LOGO_URL}" alt="Logo">'
    elif logo_result:
        b64, mime = logo_result
        logo_html = f'<img class="sb-logo-img" src="data:{mime};base64,{b64}" alt="Logo">'
    else:
        # SVG de respaldo
        logo_html = """<svg class="sb-logo-svg" viewBox="0 0 80 80" fill="none" xmlns="http://www.w3.org/2000/svg">
          <rect width="80" height="80" rx="14" fill="url(#lgfb3)"/>
          <path d="M22 58 L40 26 L58 58 Z" fill="rgba(255,255,255,0.15)" stroke="rgba(255,255,255,0.45)" stroke-width="2"/>
          <path d="M31 58 L40 38 L49 58 Z" fill="rgba(255,255,255,0.92)"/>
          <circle cx="40" cy="24" r="5.5" fill="#7dd3fc"/>
          <defs><linearGradient id="lgfb3" x1="0" y1="0" x2="80" y2="80" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stop-color="#1e3a8a"/><stop offset="100%" stop-color="#0f4c5c"/>
          </linearGradient></defs>
        </svg>"""

    with st.sidebar:
        # Logo centrado
        st.markdown(
            f"""
            <div class="sb-logo-wrap">
                {logo_html}
                <div>
                    <div class="sb-brand-name">Seminario Predictivo</div>
                    <div class="sb-brand-sub">Caso 06 · Amazon Reviews</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Nav funcional
        _nav_item("main.py",              _I_HOME,   "Inicio")
        _nav_item(pages["resumen"],       _I_FILE,   "Resumen Ejecutivo")
        _nav_item(pages["exploracion"],   _I_SEARCH, "Exploración de Datos")
        _nav_item(pages["modelos"],       _I_CHART,  "Modelos y Evaluación")
        _nav_item(pages["auditoria"],     _I_SHIELD, "Auditoría en Tiempo Real")
        _nav_item(pages["ranking"],       _I_BAR,    "Ranking y Benchmark")

        # ── Selector de tema ────────────────────────────────────────────────
        st.markdown(_THEME_BUTTONS_HTML, unsafe_allow_html=True)


def _nav_item(page: str | None, icon_svg: str, label: str) -> None:
    """Ítem de nav: columna icono + columna page_link."""
    if page is None:
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:0.5rem;padding:0.3rem 0.6rem;'
            f'color:rgba(248,250,252,0.35);font-size:0.8rem">'
            f'<div class="sb-nav-icon">{icon_svg}</div>{label}</div>',
            unsafe_allow_html=True,
        )
        return

    col_icon, col_link = st.columns([0.18, 0.82], gap="small")
    with col_icon:
        st.markdown(
            f'<div class="sb-nav-icon">{icon_svg}</div>',
            unsafe_allow_html=True,
        )
    with col_link:
        st.page_link(page, label=label)