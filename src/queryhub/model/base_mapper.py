# model/base_mapper.py
from typing import Type

from pydantic import BaseModel


def map_to_model(model: Type[BaseModel], src: dict) -> BaseModel:
    """
    Validates an Elasticsearch `_source` payload against the target Pydantic model.
    Field aliases are honored so ES field names like `host.ip` populate correctly.
    """
    return model.model_validate(src)
