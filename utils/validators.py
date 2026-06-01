def has_required_columns(columns: list[str], required_columns: list[str]) -> bool:
    """Verifica si un dataset contiene todas las columnas requeridas."""
    return all(column in columns for column in required_columns)


def is_non_empty_text(value: str) -> bool:
    """Valida que un texto no este vacio ni tenga solo espacios."""
    return bool(value and value.strip())
