from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Candidato:
    """Representación ligera de un candidato usada por la capa de sesión.

    Esta clase contiene sólo los campos requeridos por la lógica en memoria
    (no reemplaza los modelos de persistencia SQLAlchemy).
    """
    codigo: str
    nombre_completo: str
    email: str
    telefono: str = ""
    cargo: str = ""
    fecha_registro: str = ""
    evaluacion_completada: bool = False
    link_evaluacion: str = ""
    puntos_finales: float = 0.0
    nivel_final: int = 1


@dataclass
class Pregunta:
    """Representación simple de una pregunta en memoria.

    Los campos coinciden con los diccionarios que antes se construían en
    `app.py` al cargar el Excel. Mantener esta clase facilita testing
    y documentación.
    """
    id: int
    pregunta: str
    opciones: List[str]
    respuesta_correcta: str
    respuestas_correctas: List[str]
    nivel: int
    multiple: bool = False
    imagen: Optional[str] = None
    categoria: str = "General"
    fila_excel: int = 0


def safe_opt(opciones: List[str], letra: str) -> str:
    """Obtener texto de opción a partir de su letra (A..E).

    Retorna cadena vacía si la letra no es válida o no existe en la lista.
    """
    try:
        if not letra:
            return ''
        idx = ord(letra.upper()[0]) - ord('A')
        if 0 <= idx < len(opciones):
            return opciones[idx]
        return ''
    except Exception:
        return ''
