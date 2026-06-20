from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, model_validator


class UpdateItemRequest(BaseModel):
    document_id: str = Field(
        ...,
        description="Elasticsearch document id to update.",
    )
    document: Dict[str, Any] = Field(
        ...,
        description="Flat Elasticsearch document fields using model aliases.",
    )
    upsert: bool = Field(
        default=True,
        description="Create the document if it does not exist.",
    )

    @model_validator(mode="after")
    def validate_document(self):
        if not self.document:
            raise ValueError("document must contain at least one field")
        return self


class UpdateRequest(BaseModel):
    document_id: Optional[str] = Field(
        default=None,
        description="Single-document update id.",
    )
    document: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Single-document update payload.",
    )
    upsert: bool = Field(
        default=True,
        description="Create the single target document if it does not exist.",
    )
    updates: Optional[List[UpdateItemRequest]] = Field(
        default=None,
        min_length=1,
        description=(
            "Multi-document update payload. Each item has its own id and document."
        ),
    )

    @model_validator(mode="after")
    def validate_shape(self):
        has_updates = bool(self.updates)
        has_single_fields = self.document_id is not None or self.document is not None

        if has_updates and has_single_fields:
            raise ValueError(
                "Use either document_id/document for a single update "
                "or updates for multiple updates"
            )

        if has_updates:
            return self

        if self.document_id is None:
            raise ValueError("document_id is required for single update requests")

        if not self.document:
            raise ValueError("document must contain at least one field")

        return self
