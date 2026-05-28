"""Servicios para evaluar modelos con datos reales del proyecto.

Esta capa reconstruye la comparación principal del seminario usando el
parquet procesado y un split reproducible. Sirve para alimentar la
página de modelos sin depender de valores de ejemplo.
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


def _prepare_training_data() -> tuple[pd.DataFrame, pd.Series]:
    """Obtiene las features y la variable objetivo del parquet limpio."""
    df = load_processed_reviews().copy()
    required_columns = MODEL_FEATURES + ["y_util"]
    if df.empty or not all(column in df.columns for column in required_columns):
        return pd.DataFrame(), pd.Series(dtype=float)

    model_df = df[required_columns].dropna().copy()
    X = model_df[MODEL_FEATURES]
    y = model_df["y_util"].astype(int)
    return X, y


@st.cache_data(show_spinner=False)
def compute_model_evaluation() -> dict:
    """Entrena y evalúa baseline y modelo principal con split reproducible."""
    X, y = _prepare_training_data()
    if X.empty or y.empty:
        return {
            "metrics": pd.DataFrame(),
            "feature_importance": pd.DataFrame(),
            "roc_curves": {},
            "confusion_matrices": {},
        }

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    lr_model = LogisticRegression(class_weight="balanced", random_state=42, max_iter=1000)
    lr_model.fit(X_train_scaled, y_train)
    y_pred_lr = lr_model.predict(X_test_scaled)
    y_proba_lr = lr_model.predict_proba(X_test_scaled)[:, 1]

    lgb_model = LGBMClassifier(class_weight="balanced", random_state=42, verbose=-1)
    lgb_model.fit(X_train, y_train)
    y_pred_lgb = lgb_model.predict(X_test)
    y_proba_lgb = lgb_model.predict_proba(X_test)[:, 1]

    metrics_df = pd.DataFrame(
        [
            {
                "modelo": "Logistic Regression",
                "precision": precision_score(y_test, y_pred_lr),
                "recall": recall_score(y_test, y_pred_lr),
                "f1": f1_score(y_test, y_pred_lr),
                "roc_auc": roc_auc_score(y_test, y_proba_lr),
            },
            {
                "modelo": "LightGBM",
                "precision": precision_score(y_test, y_pred_lgb),
                "recall": recall_score(y_test, y_pred_lgb),
                "f1": f1_score(y_test, y_pred_lgb),
                "roc_auc": roc_auc_score(y_test, y_proba_lgb),
            },
        ]
    )

    feature_importance_df = pd.DataFrame(
        {
            "feature": MODEL_FEATURES,
            "importancia": lgb_model.feature_importances_,
        }
    )

    roc_lr = roc_curve(y_test, y_proba_lr)
    roc_lgb = roc_curve(y_test, y_proba_lgb)

    confusion_matrices = {
        "Logistic Regression": confusion_matrix(y_test, y_pred_lr),
        "LightGBM": confusion_matrix(y_test, y_pred_lgb),
    }

    return {
        "metrics": metrics_df,
        "feature_importance": feature_importance_df,
        "roc_curves": {
            "Logistic Regression": {"fpr": roc_lr[0], "tpr": roc_lr[1]},
            "LightGBM": {"fpr": roc_lgb[0], "tpr": roc_lgb[1]},
        },
        "confusion_matrices": confusion_matrices,
    }
