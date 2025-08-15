import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:converter_password@db:5432/pdf_converter")

# DATABASE_URL = "sqlite+aiosqlite:///pdfconverter.db"