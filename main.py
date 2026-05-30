"""Punto de entrada — portada del proyecto.

Vista rápida: dataset · modelo activo · API · features.
Sin texto de relleno. Todo en tarjetas.
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
from services.model_eval_service import compute_model_evaluation
from services.preprocessing_service import get_corporate_audit_db
from utils.formatters import format_compact_number, format_percentage
from utils.state import initialize_state


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
        r = requests.get(_api_url() + "/", timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        return {"status": "error", "detalle": str(exc)}


def main() -> None:
    st.set_page_config(**PAGE_CONFIG)
    load_css()
    initialize_state()

    reviews      = load_processed_reviews()
    catalog      = get_product_catalog()
    corporate_db = get_corporate_audit_db()
    evaluation   = compute_model_evaluation()
    metrics_df   = evaluation["metrics"]

    # ── Hero ───────────────────────────────────────────────────────────────────
    render_app_hero(
        title="Plataforma Analítica de Utilidad de Reseñas",
        subtitle=(
            "Predicción de utilidad percibida en Amazon Fine Food Reviews "
            "mediante ingeniería de características textuales y comparación de clasificadores."
        ),
        tag="Seminario Predictivo 2026",
    )

    # ── Sidebar ────────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-brand">
                <div class="sidebar-brand-mark">SP</div>
                <div>
                    <div class="sidebar-brand-title">Seminario Predictivo</div>
                    <div class="sidebar-brand-subtitle">Dashboard analítico</div>
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

    # ── Dataset ────────────────────────────────────────────────────────────────
    st.markdown("### Dataset")
    m1, m2, m3, m4 = st.columns(4, gap="medium")
    with m1:
        render_metric_card("Dataset bruto", format_compact_number(DEFAULT_METRICS["registros_iniciales"]), "Reseñas históricas Amazon")
    with m2:
        render_metric_card("Base analítica", format_compact_number(len(reviews)), "Con ≥ 5 votos, sin duplicados")
    with m3:
        render_metric_card("Catálogo", format_compact_number(len(catalog)), "Productos con categoría")
    with m4:
        render_metric_card("Base operativa", format_compact_number(len(corporate_db)), "Registros para auditoría")

    # ── Modelo activo ──────────────────────────────────────────────────────────
    st.markdown("### Modelo activo")
    if not metrics_df.empty:
        best         = metrics_df.sort_values("roc_auc", ascending=False).iloc[0]
        baseline     = metrics_df[metrics_df["modelo"].str.contains("Logistic|logistic", na=False)]
        baseline_row = baseline.iloc[0] if not baseline.empty else None

        mk1, mk2, mk3, mk4 = st.columns(4, gap="medium")
        with mk1:
            render_metric_card("Modelo principal", str(best["modelo"]), "Mayor ROC-AUC en test")
        with mk2:
            render_metric_card("ROC-AUC", format_percentage(float(best["roc_auc"])), "Capacidad discriminativa")
        with mk3:
            render_metric_card("F1-Score", format_percentage(float(best["f1"])), "Precisión + Recall balanceados")
        with mk4:
            if baseline_row is not None:
                delta = float(best["roc_auc"]) - float(baseline_row["roc_auc"])
                render_metric_card("Mejora vs. baseline", f"+{delta:.1%}", "LightGBM vs. Reg. Logística")
            else:
                render_metric_card("Baseline", "Reg. Logística", "Modelo de referencia")
    else:
        st.info("Entrena los modelos para ver métricas aquí.")

    # ── Variables predictoras ──────────────────────────────────────────────────
    st.markdown("### Variables predictoras")
    f1c, f2c, f3c, f4c = st.columns(4, gap="medium")
    features = [
        ("Longitud",          "Palabras en la reseña",        "Feature #1", "metric-badge-good"),
        ("Sentimiento VADER", "Score compuesto del texto",    "Feature #2", "metric-badge-info"),
        ("Coherencia",        "Tono vs. estrellas asignadas", "Feature #3", "metric-badge-warn"),
        ("Calificación",      "Estrellas 1–5",                "Contexto",   "metric-badge-info"),
    ]
    for col, (label, caption, badge_text, badge_class) in zip([f1c, f2c, f3c, f4c], features):
        with col:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">{label}</div>
                    <div class="metric-caption" style="margin-top:0.4rem">{caption}</div>
                    <span class="metric-badge {badge_class}">{badge_text}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # ── Estado de la API ───────────────────────────────────────────────────────
    st.markdown("### API de predicción")
    with st.spinner("Verificando API..."):
        api_status = _get_api_status()

    api_ok = api_status.get("status") == "ok"
    lgb_ok = "✓" in api_status.get("modelos", {}).get("lgb_model", "") if api_ok else False

    a1, a2, a3, a4 = st.columns(4, gap="medium")
    with a1:
        status_badge = "metric-badge-good" if api_ok else "metric-badge-warn"
        status_label = "Activa" if api_ok else "Sin respuesta"
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Estado</div>
                <div class="metric-value" style="font-size:1.1rem">FastAPI · Render</div>
                <span class="metric-badge {status_badge}">{status_label}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with a2:
        model_badge = "metric-badge-good" if lgb_ok else "metric-badge-warn"
        model_label = "LightGBM cargado" if lgb_ok else "Modo heurística"
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Modelo en API</div>
                <div class="metric-value" style="font-size:1.1rem">LightGBM</div>
                <span class="metric-badge {model_badge}">{model_label}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with a3:
        st.markdown(
            """
            <div class="metric-card">
                <div class="metric-label">Predicción</div>
                <div class="metric-value" style="font-size:0.9rem;word-break:break-all">POST /reviews/predict_helpfulness</div>
                <span class="metric-badge metric-badge-info">Texto + estrellas → probabilidad</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with a4:
        st.markdown(
            """
            <div class="metric-card">
                <div class="metric-label">Palabras clave</div>
                <div class="metric-value" style="font-size:0.9rem">GET /reviews/top_words</div>
                <span class="metric-badge metric-badge-info">Útiles vs. no útiles</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    main()