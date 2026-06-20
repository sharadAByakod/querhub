import fnmatch
from typing import Any, List, Optional, Type, get_args, get_origin

from fastapi import HTTPException
from pydantic import BaseModel


class QueryBuilderHelpers:
    """
    Centralized helper utilities for ESQueryBuilder.
    Handles:
        - Nested field collection
        - Field validation (wildcard + exact)
        - includes/excludes normalization
    """

    @staticmethod
    def collect_model_fields(model: Type[BaseModel], prefix: str = "") -> List[str]:  # noqa
        """
        Recursively collects queryable field names from the Pydantic model.
        Prefers field aliases so request/response payloads align with ES field names.
        """
        collected: set[str] = set()

        for field_name, field_info in model.model_fields.items():
            field_type = QueryBuilderHelpers.extract_model_type(field_info.annotation)
            field_path = field_info.alias or field_name

            if field_type is not None:
                nested_prefix = ""

                if not QueryBuilderHelpers.model_uses_flat_aliases(field_type):
                    nested_prefix = f"{prefix}{field_path}."

                collected.update(
                    QueryBuilderHelpers.collect_model_fields(
                        field_type,
                        prefix=nested_prefix,
                    )  # noqa
                )
            else:
                collected.add(f"{prefix}{field_path}")

        return sorted(collected)

    @staticmethod
    def extract_model_type(annotation: Any) -> Optional[Type[BaseModel]]:
        if isinstance(annotation, type) and issubclass(annotation, BaseModel):
            return annotation

        origin = get_origin(annotation)
        if origin is None:
            return None

        for arg in get_args(annotation):
            nested_model = QueryBuilderHelpers.extract_model_type(arg)
            if nested_model is not None:
                return nested_model

        return None

    @staticmethod
    def model_uses_flat_aliases(model: Type[BaseModel]) -> bool:
        for field_name, field_info in model.model_fields.items():
            if QueryBuilderHelpers.extract_model_type(field_info.annotation) is not None:
                return False

            if (field_info.alias or field_name) == field_name:
                return False

        return True

    @staticmethod
    def validate_field_name(field: str, valid_fields: List[str], kind: str) -> Any:  # noqa
        """
        Validates a field name for:
            - sorting
            - includes + excludes
            - future filters
        """

        # Wildcard allowed: host.*, vuln.*
        if "*" in field:
            matched = any(fnmatch.fnmatch(f, field) for f in valid_fields)
            if not matched:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid {kind} field '{field}' — wildcard matches nothing",  # noqa
                )
            return

        # Exact match
        if field not in valid_fields:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Invalid {kind} field '{field}'. "
                    f"Allowed fields: {sorted(valid_fields)}"  # noqa
                ),
            )

    @staticmethod
    def ensure_list(value: Optional[Any]) -> Optional[List[str]]:
        """
        Normalizes:
            "host.*"      -> ["host.*"]
            ["vuln.id"]   -> same
            None          -> None
        """
        if value is None:
            return None
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            return [value]

        raise HTTPException(
            status_code=400,
            detail="includes/excludes must be string or list of strings",
        )
