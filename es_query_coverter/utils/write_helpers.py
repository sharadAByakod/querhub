from typing import Any, Dict, Optional, Type

from fastapi import HTTPException
from pydantic import BaseModel, TypeAdapter

from es_query_coverter.utils.query_builder_helpers import QueryBuilderHelpers


class WriteHelpers:
    @staticmethod
    def collect_model_field_specs(
        model: Type[BaseModel], prefix: str = ""
    ) -> Dict[str, Any]:
        collected: Dict[str, Any] = {}

        for field_name, field_info in model.model_fields.items():
            field_type = QueryBuilderHelpers.extract_model_type(field_info.annotation)
            field_path = field_info.alias or field_name

            if field_type is not None:
                nested_prefix = ""
                if not QueryBuilderHelpers.model_uses_flat_aliases(field_type):
                    nested_prefix = f"{prefix}{field_path}."

                collected.update(
                    WriteHelpers.collect_model_field_specs(
                        field_type,
                        prefix=nested_prefix,
                    )
                )
                continue

            collected[f"{prefix}{field_path}"] = field_info.annotation

        return collected

    @staticmethod
    def collect_writable_fields(model: Type[BaseModel]) -> set[str]:
        writable_fields: set[str] = set()

        for cls in reversed(model.__mro__):
            writable = getattr(cls, "WRITABLE_FIELDS", None)
            if writable:
                writable_fields.update(writable)

        return writable_fields

    @staticmethod
    def validate_write_document(
        model: Type[BaseModel],
        document: Dict[str, Any],
    ) -> Dict[str, Any]:
        if not isinstance(document, dict) or not document:
            raise HTTPException(
                status_code=400,
                detail="document must be a non-empty object",
            )

        field_specs = WriteHelpers.collect_model_field_specs(model)
        writable_fields = WriteHelpers.collect_writable_fields(model)

        if not writable_fields:
            raise HTTPException(
                status_code=400,
                detail=f"View '{model.__name__}' does not define writable fields",
            )

        validated: Dict[str, Any] = {}

        for field, value in document.items():
            if field not in field_specs:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Invalid write field '{field}'. "
                        f"Allowed writable fields: {sorted(writable_fields)}"
                    ),
                )

            if field not in writable_fields:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Field '{field}' is not writable. "
                        f"Allowed writable fields: {sorted(writable_fields)}"
                    ),
                )

            try:
                adapter = TypeAdapter(field_specs[field])
                validated[field] = adapter.validate_python(value)
            except Exception as exc:  # pragma: no cover - error body is user-facing
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid value for field '{field}': {exc}",
                ) from exc

        return validated

    @staticmethod
    def writable_fields_for(model: Type[BaseModel]) -> list[str]:
        return sorted(WriteHelpers.collect_writable_fields(model))
