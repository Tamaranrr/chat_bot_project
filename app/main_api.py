from fastapi import FastAPI, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session
import re

from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.requests import Request
from starlette import status
from sqlalchemy.exc import SQLAlchemyError

from .db import Base, engine, SessionLocal
from .models import Conversation, Message
from .repository import (
    create_conversation, get_conversation, list_conversations,
    add_message, get_messages, reset_conversation,
    update_metrics, set_status, global_metrics,
)
from .bot import route_message, HELP_TEXT
from .conversation import ConversationState
from .utils.logger import get_logger

log = get_logger(__name__)

# Crear tablas si no existen
Base.metadata.create_all(bind=engine)

# =========================
# FastAPI APP
# =========================
app = FastAPI(title="Chatbot IA – API", version="0.1.0")

# Servir archivos estáticos (ej: index.html en app/static/)
app.mount("/static", StaticFiles(directory="app/static", html=True), name="static")


# =========================
# Global Exception Handlers
# =========================
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    log.warning("Validation error", extra={
        "path": str(request.url),
        "method": request.method,
        "errors": exc.errors(),
    })
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Entrada inválida. Revisa el payload enviado.", "errors": exc.errors()},
    )

@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    log.exception("Database error", extra={"path": str(request.url), "method": request.method})
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Error de base de datos. Intenta de nuevo más tarde."},
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    log.exception("Unhandled error", extra={"path": str(request.url), "method": request.method})
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Error interno del servidor. Nuestro equipo ya fue notificado."},
    )


# =========================
# Helpers
# =========================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def _rehydrate_sales_meta_from_history(state: ConversationState):
    """Infiera sales_plan / users / country / currency del historial de mensajes del usuario."""
    if state.selected_category != "ventas" and state.last_category != "ventas":
        return

    text_all = " ".join([m.text.lower() for m in state.messages if m.role == "user"])
    if not state.meta.get("sales_plan"):
        if any(w in text_all for w in ["plan mensual", "mensualidad", "mensual"]):
            state.meta["sales_plan"] = "mensual"
        elif any(w in text_all for w in ["plan anual", "anualidad", "anual"]):
            state.meta["sales_plan"] = "anual"
        elif any(w in text_all for w in ["por consumo", "consumo", "pay as you go", "variable"]):
            state.meta["sales_plan"] = "consumo"

    if not state.meta.get("sales_users"):
        nums = re.findall(r"\b(\d{1,4})\b", text_all)
        if nums:
            state.meta["sales_users"] = nums[-1]

    KNOWN_CURRENCIES = {"usd","eur","cop","mxn","ars","pen","clp"}
    KNOWN_COUNTRIES  = {"colombia","mexico","méxico","argentina","peru","perú","chile","espana","españa"}
    words = set(re.split(r"[\s,.;:]+", text_all))

    if not state.meta.get("sales_currency"):
        currency = next((w for w in words if w in KNOWN_CURRENCIES), None)
        if currency:
            state.meta["sales_currency"] = currency.upper()

    if not state.meta.get("sales_country"):
        country = next((w for w in words if w in KNOWN_COUNTRIES), None)
        if country:
            state.meta["sales_country"] = country.capitalize()


# =========================
# Schemas
# =========================
class ConversationOut(BaseModel):
    id: int
    user_tag: Optional[str] = None
    class Config:
        from_attributes = True

class MessageOut(BaseModel):
    id: int
    role: str
    text: str
    class Config:
        from_attributes = True

class ChatIn(BaseModel):
    message: str
    user_tag: Optional[str] = None

class ChatOut(BaseModel):
    conversation_id: int
    reply: str
    help: Optional[str] = None

class StatusIn(BaseModel):
    status: str  # open | needs_agent | assigned | closed

class MetricsOut(BaseModel):
    total_conversations: int
    open: int
    needs_agent: int
    assigned: int
    closed: int
    sales: int
    support: int
    general: int
    low_conf: int
    messages: int


