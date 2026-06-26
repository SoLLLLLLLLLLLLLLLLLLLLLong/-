import json
from datetime import datetime
from time import perf_counter
from typing import Dict, List, Optional

from sqlalchemy import func, select

from app.core.database import AsyncSessionLocal
from app.models.agent_trace import AgentTrace


class TraceRecorder:
    """Collects execution steps for a single agent run and persists them."""

    def __init__(self, user_id: int, conversation_id: Optional[int], question: str):
        self.user_id = user_id
        self.conversation_id = conversation_id
        self.question = question
        self.route = "chat"
        self.steps: List[Dict] = []
        self.started_at = perf_counter()

    def set_route(self, route: str):
        self.route = route or "chat"

    def add_step(
        self,
        title: str,
        detail: str,
        *,
        stage: str,
        status: str = "completed",
        tool: str = "",
        attempt: int = 1,
    ) -> Dict:
        step = {
            "stage": stage,
            "title": title,
            "detail": detail,
            "status": status,
            "tool": tool,
            "attempt": attempt,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }
        self.steps.append(step)
        return step

    async def save(self, status: str = "completed"):
        response_time_ms = (perf_counter() - self.started_at) * 1000
        async with AsyncSessionLocal() as db:
            db.add(
                AgentTrace(
                    user_id=self.user_id,
                    conversation_id=self.conversation_id,
                    route=self.route,
                    question=self.question,
                    status=status,
                    steps_json=json.dumps(self.steps, ensure_ascii=False),
                    response_time_ms=response_time_ms,
                )
            )
            await db.commit()


class AgentTraceService:
    @staticmethod
    async def dashboard_stats(user_id: int, document_count: int) -> Dict:
        async with AsyncSessionLocal() as db:
            qa_stmt = select(func.count()).select_from(AgentTrace).where(
                AgentTrace.user_id == user_id
            )
            qa_count = (await db.execute(qa_stmt)).scalar() or 0

            search_stmt = select(func.count()).select_from(AgentTrace).where(
                AgentTrace.user_id == user_id,
                AgentTrace.route.in_(["search", "hybrid", "weather"]),
            )
            search_count = (await db.execute(search_stmt)).scalar() or 0

            avg_stmt = select(func.avg(AgentTrace.response_time_ms)).where(
                AgentTrace.user_id == user_id
            )
            avg_response_time_ms = (await db.execute(avg_stmt)).scalar() or 0

            return {
                "qa_count": qa_count,
                "search_count": search_count,
                "document_count": document_count,
                "avg_response_time_ms": round(float(avg_response_time_ms or 0), 2),
            }
