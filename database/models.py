from datetime import datetime

from sqlalchemy import BigInteger, Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True)  # BigInteger для больших ID Telegram
    first_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)
    username = Column(String(100), nullable=True)
    is_premium = Column(Boolean,)
    registration_date = Column(DateTime, default=datetime.now)


class Converting(Base):
    __tablename__ = 'convertings'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=False)
    converted_at = Column(DateTime, default=datetime.now)
    number_of_files = Column(Integer, nullable=True)
    file_size = Column(BigInteger, nullable=True)
    is_premium = Column(Boolean,)
