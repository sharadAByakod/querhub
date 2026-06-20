from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, model_validator


class WriteRequest(BaseModel):
    document: Dict[str, Any] = Field(
        ..., description="Flat Elasticsearch document fields using model aliases"
    )
    document_id: Optional[str] = Field(
        default=None,
        description="Optional Elasticsearch document id. When omitted, ES generates one.",
    )
    upsert: bool = Field(
        default=True,
        description="When document_id is provided, create the document if it does not exist.",
    )

    @model_validator(mode="after")
    def validate_document(self):
        if not self.document:
            raise ValueError("document must contain at least one field")
        return self
