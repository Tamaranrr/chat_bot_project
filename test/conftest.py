import pytest

from app.conversation import ConversationState
from app.semantic_service import _retriever
import app.semantic_service as semsvc

@pytest.fixture(autouse=True)
def reset_semantic_singleton():
    """
    Resetea el singleton del recuperador semántico entre tests
    para evitar contaminación de estado.
    """
    # guardar y limpiar antes de cada test
    old = semsvc._retriever
    semsvc._retriever = None
    yield
    # restaurar al finalizar 
    semsvc._retriever = old

@pytest.fixture
def state() -> ConversationState:
    """Estado de conversación limpio para cada test."""
    return ConversationState()
