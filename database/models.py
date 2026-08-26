from datetime import datetime
from typing import Optional

from sqlalchemy import (BigInteger, Boolean, Column, DateTime, ForeignKey,
                        Integer, String, func)
from sqlalchemy.orm import (DeclarativeBase, Mapped, declarative_base,
                            mapped_column, relationship)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)


    first_name: Mapped[Optional[str]] = mapped_column(String(64))
    last_name: Mapped[Optional[str]] = mapped_column(String(64))
    username: Mapped[Optional[str]] = mapped_column(String(32))


    is_premium: Mapped[bool] = mapped_column(default=False)

    registration_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())


    # Связь с конвертациями: у одного пользователя может быть много конвертаций
    convertings: Mapped[list["Converting"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Converting(Base):
    __tablename__ = "convertings"

    id: Mapped[int] = mapped_column(primary_key=True)

    # 1. Сохраняем telegram_id для совместимости (делаем его опциональным)
    telegram_id: Mapped[Optional[int]] = mapped_column(BigInteger)

    # 2. Новый внешний ключ, указывающий на users.id (пока nullable=True, чтобы заполнить старые записи)
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )

    converted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )

    number_of_files: Mapped[Optional[int]]
    file_size: Mapped[Optional[int]] = mapped_column(BigInteger)
    is_premium: Mapped[bool] = mapped_column(default=False)

    # Обратная связь к пользователю
    user: Mapped["User"] = relationship(back_populates="convertings")
