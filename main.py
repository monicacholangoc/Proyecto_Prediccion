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
    # Sumar reseñas nuevas de Supabase al conteo del hero
    try:
        sb_count = len(load_reviews_from_supabase())
    except Exception:
        sb_count = 0
    total_reviews_count = len(reviews) + sb_count

    best      = metrics_df.sort_values("roc_auc", ascending=False).iloc[0] if not metrics_df.empty else None
    roc_val   = format_percentage(float(best["roc_auc"])) if best is not None else "—"
    model_val = str(best["modelo"])                        if best is not None else "—"

    # ── Hero ─────────────────────────────────────────────────────────────────
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, #0f1f3d 0%, #1746a2 55%, #0f4c5c 100%);
            border-radius: 20px;
            padding: 2.5rem 2.5rem 2rem;
            margin-bottom: 1.6rem;
            color: #ffffff;
            position: relative;
            overflow: hidden;
        ">
            <div style="font-size:0.7rem;font-weight:700;letter-spacing:0.12em;
                        color:rgba(255,255,255,0.45);text-transform:uppercase;margin-bottom:0.6rem">
                Seminario Predictivo 2026 · Caso 06
            </div>
            <div style="font-size:clamp(1.7rem,4vw,2.4rem);font-weight:900;
                        letter-spacing:-0.03em;line-height:1.15;margin-bottom:0.5rem">
                Predicción de Utilidad<br>de Reseñas Amazon
            </div>
            <div style="font-size:0.9rem;color:rgba(255,255,255,0.6);max-width:600px;line-height:1.6">
                ¿Qué hace que una reseña sea realmente útil para otros compradores?
                Este proyecto predice la utilidad percibida a partir de características
                textuales: longitud, sentimiento y coherencia.
            </div>
            <div style="margin-top:1.4rem;display:flex;gap:2rem;flex-wrap:wrap">
                <div>
                    <div style="font-size:1.6rem;font-weight:800;color:#7dd3fc">{format_compact_number(total_reviews_count) if has_reviews else '~100 K'}</div>
                    <div style="font-size:0.7rem;color:rgba(255,255,255,0.45);text-transform:uppercase;letter-spacing:.07em">Reseñas analizadas</div>
                </div>
                <div style="width:1px;background:rgba(255,255,255,0.15)"></div>
                <div>
                    <div style="font-size:1.6rem;font-weight:800;color:#86efac">{roc_val}</div>
                    <div style="font-size:0.7rem;color:rgba(255,255,255,0.45);text-transform:uppercase;letter-spacing:.07em">ROC-AUC · {model_val}</div>
                </div>
                <div style="width:1px;background:rgba(255,255,255,0.15)"></div>
                <div>
                    <div style="font-size:1.6rem;font-weight:800;color:#fcd34d">4</div>
                    <div style="font-size:0.7rem;color:rgba(255,255,255,0.45);text-transform:uppercase;letter-spacing:.07em">Features del modelo</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Contexto del problema ─────────────────────────────────────────────────
    st.markdown('<div class="section-label">Contexto del problema</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="highlight-card" style="margin-bottom:1rem">
            <div class="highlight-title">¿Por qué predecir utilidad y no simplemente mostrar las reseñas más recientes?</div>
            <div class="highlight-body">
                Amazon muestra primero las reseñas percibidas como útiles porque impactan directamente
                en las decisiones de compra de millones de usuarios. Sin embargo, la utilidad
                <strong>no se puede predecir con las estrellas solas</strong> — una reseña de 5 estrellas
                que solo dice "¡Excelente!" no ayuda a nadie. El verdadero predictor está
                en el texto: longitud, coherencia, sentimiento y detalle.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    ctx1, ctx2 = st.columns(2, gap="large")
    with ctx1:
        st.markdown(
            """
            <div class="metric-card">
                <div class="metric-label" style="margin-bottom:0.6rem">Desafíos del dataset</div>
                <ul style="margin:0;padding-left:1.2rem;font-size:0.83rem;color:var(--text);line-height:1.9">
                    <li>Reseñas con &lt; 5 votos producen tasas de utilidad no representativas</li>
                    <li>174 K duplicados por usuario-producto-fecha</li>
                    <li>70 % de clases "no útiles" → <em>Accuracy</em> no sirve como métrica</li>
                    <li>Texto de longitud muy variable: desde 1 palabra hasta miles</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with ctx2:
        st.markdown(
            """
            <div class="metric-card">
                <div class="metric-label" style="margin-bottom:0.6rem">Solución construida</div>
                <ul style="margin:0;padding-left:1.2rem;font-size:0.83rem;color:var(--text);line-height:1.9">
                    <li>Pipeline de limpieza reproducible con filtros documentados</li>
                    <li>4 features textuales derivadas sin modelos de lenguaje</li>
                    <li>2 clasificadores comparados con F1 y ROC-AUC</li>
                    <li>API FastAPI + Dashboard Streamlit con auditoría en tiempo real</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── Guía de navegación ────────────────────────────────────────────────────
    st.markdown('<div class="section-label">Guía del dashboard — qué encontrarás en cada sección</div>', unsafe_allow_html=True)

    pages = [
        ("📋", "Resumen Ejecutivo",        "Indicadores del pipeline de datos, métricas de modelos comparadas, hipótesis verificadas y distribuciones clave del caso."),
        ("🔍", "Exploración de Datos",     "EDA interactivo con filtros por estrellas, categoría y longitud. Relaciones entre variables y correlación con la utilidad."),
        ("🧪", "Modelos y Evaluación",     "Comparación Logistic Regression vs. LightGBM. Curva ROC, matriz de confusión e importancia de features explicada en lenguaje natural."),
        ("🛡️", "Auditoría en Tiempo Real", "Escribe una reseña y obtén en segundos su probabilidad de utilidad, diagnóstico de coherencia y recomendaciones para mejorarla."),
        ("🏆", "Ranking y Benchmark",      "Posición de cada reseña auditada dentro del catálogo del producto. Vista global y comparativa entre productos."),
    ]

    for icon, title, desc in pages:
        st.markdown(
            f"""
            <div style="display:flex;gap:1rem;align-items:flex-start;
                        padding:0.85rem 1rem;border-radius:10px;
                        border:1px solid rgba(23,70,162,0.12);
                        background:rgba(23,70,162,0.03);
                        margin-bottom:0.5rem">
                <div style="font-size:1.4rem;line-height:1;flex-shrink:0;padding-top:0.1rem">{icon}</div>
                <div>
                    <div style="font-weight:700;font-size:0.88rem;color:var(--text);margin-bottom:0.2rem">{title}</div>
                    <div style="font-size:0.8rem;color:var(--muted);line-height:1.5">{desc}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── Estado de la API ──────────────────────────────────────────────────────
    st.markdown('<div class="section-label">Estado de la API de predicción</div>', unsafe_allow_html=True)
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
                <span class="metric-badge {'metric-badge-good' if api_ok else 'metric-badge-warn'}">{'Activa' if api_ok else 'Sin respuesta'}</span>
            </div>
            <div class="api-card">
                <div class="api-card-label">Modelo en API</div>
                <div class="api-card-value">LightGBM</div>
                <span class="metric-badge {'metric-badge-good' if lgb_ok else 'metric-badge-warn'}">{'Cargado' if lgb_ok else 'Heurística'}</span>
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
    st.markdown('<div class="section-label">Equipo</div>', unsafe_allow_html=True)
    t1, t2, t3 = st.columns(3, gap="medium")
    for col, name, role in zip(
        [t1, t2, t3],
        ["Arévalo José", "Cholango Mónica", "Torres Byron"],
        ["EDA & Pipeline", "Modelado & API", "Dashboard & UI"],
    ):
        with col:
            st.markdown(
                f"""
                <div class="metric-card" style="text-align:center">
                    <div style="font-size:1.6rem;margin-bottom:0.4rem">👤</div>
                    <div style="font-weight:700;font-size:0.9rem">{name}</div>
                    <div style="font-size:0.75rem;color:var(--muted);margin-top:0.2rem">{role}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


if __name__ == "__main__":
    main()