# =========================
# Endpoints
# =========================
@app.get("/", tags=["root"])
def root():
    return {"ok": True, "message": "Chatbot IA API está corriendo.", "help": HELP_TEXT}

@app.get("/health", tags=["root"])
def health(db: Session = Depends(get_db)):
    return {"status": "ok", "db": "up"}


@app.post("/conversations", response_model=ConversationOut, tags=["conversations"])
def api_create_conversation(user_tag: Optional[str] = Query(None), db: Session = Depends(get_db)):
    return create_conversation(db, user_tag=user_tag)

@app.get("/conversations", response_model=List[ConversationOut], tags=["conversations"])
def api_list_conversations(limit: int = 50, db: Session = Depends(get_db)):
    return list_conversations(db, limit=limit)

@app.get("/conversations/{conv_id}", response_model=ConversationOut, tags=["conversations"])
def api_get_conversation(conv_id: int, db: Session = Depends(get_db)):
    conv = get_conversation(db, conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    return conv

@app.get("/conversations/{conv_id}/messages", response_model=List[MessageOut], tags=["messages"])
def api_get_messages(conv_id: int, db: Session = Depends(get_db)):
    if not get_conversation(db, conv_id):
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    return get_messages(db, conv_id)

@app.delete("/conversations/{conv_id}/messages", tags=["messages"])
def api_reset_conversation(conv_id: int, db: Session = Depends(get_db)):
    if not get_conversation(db, conv_id):
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    reset_conversation(db, conv_id)
    return {"ok": True, "message": "Conversación reiniciada"}


@app.post("/chat", response_model=ChatOut, tags=["chat"])
def api_chat(
    payload: ChatIn,
    conv_id: Optional[int] = Query(None, description="ID de conversación existente (opcional)"),
    db: Session = Depends(get_db)
):
    if conv_id is None:
        conv = create_conversation(db, user_tag=payload.user_tag)
    else:
        conv = get_conversation(db, conv_id)
        if not conv:
            raise HTTPException(status_code=404, detail="Conversación no encontrada")

    state = ConversationState()
    if conv.last_category:
        state.last_category = conv.last_category
        state.selected_category = conv.last_category
        state.stage = "chat"

    for m in get_messages(db, conv.id):
        if m.role == "user":
            state.add_user(m.text)
        else:
            state.add_bot(m.text)

    _rehydrate_sales_meta_from_history(state)

    user_text = payload.message.strip()
    reply, meta = route_message(state, user_text)

    add_message(db, conv.id, role="user", text=user_text)
    add_message(db, conv.id, role="bot", text=reply)

    update_metrics(db, conv.id,
                   category=meta.get("category"),
                   low_confidence=meta.get("low_confidence", False))

    if meta.get("needs_agent"):
        set_status(db, conv.id, status="needs_agent", needs_agent=True)
    if meta.get("end"):
        set_status(db, conv.id, status="closed", needs_agent=False)

    return ChatOut(conversation_id=conv.id, reply=reply, help=None)


@app.get("/metrics", response_model=MetricsOut, tags=["metrics"])
def api_metrics(db: Session = Depends(get_db)):
    return global_metrics(db)

@app.post("/conversations/{conv_id}/assign", response_model=ConversationOut, tags=["conversations"])
def api_assign(conv_id: int, db: Session = Depends(get_db)):
    conv = set_status(db, conv_id, status="assigned", needs_agent=False)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    return conv

@app.post("/conversations/{conv_id}/close", response_model=ConversationOut, tags=["conversations"])
def api_close(conv_id: int, db: Session = Depends(get_db)):
    conv = set_status(db, conv_id, status="closed", needs_agent=False)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    return conv

@app.post("/conversations/{conv_id}/needs_agent", response_model=ConversationOut, tags=["conversations"])
def api_mark_needs_agent(conv_id: int, db: Session = Depends(get_db)):
    conv = set_status(db, conv_id, status="needs_agent", needs_agent=True)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    return conv
