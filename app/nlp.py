import re
from typing import Dict, Tuple, Optional

SALES_KEYWORDS = {
    "precio", "precios", "costo", "costos", "plan", "planes", "pago", "pagar",
    "demo", "contratar", "factura", "licencia", "cotización", "cotizacion", "cuesta", "valor"
}
SUPPORT_KEYWORDS = {
    "error", "falla", "bug", "no funciona", "soporte", "ayuda", "problema",
    "reiniciar", "instalar", "actualizar", "restablecer", "contraseña", "contrasena", "falló", "fallo"
}
GENERAL_KEYWORDS = {
    "horarios", "empresa", "contacto", "quienes son", "quiénes son", "ubicación", "ubicacion",
    "sobre", "información", "informacion", "telefono", "correo", "email"
}

def normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text

def tokenize(text: str) -> set:
    # tokens muy simples, sin librerías externas
    text = re.sub(r"[^\wáéíóúñü ]", " ", text.lower())
    return set(text.split())

def _substring_hits(msg: str, keywords: set) -> int:
    return sum(1 for k in keywords if k in msg)

def classify(message: str, hint_category: Optional[str] = None) -> Tuple[str, float, Dict[str, int]]:
    """
    Clasificador por reglas sencillas:
    - Cuenta coincidencias de palabras clave en cada categoría.
    - Devuelve (categoria, confianza, detalle_coincidencias).
    """
    msg = normalize_text(message)
    tokens = tokenize(msg)

    # Puntuación híbrida: intersección de tokens + coincidencias por substring
    score_sales = len(tokens & SALES_KEYWORDS) + _substring_hits(msg, SALES_KEYWORDS)
    score_support = len(tokens & SUPPORT_KEYWORDS) + _substring_hits(msg, SUPPORT_KEYWORDS)
    score_general = len(tokens & GENERAL_KEYWORDS) + _substring_hits(msg, GENERAL_KEYWORDS)

    # Boost por contexto: si hay pista de categoría previa, súmale 1
    if hint_category == "ventas":
        score_sales += 1
    elif hint_category == "soporte":
        score_support += 1
    elif hint_category == "general":
        score_general += 1

    scores = {"ventas": score_sales, "soporte": score_support, "general": score_general}
    best_cat = max(scores, key=scores.get)
    best_score = scores[best_cat]
    total = score_sales + score_support + score_general

    confidence = 0.0 if total == 0 else round(best_score / max(total, 1), 2)
    return best_cat, confidence, scores

GREETINGS = {
    "hola", "buenas", "buenos dias", "buenos días", "buenas tardes", "buenas noches",
    "que tal", "qué tal", "hey", "holi", "saludos"
}

MENU_WORDS = {"menu", "inicio", "volver al inicio", "empezar", "reiniciar", "cambiar", "otra opcion", "otra opción"}

def is_greeting(text: str) -> bool:
    t = normalize_text(text)
    if any(g in t for g in GREETINGS):
        return True
    return t in {"hola", "buenas", "buenas!", "hey", "holi"}

def is_menu_request(text: str) -> bool:
    t = normalize_text(text)
    return any(w in t for w in MENU_WORDS)

import re
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"\b(?:\+?\d[\d -]{6,}\d)\b")

def seems_personal_data(text: str) -> bool:
    """Detecta si el usuario envió email/teléfono antes de dar contexto."""
    t = normalize_text(text)
    return bool(EMAIL_RE.search(t) or PHONE_RE.search(t))