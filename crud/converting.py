from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Converting
from crud.base import CRUDBase


class ConvertingRepository(CRUDBase):

    def __init__(self):
        super().__init__(Converting)


crud_convert = ConvertingRepository()
