from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)
from sqlalchemy.orm import sessionmaker

from core.core import DATABASE_URL
from core.logger import setup_logger

logger = setup_logger(__name__)


# Асинхронный движок с оптимизированным пулом соединений
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # echo=True для отладки SQL-запросов
    pool_pre_ping=True,  # Проверка соединения перед выполнением запроса
    pool_size=10,        # Базовое количество соединений в пуле
    max_overflow=20,     # Дополнительные соединения при пиковых нагрузках
)

# Фабрика сессий
# AsyncSessionLocal = sessionmaker(
#     bind=engine,
#     class_=AsyncSession,
#     expire_on_commit=False,
# )

# Фабрика сессий SQLAlchemy 2.0
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


# Асинхронный генератор сессий.
# async def get_async_session() -> AsyncSession:
#     # Через асинхронный контекстный менеджер и sessionmaker
#     # открывается сессия.
#     async with AsyncSessionLocal() as async_session:
#         # Генератор с сессией передается в вызывающую функцию.
#         logger.debug("Генерируем очередную сессию")
#         yield async_session
#         # Когда HTTP-запрос отработает - выполнение кода вернётся сюда,
#         # и при выходе из контекстного менеджера сессия будет закрыта.


# Асинхронный генератор сессий для зависимостей / middleware
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Генератор асинхронных сессий базы данных."""
    async with AsyncSessionLocal() as session:
        logger.debug("Создана новая сессия БД")
        try:
            yield session
        except Exception as e:
            logger.error(f"Ошибка во время сессии БД: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()
            logger.debug("Сессия БД закрыта")