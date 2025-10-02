from crud.base import CRUDBase
from database.models import Converting


class ConvertingRepository(CRUDBase):

    def __init__(self):
        super().__init__(Converting)


crud_convert = ConvertingRepository()
