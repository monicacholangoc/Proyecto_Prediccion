"""
Helper de sidebar: logo + selector de tema arriba + navegaciÃ³n funcional.
El fondo del Ã¡rea principal se fuerza vÃ­a CSS inline en <style> con
background-color directo (no gradiente) para garantizar cobertura total
en main.py y todas las pÃ¡ginas de pages/.
"""

import os
import base64
import streamlit as st

# â”€â”€ Logo â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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
    if LOGO_URL:
        return None
    path = _find_logo()
    if not path:
        return None
    ext  = path.rsplit(".", 1)[-1].lower()
    mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg"}.get(ext, "image/png")
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode(), mime


# â”€â”€ Iconos SVG nav â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
_I_HOME   = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="rgba(248,250,252,0.85)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>'
_I_FILE   = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="rgba(248,250,252,0.85)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>'
_I_SEARCH = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="rgba(248,250,252,0.85)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>'
_I_CHART  = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="rgba(248,250,252,0.85)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>'
_I_SHIELD = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="rgba(248,250,252,0.85)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>'
_I_BAR    = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="rgba(248,250,252,0.85)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>'


# â”€â”€ CSS completo (sidebar + fondo main + temas) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
_FULL_CSS = """
<style>
/* â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
   VARIABLES DE TEMA â€” se sobrescriben por JS con data-theme
   â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• */
:root {
    --bg-color:     #edf2f8;
    --bg-color2:    #f0f5fc;
    --surface:      #ffffff;
    --surface-soft: rgba(255,255,255,0.93);
    --text:         #0f172a;
    --muted:        #526277;
    --border:       #d8e1ec;
    --primary:      #1746a2;
    --accent:       #0f4c5c;
    --success:      #0f9f74;
    --warning:      #c97a12;
    --danger:       #d65454;
    --shadow-soft:  0 10px 24px rgba(15,23,42,0.05);
    --shadow-card:  0 18px 36px rgba(15,23,42,0.08);
}

/* â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
   FONDO PRINCIPAL â€” background-color sÃ³lido, sin gradiente,
   para garantizar cobertura en TODAS las pÃ¡ginas de Streamlit
   â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• */
html,
body,
.stApp,
#root,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] > section,
[data-testid="stAppViewContainer"] > section > div,
[data-testid="stMain"],
[data-testid="stMain"] > div,
[data-testid="block-container"],
.main,
.block-container,
div[class*="appview"],
div[class*="main"] {
    background-color: var(--bg-color) !important;
    background-image: none !important;
}

/* Gradient sutil ENCIMA del color sÃ³lido, sin romper la cobertura */
.stApp {
    background-image:
        radial-gradient(circle at 90% 0%, rgba(23,70,162,0.07) 0%, transparent 40%),
        radial-gradient(circle at 10% 5%, rgba(15,76,92,0.06) 0%, transparent 35%) !important;
}

/* â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
   MODO OSCURO
   â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• */
[data-theme="dark"] {
    --bg-color:     #0d1117;
    --bg-color2:    #161b22;
    --surface:      #1c2333;
    --surface-soft: rgba(28,35,51,0.97);
    --text:         #e6edf3;
    --muted:        #8b949e;
    --border:       #30363d;
    --primary:      #4d8ef0;
    --accent:       #56d4c4;
    --success:      #3fb950;
    --warning:      #d29922;
    --danger:       #f85149;
    --shadow-soft:  0 10px 24px rgba(0,0,0,0.35);
    --shadow-card:  0 18px 36px rgba(0,0,0,0.45);
}

[data-theme="dark"] html,
[data-theme="dark"] body,
[data-theme="dark"] .stApp,
[data-theme="dark"] #root,
[data-theme="dark"] [data-testid="stAppViewContainer"],
[data-theme="dark"] [data-testid="stAppViewContainer"] > section,
[data-theme="dark"] [data-testid="stMain"],
[data-theme="dark"] [data-testid="stMain"] > div,
[data-theme="dark"] [data-testid="block-container"],
[data-theme="dark"] .main,
[data-theme="dark"] .block-container {
    background-color: #0d1117 !important;
    background-image: none !important;
    color: #e6edf3 !important;
}

[data-theme="dark"] .stApp {
    background-image:
        radial-gradient(circle at 90% 0%, rgba(77,142,240,0.06) 0%, transparent 40%),
        radial-gradient(circle at 10% 5%, rgba(86,212,196,0.04) 0%, transparent 35%) !important;
}

/* MODO SISTEMA */
@media (prefers-color-scheme: dark) {
    [data-theme="system"] {
        --bg-color: #0d1117; --bg-color2: #161b22;
        --surface: #1c2333; --surface-soft: rgba(28,35,51,0.97);
        --text: #e6edf3; --muted: #8b949e; --border: #30363d;
        --primary: #4d8ef0; --accent: #56d4c4;
        --success: #3fb950; --warning: #d29922; --danger: #f85149;
        --shadow-soft: 0 10px 24px rgba(0,0,0,0.35);
        --shadow-card: 0 18px 36px rgba(0,0,0,0.45);
    }
    [data-theme="system"] html, [data-theme="system"] body,
    [data-theme="system"] .stApp,
    [data-theme="system"] [data-testid="stAppViewContainer"],
    [data-theme="system"] [data-testid="stMain"],
    [data-theme="system"] [data-testid="block-container"] {
        background-color: #0d1117 !important;
        color: #e6edf3 !important;
    }
}

/* Dark: textos */
[data-theme="dark"] h1,[data-theme="dark"] h2,[data-theme="dark"] h3,
[data-theme="dark"] .metric-value,[data-theme="dark"] .stat-pill-value,
[data-theme="dark"] .kpi-value,[data-theme="dark"] .review-text,
[data-theme="dark"] .review-user,[data-theme="dark"] .nav-card-title,
[data-theme="dark"] .api-card-value { color: var(--text) !important; }

[data-theme="dark"] p,[data-theme="dark"] li,[data-theme="dark"] label,
[data-theme="dark"] .metric-caption,[data-theme="dark"] .metric-label,
[data-theme="dark"] .highlight-body,[data-theme="dark"] .highlight-title,
[data-theme="dark"] .section-label,[data-theme="dark"] .stat-pill-label,
[data-theme="dark"] .kpi-label,[data-theme="dark"] .api-card-label,
[data-theme="dark"] .review-meta,[data-theme="dark"] .review-helpfulness
{ color: var(--muted) !important; }

/* Dark: cards */
[data-theme="dark"] .metric-card,[data-theme="dark"] .highlight-card,
[data-theme="dark"] .nav-card,[data-theme="dark"] .review-card,
[data-theme="dark"] .stat-pill,[data-theme="dark"] .kpi-card,
[data-theme="dark"] .api-card,[data-theme="dark"] .info-panel,
[data-theme="dark"] .section-panel,[data-theme="dark"] .accuracy-warning {
    background: var(--surface-soft) !important;
    border-color: var(--border) !important;
}

/* Dark: badges */
[data-theme="dark"] .metric-badge-good { background:#0d2b1a; color:#3fb950; }
[data-theme="dark"] .metric-badge-warn { background:#2b1f07; color:#d29922; }
[data-theme="dark"] .metric-badge-info { background:#0f1f3d; color:#4d8ef0; }

/* Dark: inputs */
[data-theme="dark"] .stTextInput input,
[data-theme="dark"] .stTextArea textarea,
[data-theme="dark"] .stSelectbox div[data-baseweb="select"] > div {
    background: var(--surface) !important;
    color: var(--text) !important;
    border-color: var(--border) !important;
}

/* Dark: header */
[data-theme="dark"] [data-testid="stHeader"] {
    background: rgba(13,17,23,0.85) !important;
    border-bottom-color: #30363d !important;
}

/* â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
   SIDEBAR
   â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• */
[data-testid="stSidebar"],
[data-testid="stSidebar"] > div,
[data-testid="stSidebar"] > div > div,
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1746a2 0%, #0f3380 100%) !important;
    border-right: 1px solid rgba(255,255,255,0.06) !important;
}
[data-testid="stSidebar"] * { color: #f8fafc; }
[data-testid="stSidebarNav"] { display: none !important; }

/* â”€â”€ Selector de tema â€” ARRIBA, junto al logo â”€â”€â”€ */
.sb-top-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.75rem 0.6rem 0.5rem;
    border-bottom: 1px solid rgba(255,255,255,0.1);
    margin-bottom: 0.6rem;
    gap: 0.4rem;
}
.sb-brand-block { flex: 1; min-width: 0; }
.sb-brand-name {
    color: #f8fafc !important;
    font-size: 0.78rem;
    font-weight: 700;
    line-height: 1.2;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.sb-brand-sub {
    color: rgba(248,250,252,0.45) !important;
    font-size: 0.62rem;
    margin-top: 0.05rem;
    white-space: nowrap;
}
.sb-theme-pills {
    display: flex;
    gap: 0.22rem;
    flex-shrink: 0;
}
.sb-theme-pill {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 26px;
    height: 26px;
    border-radius: 7px;
    border: 1px solid rgba(255,255,255,0.12);
    background: rgba(255,255,255,0.07);
    cursor: pointer;
    color: rgba(248,250,252,0.55);
    transition: background 0.15s, color 0.15s, border-color 0.15s;
    font-size: 0;
    padding: 0;
}
.sb-theme-pill:hover {
    background: rgba(255,255,255,0.16);
    color: rgba(248,250,252,0.9);
    border-color: rgba(255,255,255,0.25);
}
.sb-theme-pill.active {
    background: rgba(77,142,240,0.35);
    border-color: rgba(77,142,240,0.6);
    color: #ffffff;
}
.sb-theme-pill svg { display: block; }

/* â”€â”€ Logo centrado (debajo del top bar) â”€â”€ */
.sb-logo-wrap {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 0.6rem 0.5rem 0.8rem;
    gap: 0.5rem;
    border-bottom: 1px solid rgba(255,255,255,0.07);
    margin-bottom: 0.5rem;
}
.sb-logo-img {
    width: 72px; height: 72px;
    border-radius: 12px;
    object-fit: contain;
    background: #ffffff;
    padding: 5px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.25);
}
.sb-logo-svg { width: 72px; height: 72px; border-radius: 12px; display: block; }

/* â”€â”€ Nav items â”€â”€ */
.sb-nav-icon {
    display: flex; align-items: center; justify-content: center;
    width: 26px; height: 26px;
    border-radius: 7px;
    background: rgba(255,255,255,0.09);
    flex-shrink: 0;
}
[data-testid="stSidebar"] [data-testid="stPageLink"] {
    background: transparent !important; border: none !important;
    padding: 0 !important; margin: 0 !important;
}
[data-testid="stSidebar"] [data-testid="stPageLink"] a,
[data-testid="stSidebar"] [data-testid="stPageLink"] p {
    color: rgba(248,250,252,0.82) !important;
    font-size: 0.82rem !important; font-weight: 500 !important;
    text-decoration: none !important;
    padding: 0.28rem 0.45rem !important;
    border-radius: 8px !important;
    display: block !important;
    transition: background 0.15s !important;
    line-height: 1.3 !important;
}
[data-testid="stSidebar"] [data-testid="stPageLink"] a:hover,
[data-testid="stSidebar"] [data-testid="stPageLink"] p:hover {
    background: rgba(255,255,255,0.09) !important; color: #fff !important;
}
[data-testid="stSidebar"] [data-testid="stPageLink"][aria-current="page"] a,
[data-testid="stSidebar"] [data-testid="stPageLink"][aria-current="page"] p {
    background: rgba(255,255,255,0.15) !important; color: #fff !important;
}
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] {
    gap: 0.15rem !important; align-items: center !important;
    margin-bottom: 0.04rem !important;
}
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] > div {
    padding: 0 !important; min-width: 0 !important;
}

/* Fondo transparente en contenedores internos del sidebar */
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"],
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] > div,
[data-testid="stSidebar"] [data-testid="column"],
[data-testid="stSidebar"] [data-testid="column"] > div,
[data-testid="stSidebar"] .stMarkdown,
[data-testid="stSidebar"] .element-container {
    background: transparent !important;
    background-color: transparent !important;
}

/* â”€â”€ Header â”€â”€ */
[data-testid="stHeader"] {
    background: rgba(255,255,255,0.62);
    backdrop-filter: blur(10px);
    border-bottom: 1px solid rgba(216,225,236,0.7);
}
</style>
"""

