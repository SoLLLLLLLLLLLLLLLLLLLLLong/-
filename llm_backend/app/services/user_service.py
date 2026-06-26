from datetime import datetime
from typing import Optional

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.hashing import get_password_hash, verify_password
from app.core.logger import get_logger
from app.models.user import User
from app.schemas.user import UserCreate

logger = get_logger(service="user_service")


class UserService:
    # 这里改成“静态方法 + 显式传入 db”的写法，
    # 这样更适合你当前项目的接口层调用方式：
    # UserService.create_user(db, user_data)

    @staticmethod
    async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
        # 同时检查邮箱和用户名是否重复。
        query = select(User).where(
            or_(
                User.email == user_data.email,
                User.username == user_data.username,
            )
        )
        result = await db.execute(query)
        existing_user = result.scalar_one_or_none()

        if existing_user:
            if existing_user.email == user_data.email:
                raise ValueError("该邮箱已经被注册")
            raise ValueError("用户名已被占用")

        db_user = User(
            username=user_data.username,
            email=user_data.email,
            password_hash=get_password_hash(user_data.password),
        )
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user

    @staticmethod
    async def authenticate_user(
        db: AsyncSession,
        email: str,
        password: str,
    ) -> Optional[User]:
        # 登录时先按邮箱查用户，再校验密码哈希。
        query = select(User).where(User.email == email)
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            logger.warning(f"User not found: {email}")
            return None

        if not verify_password(password, user.password_hash):
            logger.warning(f"Invalid password for user: {email}")
            return None

        user.last_login = datetime.utcnow()
        await db.commit()
        return user

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
        query = select(User).where(User.id == user_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
        query = select(User).where(User.email == email)
        result = await db.execute(query)
        return result.scalar_one_or_none()
