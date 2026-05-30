"""Punto de entrada — dashboard ejecutivo."""

import os
import requests
import streamlit as st

from components.cards import render_metric_card
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
    # Marca la sesión como iniciada; las páginas secundarias usan esto para
    # redirigir a main.py si el usuario llega directamente (sin sesión).
    st.session_state["app_initialized"] = True

    reviews      = add_basic_text_features(load_processed_reviews())
    catalog      = get_product_catalog()
    corporate_db = get_corporate_audit_db()
    evaluation   = compute_model_evaluation()
    metrics_df   = evaluation["metrics"]
    has_reviews  = not reviews.empty

    useful_ratio = float(reviews["y_util"].mean()) if has_reviews and "y_util" in reviews.columns else 0.0
    avg_length   = int(reviews["review_len"].fillna(0).mean()) if has_reviews and "review_len" in reviews.columns else 0
    best         = metrics_df.sort_values("roc_auc", ascending=False).iloc[0] if not metrics_df.empty else None
    baseline     = metrics_df[metrics_df["modelo"].str.contains("Logistic|logistic", na=False)] if not metrics_df.empty else None
    baseline_row = baseline.iloc[0] if baseline is not None and not baseline.empty else None

    roc_val   = format_percentage(float(best["roc_auc"])) if best is not None else "—"
    f1_val    = format_percentage(float(best["f1"]))      if best is not None else "—"
    model_val = str(best["modelo"])                        if best is not None else "—"

    # ── Hero ──────────────────────────────────────────────────────────────────
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

    col_left, col_right = st.columns([1.55, 1], gap="large")

    with col_left:
        st.markdown('<div class="section-label">Dataset</div>', unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="stat-row">
                <div class="stat-pill">
                    <div class="stat-pill-icon stat-pill-icon-blue">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#1d4ed8" stroke-width="2" stroke-linecap="round"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14c0 1.66 4.03 3 9 3s9-1.34 9-3V5"/><path d="M3 12c0 1.66 4.03 3 9 3s9-1.34 9-3"/></svg>
                    </div>
                    <div><div class="stat-pill-value">{format_compact_number(DEFAULT_METRICS["registros_iniciales"])}</div><div class="stat-pill-label">Dataset bruto</div></div>
                </div>
                <div class="stat-pill">
                    <div class="stat-pill-icon stat-pill-icon-green">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#15803d" stroke-width="2" stroke-linecap="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
                    </div>
                    <div><div class="stat-pill-value">{format_compact_number(len(reviews)) if has_reviews else '—'}</div><div class="stat-pill-label">Base analítica</div></div>
                </div>
                <div class="stat-pill">
                    <div class="stat-pill-icon stat-pill-icon-teal">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#0d9488" stroke-width="2" stroke-linecap="round"><path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/><line x1="3" y1="6" x2="21" y2="6"/></svg>
                    </div>
                    <div><div class="stat-pill-value">{format_compact_number(len(catalog))}</div><div class="stat-pill-label">Catálogo</div></div>
                </div>
                <div class="stat-pill">
                    <div class="stat-pill-icon stat-pill-icon-amber">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#b45309" stroke-width="2" stroke-linecap="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
                    </div>
                    <div><div class="stat-pill-value">{format_compact_number(len(corporate_db))}</div><div class="stat-pill-label">Base operativa</div></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<div class="section-label">Distribuciones clave</div>', unsafe_allow_html=True)
        gc1, gc2 = st.columns(2, gap="small")
        with gc1:
            fig = build_stars_distribution(reviews)
            fig.update_layout(height=200, margin=dict(l=10,r=10,t=30,b=10), showlegend=False, title_font_size=12)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        with gc2:
            fig2 = build_review_length_distribution(reviews)
            if has_reviews and avg_length > 0:
                fig2.add_vline(x=avg_length, line_dash="dash", line_color="#0f9f74",
                               annotation_text=f"x̄={avg_length}", annotation_position="top right")
            fig2.update_layout(height=200, margin=dict(l=10,r=10,t=30,b=10), showlegend=False, title_font_size=12)
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

        st.markdown('<div class="section-label">Balance de clases</div>', unsafe_allow_html=True)
        fig3 = build_target_balance(reviews)
        fig3.update_layout(height=180, margin=dict(l=10,r=10,t=30,b=10), showlegend=False, title_font_size=12)
        st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

    with col_right:
        st.markdown('<div class="section-label">Modelo activo</div>', unsafe_allow_html=True)
        if best is not None:
            delta_str = ""
            if baseline_row is not None:
                delta = float(best["roc_auc"]) - float(baseline_row["roc_auc"])
                delta_str = f'<span class="metric-badge metric-badge-good">+{delta:.1%} vs baseline</span>'
            st.markdown(
                f"""
                <div class="metric-card" style="border-left:3px solid var(--primary);margin-bottom:0.6rem">
                    <div class="metric-label">Modelo ganador &nbsp;{delta_str}</div>
                    <div class="metric-value">{model_val}</div>
                    <div style="display:flex;gap:1.2rem;margin-top:0.6rem;flex-wrap:wrap">
                        <div><div style="color:var(--muted);font-size:0.72rem">ROC-AUC</div>
                             <div style="font-size:1.25rem;font-weight:800;color:var(--primary)">{roc_val}</div></div>
                        <div><div style="color:var(--muted);font-size:0.72rem">F1-Score</div>
                             <div style="font-size:1.25rem;font-weight:800;color:var(--text)">{f1_val}</div></div>
                        <div><div style="color:var(--muted);font-size:0.72rem">Útiles predichas</div>
                             <div style="font-size:1.25rem;font-weight:800;color:var(--success)">{format_percentage(useful_ratio)}</div></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            fig_m = build_model_metrics_chart(metrics_df)
            fig_m.update_layout(height=200, margin=dict(l=10,r=10,t=30,b=10), showlegend=True,
                                legend=dict(orientation="h", y=-0.3, font_size=10), title_font_size=12)
            st.plotly_chart(fig_m, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Entrena los modelos para ver métricas.")

        st.markdown('<div class="section-label">Variables predictoras</div>', unsafe_allow_html=True)
        features = [
            ("stat-pill-icon-green", "#15803d", '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>', "Longitud", "Palabras en la reseña", "Feature #1", "metric-badge-good"),
            ("stat-pill-icon-blue",  "#1d4ed8", '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>', "Sentimiento VADER", "Score compuesto", "Feature #2", "metric-badge-info"),
            ("stat-pill-icon-amber", "#b45309", '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>', "Coherencia", "Tono vs. estrellas", "Feature #3", "metric-badge-warn"),
            ("stat-pill-icon-teal",  "#0d9488", '<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>', "Calificación", "Estrellas 1–5", "Contexto", "metric-badge-info"),
        ]
        for icon_class, color, path, label, caption, badge, badge_class in features:
            st.markdown(
                f"""
                <div class="stat-pill" style="margin-bottom:0.4rem">
                    <div class="stat-pill-icon {icon_class}">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round">{path}</svg>
                    </div>
                    <div style="flex:1;display:flex;justify-content:space-between;align-items:center">
                        <div><div class="stat-pill-value" style="font-size:0.88rem;font-weight:700">{label}</div>
                             <div class="stat-pill-label">{caption}</div></div>
                        <span class="metric-badge {badge_class}">{badge}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown('<div class="section-label">API de predicción</div>', unsafe_allow_html=True)
        with st.spinner(""):
            api_status = _get_api_status()
        api_ok = api_status.get("status") == "ok"
        lgb_ok = "✓" in api_status.get("modelos", {}).get("lgb_model", "") if api_ok else False
        st.markdown(
            f"""
            <div class="api-status-grid">
                <div class="api-card">
                    <div class="api-card-label">Estado · FastAPI / Render</div>
                    <div class="api-card-value">proyecto-prediccion-v9qk</div>
                    <span class="metric-badge {'metric-badge-good' if api_ok else 'metric-badge-warn'}">{'Activa' if api_ok else 'Sin respuesta'}</span>
                </div>
                <div class="api-card">
                    <div class="api-card-label">Modelo en API</div>
                    <div class="api-card-value">LightGBM</div>
                    <span class="metric-badge {'metric-badge-good' if lgb_ok else 'metric-badge-warn'}">{'Cargado' if lgb_ok else 'Heurística'}</span>
                </div>
                <div class="api-card">
                    <div class="api-card-label">Predicción</div>
                    <div class="api-card-value">POST /reviews/predict_helpfulness</div>
                </div>
                <div class="api-card">
                    <div class="api-card-label">Palabras clave</div>
                    <div class="api-card-value">GET /reviews/top_words</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    main()