# â”€â”€ JS de tema â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Se inyecta FUERA del sidebar para llegar al <head> real del documento.
# Aplica background-color sÃ³lido en todos los contenedores de Streamlit
# inmediatamente y cada vez que el DOM cambia (Streamlit re-renderiza).
_THEME_JS = """
<script>
(function(){
    // Selectores de todos los contenedores que Streamlit genera
    var SELS = [
        'html','body','.stApp','#root',
        '[data-testid="stAppViewContainer"]',
        '[data-testid="stAppViewContainer"] > section',
        '[data-testid="stAppViewContainer"] > section > div',
        '[data-testid="stMain"]',
        '[data-testid="stMain"] > div',
        '[data-testid="block-container"]',
        '.main','.block-container'
    ];

    function isDarkMode(theme){
        return theme==='dark' ||
               (theme==='system' && window.matchMedia('(prefers-color-scheme:dark)').matches);
    }

    function applyAll(theme){
        var dark = isDarkMode(theme);
        // config.toml inyecta backgroundColor como style inline en stApp;
        // lo sobrescribimos con setProperty(..., 'important') aquÃ­.
        var bgMain  = dark ? '#0d1117' : '#edf2f8';
        var bgCard  = dark ? '#161b22' : '#ffffff';
        var txtMain = dark ? '#e6edf3' : '#0f172a';
        var grad    = dark
            ? 'radial-gradient(circle at 90% 0%,rgba(77,142,240,.06),transparent 40%)'
            : 'radial-gradient(circle at 90% 0%,rgba(23,70,162,.07),transparent 40%),radial-gradient(circle at 10% 5%,rgba(15,76,92,.06),transparent 35%)';

        // 1. data-theme en <html> para que el CSS lo capture
        document.documentElement.setAttribute('data-theme', theme);

        // 2. Sobrescribir el style inline que Streamlit inyecta desde config.toml
        SELS.forEach(function(s){
            document.querySelectorAll(s).forEach(function(el){
                // NUNCA tocar el sidebar
                if(el.closest('[data-testid="stSidebar"]')) return;
                el.style.setProperty('background-color', bgMain, 'important');
                el.style.setProperty('color', txtMain, 'important');
                el.style.removeProperty('background-image');
            });
        });

        // 2b. Forzar fondo azul del sidebar (Streamlit lo pisa con inline style)
        var sbBg = dark ? 'linear-gradient(180deg,#1c2333 0%,#0d1117 100%)' 
                        : 'linear-gradient(180deg,#1746a2 0%,#0f3380 100%)';
        [
            '[data-testid="stSidebar"]',
            '[data-testid="stSidebar"] > div',
            '[data-testid="stSidebar"] > div > div',
            'section[data-testid="stSidebar"]'
        ].forEach(function(s){
            document.querySelectorAll(s).forEach(function(el){
                el.style.setProperty('background', sbBg, 'important');
                el.style.setProperty('background-color', 'transparent', 'important');
            });
        });

        // 3. Gradiente decorativo encima del fondo sÃ³lido
        document.querySelectorAll('.stApp').forEach(function(el){
            el.style.setProperty('background-image', grad, 'important');
        });

        // 4. Cards / superficies secundarias
        var cardSels = [
            '[data-testid="stSidebarContent"]',
            '.metric-card','.stat-pill','.highlight-card',
            '.nav-card','.review-card','.kpi-card','.api-card'
        ];
        cardSels.forEach(function(s){
            document.querySelectorAll(s).forEach(function(el){
                if(!el.closest('[data-testid="stSidebar"]')){
                    el.style.setProperty('background-color', bgCard, 'important');
                }
            });
        });

        // 5. Header de Streamlit
        var hdr = document.querySelector('[data-testid="stHeader"]');
        if(hdr) hdr.style.setProperty('background',
            dark ? 'rgba(13,17,23,0.85)' : 'rgba(255,255,255,0.62)', 'important');

        // 6. Activar pÃ­ldora correcta
        ['light','dark','system'].forEach(function(id){
            var b=document.getElementById('stp-'+id);
            if(b) b.classList.toggle('active', id===theme);
        });
    }

    // Exponer globalmente para que los botones del sidebar lo llamen
    window._setAppTheme = function(t){
        localStorage.setItem('app_theme', t);
        applyAll(t);
    };

    // Aplicar inmediatamente al cargar (antes del primer paint si es posible)
    var saved = localStorage.getItem('app_theme') || 'light';
    applyAll(saved);

    // Re-aplicar cada vez que Streamlit re-renderiza el DOM
    // (Streamlit puede restablecer el style inline al navegar entre pÃ¡ginas)
    var _obs_timeout = null;
    var obs = new MutationObserver(function(){
        clearTimeout(_obs_timeout);
        _obs_timeout = setTimeout(function(){
            var t = localStorage.getItem('app_theme') || 'light';
            applyAll(t);
        }, 30);   // debounce 30ms para no saturar
    });
    var _startObs = function(){
        obs.observe(document.body, {childList:true, subtree:true, attributes:true,
                                    attributeFilter:['style','class']});
    };
    if(document.body) _startObs();
    else document.addEventListener('DOMContentLoaded', _startObs);

    // Cambio de preferencia del sistema
    window.matchMedia('(prefers-color-scheme:dark)').addEventListener('change', function(){
        if((localStorage.getItem('app_theme')||'light')==='system') applyAll('system');
    });
})();
</script>
"""


