"""Punto de entrada — Bienvenida y presentación del caso."""

import os
import requests
import streamlit as st
import streamlit.components.v1 as components

from config.constants import DEFAULT_METRICS
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


_ARCH_HTML = """
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: transparent; overflow: hidden; }
  .wrap {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    display: flex;
    align-items: center;
    gap: 0;
    width: 100%;
    padding: 6px 0 10px;
  }
  .node {
    border: 1px solid rgba(128,128,128,0.22);
    border-radius: 10px;
    padding: 11px 15px;
    flex-shrink: 0;
  }
  .nl { font-size: 12px; font-weight: 600; color: #1a1a1a; margin-bottom: 4px; white-space: nowrap; }
  .ns { font-size: 10.5px; color: #888; line-height: 1.65; white-space: nowrap; }
  .arr { flex-shrink:0; padding: 0 5px; color: rgba(128,128,128,0.55); font-size: 15px; line-height:1; }
  .branch {
    display: flex; flex-direction: column;
    align-items: flex-end; flex-shrink: 0;
    width: 30px; gap: 0;
  }
  .branch .hl { height:1px; width:100%; background:rgba(128,128,128,0.28); }
  .branch .vl { width:1px; flex:1; background:rgba(128,128,128,0.28); align-self:flex-end; }
  .merge {
    display: flex; flex-direction: column;
    align-items: flex-start; flex-shrink: 0;
    width: 30px; gap: 0;
  }
  .merge .hl { height:1px; width:100%; background:rgba(128,128,128,0.28); }
  .merge .vl { width:1px; flex:1; background:rgba(128,128,128,0.28); align-self:flex-start; }
  .services { display: flex; flex-direction: column; gap: 8px; flex-shrink: 0; }
</style>

<div class="wrap">

  <!-- Dataset -->
  <div class="node" style="min-width:108px">
    <div class="nl">Dataset</div>
    <div class="ns">Amazon Reviews<br>~100 K filas</div>
  </div>

  <div class="arr">&#8594;</div>

  <!-- Pipeline -->
  <div class="node" style="min-width:148px">
    <div class="nl">Pipeline Python</div>
    <div class="ns">
      Limpieza &amp; dedup<br>
      Feature engineering<br>
      LogReg · LightGBM<br>
      scikit-learn · pandas
    </div>
  </div>

  <!-- Bifurcación -->
  <div class="branch" style="height:88px">
    <div class="hl"></div>
    <div class="vl"></div>
    <div class="hl"></div>
  </div>

  <!-- FastAPI + Supabase -->
  <div class="services">
    <div class="node" style="min-width:136px">
      <div class="nl">FastAPI</div>
      <div class="ns">Render · predicción</div>
    </div>
    <div class="node" style="min-width:136px">
      <div class="nl">Supabase</div>
      <div class="ns">Auditorías · historial</div>
    </div>
  </div>

  <!-- Convergencia -->
  <div class="merge" style="height:88px">
    <div class="hl"></div>
    <div class="vl"></div>
    <div class="hl"></div>
  </div>

  <div class="arr">&#8594;</div>

  <!-- Dashboard -->
  <div class="node" style="min-width:118px">
    <div class="nl">Dashboard</div>
    <div class="ns">Streamlit Cloud<br>5 secciones</div>
  </div>

</div>
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

    # ── Hero ─────────────────────────────────────────────────────────────────
    st.markdown(
        f"""
        <div style="padding: 2.8rem 0 2rem;">

            <div style="
                font-size: 0.68rem; font-weight: 600; letter-spacing: 0.14em;
                text-transform: uppercase; color: var(--muted); margin-bottom: 1.1rem;
            ">
                Seminario Predictivo 2026 &nbsp;·&nbsp; Caso 06
            </div>

            <div style="
                font-size: clamp(2rem, 5vw, 3rem); font-weight: 800;
                letter-spacing: -0.04em; line-height: 1.1;
                color: var(--text); margin-bottom: 1.2rem;
            ">
                Predicción de utilidad<br>
                <span style="color: var(--muted); font-weight: 400;">en reseñas de Amazon</span>
            </div>

            <div style="
                font-size: 0.95rem; color: var(--muted);
                max-width: 520px; line-height: 1.75; margin-bottom: 2.4rem;
            ">
                No todas las reseñas ayudan por igual. Este proyecto identifica
                qué características textuales separan una reseña percibida como útil
                de una que pasa desapercibida — y construye un modelo que lo predice
                antes de que los usuarios voten.
            </div>

            <div style="display:flex; gap:0; border-top:1px solid rgba(0,0,0,0.08);">
                <div style="padding:1.4rem 2.5rem 1.4rem 0; border-right:1px solid rgba(0,0,0,0.08);">
                    <div style="font-size:1.8rem;font-weight:700;color:var(--text);letter-spacing:-0.03em;line-height:1;">
                        {reviews_label}
                    </div>
                    <div style="font-size:0.7rem;text-transform:uppercase;letter-spacing:0.09em;color:var(--muted);margin-top:0.35rem;">
                        Reseñas analizadas
                    </div>
                </div>
                <div style="padding:1.4rem 2.5rem; border-right:1px solid rgba(0,0,0,0.08);">
                    <div style="font-size:1.8rem;font-weight:700;color:var(--text);letter-spacing:-0.03em;line-height:1;">
                        {roc_val}
                    </div>
                    <div style="font-size:0.7rem;text-transform:uppercase;letter-spacing:0.09em;color:var(--muted);margin-top:0.35rem;">
                        ROC-AUC &nbsp;·&nbsp; {model_val}
                    </div>
                </div>
                <div style="padding:1.4rem 2.5rem;">
                    <div style="font-size:1.8rem;font-weight:700;color:var(--text);letter-spacing:-0.03em;line-height:1;">
                        4
                    </div>
                    <div style="font-size:0.7rem;text-transform:uppercase;letter-spacing:0.09em;color:var(--muted);margin-top:0.35rem;">
                        Features textuales
                    </div>
                </div>
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Arquitectura del proyecto ─────────────────────────────────────────────
    st.markdown(
        '<div style="font-size:0.68rem;font-weight:600;letter-spacing:0.12em;'
        'text-transform:uppercase;color:var(--muted);margin-bottom:0.8rem;">'
        'Arquitectura del proyecto</div>',
        unsafe_allow_html=True,
    )
    # components.html evita la sanitización que aplica st.markdown al HTML/SVG
    components.html(_ARCH_HTML, height=130, scrolling=False)

    st.markdown("<div style='height: 1rem'></div>", unsafe_allow_html=True)

    # ── Estado de la API ──────────────────────────────────────────────────────
    with st.spinner(""):
        api_status = _get_api_status()
    api_ok = api_status.get("status") == "ok"
    lgb_ok = "✓" in api_status.get("modelos", {}).get("lgb_model", "") if api_ok else False

    st.markdown(
        f"""
        <div class="api-status-grid">
            <div class="api-card">
                <div class="api-card-label">FastAPI · Render</div>
                <div class="api-card-value">proyecto-prediccion-v9qk</div>
                <span class="metric-badge {'metric-badge-good' if api_ok else 'metric-badge-warn'}">
                    {'Activa' if api_ok else 'Sin respuesta'}
                </span>
            </div>
            <div class="api-card">
                <div class="api-card-label">Modelo en API</div>
                <div class="api-card-value">LightGBM</div>
                <span class="metric-badge {'metric-badge-good' if lgb_ok else 'metric-badge-warn'}">
                    {'Cargado' if lgb_ok else 'Heurística'}
                </span>
            </div>
            <div class="api-card">
                <div class="api-card-label">Endpoint predicción</div>
                <div class="api-card-value">POST /reviews/predict_helpfulness</div>
            </div>
            <div class="api-card">
                <div class="api-card-label">Endpoint palabras clave</div>
                <div class="api-card-value">GET /reviews/top_words</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Equipo ────────────────────────────────────────────────────────────────
    st.markdown("<div style='height: 1.5rem'></div>", unsafe_allow_html=True)
    st.markdown(
        '<div style="font-size:0.68rem;font-weight:600;letter-spacing:0.12em;'
        'text-transform:uppercase;color:var(--muted);margin-bottom:1rem;">'
        'Equipo</div>',
        unsafe_allow_html=True,
    )

    t1, t2, t3 = st.columns(3, gap="medium")
    team = [
        ("Arévalo José",    "EDA & Pipeline"),
        ("Cholango Mónica", "Modelado & API"),
        ("Torres Byron",    "Dashboard & UI"),
    ]
    for col, (name, role) in zip([t1, t2, t3], team):
        initials = "".join(p[0] for p in name.split())
        with col:
            st.markdown(
                f"""
                <div style="
                    padding:1.2rem 1rem;
                    border:1px solid rgba(0,0,0,0.08);
                    border-radius:10px;
                    display:flex; align-items:center; gap:0.9rem;
                ">
                    <div style="
                        width:36px; height:36px; border-radius:50%;
                        background:rgba(0,0,0,0.05);
                        display:flex; align-items:center; justify-content:center;
                        font-size:0.7rem; font-weight:700; color:#888;
                        flex-shrink:0; letter-spacing:0.03em;
                    ">{initials}</div>
                    <div>
                        <div style="font-size:0.85rem;font-weight:600;color:var(--text);">{name}</div>
                        <div style="font-size:0.75rem;color:var(--muted);margin-top:0.1rem;">{role}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


if __name__ == "__main__":
    main()