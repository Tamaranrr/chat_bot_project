from typing import Dict, List, Optional
from app.nlp import normalize_text
from app.retrieval import QA
from typing import List


# Preguntas y respuestas frecuentes por categoría
FAQ: Dict[str, List[Dict[str, str]]] = {
    "ventas": [
        {"q": "precios precio cuesta valor costo plan planes", "a": "Nuestros planes se ajustan a tu necesidad. ¿Buscas mensual, anual o por consumo?"},
        {"q": "plan mensual mensualidad mensual", "a": "Perfecto, el plan mensual es flexible. ¿Para cuántos usuarios lo necesitas y en qué país/moneda?"},
        {"q": "plan anual anualidad anual", "a": "¡Buen ojo! El plan anual suele tener mejor tarifa. ¿Para cuántos usuarios y en qué país/moneda?"},
        {"q": "por consumo consumo pay as you go variable", "a": "Entendido: plan por consumo. ¿Qué volumen aproximado esperas al mes y en qué país/moneda?"}
    ],
    "soporte": [
        {"q": "error falla bug no funciona problema", "a": "Lamentamos el inconveniente. ¿Puedes compartir el mensaje de error exacto?"},
        {"q": "no funciona login acceso inicio sesión iniciar sesion", "a": "Probemos: ¿recibes un mensaje específico al iniciar sesión?"},
        {"q": "restablecer contraseña recuperar password", "a": "Puedes restablecer tu contraseña desde 'Olvidé mi contraseña' en el login."},
        {"q": "código codigo 2fa verificacion verificación otp", "a": "Ese código es de verificación en dos pasos. Revisa tu correo (incluido spam) o la app autenticadora. Si no te llega, te derivo con un agente humano."}
    ],
    "general": [
        {"q": "horarios horario atención atencion", "a": "Atendemos 24/7 por este canal. Los agentes humanos 9:00–18:00 (GMT-5)."},
        {"q": "empresa quienes son quiénes son sobre", "a": "Somos una empresa de tecnología enfocada en IA y automatización."},
        {"q": "contacto email correo teléfono telefono", "a": "Escríbenos a soporte@empresa.com o ventas@empresa.com."}
    ],
}

def search_faq(category: str, message: str) -> Optional[str]:
    msg = normalize_text(message)
    for item in FAQ.get(category, []):
        keywords = item["q"].split()
        if any(k in msg for k in keywords):
            return item["a"]
    return None

def build_semantic_corpus() -> List[QA]:
    data: List[QA] = []

    # VENTAS
    data += [
        QA("¿Cuánto cuesta? precios de los planes", "Nuestros planes se ajustan a tu necesidad. ¿Buscas mensual, anual o por consumo?", "ventas"),
        QA("¿Tienen demo o prueba gratuita?", "Ofrecemos una demo gratuita de 7 días. ¿Te agendo con un asesor?", "ventas"),
        QA("Quiero contratar / comprar / adquirir licencia", "Puedes contratar con tarjeta o transferencia. ¿País y moneda?", "ventas"),
    ]

    # SOPORTE
    data += [
        QA("no inicia el computador / pc / equipo", "¿El equipo no enciende o el sistema no termina de cargar? Si es de hardware, te derivo con un agente técnico. Si es nuestra plataforma, ¿qué mensaje exacto aparece?", "soporte"),
        QA("no ingresa / no entra a la página / pagina / web", "Entiendo. ¿Te aparece algún mensaje al intentar acceder (por ejemplo, 'usuario o contraseña incorrecta' o 'error 500')?", "soporte"),
        QA("contraseña incorrecta / password incorrecto / clave mal", "Puedes restablecer tu contraseña desde 'Olvidé mi contraseña' en el login. ¿Te llegó el correo de restablecimiento?", "soporte"),
        QA("me pide un código / 2fa / verificación / otp", "Ese código es de verificación en dos pasos (2FA). Revisa tu correo (incluida la carpeta de spam) o la app autenticadora. Si no te llega, te derivo con un agente humano.", "soporte"),
        QA("no me llega el codigo 2fa", "Como no te llega el código, te derivo con un agente humano para verificar tu identidad y restablecer el acceso.", "soporte"),
    ]

    # GENERAL
    data += [
        QA("horarios de atención", "Atendemos 24/7 por este canal. Los agentes humanos 9:00–18:00 (GMT-5).", "general"),
        QA("contacto correo email teléfono", "Escríbenos a soporte@empresa.com o ventas@empresa.com.", "general"),
        QA("quienes son / sobre la empresa", "Somos una empresa de tecnología enfocada en IA y automatización.", "general"),
    ]

    return data
