from pathlib import Path
from typing import Dict, List

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.document import KnowledgeDocument


class DocumentService:
    @staticmethod
    async def create_document(payload: Dict) -> KnowledgeDocument:
        async with AsyncSessionLocal() as db:
            document = KnowledgeDocument(**payload)
            db.add(document)
            await db.commit()
            await db.refresh(document)
            return document

    @staticmethod
    async def list_documents(user_id: int) -> List[Dict]:
        async with AsyncSessionLocal() as db:
            stmt = (
                select(KnowledgeDocument)
                .where(KnowledgeDocument.user_id == user_id)
                .order_by(KnowledgeDocument.created_at.desc(), KnowledgeDocument.id.desc())
            )
            result = await db.execute(stmt)
            documents = result.scalars().all()
            return [
                {
                    "id": item.id,
                    "user_id": item.user_id,
                    "filename": item.filename,
                    "original_name": item.original_name,
                    "path": item.path,
                    "index_id": item.index_id,
                    "chunks": item.chunks,
                    "size": item.size,
                    "content_type": item.content_type,
                    "created_at": item.created_at.isoformat() if item.created_at else None,
                }
                for item in documents
            ]

    @staticmethod
    async def delete_document(document_id: int, user_id: int) -> None:
        async with AsyncSessionLocal() as db:
            stmt = select(KnowledgeDocument).where(
                KnowledgeDocument.id == document_id,
                KnowledgeDocument.user_id == user_id,
            )
            result = await db.execute(stmt)
            document = result.scalar_one_or_none()
            if not document:
                raise ValueError("document not found")
            file_path = Path(document.path)
            if file_path.exists() and file_path.is_file():
                file_path.unlink()
            await db.delete(document)
            await db.commit()
