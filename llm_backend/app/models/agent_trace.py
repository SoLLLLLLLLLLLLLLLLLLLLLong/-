from sqlalchemy import Column, DateTime, Float, Integer, String, Text, func

from app.core.database import Base


class AgentTrace(Base):
    __tablename__ = "agent_traces"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    conversation_id = Column(Integer, index=True, nullable=True)
    route = Column(String(40), default="chat")
    question = Column(Text, default="")
    status = Column(String(40), default="completed")
    steps_json = Column(Text, default="[]")
    response_time_ms = Column(Float, default=0)
    created_at = Column(DateTime, server_default=func.now())
