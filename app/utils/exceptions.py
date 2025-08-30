class ChatbotError(Exception):
    """Excepción base del chatbot."""

class ConfigError(ChatbotError):
    """Error relacionado a configuración."""

class NLPError(ChatbotError):
    """Error de procesamiento de lenguaje natural."""
