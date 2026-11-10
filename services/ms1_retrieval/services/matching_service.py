import unicodedata
import re
from difflib import SequenceMatcher
from typing import Tuple, Optional, List

def normalize_text(text: Optional[str]) -> str:
    """
    Normaliza una cadena de texto eliminando tildes, puntuación, caracteres especiales
    y reduciendo espacios múltiples para comparación textual determinista.
    """
    if not text:
        return ""
    # Descomponer caracteres con acento
    nfkd = unicodedata.normalize("NFKD", text)
    # Filtrar marcas de acentos (diacríticos)
    sin_tildes = "".join([c for c in nfkd if not unicodedata.combining(c)])
    # Convertir a minúsculas
    minusculas = sin_tildes.lower()
    # Reemplazar signos de puntuación y caracteres no alfanuméricos por espacios
    limpio = re.sub(r"[^\w\s]", " ", minusculas)
    # Colapsar espacios múltiples
    return re.sub(r"\s+", " ", limpio).strip()


def calculate_similarity(text1: Optional[str], text2: Optional[str]) -> float:
    """
    Calcula el ratio de similitud (0.0 a 1.0) entre dos textos normalizados
    utilizando el algoritmo de emparejamiento de secuencias (Levenshtein ponderado).
    """
    norm1 = normalize_text(text1)
    norm2 = normalize_text(text2)
    if not norm1 or not norm2:
        return 0.0
    return SequenceMatcher(None, norm1, norm2).ratio()


def evaluate_doi_match(
    dspace_title: Optional[str],
    candidate_title: Optional[str],
    threshold: float = 0.85
) -> Tuple[float, bool]:
    """
    Protocolo de validación cuando existe DOI registrado:
    Si el título devuelto por la fuente externa difiere sintácticamente (< 85%),
    se clasifica como coincidencia dudosa para evitar asignar metadatos erróneos.
    """
    score = calculate_similarity(dspace_title, candidate_title)
    is_valid = score >= threshold
    return score, is_valid


def evaluate_no_doi_match(
    dspace_title: Optional[str],
    candidate_title: Optional[str],
    acceptance_threshold: float = 0.95,
    doubtful_threshold: float = 0.70
) -> Tuple[float, str]:
    """
    Protocolo de validación cuando NO existe DOI:
    - >= 95%: Alta certidumbre (Aceptación automática de coincidencia).
    - 70% a 94%: Coincidencia dudosa (Derivar a revisión de curador).
    - < 70%: Descartada.
    """
    score = calculate_similarity(dspace_title, candidate_title)
    if score >= acceptance_threshold:
        return score, "ACEPTADA"
    elif score >= doubtful_threshold:
        return score, "DUDOSA"
    else:
        return score, "DESCARTADA"

