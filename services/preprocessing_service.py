"""Servicios de preparacion y base operativa para la app.

Este modulo conecta la data historica con la experiencia del dashboard:
- filtra y deduplica
- inicializa una base corporativa en memoria
- agrega nuevas reseñas auditadas
- prepara tablas de ranking y vistas globales
"""

import pandas as pd
import numpy as np
import streamlit as st

from services.supabase_service import save_review_to_supabase, clear_supabase_cache
from services.catalog_service import get_product_catalog, get_product_detail, map_product_metadata
from services.data_loader import ensure_generated_data_dirs, load_audited_reviews_file, load_processed_reviews, read_uploaded_csv
from services.ml_service import audit_review_text
from config.settings import AUDITED_REVIEWS_PATH
from utils.validators import has_required_columns


def _build_created_at_series(df: pd.DataFrame) -> pd.Series:
    """Normaliza una columna temporal para ordenar reseñas por fecha."""
    if "CreatedAt" in df.columns:
        return pd.to_datetime(df["CreatedAt"], errors="coerce")
    if "Time" in df.columns:
        converted = pd.to_datetime(df["Time"], unit="s", errors="coerce")
        return converted.fillna(pd.Timestamp.now())
    return pd.Series(pd.Timestamp.now(), index=df.index)


def filter_valid_reviews(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica el filtro minimo de votos utiles definido por el caso."""
    if "HelpfulnessDenominator" not in df.columns:
        return df.copy()
    return df[df["HelpfulnessDenominator"] >= 5].copy()


def deduplicate_reviews(df: pd.DataFrame) -> pd.DataFrame:
    """Elimina duplicados usando la llave sugerida en la guia."""
    subset = [col for col in ["UserId", "ProductId", "Time"] if col in df.columns]
    if not subset:
        return df.copy()
    return df.drop_duplicates(subset=subset).copy()


def initialize_corporate_audit_db() -> pd.DataFrame:
    """Crea o recupera la base transaccional que usa la app en memoria.

    Si existe data procesada suficiente, construye una base inicial desde ella.
    Si no, genera una base de respaldo para que la interfaz siga operando.
    """
    existing = st.session_state.get("db_central_corporativa")
    if isinstance(existing, pd.DataFrame) and not existing.empty:
        return existing

    processed = load_processed_reviews()
    audited_file_df = load_audited_reviews_file()
    catalog = get_product_catalog()
    pool_ids = catalog["ProductId"].astype(str).unique() if not catalog.empty else ["B001E4KFG0"]

    if not processed.empty and {"ProductId", "Score", "Text"}.issubset(processed.columns):
        base = processed.copy().tail(1000)
        base = base.rename(columns={"Score": "Stars"})
        base["ID_Transaccion"] = range(10001, 10001 + len(base))
        if "ProfileName" in base.columns:
            base["User"] = base["ProfileName"].fillna("Historico")
        else:
            base["User"] = [f"Historico_{i}" for i in range(1, len(base) + 1)]
        if "Helpfulness" not in base.columns:
            if "HelpfulnessNumerator" in base.columns and "HelpfulnessDenominator" in base.columns:
                denominator = base["HelpfulnessDenominator"].replace(0, pd.NA)
                base["Helpfulness"] = (base["HelpfulnessNumerator"] / denominator).fillna(0)
            elif "y_util" in base.columns:
                base["Helpfulness"] = base["y_util"].astype(float)
            else:
                base["Helpfulness"] = 0.45
        base["Estado"] = np.where(base["Helpfulness"] >= 0.70, "APROBADA (Publicada)", "RECHAZADA (Baja Calidad)")
        base["ProductId"] = base["ProductId"].astype(str)
        base["Text"] = base["Text"].astype(str).str.slice(0, 240)
        base["CreatedAt"] = _build_created_at_series(base)
        corporate_db = base[["ID_Transaccion", "ProductId", "User", "Stars", "Helpfulness", "Text", "Estado", "CreatedAt"]].copy()
    else:
        np.random.seed(42)
        created_at = pd.date_range(end=pd.Timestamp.now(), periods=1000, freq="h")
        corporate_db = pd.DataFrame(
            {
                "ID_Transaccion": range(10001, 11001),
                "ProductId": np.random.choice(pool_ids, 1000),
                "User": [f"Historico_{i}" for i in range(1, 1001)],
                "Stars": np.random.choice([1, 2, 3, 4, 5], 1000, p=[0.1, 0.05, 0.1, 0.25, 0.5]),
                "Helpfulness": np.random.uniform(0.15, 0.92, 1000),
                "Text": ["Resena historica real analizada para el tablero."] * 1000,
                "Estado": ["APROBADA (Publicada)"] * 1000,
                "CreatedAt": created_at,
            }
        )

    if not audited_file_df.empty:
        audited_file_df = audited_file_df.copy()
        if "CreatedAt" in audited_file_df.columns:
            audited_file_df["CreatedAt"] = pd.to_datetime(audited_file_df["CreatedAt"], errors="coerce")
        corporate_db = pd.concat([corporate_db, audited_file_df], ignore_index=True)

    st.session_state["db_central_corporativa"] = corporate_db
    return corporate_db


def get_corporate_audit_db() -> pd.DataFrame:
    """Expone una copia segura de la base corporativa en memoria."""
    db = initialize_corporate_audit_db()
    return db.copy()


def append_audited_review(
    product_id: str,
    user_name: str,
    stars: int,
    text: str,
    validate_context: bool = True,
) -> dict:
    db = initialize_corporate_audit_db()
    product_detail = get_product_detail(product_id)
    audit_result = audit_review_text(
        text, stars, product_id,
        product_name=product_detail.get("ProductName"),
        category_name=product_detail.get("Categoria_Real"),
        validate_context=validate_context,
    )
    new_id = int(db["ID_Transaccion"].max()) + 1 if not db.empty else 10001

    new_row = pd.DataFrame([{
        "ID_Transaccion": new_id,
        "ProductId":      str(product_id),
        "User":           user_name,
        "Stars":          int(stars),
        "Helpfulness":    audit_result["probability"],
        "Text":           text,
        "Estado":         audit_result["status"],
        "CreatedAt":      pd.Timestamp.now(),
    }])

    # Memoria sesión actual
    updated_db = pd.concat([db, new_row], ignore_index=True)
    st.session_state["db_central_corporativa"] = updated_db
    st.session_state["latest_review_id"]       = new_id
    st.session_state["latest_audit_result"]    = audit_result

    # Persistencia Supabase
    save_review_to_supabase(audit_result, new_row.iloc[0].to_dict())
    clear_supabase_cache()

    return audit_result


def _serialize_generated_review_row(row_df: pd.DataFrame, product_detail: dict, audit_result: dict) -> pd.DataFrame:
    """Prepara la fila de reseña auditada para persistencia en CSV."""
    serialized = row_df.copy()
    serialized["ProductName"] = product_detail.get("ProductName")
    serialized["Categoria_Real"] = product_detail.get("Categoria_Real")
    serialized["context_validation_enabled"] = audit_result.get("context_validation_enabled")
    serialized["context_blind_spot"] = audit_result.get("context_blind_spot")
    serialized["context_hits"] = ", ".join(audit_result.get("context_hits", []))
    serialized["tech_hits"] = ", ".join(audit_result.get("tech_hits", []))
    serialized["context_explanation"] = audit_result.get("context_explanation")
    serialized["review_len"] = audit_result.get("review_len")
    serialized["sentiment_score"] = audit_result.get("sentiment_score")
    serialized["incoherente"] = audit_result.get("incoherente")
    return serialized


def save_latest_review_to_file(product_id: str) -> tuple[bool, str]:
    """Guarda la última reseña auditada en el CSV operativo separado."""
    latest_review_id = st.session_state.get("latest_review_id")
    latest_result = st.session_state.get("latest_audit_result")
    if latest_review_id is None or latest_result is None:
        return False, "No hay una reseña auditada reciente para guardar."

    db = get_corporate_audit_db()
    match = db[db["ID_Transaccion"] == latest_review_id].copy()
    if match.empty:
        return False, "No se encontró la reseña evaluada dentro de la base operativa."

    ensure_generated_data_dirs()
    product_detail = get_product_detail(product_id)
    row_to_save = _serialize_generated_review_row(match, product_detail, latest_result)

    existing_df = load_audited_reviews_file()
    if not existing_df.empty and latest_review_id in existing_df.get("ID_Transaccion", pd.Series(dtype=int)).tolist():
        return False, "Esa reseña ya fue guardada previamente en el archivo operativo."

    if AUDITED_REVIEWS_PATH.exists():
        row_to_save.to_csv(AUDITED_REVIEWS_PATH, mode="a", header=False, index=False, encoding="utf-8-sig")
    else:
        row_to_save.to_csv(AUDITED_REVIEWS_PATH, index=False, encoding="utf-8-sig")

    load_audited_reviews_file.clear()
    return True, f"Reseña guardada en {AUDITED_REVIEWS_PATH.name}."


def process_uploaded_audit_batch(df_input: pd.DataFrame) -> tuple[pd.DataFrame, str | None]:
    """Procesa un lote CSV subido por el usuario y lo integra a la base."""
    required_columns = ["ProductId", "ProfileName", "Score", "Text"]
    if df_input.empty:
        return pd.DataFrame(), "No se encontro informacion en el archivo cargado."
    if not has_required_columns(df_input.columns.tolist(), required_columns):
        return pd.DataFrame(), "El archivo debe contener ProductId, ProfileName, Score y Text."

    db = initialize_corporate_audit_db()
    next_id = int(db["ID_Transaccion"].max()) if not db.empty else 10000
    processed_rows = []

    for _, row in df_input.iterrows():
        next_id += 1
        product_id = str(row["ProductId"])
        product_detail = get_product_detail(product_id)
        audit_result = audit_review_text(
            str(row["Text"]),
            int(row["Score"]),
            product_id,
            product_name=product_detail.get("ProductName"),
            category_name=product_detail.get("Categoria_Real"),
            validate_context=True,
        )
        processed_rows.append(
            {
                "ID_Transaccion": next_id,
                "ProductId": product_id,
                "User": str(row["ProfileName"]),
                "Stars": int(row["Score"]),
                "Helpfulness": audit_result["probability"],
                "Text": str(row["Text"])[:140] + ("..." if len(str(row["Text"])) > 140 else ""),
                "Estado": audit_result["status"],
                "CreatedAt": pd.Timestamp.now(),
            }
        )

    batch_df = pd.DataFrame(processed_rows)
    st.session_state["db_central_corporativa"] = pd.concat([db, batch_df], ignore_index=True)

    # ── Guardar cada fila del lote en Supabase ───────────────────────────────
    sb_errors = 0
    for i, (proc_row, orig_row) in enumerate(zip(processed_rows, df_input.itertuples())):
        audit_r = audit_review_text(
            str(proc_row["Text"].replace("...", "")),
            int(proc_row["Stars"]),
            proc_row["ProductId"],
            validate_context=False,  # ya se auditó arriba, evitar doble cómputo
        )
        row_data = {
            "ID_Transaccion": proc_row["ID_Transaccion"],
            "ProductId":      proc_row["ProductId"],
            "User":           proc_row["User"],
            "Stars":          proc_row["Stars"],
            "Text":           proc_row["Text"],
        }
        ok, _ = save_review_to_supabase(audit_r, row_data)
        if not ok:
            sb_errors += 1

    clear_supabase_cache()
    if sb_errors > 0:
        return batch_df, f"{sb_errors} filas no pudieron guardarse en Supabase."
    return batch_df, None


def process_uploaded_audit_file(uploaded_file) -> tuple[pd.DataFrame, str | None]:
    """Atajo para leer y procesar un CSV de auditoría desde Streamlit."""
    df_input = read_uploaded_csv(uploaded_file)
    return process_uploaded_audit_batch(df_input)


def get_local_product_ranking(product_id: str) -> pd.DataFrame:
    """Construye el ranking local de reseñas para un producto."""
    db = get_corporate_audit_db()
    local_df = db[db["ProductId"].astype(str) == str(product_id)].copy()
    if local_df.empty:
        return local_df
    local_df = local_df.sort_values(by="Helpfulness", ascending=False).reset_index(drop=True)
    local_df.insert(0, "Puesto Local", range(1, len(local_df) + 1))
    return local_df


def get_global_ranking() -> pd.DataFrame:
    """Ranking global por utilidad sobre toda la base visible."""
    db = get_corporate_audit_db()
    if db.empty:
        return db
    ranking_df = db.sort_values(by="Helpfulness", ascending=False).reset_index(drop=True)
    ranking_df.insert(0, "Puesto Global", range(1, len(ranking_df) + 1))
    return ranking_df


def get_product_benchmark(product_id: str) -> dict:
    """Resume el desempeño histórico del producto seleccionado."""
    ranking_df = get_local_product_ranking(product_id)
    if ranking_df.empty:
        return {
            "count": 0,
            "avg_helpfulness": 0.0,
            "top_helpfulness": 0.0,
            "median_helpfulness": 0.0,
        }

    return {
        "count": int(len(ranking_df)),
        "avg_helpfulness": float(ranking_df["Helpfulness"].mean()),
        "top_helpfulness": float(ranking_df["Helpfulness"].max()),
        "median_helpfulness": float(ranking_df["Helpfulness"].median()),
    }


def get_product_reviews_by_date(product_id: str, ascending: bool = False) -> pd.DataFrame:
    """Historial de reseñas del producto ordenado por fecha."""
    db = get_corporate_audit_db()
    product_df = db[db["ProductId"].astype(str) == str(product_id)].copy()
    if product_df.empty:
        return product_df
    product_df["CreatedAt"] = pd.to_datetime(product_df["CreatedAt"], errors="coerce")
    return product_df.sort_values(by="CreatedAt", ascending=ascending).reset_index(drop=True)


def get_position_summary(product_id: str, review_id: int | None) -> dict:
    """Calcula posición local y global de una reseña evaluada."""
    if review_id is None:
        return {"local_rank": None, "global_rank": None, "product_count": 0, "global_count": 0}

    local_ranking = get_local_product_ranking(product_id)
    global_ranking = get_global_ranking()

    local_rank = None
    global_rank = None
    if not local_ranking.empty:
        match = local_ranking[local_ranking["ID_Transaccion"] == review_id]
        if not match.empty:
            local_rank = int(match.iloc[0]["Puesto Local"])
    if not global_ranking.empty:
        match = global_ranking[global_ranking["ID_Transaccion"] == review_id]
        if not match.empty:
            global_rank = int(match.iloc[0]["Puesto Global"])

    return {
        "local_rank": local_rank,
        "global_rank": global_rank,
        "product_count": int(len(local_ranking)),
        "global_count": int(len(global_ranking)),
    }


def get_review_context_window(product_id: str, review_id: int | None, window_size: int = 1) -> pd.DataFrame:
    """Construye la ventana tipo sandwich alrededor de una reseña en el ranking local."""
    local_ranking = get_local_product_ranking(product_id)
    if local_ranking.empty or review_id is None:
        return pd.DataFrame()

    match = local_ranking[local_ranking["ID_Transaccion"] == review_id]
    if match.empty:
        return pd.DataFrame()

    index = int(match.index[0])
    start = max(0, index - window_size)
    end = min(len(local_ranking), index + window_size + 1)
    window_df = local_ranking.iloc[start:end].copy()
    window_df["EsActual"] = window_df["ID_Transaccion"] == review_id
    return window_df


def get_visible_global_audit_table() -> pd.DataFrame:
    """Devuelve la tabla global enriquecida con metadata legible."""
    return map_product_metadata(get_corporate_audit_db())


def get_audited_reviews_operational_table() -> pd.DataFrame:
    """Expone la tabla persistida de reseñas nuevas guardadas por la app."""
    return load_audited_reviews_file().copy()