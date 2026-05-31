"""Página 1 — Resumen Ejecutivo."""

import streamlit as st
from config.theme import PAGE_CONFIG
from services.data_loader import load_processed_reviews
from services.feature_service import add_basic_text_features
from services.model_eval_service import compute_model_evaluation
from services.catalog_service import get_product_catalog
from services.preprocessing_service import get_corporate_audit_db
from utils.formatters import format_compact_number, format_percentage
from utils.state import initialize_state
from shared_sidebar import render_sidebar
import os


def _setup() -> None:
    css_path = "styles/styles.css"
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    render_sidebar()


def main() -> None:
    st.set_page_config(
        page_title="Resumen Ejecutivo · Seminario Predictivo",
        page_icon="📋",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _setup()
    initialize_state()

    reviews    = add_basic_text_features(load_processed_reviews())
    catalog    = get_product_catalog()
    corp_db    = get_corporate_audit_db()
    evaluation = compute_model_evaluation()
    metrics_df = evaluation["metrics"]
    has_rev    = not reviews.empty

    best = metrics_df.sort_values("roc_auc", ascending=False).iloc[0] if not metrics_df.empty else None
    baseline = metrics_df[metrics_df["modelo"].str.contains("Logistic|logistic", na=False)] if not metrics_df.empty else None
    baseline_row = baseline.iloc[0] if baseline is not None and not baseline.empty else None

    useful_ratio = float(reviews["y_util"].mean()) if has_rev and "y_util" in reviews.columns else 0.0
    avg_len      = int(reviews["review_len"].fillna(0).mean()) if has_rev and "review_len" in reviews.columns else 0

    roc_val   = format_percentage(float(best["roc_auc"])) if best is not None else "—"
    f1_val    = format_percentage(float(best["f1"]))      if best is not None else "—"
    model_val = str(best["modelo"])                        if best is not None else "—"

    # ── Hero ─────────────────────────────────────────────────────────────────
    st.markdown(
        """
        <div class="hero-compact">
            <div class="hero-compact-left">
                <span class="hero-compact-tag">Seminario Predictivo 2026 · Caso 06</span>
                <h1>Resumen Ejecutivo</h1>
                <p>Síntesis de hallazgos, métricas clave y recomendaciones del proyecto de predicción de utilidad de reseñas Amazon Fine Food.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── KPIs ──────────────────────────────────────────────────────────────────
    st.markdown('<div class="section-label">Métricas principales</div>', unsafe_allow_html=True)
    k1, k2, k3, k4 = st.columns(4, gap="small")
    with k1:
        st.markdown(
            f"""<div class="kpi-card">
                <div class="kpi-label">Reseñas analizadas</div>
                <div class="kpi-value">{format_compact_number(len(reviews)) if has_rev else "—"}</div>
            </div>""",
            unsafe_allow_html=True,
        )
    with k2:
        st.markdown(
            f"""<div class="kpi-card">
                <div class="kpi-label">ROC-AUC (mejor modelo)</div>
                <div class="kpi-value">{roc_val}</div>
            </div>""",
            unsafe_allow_html=True,
        )
    with k3:
        st.markdown(
            f"""<div class="kpi-card">
                <div class="kpi-label">F1-Score</div>
                <div class="kpi-value">{f1_val}</div>
            </div>""",
            unsafe_allow_html=True,
        )
    with k4:
        st.markdown(
            f"""<div class="kpi-card">
                <div class="kpi-label">Reseñas útiles</div>
                <div class="kpi-value">{format_percentage(useful_ratio)}</div>
            </div>""",
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Columnas principales ──────────────────────────────────────────────────
    col_l, col_r = st.columns([1.2, 1], gap="large")

    with col_l:
        # Modelo ganador
        st.markdown('<div class="section-label">Modelo ganador</div>', unsafe_allow_html=True)
        if best is not None:
            delta_str = ""
            if baseline_row is not None:
                delta = float(best["roc_auc"]) - float(baseline_row["roc_auc"])
                delta_str = f'<span class="metric-badge metric-badge-good">+{delta:.1%} vs baseline</span>'
            st.markdown(
                f"""
                <div class="metric-card" style="border-left:3px solid var(--primary);margin-bottom:0.8rem">
                    <div class="metric-label">Algoritmo &nbsp;{delta_str}</div>
                    <div class="metric-value">{model_val}</div>
                    <div style="display:flex;gap:1.4rem;margin-top:0.7rem;flex-wrap:wrap">
                        <div>
                            <div style="color:var(--muted);font-size:0.72rem">ROC-AUC</div>
                            <div style="font-size:1.3rem;font-weight:800;color:var(--primary)">{roc_val}</div>
                        </div>
                        <div>
                            <div style="color:var(--muted);font-size:0.72rem">F1-Score</div>
                            <div style="font-size:1.3rem;font-weight:800;color:var(--text)">{f1_val}</div>
                        </div>
                        <div>
                            <div style="color:var(--muted);font-size:0.72rem">Útiles predichas</div>
                            <div style="font-size:1.3rem;font-weight:800;color:var(--success)">{format_percentage(useful_ratio)}</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.info("Entrena los modelos para ver métricas.")

        # Tabla de modelos
        if not metrics_df.empty:
            st.markdown('<div class="section-label">Comparativa de modelos</div>', unsafe_allow_html=True)
            display_cols = [c for c in ["modelo", "roc_auc", "f1", "accuracy", "precision", "recall"] if c in metrics_df.columns]
            df_show = metrics_df[display_cols].copy()
            for col in display_cols:
                if col != "modelo":
                    df_show[col] = df_show[col].apply(lambda x: f"{x:.3f}" if isinstance(x, float) else x)
            st.dataframe(df_show, use_container_width=True, hide_index=True)

    with col_r:
        # Dataset
        st.markdown('<div class="section-label">Dataset</div>', unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="stat-pill" style="margin-bottom:0.4rem">
                <div class="stat-pill-icon stat-pill-icon-blue">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#1d4ed8" stroke-width="2" stroke-linecap="round"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14c0 1.66 4.03 3 9 3s9-1.34 9-3V5"/><path d="M3 12c0 1.66 4.03 3 9 3s9-1.34 9-3"/></svg>
                </div>
                <div><div class="stat-pill-value">Reseñas procesadas</div>
                     <div class="stat-pill-label">{format_compact_number(len(reviews)) if has_rev else "—"} registros</div></div>
            </div>
            <div class="stat-pill" style="margin-bottom:0.4rem">
                <div class="stat-pill-icon stat-pill-icon-teal">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#0d9488" stroke-width="2" stroke-linecap="round"><path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/><line x1="3" y1="6" x2="21" y2="6"/></svg>
                </div>
                <div><div class="stat-pill-value">Catálogo de productos</div>
                     <div class="stat-pill-label">{format_compact_number(len(catalog))} productos</div></div>
            </div>
            <div class="stat-pill" style="margin-bottom:0.4rem">
                <div class="stat-pill-icon stat-pill-icon-amber">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#b45309" stroke-width="2" stroke-linecap="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
                </div>
                <div><div class="stat-pill-value">Base operativa corporativa</div>
                     <div class="stat-pill-label">{format_compact_number(len(corp_db))} registros</div></div>
            </div>
            <div class="stat-pill" style="margin-bottom:0.4rem">
                <div class="stat-pill-icon stat-pill-icon-green">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#15803d" stroke-width="2" stroke-linecap="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
                </div>
                <div><div class="stat-pill-value">Longitud promedio de reseña</div>
                     <div class="stat-pill-label">{avg_len} palabras por reseña</div></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Conclusiones
        st.markdown('<div class="section-label" style="margin-top:1rem">Conclusiones clave</div>', unsafe_allow_html=True)
        conclusiones = [
            ("metric-badge-good", "LightGBM supera al baseline logístico en ROC-AUC y F1."),
            ("metric-badge-info", "La longitud del texto y el sentimiento VADER son los predictores más relevantes."),
            ("metric-badge-info", "El desbalance de clases fue manejado con class_weight y SMOTE."),
            ("metric-badge-warn", "Las reseñas muy cortas (<10 palabras) tienen menor utilidad predicha."),
            ("metric-badge-good", "La API REST en Render permite predicción en tiempo real con latencia <500ms."),
        ]
        for badge, texto in conclusiones:
            st.markdown(
                f'<div style="display:flex;align-items:flex-start;gap:0.6rem;margin-bottom:0.5rem">'
                f'<span class="metric-badge {badge}" style="margin-top:0.1rem;white-space:nowrap">●</span>'
                f'<span style="font-size:0.82rem;color:var(--text);line-height:1.5">{texto}</span></div>',
                unsafe_allow_html=True,
            )

    # ── Panel metodológico ────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-label">Metodología</div>', unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4, gap="small")
    pasos = [
        ("1", "Adquisición", "Descarga y limpieza del dataset Amazon Fine Food Reviews (568K+ reseñas)."),
        ("2", "Ingeniería", "Extracción de características textuales: longitud, sentimiento VADER, coherencia tono-estrella."),
        ("3", "Modelado", "Entrenamiento y comparación de Logistic Regression, Random Forest, XGBoost y LightGBM."),
        ("4", "Despliegue", "API FastAPI en Render con modelo LightGBM serializado; dashboard Streamlit en Cloud."),
    ]
    for col, (num, titulo, desc) in zip([m1, m2, m3, m4], pasos):
        with col:
            st.markdown(
                f"""
                <div class="highlight-card" style="text-align:center;padding:1rem 0.75rem">
                    <div style="font-size:1.8rem;font-weight:900;color:var(--primary);line-height:1">{num}</div>
                    <div class="highlight-title" style="font-size:0.82rem;font-weight:700;margin:0.3rem 0 0.4rem">{titulo}</div>
                    <div class="highlight-body" style="font-size:0.75rem;line-height:1.45">{desc}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


if __name__ == "__main__":
    main()
