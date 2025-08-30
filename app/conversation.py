from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class Message:
    role: str  # "user" o "bot"
    text: str

@dataclass
class ConversationState:
    messages: List[Message] = field(default_factory=list)
    meta: Dict[str, str] = field(default_factory=dict)

    last_category: Optional[str] = None
    low_conf_streak: int = 0
    unresolved_streak: int = 0

    # NUEVO: etapa/menú
    stage: str = "menu"  # "menu" | "chat"
    selected_category: Optional[str] = None

    def add_user(self, text: str):
        self.messages.append(Message(role="user", text=text))

    def add_bot(self, text: str):
        self.messages.append(Message(role="bot", text=text))

    def reset(self):
        self.messages.clear()
        self.meta.clear()
        self.last_category = None
        self.low_conf_streak = 0
        self.unresolved_streak = 0
        self.stage = "menu"
        self.selected_category = None