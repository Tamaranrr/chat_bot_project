from app.bot import route_message

def test_support_password_then_2fa(state):
    # Menú a soporte
    reply, meta = route_message(state, "2")
    assert "soporte" in meta["category"]

    # Problema de contraseña
    reply, meta = route_message(state, "no me funciona la contraseña")
    assert "restablecer tu contraseña" in reply.lower()

    # Menciona código/2FA
    reply, meta = route_message(state, "me pide un código")
    assert "dos pasos" in reply.lower() or "2fa" in reply.lower()

    # Sigo con el problema → derivación
    reply, meta = route_message(state, "no me llega")
    assert meta.get("needs_agent") is True
