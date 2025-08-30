from app.semantic_service import semantic_answer

def test_semantic_support_phrase():
    res = semantic_answer("no ingresa a la pagina", threshold=0.30)
    assert res is not None
    qa, score = res
    assert score >= 0.30
    assert getattr(qa, "category", None) in {"soporte", "ventas", "general"}
