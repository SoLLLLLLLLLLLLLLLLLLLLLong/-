import asyncio
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))

from app.core.database import init_database
from app.core.logger import get_logger


logger = get_logger(service="init_db")


async def init_db():
    try:
        logger.info("Initializing database...")
        await init_database()
        logger.info("Database initialization completed successfully!")
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise


def main():
    asyncio.run(init_db())


if __name__ == "__main__":
    main()
