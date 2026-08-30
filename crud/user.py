from typing import Optional
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from crud.base import CRUDBase
from database.models import User


class UserRepository(CRUDBase[User]):
    def __init__(self):
        super().__init__(User)

    async def get_by_telegram_id(
        self, telegram_id: int, session: AsyncSession
    ) -> Optional[User]:
        """Найти пользователя по telegram_id."""
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def create_or_update(
        self, telegram_id: int, session: AsyncSession, **kwargs
    ) -> User:
        """Создать пользователя или обновить его параметры, если он уже существует."""
        user = await self.get_by_telegram_id(telegram_id=telegram_id, session=session)
        
        if user:
            # Используем обновление экземпляра класса
            user = await self.update(session=session, db_obj=user, update_data=kwargs)
        else:
            # Создаем нового пользователя с telegram_id и дополнительными полями
            data = {
                "telegram_id": telegram_id,
                "registration_date": datetime.now(),
                **kwargs}
            user = await self.create(session=session, data=data)
            
        return user


crud_user = UserRepository()
