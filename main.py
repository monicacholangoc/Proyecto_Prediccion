"""Punto de entrada — portada dashboard completo.

Layout tipo executive dashboard:
- Logo + branding en sidebar
- Hero compacto
- KPIs en fila
- Mini-charts inline
- API status
"""

import os

import requests
import streamlit as st

from components.cards import render_metric_card
from components.headers import render_app_hero
from config.constants import DEFAULT_METRICS
from config.theme import PAGE_CONFIG
from services.catalog_service import get_product_catalog
from services.data_loader import load_processed_reviews
from services.feature_service import add_basic_text_features
from services.model_eval_service import compute_model_evaluation
from services.preprocessing_service import get_corporate_audit_db
from utils.formatters import format_compact_number, format_percentage
from utils.state import initialize_state
from plots.eda_charts import build_stars_distribution, build_review_length_distribution, build_target_balance
from plots.model_charts import build_model_metrics_chart


def load_css() -> None:
    with open("styles/styles.css", "r", encoding="utf-8") as css_file:
        st.markdown(f"<style>{css_file.read()}</style>", unsafe_allow_html=True)


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


# ── Estilos extra para el dashboard ───────────────────────────────────────────
EXTRA_CSS = """
<style>
/* Logo sidebar */
.sidebar-logo-wrap {
    display: flex;
    align-items: center;
    gap: 0.65rem;
    padding: 0.6rem 0.2rem 1rem;
    border-bottom: 1px solid rgba(255,255,255,0.08);
    margin-bottom: 0.8rem;
}
.sidebar-logo-svg {
    flex-shrink: 0;
}
.sidebar-logo-text-main {
    color: #f8fafc;
    font-size: 0.95rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    line-height: 1.1;
}
.sidebar-logo-text-sub {
    color: rgba(248,250,252,0.55);
    font-size: 0.72rem;
    letter-spacing: 0.03em;
}

/* Hero compacto */
.hero-compact {
    background: linear-gradient(135deg, #0f172a 0%, #1746a2 60%, #0f4c5c 100%);
    border-radius: 16px;
    padding: 1.2rem 1.6rem;
    margin-bottom: 1.2rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    box-shadow: 0 16px 32px rgba(15,23,42,0.18);
}
.hero-compact-left h1 {
    color: #fff;
    font-size: clamp(1.15rem, 2.5vw, 1.55rem);
    font-weight: 800;
    margin: 0 0 0.25rem;
    letter-spacing: -0.03em;
}
.hero-compact-left p {
    color: rgba(255,255,255,0.72);
    font-size: 0.82rem;
    margin: 0;
    max-width: 52ch;
}
.hero-compact-tag {
    font-size: 0.73rem;
    background: rgba(255,255,255,0.12);
    border: 1px solid rgba(255,255,255,0.18);
    border-radius: 999px;
    padding: 0.22rem 0.65rem;
    color: rgba(255,255,255,0.85);
    display: inline-block;
    margin-bottom: 0.4rem;
}
.hero-compact-stats {
    display: flex;
    gap: 1.2rem;
    flex-shrink: 0;
}
.hero-stat {
    text-align: center;
}
.hero-stat-value {
    color: #fff;
    font-size: 1.4rem;
    font-weight: 800;
    line-height: 1;
}
.hero-stat-label {
    color: rgba(255,255,255,0.6);
    font-size: 0.72rem;
    margin-top: 0.15rem;
}
.hero-stat-divider {
    width: 1px;
    background: rgba(255,255,255,0.15);
    align-self: stretch;
}

/* API status cards */
.api-status-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 0.6rem;
}
.api-card {
    background: var(--surface-soft);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 0.75rem 0.9rem;
    box-shadow: var(--shadow-soft);
}
.api-card-label {
    color: var(--muted);
    font-size: 0.75rem;
    margin-bottom: 0.2rem;
}
.api-card-value {
    color: var(--text);
    font-size: 0.88rem;
    font-weight: 600;
    word-break: break-all;
}

/* Sección label */
.section-label {
    color: var(--muted);
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin: 1rem 0 0.5rem;
}

/* Metric card compacta para el dashboard */
.kpi-card {
    background: var(--surface-soft);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 0.85rem 1rem;
    box-shadow: var(--shadow-soft);
    height: 100%;
}
.kpi-label {
    color: var(--muted);
    font-size: 0.76rem;
    margin-bottom: 0.25rem;
}
.kpi-value {
    color: var(--text);
    font-size: clamp(1.25rem, 2.5vw, 1.6rem);
    font-weight: 800;
    line-height: 1;
    margin-bottom: 0.2rem;
}
.kpi-caption {
    color: var(--muted);
    font-size: 0.75rem;
}
</style>
"""


