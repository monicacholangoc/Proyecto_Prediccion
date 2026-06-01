import pandas as pd

from config.constants import TOPIC_NAMES
from services.data_loader import load_product_context


def get_product_catalog() -> pd.DataFrame:
    """Devuelve el catalogo enriquecido con categoria legible."""
    catalog = load_product_context().copy()
    if catalog.empty:
        return pd.DataFrame(
            {
                "ProductId": ["B001E4KFG0", "B00813GRG4", "B000G6RYNE"],
                "product_topic": [0, 1, 2],
                "ProductName": [
                    "Cafe molido premium",
                    "Premios para mascotas",
                    "Chocolate organico 85%",
                ],
            }
        )

    if "product_topic" in catalog.columns:
        catalog["Categoria_Real"] = catalog["product_topic"].map(TOPIC_NAMES).fillna("Alimentos generales")
    elif "Categoria_Real" not in catalog.columns:
        catalog["Categoria_Real"] = "Alimentos generales"
    return catalog


def get_product_options() -> list[str]:
    """Entrega ids de producto listos para widgets de seleccion."""
    catalog = get_product_catalog()
    if catalog.empty or "ProductId" not in catalog.columns:
        return []
    return sorted(catalog["ProductId"].dropna().astype(str).unique().tolist())


def get_product_detail(product_id: str) -> dict:
    """Busca el detalle resumido de un producto para la UI."""
    catalog = get_product_catalog()
    default = {
        "ProductId": product_id,
        "ProductName": "Producto comercial",
        "Categoria_Real": "Alimentos generales",
    }
    if catalog.empty or "ProductId" not in catalog.columns:
        return default

    match = catalog[catalog["ProductId"].astype(str) == str(product_id)]
    if match.empty:
        return default

    row = match.iloc[0]
    return {
        "ProductId": str(row.get("ProductId", product_id)),
        "ProductName": row.get("ProductName", default["ProductName"]),
        "Categoria_Real": row.get("Categoria_Real", default["Categoria_Real"]),
    }


def map_product_metadata(df: pd.DataFrame) -> pd.DataFrame:
    """Anexa nombre y categoria legible a tablas transaccionales."""
    catalog = get_product_catalog()
    if df.empty or catalog.empty or "ProductId" not in df.columns:
        return df.copy()

    enriched = df.copy()
    name_map = catalog.set_index("ProductId")["ProductName"].to_dict() if "ProductName" in catalog.columns else {}
    category_map = catalog.set_index("ProductId")["Categoria_Real"].to_dict()

    enriched["Nombre Comercial"] = enriched["ProductId"].map(name_map).fillna("Producto alimenticio general")
    enriched["Categoria de Modelo"] = enriched["ProductId"].map(category_map).fillna("Alimentos generales")
    return enriched
