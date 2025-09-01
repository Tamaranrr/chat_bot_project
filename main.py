from app.utils.logger import get_logger
from app.conversation import ConversationState
from app.bot import route_message, HELP_TEXT

log = get_logger(__name__)

def chat_loop():
    state = ConversationState()
    print("Chatbot IA – Soporte 24/7")
    print(HELP_TEXT)
    print("-" * 60)

    while True:
        try:
            user = input("Tú: ").strip()
            if not user:
                continue
            if user.lower() in {"salir", "exit", "quit"}:
                print("¡Hasta luego!")
                break

            reply, meta = route_message(state, user)
            print(f"Bot: {reply}")

            # salir si el bot derivó a humano
            if meta.get("needs_agent"):
                print("Te dejo en manos de un asesor humano. ¡Gracias!")
                break

            # salir si el bot detectó despedida
            if meta.get("end"):
                print("¡Hasta luego!")
                break


            # si el bot marcó fin, termina el loop
            if meta.get("end"):
                print("¡Hasta luego!")
                break

        except KeyboardInterrupt:
            print("\n¡Hasta luego!")
            break
        except Exception:
            log.exception("Error en el loop de chat")
            print("Ocurrió un error inesperado. Intenta de nuevo o escribe 'reiniciar'.")

def main():
    log.info("Chatbot iniciado (modo terminal).")
    chat_loop()

if __name__ == "__main__":
    main()
