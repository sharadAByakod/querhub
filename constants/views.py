from enum import Enum
from typing import Type

from constants.es_indices import EsIndices
from model.vulniqitsm_model import VulniqItsm


class Views(str, Enum):

    index_name: str
    model: Type

    VULNIQ_ITSM = (
        "vulnitsm",
        EsIndices.VULNIQ_ITSM.value,
        VulniqItsm,
    )

    def __new__(
        cls,
        value: str,
        index_name: str,
        model: Type,
    ) -> "Views":
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj.index_name = index_name
        obj.model = model
        return obj
