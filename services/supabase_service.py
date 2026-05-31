import pandas as pd
import streamlit as st
from services.supabase_client import get_supabase


def save_review_to_supabase(audit_result: dict, row_data: dict) -> tuple[bool, str]:
    try:
        payload = {
            "id_transaccion":    int(row_data.get("ID_Transaccion", 0)),
            "product_id":        str(row_data.get("ProductId", "")),
            "usuario":           str(row_data.get("User", "")),
            "stars":             int(row_data.get("Stars", 0)),
            "helpfulness":       float(audit_result.get("probability", 0)),
            "status":            str(audit_result.get("status", "")),
            "texto":             str(row_data.get("Text", ""))[:500],
            "review_len":        int(audit_result.get("review_len", 0)),
            "sentiment_score":   float(audit_result.get("sentiment_score", 0)),
            "incoherente":       bool(audit_result.get("incoherente", False)),
            "context_blind_spot": bool(audit_result.get("context_blind_spot", False)),
            "context_hits":      ", ".join(audit_result.get("context_hits", [])),
            "context_explanation": str(audit_result.get("context_explanation", "")),
        }
        get_supabase().table("auditoria_reviews").insert(payload).execute()
        return True, "Guardado en Supabase."
    except Exception as e:
        return False, f"Error: {e}"


@st.cache_data(ttl=30, show_spinner=False)
def load_reviews_from_supabase() -> pd.DataFrame:
    try:
        response = (
            get_supabase()
            .table("auditoria_reviews")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except Exception:
        return pd.DataFrame()


def clear_supabase_cache() -> None:
    load_reviews_from_supabase.clear()