from typing import List, Optional, Tuple, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import Conversation, Message

def create_conversation(db: Session, user_tag: Optional[str] = None) -> Conversation:
    conv = Conversation(user_tag=user_tag)
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv

def get_conversation(db: Session, conv_id: int) -> Optional[Conversation]:
    return db.query(Conversation).filter(Conversation.id == conv_id).first()

def list_conversations(db: Session, limit: int = 50) -> List[Conversation]:
    return db.query(Conversation).order_by(Conversation.id.desc()).limit(limit).all()

def add_message(db: Session, conv_id: int, role: str, text: str) -> Message:
    msg = Message(conversation_id=conv_id, role=role, text=text)
    db.add(msg)
    # incrementar contador de mensajes
    conv = get_conversation(db, conv_id)
    if conv:
        conv.messages_count = (conv.messages_count or 0) + 1
    db.commit()
    db.refresh(msg)
    return msg

def get_messages(db: Session, conv_id: int) -> List[Message]:
    return db.query(Message).filter(Message.conversation_id == conv_id).order_by(Message.id.asc()).all()

def reset_conversation(db: Session, conv_id: int) -> None:
    conv = get_conversation(db, conv_id)
    if conv:
        for m in list(conv.messages):
            db.delete(m)
        # reset métricas básicas
        conv.messages_count = 0
        conv.sales_count = 0
        conv.support_count = 0
        conv.general_count = 0
        conv.low_conf_count = 0
        conv.needs_agent = False
        conv.status = "open"
        conv.last_category = None
        db.commit()

# === NUEVO: actualizar métricas por categoría/ confianza ===
def update_metrics(
    db: Session,
    conv_id: int,
    category: Optional[str],
    low_confidence: bool
) -> None:
    conv = get_conversation(db, conv_id)
    if not conv:
        return
    if category == "ventas":
        conv.sales_count = (conv.sales_count or 0) + 1
    elif category == "soporte":
        conv.support_count = (conv.support_count or 0) + 1
    elif category == "general":
        conv.general_count = (conv.general_count or 0) + 1

    if low_confidence:
        conv.low_conf_count = (conv.low_conf_count or 0) + 1
        conv.needs_agent = True
        conv.status = "needs_agent"

    conv.last_category = category
    db.commit()

# === NUEVO: estado de conversación ===
def set_status(db: Session, conv_id: int, status: str, needs_agent: Optional[bool] = None) -> Optional[Conversation]:
    conv = get_conversation(db, conv_id)
    if not conv:
        return None
    conv.status = status
    if needs_agent is not None:
        conv.needs_agent = needs_agent
    db.commit()
    db.refresh(conv)
    return conv

# === NUEVO: métricas globales simples ===
def global_metrics(db: Session) -> Dict[str, int]:
    total_conversations = db.query(func.count(Conversation.id)).scalar() or 0
    open_count = db.query(func.count(Conversation.id)).filter(Conversation.status == "open").scalar() or 0
    needs_agent_count = db.query(func.count(Conversation.id)).filter(Conversation.status == "needs_agent").scalar() or 0
    assigned_count = db.query(func.count(Conversation.id)).filter(Conversation.status == "assigned").scalar() or 0
    closed_count = db.query(func.count(Conversation.id)).filter(Conversation.status == "closed").scalar() or 0

    sales_sum = db.query(func.coalesce(func.sum(Conversation.sales_count), 0)).scalar() or 0
    support_sum = db.query(func.coalesce(func.sum(Conversation.support_count), 0)).scalar() or 0
    general_sum = db.query(func.coalesce(func.sum(Conversation.general_count), 0)).scalar() or 0
    low_conf_sum = db.query(func.coalesce(func.sum(Conversation.low_conf_count), 0)).scalar() or 0
    messages_sum = db.query(func.coalesce(func.sum(Conversation.messages_count), 0)).scalar() or 0

    return {
        "total_conversations": total_conversations,
        "open": open_count,
        "needs_agent": needs_agent_count,
        "assigned": assigned_count,
        "closed": closed_count,
        "sales": sales_sum,
        "support": support_sum,
        "general": general_sum,
        "low_conf": low_conf_sum,
        "messages": messages_sum,
    }