def _theme_pills_html() -> str:
    """HTML de las tres pÃ­ldoras de tema (renderizado en el top bar del sidebar)."""
    return """
<div class="sb-theme-pills" id="sb-theme-pills">
    <button class="sb-theme-pill" id="stp-light" title="Modo claro"
        onclick="window._setAppTheme('light')">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
             stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="5"/>
            <line x1="12" y1="1" x2="12" y2="3"/>
            <line x1="12" y1="21" x2="12" y2="23"/>
            <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
            <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
            <line x1="1" y1="12" x2="3" y2="12"/>
            <line x1="21" y1="12" x2="23" y2="12"/>
            <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
            <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
        </svg>
    </button>
    <button class="sb-theme-pill" id="stp-dark" title="Modo oscuro"
        onclick="window._setAppTheme('dark')">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
             stroke="currentColor" stroke-width="2">
            <path d="M21 12.79A9 9 0 1 1 11.21 3a7 7 0 0 0 9.79 9.79z"/>
        </svg>
    </button>
    <button class="sb-theme-pill" id="stp-system" title="Tema del sistema"
        onclick="window._setAppTheme('system')">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
             stroke="currentColor" stroke-width="2">
            <rect x="2" y="3" width="20" height="14" rx="2"/>
            <line x1="8" y1="21" x2="16" y2="21"/>
            <line x1="12" y1="17" x2="12" y2="21"/>
        </svg>
    </button>
</div>
<script>
(function(){
    var cur = localStorage.getItem('app_theme') || 'light';
    ['light','dark','system'].forEach(function(id){
        var b = document.getElementById('stp-'+id);
        if(b) b.classList.toggle('active', id===cur);
    });
})();
</script>
"""


