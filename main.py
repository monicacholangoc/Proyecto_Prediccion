"""Punto de entrada de la aplicacion Streamlit.

Portada compacta: hero + KPIs del modelo + mapa de navegacion.
Sin texto redundante, sin nav-cards de relleno.
"""

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


def main() -> None:
    st.set_page_config(**PAGE_CONFIG)
    load_css()
    initialize_state()

    reviews      = load_processed_reviews()
    catalog      = get_product_catalog()
    corporate_db = get_corporate_audit_db()
    evaluation   = compute_model_evaluation()
    metrics_df   = evaluation["metrics"]

    # ── Hero ──────────────────────────────────────────────────────────────────
    render_app_hero(
        title="Plataforma Analítica de Utilidad de Reseñas",
        subtitle=(
            "Predicción de utilidad percibida en Amazon Fine Food Reviews "
            "mediante ingeniería de características textuales y comparación de clasificadores."
        ),
        tag="Seminario Predictivo 2026",
    )

    # ── Sidebar compacto ──────────────────────────────────────────────────────
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
                <div class="sidebar-panel-title">Ruta recomendada</div>
                <div class="sidebar-panel-item">1. Resumen ejecutivo</div>
                <div class="sidebar-panel-item">2. Exploración de datos</div>
                <div class="sidebar-panel-item">3. Modelos y evaluación</div>
                <div class="sidebar-panel-item">4. Auditoría en tiempo real</div>
                <div class="sidebar-panel-item">5. Ranking y benchmark</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── KPIs del dataset ──────────────────────────────────────────────────────
    st.markdown("### Dataset")
    m1, m2, m3, m4 = st.columns(4, gap="medium")
    with m1:
        render_metric_card(
            "Dataset bruto",
            format_compact_number(DEFAULT_METRICS["registros_iniciales"]),
            "Reseñas históricas Amazon",
        )
    with m2:
        render_metric_card(
            "Base analítica",
            format_compact_number(len(reviews)),
            "Filtrado ≥ 5 votos, sin duplicados",
        )
    with m3:
        render_metric_card(
            "Catálogo",
            format_compact_number(len(catalog)),
            "Productos con categoría",
        )
    with m4:
        render_metric_card(
            "Base operativa",
            format_compact_number(len(corporate_db)),
            "Auditorías disponibles",
        )

    # ── KPIs del modelo — esto es lo que agrega valor en la portada ──────────
    st.markdown("### Modelo activo")

    if not metrics_df.empty:
        best = metrics_df.sort_values("roc_auc", ascending=False).iloc[0]
        baseline = metrics_df[metrics_df["modelo"].str.contains("Logistic|logistic", na=False)]
        baseline_row = baseline.iloc[0] if not baseline.empty else None

        mk1, mk2, mk3, mk4 = st.columns(4, gap="medium")
        with mk1:
            render_metric_card(
                "Modelo principal",
                str(best["modelo"]),
                "Mayor ROC-AUC en test (20 %)",
            )
        with mk2:
            render_metric_card(
                "ROC-AUC",
                format_percentage(float(best["roc_auc"])),
                "Capacidad discriminativa",
            )
        with mk3:
            render_metric_card(
                "F1-Score",
                format_percentage(float(best["f1"])),
                "Precisión + Recall balanceados",
            )
        with mk4:
            if baseline_row is not None:
                delta = float(best["roc_auc"]) - float(baseline_row["roc_auc"])
                render_metric_card(
                    "Mejora vs. baseline",
                    f"+{delta:.1%}",
                    "LightGBM vs. Regresión Logística",
                )
            else:
                render_metric_card("Baseline", "Reg. Logística", "Modelo de referencia")
    else:
        st.info("Entrena los modelos para ver métricas aquí.")

    # ── Features del modelo ───────────────────────────────────────────────────
    st.markdown("### ¿Qué predice la utilidad?")
    st.caption(
        "El modelo usa solo 4 características derivadas del texto — ninguna requiere embeddings ni modelos de lenguaje."
    )

    f1c, f2c, f3c, f4c = st.columns(4, gap="medium")
    features_info = [
        ("review_len", "Longitud", "Palabras en la reseña", "Feature #1 más importante"),
        ("sentiment_score", "Sentimiento VADER", "Score compuesto del texto", "Contribución media"),
        ("incoherente", "Coherencia", "Tono vs. estrellas asignadas", "Penaliza incoherencias"),
        ("Score", "Calificación", "Estrellas 1–5", "Feature de contexto"),
    ]
    badge_classes = ["metric-badge-good", "metric-badge-info", "metric-badge-warn", "metric-badge-info"]
    for col, (_, label, caption, badge_text), badge_class in zip(
        [f1c, f2c, f3c, f4c], features_info, badge_classes
    ):
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


if __name__ == "__main__":
    main()