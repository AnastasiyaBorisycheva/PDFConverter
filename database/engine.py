from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from core.core import DATABASE_URL
from core.logger import setup_logger

logger = setup_logger(__name__)


# Асинхронный движок
engine = create_async_engine(DATABASE_URL, echo=False)  # echo=True для логов SQL

# Фабрика сессий
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# Асинхронный генератор сессий.
async def get_async_session() -> AsyncSession:
    # Через асинхронный контекстный менеджер и sessionmaker
    # открывается сессия.
    async with AsyncSessionLocal() as async_session:
        # Генератор с сессией передается в вызывающую функцию.
        logger.debug("Генерируем очередную сессию")
        yield async_session
        # Когда HTTP-запрос отработает - выполнение кода вернётся сюда,
        # и при выходе из контекстного менеджера сессия будет закрыта.
