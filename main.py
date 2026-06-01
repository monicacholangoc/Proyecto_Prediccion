"""Punto de entrada — Bienvenida y presentación del caso."""

import os
import requests
import streamlit as st

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

    best      = metrics_df.sort_values("roc_auc", ascending=False).iloc[0] if not metrics_df.empty else None
    roc_val   = format_percentage(float(best["roc_auc"])) if best is not None else "—"
    model_val = str(best["modelo"])                        if best is not None else "—"
    reviews_label = format_compact_number(total_reviews_count) if has_reviews else "~100 K"

    # ── Hero ─────────────────────────────────────────────────────────────────
    st.markdown(
        f"""
        <div style="padding: 2.8rem 0 2rem;">

            <div style="
                font-size: 0.68rem;
                font-weight: 600;
                letter-spacing: 0.14em;
                text-transform: uppercase;
                color: var(--muted);
                margin-bottom: 1.1rem;
            ">
                Seminario Predictivo 2026 &nbsp;·&nbsp; Caso 06
            </div>

            <div style="
                font-size: clamp(2rem, 5vw, 3rem);
                font-weight: 800;
                letter-spacing: -0.04em;
                line-height: 1.1;
                color: var(--text);
                margin-bottom: 1.2rem;
            ">
                Predicción de utilidad<br>
                <span style="color: var(--muted); font-weight: 400;">en reseñas de Amazon</span>
            </div>

            <div style="
                font-size: 0.95rem;
                color: var(--muted);
                max-width: 520px;
                line-height: 1.75;
                margin-bottom: 2.4rem;
            ">
                No todas las reseñas ayudan por igual. Este proyecto identifica
                qué características textuales separan una reseña percibida como útil
                de una que pasa desapercibida — y construye un modelo que lo predice
                antes de que los usuarios voten.
            </div>

            <div style="display: flex; gap: 0; border-top: 1px solid var(--border, rgba(0,0,0,0.08));">
                <div style="padding: 1.4rem 2.5rem 1.4rem 0; border-right: 1px solid var(--border, rgba(0,0,0,0.08));">
                    <div style="font-size: 1.8rem; font-weight: 700; color: var(--text); letter-spacing: -0.03em; line-height: 1;">
                        {reviews_label}
                    </div>
                    <div style="font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.09em; color: var(--muted); margin-top: 0.35rem;">
                        Reseñas analizadas
                    </div>
                </div>
                <div style="padding: 1.4rem 2.5rem; border-right: 1px solid var(--border, rgba(0,0,0,0.08));">
                    <div style="font-size: 1.8rem; font-weight: 700; color: var(--text); letter-spacing: -0.03em; line-height: 1;">
                        {roc_val}
                    </div>
                    <div style="font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.09em; color: var(--muted); margin-top: 0.35rem;">
                        ROC-AUC &nbsp;·&nbsp; {model_val}
                    </div>
                </div>
                <div style="padding: 1.4rem 2.5rem;">
                    <div style="font-size: 1.8rem; font-weight: 700; color: var(--text); letter-spacing: -0.03em; line-height: 1;">
                        4
                    </div>
                    <div style="font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.09em; color: var(--muted); margin-top: 0.35rem;">
                        Features textuales
                    </div>
                </div>
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Separador ────────────────────────────────────────────────────────────
    st.markdown("<div style='height: 0.5rem'></div>", unsafe_allow_html=True)

    # ── Arquitectura del proyecto ─────────────────────────────────────────────
    st.markdown(
        '<div style="font-size:0.68rem;font-weight:600;letter-spacing:0.12em;'
        'text-transform:uppercase;color:var(--muted);margin-bottom:1.2rem;">'
        'Arquitectura del proyecto</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <svg width="100%" viewBox="0 0 760 210" role="img"
             xmlns="http://www.w3.org/2000/svg"
             style="display:block; max-width:760px;">

            <title>Arquitectura del proyecto</title>
            <desc>Flujo de datos: Dataset → Pipeline Python → FastAPI + Supabase → Dashboard Streamlit</desc>

            <defs>
                <marker id="arr" viewBox="0 0 10 10" refX="8" refY="5"
                        markerWidth="5" markerHeight="5" orient="auto-start-reverse">
                    <path d="M2 1L8 5L2 9" fill="none" stroke="context-stroke"
                          stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
                </marker>
            </defs>

            <!-- ── Nodo 1: Dataset ── -->
            <rect x="20" y="72" width="116" height="64" rx="10"
                  fill="none" stroke="rgba(128,128,128,0.25)" stroke-width="1"/>
            <text x="78" y="97" text-anchor="middle"
                  font-size="12" font-weight="600"
                  fill="var(--text, #1a1a1a)">Dataset</text>
            <text x="78" y="114" text-anchor="middle"
                  font-size="10" fill="var(--muted, #6b6b6b)">Amazon Reviews</text>
            <text x="78" y="128" text-anchor="middle"
                  font-size="10" fill="var(--muted, #6b6b6b)">~100 K filas</text>

            <!-- ── Flecha 1→2 ── -->
            <line x1="136" y1="104" x2="172" y2="104"
                  stroke="rgba(128,128,128,0.35)" stroke-width="1.2"
                  marker-end="url(#arr)" fill="none"/>

            <!-- ── Nodo 2: Pipeline ── -->
            <rect x="172" y="52" width="160" height="104" rx="10"
                  fill="none" stroke="rgba(128,128,128,0.25)" stroke-width="1"/>
            <text x="252" y="78" text-anchor="middle"
                  font-size="12" font-weight="600"
                  fill="var(--text, #1a1a1a)">Pipeline Python</text>
            <text x="252" y="97"  text-anchor="middle" font-size="10" fill="var(--muted, #6b6b6b)">Limpieza · dedup</text>
            <text x="252" y="112" text-anchor="middle" font-size="10" fill="var(--muted, #6b6b6b)">Feature engineering</text>
            <text x="252" y="127" text-anchor="middle" font-size="10" fill="var(--muted, #6b6b6b)">LogReg · LightGBM</text>
            <text x="252" y="142" text-anchor="middle" font-size="10" fill="var(--muted, #6b6b6b)">scikit-learn · pandas</text>

            <!-- ── Flecha 2→3a ── -->
            <line x1="332" y1="84" x2="400" y2="84"
                  stroke="rgba(128,128,128,0.35)" stroke-width="1.2"
                  marker-end="url(#arr)" fill="none"/>

            <!-- ── Flecha 2→3b ── -->
            <line x1="332" y1="124" x2="400" y2="124"
                  stroke="rgba(128,128,128,0.35)" stroke-width="1.2"
                  marker-end="url(#arr)" fill="none"/>

            <!-- ── Nodo 3a: FastAPI ── -->
            <rect x="400" y="52" width="140" height="56" rx="10"
                  fill="none" stroke="rgba(128,128,128,0.25)" stroke-width="1"/>
            <text x="470" y="76" text-anchor="middle"
                  font-size="12" font-weight="600"
                  fill="var(--text, #1a1a1a)">FastAPI</text>
            <text x="470" y="93" text-anchor="middle"
                  font-size="10" fill="var(--muted, #6b6b6b)">Render · predicción</text>

            <!-- ── Nodo 3b: Supabase ── -->
            <rect x="400" y="100" width="140" height="56" rx="10"
                  fill="none" stroke="rgba(128,128,128,0.25)" stroke-width="1"/>
            <text x="470" y="124" text-anchor="middle"
                  font-size="12" font-weight="600"
                  fill="var(--text, #1a1a1a)">Supabase</text>
            <text x="470" y="141" text-anchor="middle"
                  font-size="10" fill="var(--muted, #6b6b6b)">Auditorías · historial</text>

            <!-- ── Flecha 3→4 (desde FastAPI y Supabase hacia Dashboard) ── -->
            <line x1="540" y1="80" x2="576" y2="80"
                  stroke="rgba(128,128,128,0.35)" stroke-width="1.2" fill="none"/>
            <line x1="540" y1="128" x2="576" y2="128"
                  stroke="rgba(128,128,128,0.35)" stroke-width="1.2" fill="none"/>
            <line x1="576" y1="80" x2="576" y2="128"
                  stroke="rgba(128,128,128,0.35)" stroke-width="1.2" fill="none"/>
            <line x1="576" y1="104" x2="610" y2="104"
                  stroke="rgba(128,128,128,0.35)" stroke-width="1.2"
                  marker-end="url(#arr)" fill="none"/>

            <!-- ── Nodo 4: Dashboard ── -->
            <rect x="610" y="72" width="130" height="64" rx="10"
                  fill="none" stroke="rgba(128,128,128,0.25)" stroke-width="1"/>
            <text x="675" y="97" text-anchor="middle"
                  font-size="12" font-weight="600"
                  fill="var(--text, #1a1a1a)">Dashboard</text>
            <text x="675" y="114" text-anchor="middle"
                  font-size="10" fill="var(--muted, #6b6b6b)">Streamlit Cloud</text>
            <text x="675" y="128" text-anchor="middle"
                  font-size="10" fill="var(--muted, #6b6b6b)">5 secciones</text>

        </svg>
        """,
        unsafe_allow_html=True,
    )

    # ── Separador ────────────────────────────────────────────────────────────
    st.markdown("<div style='height: 1.5rem'></div>", unsafe_allow_html=True)

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
        ("Arévalo José",   "EDA & Pipeline"),
        ("Cholango Mónica", "Modelado & API"),
        ("Torres Byron",    "Dashboard & UI"),
    ]
    for col, (name, role) in zip([t1, t2, t3], team):
        initials = "".join(p[0] for p in name.split())
        with col:
            st.markdown(
                f"""
                <div style="
                    padding: 1.2rem 1rem;
                    border: 1px solid var(--border, rgba(0,0,0,0.08));
                    border-radius: 10px;
                    display: flex;
                    align-items: center;
                    gap: 0.9rem;
                ">
                    <div style="
                        width: 36px; height: 36px; border-radius: 50%;
                        background: var(--border, rgba(0,0,0,0.06));
                        display: flex; align-items: center; justify-content: center;
                        font-size: 0.7rem; font-weight: 700;
                        color: var(--muted); flex-shrink: 0;
                        letter-spacing: 0.03em;
                    ">{initials}</div>
                    <div>
                        <div style="font-size: 0.85rem; font-weight: 600; color: var(--text);">{name}</div>
                        <div style="font-size: 0.75rem; color: var(--muted); margin-top: 0.1rem;">{role}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


if __name__ == "__main__":
    main()