def _render_logo() -> str:
    """SVG logo geométrico para el sidebar."""
    return """
    <svg class="sidebar-logo-svg" width="38" height="38" viewBox="0 0 38 38" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect width="38" height="38" rx="10" fill="url(#lg1)"/>
      <path d="M10 26 L19 12 L28 26 Z" fill="rgba(255,255,255,0.15)" stroke="rgba(255,255,255,0.5)" stroke-width="1.2"/>
      <path d="M14 26 L19 17 L24 26 Z" fill="rgba(255,255,255,0.9)"/>
      <circle cx="19" cy="11" r="2.5" fill="#7dd3fc"/>
      <defs>
        <linearGradient id="lg1" x1="0" y1="0" x2="38" y2="38" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stop-color="#1e3a8a"/>
          <stop offset="100%" stop-color="#0f4c5c"/>
        </linearGradient>
      </defs>
    </svg>
    """


def main() -> None:
    st.set_page_config(**PAGE_CONFIG)
    load_css()
    st.markdown(EXTRA_CSS, unsafe_allow_html=True)
    initialize_state()

    # Carga de datos
    reviews      = add_basic_text_features(load_processed_reviews())
    catalog      = get_product_catalog()
    corporate_db = get_corporate_audit_db()
    evaluation   = compute_model_evaluation()
    metrics_df   = evaluation["metrics"]
    has_reviews  = not reviews.empty

    # Métricas derivadas
    useful_ratio = (
        float(reviews["y_util"].mean())
        if has_reviews and "y_util" in reviews.columns else 0.0
    )
    avg_length = (
        int(reviews["review_len"].fillna(0).mean())
        if has_reviews and "review_len" in reviews.columns else 0
    )
    best = metrics_df.sort_values("roc_auc", ascending=False).iloc[0] if not metrics_df.empty else None
    baseline = metrics_df[metrics_df["modelo"].str.contains("Logistic|logistic", na=False)] if not metrics_df.empty else None
    baseline_row = baseline.iloc[0] if baseline is not None and not baseline.empty else None

    # ── Sidebar con logo ───────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown(
            f"""
            <div class="sidebar-logo-wrap">
                {_render_logo()}
                <div>
                    <div class="sidebar-logo-text-main">Seminario<br>Predictivo</div>
                    <div class="sidebar-logo-text-sub">Caso 06 · Amazon Reviews</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <div class="sidebar-panel">
                <div class="sidebar-panel-title">Navegación</div>
                <div class="sidebar-panel-item">1. Resumen Ejecutivo</div>
                <div class="sidebar-panel-item">2. Exploración de Datos</div>
                <div class="sidebar-panel-item">3. Modelos y Evaluación</div>
                <div class="sidebar-panel-item">4. Auditoría en Tiempo Real</div>
                <div class="sidebar-panel-item">5. Ranking y Benchmark</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── Hero compacto con stats inline ────────────────────────────────────────
    roc_val   = format_percentage(float(best["roc_auc"])) if best is not None else "—"
    f1_val    = format_percentage(float(best["f1"]))      if best is not None else "—"
    model_val = str(best["modelo"])                        if best is not None else "—"

    st.markdown(
        f"""
        <div class="hero-compact">
            <div class="hero-compact-left">
                <span class="hero-compact-tag">Seminario Predictivo 2026 · Caso 06</span>
                <h1>Plataforma Analítica de Utilidad de Reseñas</h1>
                <p>Amazon Fine Food Reviews · Ingeniería de características textuales · Clasificadores comparados</p>
            </div>
            <div class="hero-compact-stats">
                <div class="hero-stat">
                    <div class="hero-stat-value">{format_compact_number(len(reviews)) if has_reviews else '—'}</div>
                    <div class="hero-stat-label">Reseñas</div>
                </div>
                <div class="hero-stat-divider"></div>
                <div class="hero-stat">
                    <div class="hero-stat-value">{roc_val}</div>
                    <div class="hero-stat-label">ROC-AUC</div>
                </div>
                <div class="hero-stat-divider"></div>
                <div class="hero-stat">
                    <div class="hero-stat-value">{format_percentage(useful_ratio)}</div>
                    <div class="hero-stat-label">Útiles</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ══════════════════════════════════════════════════════════════════════════
    # LAYOUT PRINCIPAL: izquierda (KPIs + gráficos) | derecha (modelo + API)
    # ══════════════════════════════════════════════════════════════════════════
    col_left, col_right = st.columns([1.55, 1], gap="large")

    # ── Columna izquierda ──────────────────────────────────────────────────────
    with col_left:

        # --- Dataset KPIs ---
        st.markdown('<div class="section-label">Dataset</div>', unsafe_allow_html=True)
        d1, d2, d3, d4 = st.columns(4, gap="small")
        kpis_dataset = [
            ("Dataset bruto",   format_compact_number(DEFAULT_METRICS["registros_iniciales"]), "Reseñas originales"),
            ("Base analítica",  format_compact_number(len(reviews)) if has_reviews else "—",   "Con ≥ 5 votos"),
            ("Catálogo",        format_compact_number(len(catalog)),                            "Productos"),
            ("Operativa",       format_compact_number(len(corporate_db)),                       "Para auditoría"),
        ]
        for col, (label, value, caption) in zip([d1, d2, d3, d4], kpis_dataset):
            with col:
                st.markdown(
                    f"""<div class="kpi-card">
                        <div class="kpi-label">{label}</div>
                        <div class="kpi-value">{value}</div>
                        <div class="kpi-caption">{caption}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )

        # --- Gráfico distribución calificaciones + longitud ---
        st.markdown('<div class="section-label">Distribuciones clave</div>', unsafe_allow_html=True)
        gc1, gc2 = st.columns(2, gap="small")
        with gc1:
            fig_stars = build_stars_distribution(reviews)
            fig_stars.update_layout(
                height=200, margin=dict(l=10, r=10, t=30, b=10),
                showlegend=False, title_font_size=12,
            )
            st.plotly_chart(fig_stars, use_container_width=True, config={"displayModeBar": False})
        with gc2:
            fig_len = build_review_length_distribution(reviews)
            if has_reviews and avg_length > 0:
                fig_len.add_vline(x=avg_length, line_dash="dash", line_color="#0f9f74",
                                  annotation_text=f"x̄={avg_length}", annotation_position="top right")
            fig_len.update_layout(
                height=200, margin=dict(l=10, r=10, t=30, b=10),
                showlegend=False, title_font_size=12,
            )
            st.plotly_chart(fig_len, use_container_width=True, config={"displayModeBar": False})

        # --- Balance objetivo ---
        st.markdown('<div class="section-label">Balance de clases</div>', unsafe_allow_html=True)
        fig_bal = build_target_balance(reviews)
        fig_bal.update_layout(
            height=180, margin=dict(l=10, r=10, t=30, b=10),
            showlegend=False, title_font_size=12,
        )
        st.plotly_chart(fig_bal, use_container_width=True, config={"displayModeBar": False})

    # ── Columna derecha ────────────────────────────────────────────────────────
    with col_right:

        # --- Modelo activo ---
        st.markdown('<div class="section-label">Modelo activo</div>', unsafe_allow_html=True)

        if best is not None:
            delta_str = ""
            if baseline_row is not None:
                delta = float(best["roc_auc"]) - float(baseline_row["roc_auc"])
                delta_str = f'<span class="metric-badge metric-badge-good" style="margin-left:0.4rem">+{delta:.1%} vs baseline</span>'

            st.markdown(
                f"""
                <div class="metric-card" style="border-left: 3px solid var(--primary); margin-bottom:0.6rem">
                    <div class="metric-label">Modelo ganador {delta_str}</div>
                    <div class="metric-value">{model_val}</div>
                    <div style="display:flex;gap:1rem;margin-top:0.5rem;flex-wrap:wrap">
                        <div>
                            <div class="kpi-label">ROC-AUC</div>
                            <div style="font-size:1.2rem;font-weight:800;color:var(--text)">{roc_val}</div>
                        </div>
                        <div>
                            <div class="kpi-label">F1-Score</div>
                            <div style="font-size:1.2rem;font-weight:800;color:var(--text)">{f1_val}</div>
                        </div>
                        <div>
                            <div class="kpi-label">Utilidad predicha</div>
                            <div style="font-size:1.2rem;font-weight:800;color:var(--text)">{format_percentage(useful_ratio)}</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Mini gráfico comparativo de métricas
            fig_met = build_model_metrics_chart(metrics_df)
            fig_met.update_layout(
                height=200, margin=dict(l=10, r=10, t=30, b=10),
                showlegend=True,
                legend=dict(orientation="h", y=-0.25, font_size=10),
                title_font_size=12,
            )
            st.plotly_chart(fig_met, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Entrena los modelos para ver métricas.")

        # --- Variables predictoras ---
        st.markdown('<div class="section-label">Variables predictoras</div>', unsafe_allow_html=True)
        features = [
            ("Longitud",          "Palabras en la reseña",        "Feature #1", "metric-badge-good"),
            ("Sentimiento VADER", "Score compuesto (VADER)",      "Feature #2", "metric-badge-info"),
            ("Coherencia",        "Tono vs. estrellas asignadas", "Feature #3", "metric-badge-warn"),
            ("Calificación",      "Estrellas 1–5",                "Contexto",   "metric-badge-info"),
        ]
        fv1, fv2 = st.columns(2, gap="small")
        for i, (label, caption, badge_text, badge_class) in enumerate(features):
            col = fv1 if i % 2 == 0 else fv2
            with col:
                st.markdown(
                    f"""<div class="kpi-card" style="margin-bottom:0.5rem">
                        <div class="kpi-label">{label}</div>
                        <div class="kpi-caption">{caption}</div>
                        <span class="metric-badge {badge_class}">{badge_text}</span>
                    </div>""",
                    unsafe_allow_html=True,
                )

        # --- API de predicción ---
        st.markdown('<div class="section-label">API de predicción</div>', unsafe_allow_html=True)
        with st.spinner(""):
            api_status = _get_api_status()
        api_ok = api_status.get("status") == "ok"
        lgb_ok = "✓" in api_status.get("modelos", {}).get("lgb_model", "") if api_ok else False

        status_badge = "metric-badge-good" if api_ok else "metric-badge-warn"
        status_label = "Activa" if api_ok else "Sin respuesta"
        lgb_badge    = "metric-badge-good" if lgb_ok else "metric-badge-warn"
        lgb_label    = "Cargado" if lgb_ok else "Heurística"

        st.markdown(
            f"""
            <div class="api-status-grid">
                <div class="api-card">
                    <div class="api-card-label">Estado · FastAPI / Render</div>
                    <div class="api-card-value">proyecto-prediccion-v9qk</div>
                    <span class="metric-badge {status_badge}">{status_label}</span>
                </div>
                <div class="api-card">
                    <div class="api-card-label">Modelo en API</div>
                    <div class="api-card-value">LightGBM</div>
                    <span class="metric-badge {lgb_badge}">{lgb_label}</span>
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


if __name__ == "__main__":
    main()