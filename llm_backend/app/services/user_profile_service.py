import json
from typing import Dict, List

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.user_profile import UserProfile


class UserProfileService:
    """Stores simple user preference memory extracted from dialogue."""

    KEYWORDS = ["我喜欢", "我希望", "我的偏好", "以后回答", "请记住", "我习惯"]

    @staticmethod
    async def get_profile(user_id: int) -> Dict:
        async with AsyncSessionLocal() as db:
            stmt = select(UserProfile).where(UserProfile.user_id == user_id)
            result = await db.execute(stmt)
            profile = result.scalar_one_or_none()
            if not profile:
                return {"preferences": []}
            try:
                return json.loads(profile.profile_json or "{}")
            except json.JSONDecodeError:
                return {"preferences": []}

    @staticmethod
    async def upsert_profile(user_id: int, profile_data: Dict) -> Dict:
        async with AsyncSessionLocal() as db:
            stmt = select(UserProfile).where(UserProfile.user_id == user_id)
            result = await db.execute(stmt)
            profile = result.scalar_one_or_none()
            payload = json.dumps(profile_data, ensure_ascii=False)
            if profile:
                profile.profile_json = payload
            else:
                db.add(UserProfile(user_id=user_id, profile_json=payload))
            await db.commit()
            return profile_data

    @staticmethod
    async def clear_profile(user_id: int) -> Dict:
        return await UserProfileService.upsert_profile(user_id, {"preferences": []})

    @staticmethod
    async def extract_preferences(user_id: int, text: str) -> List[str]:
        content = (text or "").strip()
        if not content or not any(keyword in content for keyword in UserProfileService.KEYWORDS):
            return []

        profile = await UserProfileService.get_profile(user_id)
        preferences = list(profile.get("preferences") or [])
        if content not in preferences:
            preferences.append(content[:300])

        next_preferences = preferences[-20:]
        await UserProfileService.upsert_profile(user_id, {"preferences": next_preferences})
        return next_preferences
