from typing import Tuple, Dict, Any
from app.utils.logger import get_logger
from app.conversation import ConversationState
from app.nlp import classify, is_greeting, is_menu_request, seems_personal_data
from app.knowledge_base import search_faq
from app.semantic_service import semantic_answer

log = get_logger(__name__)

LOW_CONFIDENCE_THRESHOLD = 0.45
MAX_LOW_CONF_STREAK = 2
MAX_UNRESOLVED_STREAK = 2
MISUNDERSTAND_LIMIT = 2  # Derivar si no entiende 2 veces

HELP_TEXT = (
    "Puedo ayudarte con: ventas (planes, demo, precios), soporte (errores, restablecer contraseña), "
    "e información general (horarios, contacto). Escribe 'reiniciar' para limpiar la conversación."
)

AGENT_KEYWORDS = {"agente", "humano", "representante", "asesor", "soporte humano", "hablar con alguien"}

MAIN_MENU = (
    "👋 ¡Hola! Soy tu asistente.\n"
    "¿En qué te puedo ayudar?\n"
    "1) Ventas (planes, demo, precios)\n"
    "2) Soporte (errores, acceso, contraseña)\n"
    "3) Información general (horarios, contacto)\n"
    "Escribe 1, 2 o 3 — o el nombre de la opción.\n"
    "Puedes escribir 'inicio' o 'menu' para volver aquí cuando quieras."
)

# ---------------------
# Helpers generales
# ---------------------
def _norm(s: str) -> str:
    return s.strip().lower()

def _get_misunder_count(state: ConversationState) -> int:
    try:
        return int(state.meta.get("misunder_count", "0"))
    except Exception:
        return 0

def _set_misunder_count(state: ConversationState, value: int) -> None:
    state.meta["misunder_count"] = str(value)

def _bump_misunder(state: ConversationState, inc: int = 1) -> bool:
    count = _get_misunder_count(state) + inc
    _set_misunder_count(state, count)
    return count >= MISUNDERSTAND_LIMIT

def _clear_misunder(state: ConversationState) -> None:
    _set_misunder_count(state, 0)

THANKS_WORDS = {
    "gracias", "muchas gracias", "mil gracias", "gracias!", "gracias.", "gracias!!",
    "thanks", "thank you"
}
def _is_thanks(text: str) -> bool:
    t = _norm(text)
    return any(t == w or w in t for w in THANKS_WORDS)

def _detect_support_issue(msg: str) -> str:
    t = msg.lower()
    if any(k in t for k in ["contraseña", "contrasena", "password"]):
        return "password_issue"
    if any(k in t for k in ["código", "codigo", "2fa", "verificación", "verificacion", "otp"]):
        return "2fa_issue"
    return ""

def _maybe_choose_category_from_menu(text: str) -> str | None:
    t = text.strip().lower()
    if t in {"1", "ventas"}:
        return "ventas"
    if t in {"2", "soporte"}:
        return "soporte"
    if t in {"3", "informacion", "información", "info"}:
        return "general"
    return None

def _go_to_menu(state: ConversationState) -> Tuple[str, Dict[str, Any]]:
    state.stage = "menu"
    state.selected_category = None
    state.last_category = None
    state.low_conf_streak = 0
    state.unresolved_streak = 0
    reply = MAIN_MENU
    return reply, {"category": None, "confidence": 1.0, "low_confidence": False, "command_menu": True}

def default_reply_for(category: str) -> str:
    if category == "ventas":
        return "Sobre ventas: puedo contarte de planes, demo y precios. ¿Qué necesitas exactamente?"
    if category == "soporte":
        return "Entiendo que necesitas soporte. ¿Puedes describirme el problema con más detalle?"
    return "Con gusto. ¿Buscas información general como horarios, contacto o quiénes somos?"

# ---------------------
# Flujo VENTAS
# ---------------------
AGREE_WORDS = {"si", "sí", "ok", "okay", "vale", "claro", "de acuerdo", "por favor", "dale", "correcto", "afirmativo", "hagamoslo", "hagámoslo"}
def _is_yes(text: str) -> bool:
    t = _norm(text)
    return any(w == t or w in t for w in AGREE_WORDS)