def _detect_pages() -> dict:
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
        if "resumen"  in lower: mapping["resumen"]     = fpath
        elif "explor" in lower: mapping["exploracion"] = fpath
        elif "model"  in lower: mapping["modelos"]     = fpath
        elif "audit"  in lower: mapping["auditoria"]   = fpath
        elif "rank"   in lower: mapping["ranking"]     = fpath
    return mapping


def render_sidebar() -> None:
    """Inyecta CSS + JS de tema y renderiza sidebar completo."""
    # CSS y JS van FUERA del sidebar (Streamlit los pone en <head>)
    st.markdown(_FULL_CSS,  unsafe_allow_html=True)
    st.markdown(_THEME_JS, unsafe_allow_html=True)

    pages = _detect_pages()

    # Logo HTML
    logo_result = _logo_b64()
    if LOGO_URL:
        logo_html = f'<img class="sb-logo-img" src="{LOGO_URL}" alt="Logo">'
    elif logo_result:
        b64, mime = logo_result
        logo_html = f'<img class="sb-logo-img" src="data:{mime};base64,{b64}" alt="Logo">'
    else:
        logo_html = """<svg class="sb-logo-svg" viewBox="0 0 80 80" fill="none"
          xmlns="http://www.w3.org/2000/svg">
          <rect width="80" height="80" rx="14" fill="url(#lgfb4)"/>
          <path d="M22 58 L40 26 L58 58 Z" fill="rgba(255,255,255,0.15)"
                stroke="rgba(255,255,255,0.45)" stroke-width="2"/>
          <path d="M31 58 L40 38 L49 58 Z" fill="rgba(255,255,255,0.92)"/>
          <circle cx="40" cy="24" r="5.5" fill="#7dd3fc"/>
          <defs><linearGradient id="lgfb4" x1="0" y1="0" x2="80" y2="80"
            gradientUnits="userSpaceOnUse">
            <stop offset="0%" stop-color="#1e3a8a"/>
            <stop offset="100%" stop-color="#0f4c5c"/>
          </linearGradient></defs>
        </svg>"""

    with st.sidebar:
        # â”€â”€ TOP BAR: brand + pÃ­ldoras de tema â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        st.markdown(
            f"""
            <div class="sb-top-bar">
                <div class="sb-brand-block">
                    <div class="sb-brand-name">Seminario Predictivo</div>
                    <div class="sb-brand-sub">Caso 06 Â· Amazon Reviews</div>
                </div>
                {_theme_pills_html()}
            </div>
            """,
            unsafe_allow_html=True,
        )

        # â”€â”€ Logo â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        st.markdown(
            f'<div class="sb-logo-wrap">{logo_html}</div>',
            unsafe_allow_html=True,
        )

        # â”€â”€ Nav â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        _nav_item("main.py",            _I_HOME,   "Inicio")
        _nav_item(pages["resumen"],     _I_FILE,   "Resumen Ejecutivo")
        _nav_item(pages["exploracion"], _I_SEARCH, "ExploraciÃ³n de Datos")
        _nav_item(pages["modelos"],     _I_CHART,  "Modelos y EvaluaciÃ³n")
        _nav_item(pages["auditoria"],   _I_SHIELD, "AuditorÃ­a en Tiempo Real")
        _nav_item(pages["ranking"],     _I_BAR,    "Ranking y Benchmark")

        # â”€â”€ Autores â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        st.markdown(
            """
            <div style="
                margin-top: 1.4rem;
                padding: 0.75rem 0.6rem 0.6rem;
                border-top: 1px solid rgba(255,255,255,0.12);
            ">
                <div style="
                    color: rgba(248,250,252,0.40);
                    font-size: 0.62rem;
                    font-weight: 700;
                    letter-spacing: 0.08em;
                    text-transform: uppercase;
                    margin-bottom: 0.45rem;
                ">Autores</div>
                <div style="color:rgba(248,250,252,0.82);font-size:0.78rem;line-height:1.9">
                    ArÃ©valo JosÃ©<br>
                    Cholango MÃ³nica<br>
                    Torres Byron
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _nav_item(page: str | None, icon_svg: str, label: str) -> None:
    if page is None:
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:0.5rem;'
            f'padding:0.3rem 0.6rem;color:rgba(248,250,252,0.3);font-size:0.8rem">'
            f'<div class="sb-nav-icon">{icon_svg}</div>{label}</div>',
            unsafe_allow_html=True,
        )
        return
    col_icon, col_link = st.columns([0.18, 0.82], gap="small")
    with col_icon:
        st.markdown(f'<div class="sb-nav-icon">{icon_svg}</div>', unsafe_allow_html=True)
    with col_link:
        st.page_link(page, label=label)
