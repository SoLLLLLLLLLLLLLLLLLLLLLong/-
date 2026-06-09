import enum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class DialogueType(enum.Enum):
    NORMAL = "normal"
    DEEP_THINKING = "deep_thinking"
    WEB_SEARCH = "web_search"
    RAG = "rag"
    AGENT = "agent"


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    title = Column(String(100), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    status = Column(String(20), default="ongoing")
    dialogue_type = Column(Enum(DialogueType), nullable=False, default=DialogueType.AGENT)
    summary = Column(Text, default="")
    summarized_message_count = Column(Integer, default=0)

    user = relationship("User", back_populates="conversations")
    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
    )
