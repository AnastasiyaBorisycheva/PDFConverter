from typing import Any, Dict

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from typing import Any, Generic, Sequence, Type, TypeVar
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Base  # Базовая модель SQLAlchemy


ModelType = TypeVar("ModelType", bound=Base)

class CRUDBase(Generic[ModelType]):

    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get(self, id: Any, session: AsyncSession) -> ModelType | None:
        """Получить объект по первичному ключу (ID)."""
        result = await session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        session: AsyncSession,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[ModelType]:
        """Получить список объектов с пагинацией."""
        result = await session.execute(
            select(self.model).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def create(self, session: AsyncSession, data: dict[str, Any]) -> ModelType:
        """Создать и сохранить новый объект."""
        db_obj = self.model(**data)
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def update(
        self,
        session: AsyncSession,
        db_obj: ModelType,
        update_data: dict[str, Any],
    ) -> ModelType:
        """Обновить существующий объект (ORM-way)."""
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def delete(self, session: AsyncSession, id: Any) -> bool:
        """Удалить объект по ID."""
        db_obj = await self.get(id, session)
        if db_obj:
            await session.delete(db_obj)
            await session.commit()
            return True
        return False

    async def get_by_attribute(
        self,
        session: AsyncSession,
        attr_name: str,
        attr_value: Any,
    ) -> ModelType | None:
        """Получить один объект по названию атрибута."""
        if not hasattr(self.model, attr_name):
            raise AttributeError(f"Модель {self.model.__name__} не имеет атрибута '{attr_name}'")
            
        attr = getattr(self.model, attr_name)
        result = await session.execute(
            select(self.model).where(attr == attr_value)
        )
        return result.scalars().first()