NUM_WORDS = {
    "uno": 1, "una": 1, "un": 1,
    "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5,
    "seis": 6, "siete": 7, "ocho": 8, "nueve": 9,
    "diez": 10, "once": 11, "doce": 12, "trece": 13, "catorce": 14, "quince": 15
}
def _extract_users_from_text(text: str) -> int | None:
    import re
    t = _norm(text)
    m = re.search(r"\b(\d{1,4})\b", t)
    if m:
        return int(m.group(1))
    for w, n in NUM_WORDS.items():
        if f" {w} " in f" {t} ":
            return n
    return None

VENTAS_MENSUAL = {"mensual", "mensualidad", "plan mensual"}
VENTAS_ANUAL   = {"anual", "anualidad", "plan anual"}
VENTAS_CONSUMO = {"consumo", "por consumo", "pay as you go", "variable"}

def _sales_flow(state: ConversationState, user_text: str) -> tuple[str, dict]:
    
    txt = _norm(user_text)

    # Confirmación para derivar
    if state.meta.get("sales_ready_to_assign") and _is_yes(txt):
        reply = "Perfecto, te derivo con un asesor humano para que te comparta la cotización exacta. Te contactarán en breve."
        return reply, {"category": "ventas", "confidence": 1.0, "low_confidence": False, "needs_agent": True}

    # Tipo de plan
    if not state.meta.get("sales_plan"):
        if any(w in txt for w in VENTAS_MENSUAL):
            state.meta["sales_plan"] = "mensual"
        elif any(w in txt for w in VENTAS_ANUAL):
            state.meta["sales_plan"] = "anual"
        elif any(w in txt for w in VENTAS_CONSUMO):
            state.meta["sales_plan"] = "consumo"
        if state.meta.get("sales_plan"):
            plan = state.meta["sales_plan"]
            reply = {
                "mensual": "Perfecto, plan mensual. ¿Para cuántos usuarios y en qué país/moneda?",
                "anual":   "Genial, plan anual. ¿Para cuántos usuarios y en qué país/moneda?",
                "consumo": "Ok, plan por consumo. ¿Qué volumen aproximado al mes y en qué país/moneda?"
            }[plan]
            return reply, {"category": "ventas", "confidence": 1.0, "low_confidence": False}

    # Usuarios (número o palabra)
    users = _extract_users_from_text(txt)
    if users and not state.meta.get("sales_users"):
        state.meta["sales_users"] = str(users)

    # País / moneda (heurística simple)
    KNOWN_CURRENCIES = {"usd","eur","cop","mxn","ars","pen","clp"}
    KNOWN_COUNTRIES = {"colombia","mexico","méxico","argentina","peru","perú","chile","espana","españa"}
    words = set(txt.replace(",", " ").split())
    currency = next((w for w in words if w in KNOWN_CURRENCIES), None)
    country = next((w for w in words if w in KNOWN_COUNTRIES), None)
    if currency and not state.meta.get("sales_currency"):
        state.meta["sales_currency"] = currency.upper()
    if country and not state.meta.get("sales_country"):
        state.meta["sales_country"] = country.capitalize()

    # Decidir siguiente paso
    has_plan    = bool(state.meta.get("sales_plan"))
    has_users   = bool(state.meta.get("sales_users"))
    has_country = bool(state.meta.get("sales_country")) or bool(state.meta.get("sales_currency"))

    if not has_plan:
        return ("¿Buscas mensual, anual o por consumo?", {"category": "ventas","confidence":1.0,"low_confidence":False})
    if not has_users and not has_country:
        return ("Perfecto. Para cotizarte, ¿en qué país/moneda y para cuántos usuarios lo necesitas?",
                {"category": "ventas","confidence":1.0,"low_confidence":False})
    if not has_users:
        return ("Anotado el país/moneda. ¿Para cuántos usuarios?", {"category":"ventas","confidence":1.0,"low_confidence":False})
    if not has_country:
        return ("¿En qué país/moneda lo necesitas?", {"category":"ventas","confidence":1.0,"low_confidence":False})

    # Oferta final -> próxima confirmación deriva
    state.meta["sales_ready_to_assign"] = "1"
    reply = ("Gracias, con esa información puedo generarte una cotización exacta. "
             "¿Deseas que te contacte un asesor humano para cerrar los detalles?")
    return reply, {"category":"ventas","confidence":1.0,"low_confidence":False}

