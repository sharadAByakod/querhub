from typing import ClassVar, Optional

from pydantic import BaseModel, ConfigDict, Field


class OrgModel(BaseModel):
    WRITABLE_FIELDS: ClassVar[set[str]] = {
        "organization.id",
        "organization.name",
        "organization.contract.id",
        "ticket.system",
    }

    org_id: Optional[str] = Field(None, alias="organization.id")
    org_name: Optional[str] = Field(None, alias="organization.name")
    contract_id: Optional[str] = Field(None, alias="organization.contract.id")

    internal_category: Optional[str] = Field(None, alias="internal.event.category")  # noqa
    internal_code: Optional[str] = Field(None, alias="internal.event.code")
    internal_event_id: Optional[str] = Field(None, alias="internal.event.id")
    internal_tag: Optional[str] = Field(None, alias="internal.event.tag")

    internal_index: Optional[str] = Field(None, alias="internal.index")
    internal_subject_identifier: Optional[str] = Field(
        None, alias="internal.subject_identifier"
    )  # noqa

    critical_state_duration: Optional[int] = Field(
        None, alias="monitoring.threshold.critical.state_duration"
    )

    ticket_system: Optional[str] = Field(None, alias="ticket.system")

    model_config = ConfigDict(populate_by_name=True)
