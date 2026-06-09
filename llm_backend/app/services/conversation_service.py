from typing import Dict, List, Optional

from openai import AsyncOpenAI
from sqlalchemy import select

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.logger import get_logger
from app.models.conversation import Conversation, DialogueType
from app.models.message import Message


logger = get_logger(service="conversation")


class ConversationService:
    SUMMARY_SYSTEM_PROMPT = (
        "You maintain long-term conversation memory for an assistant. "
        "Merge older dialogue into a concise summary in Chinese. "
        "Keep the user's goals, preferences, constraints, decisions already made, "
        "unfinished tasks, and important facts. Output plain text only."
    )

    DEFAULT_TITLE = "新对话"

    @staticmethod
    def get_conversation_title(message: str, max_length: int = 20) -> str:
        title = " ".join(message.split()) or ConversationService.DEFAULT_TITLE
        if len(title) > max_length:
            title = title[:max_length] + "..."
        return title

    @staticmethod
    def _latest_user_message(messages: List[Dict]) -> str:
        for message in reversed(messages):
            if message.get("role") == "user":
                return message.get("content", "")
        return ""

    @staticmethod
    def _message_to_chat_dict(message: Message) -> Dict[str, str]:
        role = "assistant" if message.sender == "assistant" else "user"
        return {"role": role, "content": message.content}

    @staticmethod
    async def create_conversation(user_id: int) -> int:
        async with AsyncSessionLocal() as db:
            conversation = Conversation(
                user_id=user_id,
                title=ConversationService.DEFAULT_TITLE,
                dialogue_type=DialogueType.AGENT,
            )
            db.add(conversation)
            await db.commit()
            await db.refresh(conversation)
            logger.info(f"Created conversation {conversation.id} for user {user_id}")
            return conversation.id

    @staticmethod
    async def _load_conversation(db, conversation_id: int) -> Optional[Conversation]:
        stmt = select(Conversation).where(Conversation.id == conversation_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def _load_messages(db, conversation_id: int) -> List[Message]:
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at, Message.id)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def build_chat_messages(
        conversation_id: int,
        incoming_messages: List[Dict],
    ) -> List[Dict]:
        async with AsyncSessionLocal() as db:
            conversation = await ConversationService._load_conversation(db, conversation_id)
            if not conversation:
                return incoming_messages

            stored_messages = await ConversationService._load_messages(db, conversation_id)
            summarized_count = conversation.summarized_message_count or 0
            recent_messages = stored_messages[summarized_count:]

            hydrated_messages: List[Dict] = []
            if conversation.summary:
                hydrated_messages.append(
                    {
                        "role": "system",
                        "content": (
                            "以下是当前会话的历史摘要，请在回答时继承这些上下文信息：\n"
                            f"{conversation.summary}"
                        ),
                    }
                )

            hydrated_messages.extend(
                ConversationService._message_to_chat_dict(message)
                for message in recent_messages
            )

            latest_user_message = ConversationService._latest_user_message(incoming_messages)
            if latest_user_message:
                if (
                    not hydrated_messages
                    or hydrated_messages[-1].get("role") != "user"
                    or hydrated_messages[-1].get("content") != latest_user_message
                ):
                    hydrated_messages.append({"role": "user", "content": latest_user_message})
            else:
                hydrated_messages.extend(incoming_messages)

            return hydrated_messages

    @staticmethod
    async def _summarize_messages(
        existing_summary: str,
        archived_messages: List[Message],
    ) -> str:
        client = AsyncOpenAI(
            api_key=settings.CHAT_API_KEY,
            base_url=settings.CHAT_BASE_URL,
        )
        history_text = "\n".join(
            [
                f"{'用户' if msg.sender == 'user' else '助手'}: {msg.content}"
                for msg in archived_messages
            ]
        )
        summary_prompt = (
            f"当前已有摘要：\n{existing_summary or '无'}\n\n"
            f"请把下面新增历史整合进摘要：\n{history_text}\n\n"
            "输出更新后的统一摘要，尽量精炼，并突出用户需求、偏好、重要事实和未解决问题。"
        )
        response = await client.chat.completions.create(
            model=settings.CHAT_MODEL_NAME,
            messages=[
                {"role": "system", "content": ConversationService.SUMMARY_SYSTEM_PROMPT},
                {"role": "user", "content": summary_prompt},
            ],
            stream=False,
        )
        return (response.choices[0].message.content or "").strip()

    @staticmethod
    async def _refresh_summary_if_needed(db, conversation: Conversation) -> None:
        stored_messages = await ConversationService._load_messages(db, conversation.id)
        total_messages = len(stored_messages)
        keep_recent = settings.MEMORY_KEEP_RECENT_MESSAGES
        archive_end = max(0, total_messages - keep_recent)
        summarized_count = conversation.summarized_message_count or 0
        pending_count = archive_end - summarized_count

        if total_messages < settings.MEMORY_SUMMARY_TRIGGER_MESSAGES:
            return
        if pending_count < settings.MEMORY_SUMMARY_MIN_MESSAGES:
            return

        archived_messages = stored_messages[summarized_count:archive_end]
        if not archived_messages:
            return

        conversation.summary = await ConversationService._summarize_messages(
            conversation.summary or "",
            archived_messages,
        )
        conversation.summarized_message_count = archive_end
        logger.info(
            f"Updated summary for conversation {conversation.id}, "
            f"summarized_count={conversation.summarized_message_count}"
        )

    @staticmethod
    async def save_message(
        user_id: int,
        conversation_id: int,
        messages: List[Dict],
        response: str,
    ):
        try:
            async with AsyncSessionLocal() as db:
                conversation = await ConversationService._load_conversation(db, conversation_id)
                if not conversation:
                    logger.error(f"Conversation {conversation_id} not found")
                    return

                user_content = ConversationService._latest_user_message(messages)
                if not user_content:
                    user_content = next(
                        (
                            msg.get("content", "")
                            for msg in messages
                            if msg.get("role") == "user"
                        ),
                        "",
                    )

                existing_messages = await ConversationService._load_messages(db, conversation_id)
                if not existing_messages:
                    conversation.title = ConversationService.get_conversation_title(user_content)

                db.add(
                    Message(
                        conversation_id=conversation_id,
                        sender="user",
                        content=user_content,
                    )
                )
                db.add(
                    Message(
                        conversation_id=conversation_id,
                        sender="assistant",
                        content=response,
                    )
                )

                await db.flush()
                await ConversationService._refresh_summary_if_needed(db, conversation)
                await db.commit()
        except Exception as exc:
            logger.error(f"Error saving conversation: {str(exc)}", exc_info=True)
            logger.error(
                f"Save failed for user_id={user_id}, conversation_id={conversation_id}"
            )

    @staticmethod
    async def get_user_conversations(user_id: int) -> List[Dict]:
        async with AsyncSessionLocal() as db:
            stmt = (
                select(Conversation)
                .where(Conversation.user_id == user_id)
                .order_by(Conversation.updated_at.desc(), Conversation.created_at.desc())
            )
            result = await db.execute(stmt)
            conversations = result.scalars().all()
            return [
                {
                    "id": conv.id,
                    "title": conv.title,
                    "created_at": conv.created_at.isoformat(),
                    "updated_at": conv.updated_at.isoformat() if conv.updated_at else None,
                    "status": conv.status,
                    "dialogue_type": conv.dialogue_type.value,
                    "has_summary": bool(conv.summary),
                }
                for conv in conversations
            ]

    @staticmethod
    async def get_conversation_messages(conversation_id: int, user_id: int) -> List[Dict]:
        async with AsyncSessionLocal() as db:
            stmt = select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
            )
            result = await db.execute(stmt)
            conversation = result.scalar_one_or_none()
            if not conversation:
                raise ValueError(
                    f"Conversation {conversation_id} not found or not owned by user {user_id}"
                )

            messages = await ConversationService._load_messages(db, conversation_id)
            return [
                {
                    "id": msg.id,
                    "sender": msg.sender,
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat(),
                    "message_type": msg.message_type,
                }
                for msg in messages
            ]

    @staticmethod
    async def delete_conversation(conversation_id: int):
        async with AsyncSessionLocal() as db:
            conversation = await ConversationService._load_conversation(db, conversation_id)
            if not conversation:
                raise ValueError(f"Conversation {conversation_id} not found")

            await db.delete(conversation)
            await db.commit()
            logger.info(f"Deleted conversation {conversation_id}")

    @staticmethod
    async def update_conversation_name(conversation_id: int, name: str):
        async with AsyncSessionLocal() as db:
            conversation = await ConversationService._load_conversation(db, conversation_id)
            if not conversation:
                raise ValueError(f"Conversation {conversation_id} not found")

            conversation.title = name.strip() or ConversationService.DEFAULT_TITLE
            await db.commit()
            logger.info(f"Updated conversation {conversation_id} title to {conversation.title}")