# ---------------------
# ROUTE MESSAGE
# ---------------------
def route_message(state: ConversationState, user_text: str) -> Tuple[str, Dict[str, Any]]:
    text = user_text.strip().lower()

    # Comandos globales
    if text in {"reiniciar", "reset", "/reset"}:
        state.reset()
        log.info("Conversación reiniciada por el usuario.")
        return _go_to_menu(state)

    if is_menu_request(user_text):
        return _go_to_menu(state)

    # Despedida amable
    if _is_thanks(user_text):
        reply = "¡Con gusto! Si necesitas algo más, aquí estaré."
        state.add_user(user_text); state.add_bot(reply)
        return reply, {"category": state.last_category, "confidence": 1.0, "low_confidence": False, "end": True}

    # Menú
    if state.stage == "menu":
        if is_greeting(user_text) or seems_personal_data(user_text):
            reply = "¡Hola! 😊 " + MAIN_MENU
            return reply, {"category": None, "confidence": 1.0, "low_confidence": False, "command_menu": True}

        chosen = _maybe_choose_category_from_menu(user_text)
        if chosen:
            state.stage = "chat"
            state.selected_category = chosen
            state.last_category = chosen
            if chosen == "ventas":
                return "Perfecto, hablemos de ventas. ¿Buscas precios, demo o planes?", {"category": "ventas", "confidence": 1.0, "low_confidence": False}
            if chosen == "soporte":
                return "De acuerdo, voy a ayudarte con soporte. Cuéntame exactamente qué ocurre (por ejemplo: mensaje de error, en qué paso).", {"category": "soporte", "confidence": 1.0, "low_confidence": False}
            return "Genial, información general. ¿Te interesan horarios, contacto o quiénes somos?", {"category": "general", "confidence": 1.0, "low_confidence": False}

        return MAIN_MENU, {"category": None, "confidence": 1.0, "low_confidence": False, "command_menu": True}

    # Solicitud explícita de agente
    if any(k in text for k in AGENT_KEYWORDS):
        reply = "De acuerdo, te derivo con un agente humano. En breve te contactarán."
        state.add_user(user_text); state.add_bot(reply)
        return reply, {"category": state.last_category, "confidence": 1.0, "low_confidence": False, "needs_agent": True}

    # Clasificación con pista
    hint = state.selected_category or state.last_category
    category, confidence, _ = classify(user_text, hint_category=hint)
    low_conf = confidence < LOW_CONFIDENCE_THRESHOLD

    # Racha baja confianza
    state.low_conf_streak = state.low_conf_streak + 1 if low_conf else 0
    if state.low_conf_streak >= MAX_LOW_CONF_STREAK:
        reply = "Veo que esto requiere más detalle. Te derivo con un agente humano para que lo revisen contigo."
        state.add_user(user_text); state.add_bot(reply)
        return reply, {"category": category, "confidence": confidence, "low_confidence": True, "needs_agent": True}

    # Derivación GLOBAL por baja confianza
    if low_conf:
        if _bump_misunder(state, 1):
            reply = "No estoy logrando entenderte correctamente. Para ayudarte mejor, te derivo con un asesor humano."
            state.add_user(user_text); state.add_bot(reply)
            state.last_category = category or state.last_category
            return reply, {"category": category, "confidence": confidence, "low_confidence": True, "needs_agent": True}
    else:
        _clear_misunder(state)

    # Comandos de volver
    if any(kw in text for kw in ["no es eso", "otra cosa", "me equivoqué", "me equivoque"]):
        return _go_to_menu(state)

    # Mantener categoría elegida
    if state.selected_category and category != state.selected_category and low_conf:
        category = state.selected_category

    # Flujo VENTAS
    if category == "ventas" or (state.selected_category == "ventas"):
        sales_reply, sales_meta = _sales_flow(state, user_text)
        state.add_user(user_text); state.add_bot(sales_reply)
        state.last_category = "ventas"
        state.selected_category = "ventas"
        return sales_reply, {**sales_meta}

    # Flujo SOPORTE
    if category == "soporte":
        issue = _detect_support_issue(user_text)
        if issue == "password_issue":
            if not state.meta.get("did_password_reset_tip"):
                reply = "Puedes restablecer tu contraseña desde 'Olvidé mi contraseña' en el login. ¿Te llegó el correo de restablecimiento?"
                state.meta["did_password_reset_tip"] = "1"
                state.unresolved_streak = 0
            else:
                state.unresolved_streak += 1
                reply = "Entiendo. Si ya intentaste restablecer y no funcionó, ¿te aparece algún mensaje adicional o te pide un código?"
                if state.unresolved_streak >= MAX_UNRESOLVED_STREAK:
                    reply = ("Veo que persiste el problema con la contraseña. "
                             "Te derivo con un agente humano para verificar tu identidad y ayudarte a recuperar el acceso.")
                    state.add_user(user_text); state.add_bot(reply)
                    state.last_category = category
                    return reply, {"category": category, "confidence": confidence, "low_confidence": False, "needs_agent": True}
            state.add_user(user_text); state.add_bot(reply)
            state.last_category = category
            return reply, {"category": category, "confidence": confidence, "low_confidence": False}

        if issue == "2fa_issue":
            if not state.meta.get("did_2fa_tip"):
                reply = ("Ese código es de verificación en dos pasos (2FA). Revisa tu correo (incluida la carpeta de spam) "
                         "o la app autenticadora. Si no te llega en 2-3 minutos, avísame y te derivo con un agente humano.")
                state.meta["did_2fa_tip"] = "1"
                state.unresolved_streak = 0
            else:
                reply = ("Como no te llega el código, te derivo con un agente humano para verificar tu identidad y restablecer el acceso.")
                state.add_user(user_text); state.add_bot(reply)
                state.last_category = category
                return reply, {"category": category, "confidence": confidence, "low_confidence": False, "needs_agent": True}
            state.add_user(user_text); state.add_bot(reply)
            state.last_category = category
            return reply, {"category": category, "confidence": confidence, "low_confidence": False}

        if state.meta.get("did_2fa_tip"):
            t = text  # ya está en lower()
            if any(pat in t for pat in [
                "no me llega", "no llega", "no recibo", "no recibí", "no recibi",
                "no aparece", "no llega el código", "no llega el codigo"
            ]):
                reply = (
                    "Como el código de verificación no te está llegando, "
                    "te derivo con un agente humano para verificar tu identidad "
                    "y restablecer el acceso."
                )
                state.add_user(user_text)
                state.add_bot(reply)
                state.last_category = "soporte"
                return reply, {
                    "category": "soporte",
                    "confidence": 1.0,
                    "low_confidence": False,
                    "needs_agent": True
                }
    # KB + Fallback semántico + Derivación global
    kb_answer = search_faq(category, user_text)
    if kb_answer:
        reply = kb_answer
        state.unresolved_streak = 0
        _clear_misunder(state)
    else:
        sem = semantic_answer(user_text, threshold=0.35)
        if sem:
            qa, score = sem
            reply = qa.answer
            category = category or qa.category
            state.unresolved_streak = 0
            _clear_misunder(state)
        else:
            if _bump_misunder(state, 1):
                reply = "No estoy logrando entenderte correctamente. Para ayudarte mejor, te derivo con un asesor humano."
                state.add_user(user_text); state.add_bot(reply)
                state.last_category = category
                return reply, {"category": category, "confidence": 0.0, "low_confidence": True, "needs_agent": True}

            reply = default_reply_for(category)
            state.unresolved_streak = state.unresolved_streak + 1 if state.last_category == category else 0
            if state.unresolved_streak >= MAX_UNRESOLVED_STREAK:
                reply = "Para darte una respuesta precisa, te derivo con un asesor humano."
                state.add_user(user_text); state.add_bot(reply)
                state.last_category = category
                return reply, {"category": category, "confidence": 0.0, "low_confidence": False, "needs_agent": True}

    state.add_user(user_text); state.add_bot(reply)
    state.last_category = category
    return reply, {"category": category, "confidence": confidence, "low_confidence": False}
