

from typing import Optional
from recoma.models.core.base_model import BaseModel


class IntercodeModel(BaseModel):

    def __init__(self, data_file, **kwargs):
        super().__init__(**kwargs)
        