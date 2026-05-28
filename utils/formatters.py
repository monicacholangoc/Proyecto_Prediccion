"""Funciones de formato reutilizables para presentar datos en UI."""

def format_percentage(value: float) -> str:
    """Convierte un float decimal a porcentaje legible."""
    return f"{value:.1%}"


def format_compact_number(value: int) -> str:
    """Formatea enteros con separador visual consistente."""
    return f"{value:,}".replace(",", ".")
