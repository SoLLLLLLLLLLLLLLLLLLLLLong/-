from sqlalchemy import Column, DateTime, Integer, String, Text, func

from app.core.database import Base


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    filename = Column(String(255), nullable=False)
    original_name = Column(String(255), nullable=False)
    path = Column(Text, nullable=False)
    index_id = Column(String(120), default="")
    chunks = Column(Integer, default=0)
    size = Column(Integer, default=0)
    content_type = Column(String(120), default="")
    created_at = Column(DateTime, server_default=func.now())
