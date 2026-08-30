from typing import Sequence
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from crud.base import CRUDBase
from database.models import Converting


class ConvertingRepository(CRUDBase[Converting]):

    def __init__(self):
        super().__init__(Converting)

    async def get_user_conversions(
        self,
        session: AsyncSession,
        user_id: int,
        limit: int = 10,
        skip: int = 0,
    ) -> Sequence[Converting]:
        """Получить историю конвертаций конкретного пользователя."""
        result = await session.execute(
            select(Converting)
            .where(Converting.user_id == user_id)
            .order_by(Converting.converted_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def count_user_conversions(
        self,
        session: AsyncSession,
        user_id: int,
    ) -> int:
        """Посчитать общее количество конвертаций пользователя."""
        result = await session.execute(
            select(func.count(Converting.id)).where(Converting.user_id == user_id)
        )
        return result.scalar() or 0


crud_converting = ConvertingRepository()