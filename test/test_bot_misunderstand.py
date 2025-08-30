from app.bot import route_message

def test_global_misunderstand_derives(state):
    # Cualquier categoría, incluso general
    reply, meta = route_message(state, "3")
    assert meta["category"] == "general"

    # Dos mensajes confusos
    reply, meta = route_message(state, "asdfgh qwerty")
    assert meta.get("needs_agent", False) is False  

    reply, meta = route_message(state, "zxcvb mnbvc")
    # Al segundo, derivar
    assert meta.get("needs_agent") is True
    assert "derivo" in reply.lower() or "asesor" in reply.lower()
