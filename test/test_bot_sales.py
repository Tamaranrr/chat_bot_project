from app.bot import route_message

def test_sales_flow_monthly_confirm(state):
    # Entrar por menú a ventas
    reply, meta = route_message(state, "1")
    assert "ventas" in reply.lower()
    assert meta["category"] == "ventas"

    # Pedir precios → pregunta tipo de plan
    reply, meta = route_message(state, "precios")
    assert "mensual" in reply.lower() or "anual" in reply.lower() or "consumo" in reply.lower()
    assert meta["category"] == "ventas"

    # Elegir mensual
    reply, meta = route_message(state, "plan mensual")
    assert "cuántos usuarios" in reply.lower()
    assert meta["category"] == "ventas"

    # Dar datos en texto
    reply, meta = route_message(state, "para dos en colombia")
    # Debe pedir confirmación (oferta final)
    assert "cotización" in reply.lower() or "cotizacion" in reply.lower()
    assert meta["category"] == "ventas"

    # Confirmar derivación
    reply, meta = route_message(state, "sí")
    assert meta.get("needs_agent") is True
    assert "asesor humano" in reply.lower()
