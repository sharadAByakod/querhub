from typing import Any, ClassVar

from pydantic import BaseModel


class ViewDefinition:
    index_name: ClassVar[str]
    model: ClassVar[type[BaseModel]]
    base_query: ClassVar[dict[str, Any] | None] = None
