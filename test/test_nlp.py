from app.nlp import is_greeting, is_menu_request, seems_personal_data, classify

def test_is_greeting():
    assert is_greeting("hola")
    assert is_greeting("buenas tardes")
    assert not is_greeting("necesito soporte")

def test_is_menu_request():
    assert is_menu_request("menu")
    assert is_menu_request("volver al inicio")
    assert not is_menu_request("quiero precios")

def test_seems_personal_data():
    assert seems_personal_data("mi correo es alguien@test.com")
    assert seems_personal_data("mi telefono es +57 300 123 4567")
    assert not seems_personal_data("hola, quiero probar")

def test_classify_with_hint():
    cat, conf, _ = classify("no me entra a la pagina", hint_category="soporte")
    assert cat in {"soporte", "general", "ventas"}
    assert 0.0 <= conf <= 1.0
