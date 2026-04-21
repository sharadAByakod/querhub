from typing import ClassVar, Optional

from pydantic import ConfigDict, Field

from model.vulnerability_model import VulnerabilityModel


class VulniqItsm(VulnerabilityModel):
    WRITABLE_FIELDS: ClassVar[set[str]] = {
        "host.count",
        "vulnerability.asi_severity",
        "vulnerability.summary",
        "vulnerability.changeType",
    }

    host_count: Optional[int] = Field(None, alias="host.count")
    asi_severity: Optional[str] = Field(None, alias="vulnerability.asi_severity")  # noqa
    vuln_summary: Optional[str] = Field(None, alias="vulnerability.summary")
    vuln_changeType: Optional[str] = Field(None, alias="vulnerability.changeType")  # noqa

    model_config = ConfigDict(populate_by_name=True)
