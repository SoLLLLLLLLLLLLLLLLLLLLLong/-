import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings


logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

engine_kwargs = {"echo": False}
if settings.DB_TYPE.lower() != "sqlite":
    engine_kwargs.update(
        {
            "pool_pre_ping": True,
            "pool_size": 5,
            "max_overflow": 10,
        }
    )

engine = create_async_engine(settings.DATABASE_URL, **engine_kwargs)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_database():
    import app.models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        if settings.DB_TYPE.lower() == "sqlite":
            result = await conn.execute(text("PRAGMA table_info(conversations)"))
            columns = {row[1] for row in result.fetchall()}
            if "summary" not in columns:
                await conn.execute(
                    text("ALTER TABLE conversations ADD COLUMN summary TEXT DEFAULT ''")
                )
            if "summarized_message_count" not in columns:
                await conn.execute(
                    text(
                        "ALTER TABLE conversations ADD COLUMN summarized_message_count "
                        "INTEGER DEFAULT 0"
                    )
                )
