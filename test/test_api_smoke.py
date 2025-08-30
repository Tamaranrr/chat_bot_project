from fastapi.testclient import TestClient
from app.main_api import app

client = TestClient(app)

def test_root():
    r = client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert data.get("ok") is True

def test_chat_flow():
    # crear conversación
    r = client.post("/conversations")
    assert r.status_code == 200
    conv_id = r.json()["id"]

    # menú → ventas
    r = client.post(f"/chat?conv_id={conv_id}", json={"message": "1"})
    assert r.status_code == 200

    # precios → mensual → datos → confirmación
    client.post(f"/chat?conv_id={conv_id}", json={"message": "precios"})
    client.post(f"/chat?conv_id={conv_id}", json={"message": "plan mensual"})
    r = client.post(f"/chat?conv_id={conv_id}", json={"message": "para dos en colombia"})
    assert r.status_code == 200
    assert "cotización" in r.json()["reply"].lower() or "cotizacion" in r.json()["reply"].lower()

    # confirmar derivación
    r = client.post(f"/chat?conv_id={conv_id}", json={"message": "sí"})
    data = r.json()
    # El endpoint ya marca needs_agent en DB, pero aquí solo comprueba que responde.
    assert "asesor" in data["reply"].lower()
