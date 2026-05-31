"""Servicios para evaluar modelos con datos reales del proyecto.

Compara 4 clasificadores: Logistic Regression, LightGBM, XGBoost y CatBoost.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st
from lightgbm import LGBMClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, precision_score, recall_score, f1_score, roc_auc_score, roc_curve
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from config.constants import MODEL_FEATURES
from services.data_loader import load_processed_reviews

# Importar XGBoost y CatBoost con fallback si no están instalados
try:
    from xgboost import XGBClassifier
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

try:
    from catboost import CatBoostClassifier
    CATBOOST_AVAILABLE = True
except ImportError:
    CATBOOST_AVAILABLE = False


def _prepare_training_data() -> tuple[pd.DataFrame, pd.Series]:
    df = load_processed_reviews().copy()
    required_columns = MODEL_FEATURES + ["y_util"]
    if df.empty or not all(c in df.columns for c in required_columns):
        return pd.DataFrame(), pd.Series(dtype=float)
    model_df = df[required_columns].dropna().copy()
    return model_df[MODEL_FEATURES], model_df["y_util"].astype(int)


def _metrics_row(name, y_test, y_pred, y_proba) -> dict:
    return {
        "modelo":    name,
        "precision": precision_score(y_test, y_pred),
        "recall":    recall_score(y_test, y_pred),
        "f1":        f1_score(y_test, y_pred),
        "roc_auc":   roc_auc_score(y_test, y_proba),
    }


@st.cache_data(show_spinner=False)
def compute_model_evaluation() -> dict:
    X, y = _prepare_training_data()
    if X.empty or y.empty:
        return {"metrics": pd.DataFrame(), "feature_importance": pd.DataFrame(),
                "roc_curves": {}, "confusion_matrices": {}}

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    scaler = StandardScaler()
    X_tr_sc = scaler.fit_transform(X_train)
    X_te_sc = scaler.transform(X_test)

    # ── Logistic Regression ───────────────────────────────────────────────────
    lr = LogisticRegression(class_weight="balanced", random_state=42, max_iter=1000)
    lr.fit(X_tr_sc, y_train)
    y_pred_lr   = lr.predict(X_te_sc)
    y_proba_lr  = lr.predict_proba(X_te_sc)[:, 1]

    # ── LightGBM ──────────────────────────────────────────────────────────────
    lgb = LGBMClassifier(class_weight="balanced", random_state=42, verbose=-1)
    lgb.fit(X_train, y_train)
    y_pred_lgb  = lgb.predict(X_test)
    y_proba_lgb = lgb.predict_proba(X_test)[:, 1]

    # ── XGBoost ───────────────────────────────────────────────────────────────
    if XGBOOST_AVAILABLE:
        xgb = XGBClassifier(
            scale_pos_weight=(y_train == 0).sum() / (y_train == 1).sum(),
            random_state=42, eval_metric="logloss",
            use_label_encoder=False, verbosity=0,
        )
        xgb.fit(X_train, y_train)
        y_pred_xgb  = xgb.predict(X_test)
        y_proba_xgb = xgb.predict_proba(X_test)[:, 1]
    else:
        y_pred_xgb  = y_pred_lgb   # fallback visual
        y_proba_xgb = y_proba_lgb

    # ── CatBoost ──────────────────────────────────────────────────────────────
    if CATBOOST_AVAILABLE:
        cb = CatBoostClassifier(
            auto_class_weights="Balanced", random_seed=42,
            verbose=0, iterations=300,
        )
        cb.fit(X_train, y_train)
        y_pred_cb  = cb.predict(X_test)
        y_proba_cb = cb.predict_proba(X_test)[:, 1]
    else:
        y_pred_cb  = y_pred_lgb    # fallback visual
        y_proba_cb = y_proba_lgb

    # ── Métricas ──────────────────────────────────────────────────────────────
    metrics_df = pd.DataFrame([
        _metrics_row("Logistic Regression", y_test, y_pred_lr,  y_proba_lr),
        _metrics_row("LightGBM",            y_test, y_pred_lgb, y_proba_lgb),
        _metrics_row("XGBoost",             y_test, y_pred_xgb, y_proba_xgb),
        _metrics_row("CatBoost",            y_test, y_pred_cb,  y_proba_cb),
    ])

    # ── Feature importance (LightGBM como referencia) ─────────────────────────
    feature_importance_df = pd.DataFrame({
        "feature":    MODEL_FEATURES,
        "importancia": lgb.feature_importances_,
    })

    # ── Curvas ROC ────────────────────────────────────────────────────────────
    roc_lr  = roc_curve(y_test, y_proba_lr)
    roc_lgb = roc_curve(y_test, y_proba_lgb)
    roc_xgb = roc_curve(y_test, y_proba_xgb)
    roc_cb  = roc_curve(y_test, y_proba_cb)

    # ── Matrices de confusión ─────────────────────────────────────────────────
    confusion_matrices = {
        "Logistic Regression": confusion_matrix(y_test, y_pred_lr),
        "LightGBM":            confusion_matrix(y_test, y_pred_lgb),
        "XGBoost":             confusion_matrix(y_test, y_pred_xgb),
        "CatBoost":            confusion_matrix(y_test, y_pred_cb),
    }

    return {
        "metrics":            metrics_df,
        "feature_importance": feature_importance_df,
        "roc_curves": {
            "Logistic Regression": {"fpr": roc_lr[0],  "tpr": roc_lr[1]},
            "LightGBM":            {"fpr": roc_lgb[0], "tpr": roc_lgb[1]},
            "XGBoost":             {"fpr": roc_xgb[0], "tpr": roc_xgb[1]},
            "CatBoost":            {"fpr": roc_cb[0],  "tpr": roc_cb[1]},
        },
        "confusion_matrices": confusion_matrices,
    }