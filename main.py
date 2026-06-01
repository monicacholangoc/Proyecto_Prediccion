"""Punto de entrada — Bienvenida y presentación del caso."""

import os
import requests
import streamlit as st
import streamlit.components.v1 as components

from config.theme import PAGE_CONFIG
from services.data_loader import load_processed_reviews
from services.supabase_service import load_reviews_from_supabase
from services.model_eval_service import compute_model_evaluation
from utils.formatters import format_compact_number, format_percentage
from utils.state import initialize_state
from shared_sidebar import render_sidebar


def _setup() -> None:
    with open("styles/styles.css", "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    render_sidebar()


def _api_url() -> str:
    try:
        return st.secrets["API_URL"].rstrip("/")
    except Exception:
        return os.getenv("API_URL", "https://proyecto-prediccion-v9qk.onrender.com").rstrip("/")


def _get_api_status() -> dict:
    try:
        r = requests.get(_api_url() + "/", timeout=8)
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        return {"status": "error", "detalle": str(exc)}


def _build_page_html(
    reviews_label: str,
    roc_val: str,
    model_val: str,
    api_ok: bool,
    lgb_ok: bool,
) -> str:
    api_badge_txt = "Activa"   if api_ok  else "Sin respuesta"
    lgb_badge_txt = "Cargado"  if lgb_ok  else "Heurística"
    api_badge_ok  = "true"     if api_ok  else "false"
    lgb_badge_ok  = "true"     if lgb_ok  else "false"

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html {{ height: 100%; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    background: transparent;
    padding: 0 0 36px;
    /* colores base — se sobreescriben por dark mode */
    --c-bg:       #ffffff;
    --c-text:     #111111;
    --c-muted:    #777777;
    --c-faint:    #aaaaaa;
    --c-border:   rgba(0,0,0,0.09);
    --c-surface:  #f7f7f5;
    --c-ok-bg:    #dcfce7;
    --c-ok-txt:   #166534;
    --c-warn-bg:  #fef9c3;
    --c-warn-txt: #854d0e;
    color: var(--c-text);
  }}

  /* ── dark mode automático ── */
  @media (prefers-color-scheme: dark) {{
    body {{
      --c-bg:       #0e1117;
      --c-text:     #e8e8e8;
      --c-muted:    #999999;
      --c-faint:    #555555;
      --c-border:   rgba(255,255,255,0.09);
      --c-surface:  #1a1d27;
      --c-ok-bg:    #14532d;
      --c-ok-txt:   #86efac;
      --c-warn-bg:  #422006;
      --c-warn-txt: #fcd34d;
    }}
  }}

  /* ── Hero ──────────────────────────────────────────────────── */
  .eyebrow {{
    font-size: 0.62rem; font-weight: 600; letter-spacing: 0.15em;
    text-transform: uppercase; color: var(--c-faint);
    padding-top: 2rem; margin-bottom: 0.9rem;
  }}
  .headline {{
    font-size: clamp(1.9rem, 4.5vw, 2.9rem);
    font-weight: 800; letter-spacing: -0.04em;
    line-height: 1.08; margin-bottom: 1.1rem; color: var(--c-text);
  }}
  .headline-sub {{
    font-weight: 400; color: var(--c-muted);
  }}
  .body-txt {{
    font-size: 0.88rem; color: var(--c-muted);
    max-width: 480px; line-height: 1.8; margin-bottom: 2rem;
  }}
  .stats {{
    display: flex; gap: 0;
    border-top: 1px solid var(--c-border);
    margin-bottom: 2.6rem;
  }}
  .stat {{
    padding: 1.2rem 2.2rem 1.2rem 0;
    border-right: 1px solid var(--c-border);
    margin-right: 2.2rem;
  }}
  .stat:last-child {{ border-right: none; margin-right: 0; }}
  .stat-val {{
    font-size: 1.75rem; font-weight: 700; color: var(--c-text);
    letter-spacing: -0.03em; line-height: 1;
  }}
  .stat-lbl {{
    font-size: 0.6rem; text-transform: uppercase;
    letter-spacing: 0.1em; color: var(--c-faint); margin-top: 0.3rem;
  }}

  /* ── Section label ─────────────────────────────────────────── */
  .section-lbl {{
    font-size: 0.6rem; font-weight: 700; letter-spacing: 0.13em;
    text-transform: uppercase; color: var(--c-faint); margin-bottom: 1rem;
  }}

  /* ── Arquitectura ──────────────────────────────────────────── */
  .arch {{
    display: flex; align-items: center; flex-wrap: nowrap;
    margin-bottom: 2.6rem; overflow-x: auto; padding-bottom: 2px;
    gap: 0;
  }}
  .node {{
    border: 1px solid var(--c-border); border-radius: 10px;
    padding: 11px 15px; flex-shrink: 0;
    background: var(--c-surface);
  }}
  .node-title {{
    font-size: 11.5px; font-weight: 700; color: var(--c-text);
    margin-bottom: 4px; white-space: nowrap;
  }}
  .node-sub {{
    font-size: 10px; color: var(--c-muted); line-height: 1.65; white-space: nowrap;
  }}
  .node-tag {{
    display: inline-block; margin-top: 6px;
    font-size: 8.5px; font-weight: 700; letter-spacing: 0.07em;
    text-transform: uppercase; padding: 2px 8px; border-radius: 99px;
    background: var(--c-border); color: var(--c-muted);
    border: 1px solid var(--c-border);
  }}
  .arrow {{ flex-shrink: 0; padding: 0 4px; color: var(--c-faint); font-size: 14px; }}
  .branch {{
    display: flex; flex-direction: column;
    align-items: flex-end; flex-shrink: 0; width: 26px;
  }}
  .hl {{ height: 1px; width: 100%; background: var(--c-border); }}
  .vl-r {{ width: 1px; flex: 1; background: var(--c-border); align-self: flex-end; }}
  .merge {{
    display: flex; flex-direction: column;
    align-items: flex-start; flex-shrink: 0; width: 26px;
  }}
  .vl-l {{ width: 1px; flex: 1; background: var(--c-border); align-self: flex-start; }}
  .services {{ display: flex; flex-direction: column; gap: 8px; flex-shrink: 0; }}

  /* ── API status ────────────────────────────────────────────── */
  .api-grid {{
    display: grid; grid-template-columns: 1fr 1fr;
    gap: 10px; margin-bottom: 2.2rem;
  }}
  .api-card {{
    border: 1px solid var(--c-border); border-radius: 10px;
    padding: 14px 16px; background: var(--c-surface);
  }}
  .api-lbl {{ font-size: 10px; color: var(--c-faint); margin-bottom: 5px; }}
  .api-val {{ font-size: 13px; font-weight: 600; color: var(--c-text); margin-bottom: 8px; }}
  .badge {{
    display: inline-block; font-size: 9.5px; font-weight: 700;
    padding: 2px 10px; border-radius: 99px;
  }}
  .badge[data-ok="true"]  {{ background: var(--c-ok-bg);   color: var(--c-ok-txt); }}
  .badge[data-ok="false"] {{ background: var(--c-warn-bg); color: var(--c-warn-txt); }}

  /* ── Equipo ────────────────────────────────────────────────── */
  .team-grid {{
    display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px;
  }}
  .team-card {{
    border: 1px solid var(--c-border); border-radius: 10px;
    padding: 14px; display: flex; align-items: center; gap: 12px;
    background: var(--c-surface);
  }}
  .avatar {{
    width: 34px; height: 34px; border-radius: 50%;
    background: var(--c-border);
    display: flex; align-items: center; justify-content: center;
    font-size: 9.5px; font-weight: 700; color: var(--c-muted);
    flex-shrink: 0; letter-spacing: 0.04em;
  }}
  .team-name {{ font-size: 12.5px; font-weight: 600; color: var(--c-text); }}
  .team-role {{ font-size: 10.5px; color: var(--c-muted); margin-top: 2px; }}
</style>
</head>
<body>

<!-- ── Hero ─────────────────────────────────────────────────────────────── -->
<p class="eyebrow">Seminario Predictivo 2026 &nbsp;&middot;&nbsp; Caso 06</p>

<h1 class="headline">
  Predicción de utilidad<br>
  <span class="headline-sub">en reseñas de Amazon</span>
</h1>

<p class="body-txt">
  No todas las reseñas ayudan por igual. Este proyecto identifica qué
  características textuales separan una reseña percibida como útil de una
  que pasa desapercibida — y construye un modelo que lo predice antes de
  que los usuarios voten.
</p>

<div class="stats">
  <div class="stat">
    <div class="stat-val">{reviews_label}</div>
    <div class="stat-lbl">Reseñas analizadas</div>
  </div>
  <div class="stat">
    <div class="stat-val">{roc_val}</div>
    <div class="stat-lbl">ROC-AUC &nbsp;&middot;&nbsp; {model_val}</div>
  </div>
  <div class="stat">
    <div class="stat-val">4</div>
    <div class="stat-lbl">Features textuales</div>
  </div>
</div>

<!-- ── Arquitectura ──────────────────────────────────────────────────────── -->
<p class="section-lbl">Arquitectura del proyecto</p>

<div class="arch">
  <div class="node" style="min-width:108px">
    <div class="node-title">Dataset</div>
    <div class="node-sub">Amazon Reviews<br>~100 K filas</div>
  </div>

  <div class="arrow">&#8594;</div>

  <div class="node" style="min-width:148px">
    <div class="node-title">Pipeline Python</div>
    <div class="node-sub">Limpieza &amp; dedup<br>Feature engineering<br>LogReg &middot; LightGBM</div>
  </div>

  <div class="branch" style="height:92px">
    <div class="hl"></div>
    <div class="vl-r"></div>
    <div class="hl"></div>
  </div>

  <div class="services">
    <div class="node" style="min-width:155px">
      <div class="node-title">FastAPI</div>
      <div class="node-sub">POST /predict_helpfulness<br>GET /top_words</div>
      <span class="node-tag">Render</span>
    </div>
    <div class="node" style="min-width:155px">
      <div class="node-title">Supabase</div>
      <div class="node-sub">Auditorías &middot; historial<br>PostgreSQL</div>
      <span class="node-tag">Supabase Cloud</span>
    </div>
  </div>

  <div class="merge" style="height:92px">
    <div class="hl"></div>
    <div class="vl-l"></div>
    <div class="hl"></div>
  </div>

  <div class="arrow">&#8594;</div>

  <div class="node" style="min-width:118px">
    <div class="node-title">Dashboard</div>
    <div class="node-sub">5 secciones<br>Streamlit</div>
    <span class="node-tag">Streamlit Cloud</span>
  </div>
</div>

<!-- ── Estado de la API ───────────────────────────────────────────────────── -->
<p class="section-lbl">Estado de la API</p>
<div class="api-grid">
  <div class="api-card">
    <div class="api-lbl">FastAPI &middot; Render</div>
    <div class="api-val">proyecto-prediccion-v9qk</div>
    <span class="badge" data-ok="{api_badge_ok}">{api_badge_txt}</span>
  </div>
  <div class="api-card">
    <div class="api-lbl">Modelo en API</div>
    <div class="api-val">LightGBM</div>
    <span class="badge" data-ok="{lgb_badge_ok}">{lgb_badge_txt}</span>
  </div>
  <div class="api-card">
    <div class="api-lbl">Endpoint predicción</div>
    <div class="api-val">POST /reviews/predict_helpfulness</div>
  </div>
  <div class="api-card">
    <div class="api-lbl">Endpoint palabras clave</div>
    <div class="api-val">GET /reviews/top_words</div>
  </div>
</div>

<!-- ── Equipo ─────────────────────────────────────────────────────────────── -->
<p class="section-lbl">Equipo</p>
<div class="team-grid">
  <div class="team-card">
    <div class="avatar">AJ</div>
    <div><div class="team-name">Arévalo José</div><div class="team-role">EDA &amp; Pipeline</div></div>
  </div>
  <div class="team-card">
    <div class="avatar">CM</div>
    <div><div class="team-name">Cholango Mónica</div><div class="team-role">Modelado &amp; API</div></div>
  </div>
  <div class="team-card">
    <div class="avatar">TB</div>
    <div><div class="team-name">Torres Byron</div><div class="team-role">Dashboard &amp; UI</div></div>
  </div>
</div>

</body>
</html>"""


def main() -> None:
    st.set_page_config(**PAGE_CONFIG)
    _setup()
    initialize_state()
    st.session_state["app_initialized"] = True

    reviews    = load_processed_reviews()
    evaluation = compute_model_evaluation()
    metrics_df = evaluation["metrics"]
    has_reviews = not reviews.empty

    try:
        sb_count = len(load_reviews_from_supabase())
    except Exception:
        sb_count = 0
    total_reviews_count = len(reviews) + sb_count

    best          = metrics_df.sort_values("roc_auc", ascending=False).iloc[0] if not metrics_df.empty else None
    roc_val       = format_percentage(float(best["roc_auc"])) if best is not None else "—"
    model_val     = str(best["modelo"])                        if best is not None else "—"
    reviews_label = format_compact_number(total_reviews_count) if has_reviews else "~100 K"

    with st.spinner(""):
        api_status = _get_api_status()
    api_ok = api_status.get("status") == "ok"
    lgb_ok = "✓" in api_status.get("modelos", {}).get("lgb_model", "") if api_ok else False

    components.html(
        _build_page_html(
            reviews_label=reviews_label,
            roc_val=roc_val,
            model_val=model_val,
            api_ok=api_ok,
            lgb_ok=lgb_ok,
        ),
        height=950,
        scrolling=False,
    )


if __name__ == "__main__":
    main()