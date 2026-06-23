from enum import Enum

from queryhub.view_definitions.base import ViewDefinition
from queryhub.view_definitions.vulniq_itsm import VulniqItsmViewDefinition


class Views(str, Enum):
    definition: type[ViewDefinition]

    VULNIQ_ITSM = (
        "vulnitsm",
        VulniqItsmViewDefinition,
    )

    def __new__(
        cls,
        value: str,
        definition: type[ViewDefinition],
    ) -> "Views":
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj.definition = definition
        return obj

    @property
    def index_name(self) -> str:
        return self.definition.index_name

    @property
    def model(self):
        return self.definition.model

    @property
    def base_query(self):
        return self.definition.base_query
