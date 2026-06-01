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
    api_badge_cls  = "badge-ok"  if api_ok  else "badge-warn"
    api_badge_txt  = "Activa"    if api_ok  else "Sin respuesta"
    lgb_badge_cls  = "badge-ok"  if lgb_ok  else "badge-warn"
    lgb_badge_txt  = "Cargado"   if lgb_ok  else "Heurística"

    return f"""
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html, body {{ background: transparent; overflow-x: hidden; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    color: #1a1a1a;
    padding: 0 2px 32px;
  }}

  /* ── Hero ── */
  .eyebrow {{
    font-size: 0.65rem; font-weight: 600; letter-spacing: 0.14em;
    text-transform: uppercase; color: #888; margin-bottom: 1rem;
    padding-top: 2rem;
  }}
  .headline {{
    font-size: clamp(1.8rem, 5vw, 2.8rem); font-weight: 800;
    letter-spacing: -0.04em; line-height: 1.1; margin-bottom: 1.1rem;
    color: #111;
  }}
  .headline .sub {{ color: #999; font-weight: 400; }}
  .body-text {{
    font-size: 0.9rem; color: #777; max-width: 500px;
    line-height: 1.75; margin-bottom: 2.2rem;
  }}
  .stats {{
    display: flex; gap: 0;
    border-top: 1px solid rgba(0,0,0,0.08);
    margin-bottom: 2.4rem;
  }}
  .stat {{
    padding: 1.2rem 2rem 1.2rem 0;
    border-right: 1px solid rgba(0,0,0,0.08);
    margin-right: 2rem;
  }}
  .stat:last-child {{ border-right: none; margin-right: 0; }}
  .stat-val {{
    font-size: 1.7rem; font-weight: 700; color: #111;
    letter-spacing: -0.03em; line-height: 1;
  }}
  .stat-lbl {{
    font-size: 0.62rem; text-transform: uppercase;
    letter-spacing: 0.09em; color: #999; margin-top: 0.3rem;
  }}

  /* ── Section label ── */
  .section-lbl {{
    font-size: 0.62rem; font-weight: 600; letter-spacing: 0.12em;
    text-transform: uppercase; color: #999; margin-bottom: 1rem;
  }}

  /* ── Arquitectura ── */
  .arch {{
    display: flex; align-items: center;
    gap: 0; margin-bottom: 2.4rem; flex-wrap: nowrap;
    overflow-x: auto; padding-bottom: 4px;
  }}
  .node {{
    border: 1px solid rgba(0,0,0,0.1);
    border-radius: 10px; padding: 10px 14px;
    flex-shrink: 0; background: #fff;
  }}
  .node-title {{ font-size: 11.5px; font-weight: 600; color: #1a1a1a; margin-bottom: 3px; white-space: nowrap; }}
  .node-sub   {{ font-size: 10px; color: #999; line-height: 1.6; white-space: nowrap; }}
  .node-tag {{
    display: inline-block; margin-top: 5px;
    font-size: 9px; font-weight: 600; letter-spacing: 0.06em;
    text-transform: uppercase; padding: 2px 7px; border-radius: 99px;
    background: rgba(0,0,0,0.05); color: #888;
  }}
  .arrow {{ flex-shrink: 0; padding: 0 4px; color: #ccc; font-size: 14px; }}
  .branch {{
    display: flex; flex-direction: column;
    align-items: flex-end; flex-shrink: 0; width: 28px;
  }}
  .branch .hl {{ height: 1px; width: 100%; background: rgba(0,0,0,0.12); }}
  .branch .vl {{ width: 1px; flex: 1; background: rgba(0,0,0,0.12); align-self: flex-end; }}
  .merge {{
    display: flex; flex-direction: column;
    align-items: flex-start; flex-shrink: 0; width: 28px;
  }}
  .merge .hl {{ height: 1px; width: 100%; background: rgba(0,0,0,0.12); }}
  .merge .vl {{ width: 1px; flex: 1; background: rgba(0,0,0,0.12); align-self: flex-start; }}
  .services {{ display: flex; flex-direction: column; gap: 8px; flex-shrink: 0; }}

  /* ── API status grid ── */
  .api-grid {{
    display: grid; grid-template-columns: 1fr 1fr;
    gap: 10px; margin-bottom: 2.2rem;
  }}
  .api-card {{
    border: 1px solid rgba(0,0,0,0.08); border-radius: 10px;
    padding: 14px 16px;
  }}
  .api-lbl  {{ font-size: 10.5px; color: #999; margin-bottom: 4px; }}
  .api-val  {{ font-size: 13px; font-weight: 600; color: #111; margin-bottom: 8px; }}
  .badge-ok   {{ display:inline-block; font-size:10px; font-weight:600; padding:2px 10px; border-radius:99px; background:#dcfce7; color:#166534; }}
  .badge-warn {{ display:inline-block; font-size:10px; font-weight:600; padding:2px 10px; border-radius:99px; background:#fef9c3; color:#854d0e; }}

  /* ── Equipo ── */
  .team-grid {{
    display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px;
  }}
  .team-card {{
    border: 1px solid rgba(0,0,0,0.08); border-radius: 10px;
    padding: 14px 14px; display: flex; align-items: center; gap: 12px;
  }}
  .avatar {{
    width: 34px; height: 34px; border-radius: 50%;
    background: rgba(0,0,0,0.05);
    display: flex; align-items: center; justify-content: center;
    font-size: 10px; font-weight: 700; color: #888; flex-shrink: 0;
    letter-spacing: 0.03em;
  }}
  .team-name {{ font-size: 13px; font-weight: 600; color: #111; }}
  .team-role {{ font-size: 11px; color: #999; margin-top: 2px; }}
</style>
</head>
<body>

<!-- ── Hero ────────────────────────────────────────────────────────────── -->
<div class="eyebrow">Seminario Predictivo 2026 &nbsp;·&nbsp; Caso 06</div>

<div class="headline">
  Predicción de utilidad<br>
  <span class="sub">en reseñas de Amazon</span>
</div>

<p class="body-text">
  No todas las reseñas ayudan por igual. Este proyecto identifica qué
  características textuales separan una reseña percibida como útil de una que
  pasa desapercibida — y construye un modelo que lo predice antes de que los
  usuarios voten.
</p>

<div class="stats">
  <div class="stat">
    <div class="stat-val">{reviews_label}</div>
    <div class="stat-lbl">Reseñas analizadas</div>
  </div>
  <div class="stat">
    <div class="stat-val">{roc_val}</div>
    <div class="stat-lbl">ROC-AUC &nbsp;·&nbsp; {model_val}</div>
  </div>
  <div class="stat">
    <div class="stat-val">4</div>
    <div class="stat-lbl">Features textuales</div>
  </div>
</div>

<!-- ── Arquitectura ─────────────────────────────────────────────────────── -->
<div class="section-lbl">Arquitectura del proyecto</div>

<div class="arch">

  <!-- Dataset -->
  <div class="node" style="min-width:108px">
    <div class="node-title">Dataset</div>
    <div class="node-sub">Amazon Reviews<br>~100 K filas</div>
  </div>

  <div class="arrow">&#8594;</div>

  <!-- Pipeline -->
  <div class="node" style="min-width:148px">
    <div class="node-title">Pipeline Python</div>
    <div class="node-sub">
      Limpieza &amp; dedup<br>
      Feature engineering<br>
      LogReg · LightGBM
    </div>
  </div>

  <!-- Bifurcación -->
  <div class="branch" style="height:86px">
    <div class="hl"></div>
    <div class="vl"></div>
    <div class="hl"></div>
  </div>

  <!-- FastAPI + Supabase -->
  <div class="services">
    <div class="node" style="min-width:148px">
      <div class="node-title">FastAPI</div>
      <div class="node-sub">POST /predict_helpfulness<br>GET /top_words</div>
      <span class="node-tag">Render</span>
    </div>
    <div class="node" style="min-width:148px">
      <div class="node-title">Supabase</div>
      <div class="node-sub">Auditorías · historial<br>PostgreSQL</div>
      <span class="node-tag">Supabase Cloud</span>
    </div>
  </div>

  <!-- Convergencia -->
  <div class="merge" style="height:86px">
    <div class="hl"></div>
    <div class="vl"></div>
    <div class="hl"></div>
  </div>

  <div class="arrow">&#8594;</div>

  <!-- Dashboard -->
  <div class="node" style="min-width:120px">
    <div class="node-title">Dashboard</div>
    <div class="node-sub">5 secciones<br>Streamlit</div>
    <span class="node-tag">Streamlit Cloud</span>
  </div>

</div>

<!-- ── Estado de la API ──────────────────────────────────────────────────── -->
<div class="section-lbl">Estado de la API</div>
<div class="api-grid">
  <div class="api-card">
    <div class="api-lbl">FastAPI · Render</div>
    <div class="api-val">proyecto-prediccion-v9qk</div>
    <span class="{api_badge_cls}">{api_badge_txt}</span>
  </div>
  <div class="api-card">
    <div class="api-lbl">Modelo en API</div>
    <div class="api-val">LightGBM</div>
    <span class="{lgb_badge_cls}">{lgb_badge_txt}</span>
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

<!-- ── Equipo ────────────────────────────────────────────────────────────── -->
<div class="section-lbl">Equipo</div>
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
</html>
"""


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

    # Todo el contenido de inicio en un único components.html
    # para evitar que st.markdown sanitice el HTML/CSS
    components.html(
        _build_page_html(
            reviews_label=reviews_label,
            roc_val=roc_val,
            model_val=model_val,
            api_ok=api_ok,
            lgb_ok=lgb_ok,
        ),
        height=980,
        scrolling=False,
    )


if __name__ == "__main__":
    main()