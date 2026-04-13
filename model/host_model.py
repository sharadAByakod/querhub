from typing import ClassVar, Optional

from pydantic import BaseModel, Field

from model.org_model import OrgModel


class HostModel(BaseModel):
    WRITABLE_FIELDS: ClassVar[set[str]] = {
        "host.hostname",
        "host.id",
        "host.ip",
        "host.name",
        "host.state",
    }

    firewall_blocking_enabled: Optional[bool] = Field(
        None, alias="bt.eaglei.firewall.blocking.is_enabled"
    )
    acs_configuration: Optional[str] = Field(None, alias="cisco.acs.configuration")  # noqa
    host_business_unit: Optional[str] = Field(None, alias="host.business_unit")
    host_exempted: Optional[bool] = Field(None, alias="host.exempted")
    host_hostname: Optional[str] = Field(None, alias="host.hostname")
    host_id: Optional[str] = Field(None, alias="host.id")
    host_ip: Optional[str] = Field(None, alias="host.ip")
    host_name: Optional[str] = Field(None, alias="host.name")
    host_state: Optional[str] = Field(None, alias="host.state")

    host_crowdstrike_enabled: Optional[bool] = Field(
        None, alias="host.crowdstrike.is_enabled"
    )  # noqa
    host_qualys_enabled: Optional[bool] = Field(None, alias="host.qualys.is_enabled")  # noqa
    host_opsview_enabled: Optional[bool] = Field(
        None, alias="host.opsview_monitoring.is_enabled"
    )  # noqa

    geo_city: Optional[str] = Field(None, alias="host.geo.city_name")
    geo_country: Optional[str] = Field(None, alias="host.geo.country_name")
    geo_office: Optional[str] = Field(None, alias="host.geo.office")
    geo_region: Optional[str] = Field(None, alias="host.geo.region_name")

    os_name: Optional[str] = Field(None, alias="host.os.name")
    os_build: Optional[str] = Field(None, alias="host.os.build")
    os_last_update: Optional[str] = Field(None, alias="host.os.lifecycle.last_update")  # noqa
    os_end_of_support: Optional[str] = Field(None, alias="host.os.lifecycle.end_of_support")  # noqa
    os_end_of_engineering: Optional[str] = Field(
        None, alias="host.os.lifecycle.end_of_engineering_support"
    )

    os_state_current: Optional[str] = Field(None, alias="host.os.lifecycle.state.current")  # noqa
    os_state_3m: Optional[str] = Field(None, alias="host.os.lifecycle.state.3m")  # noqa
    os_state_6m: Optional[str] = Field(None, alias="host.os.lifecycle.state.6m")  # noqa
    os_state_12m: Optional[str] = Field(None, alias="host.os.lifecycle.state.12m")  # noqa
    os_state_18m: Optional[str] = Field(None, alias="host.os.lifecycle.state.18m")  # noqa
    os_state_24m: Optional[str] = Field(None, alias="host.os.lifecycle.state.24m")  # noqa

    serial_number: Optional[str] = Field(None, alias="host.serial_number")

    service_level: Optional[str] = Field(None, alias="host.service.level")

    service_acceptance_date: Optional[str] = Field(
        None, alias="host.service_acceptance.date"
    )  # noqa
    service_acceptance_id: Optional[str] = Field(None, alias="host.service_acceptance.id")  # noqa

    monitoring_cluster_name: Optional[str] = Field(None, alias="monitoring.cluster.name")  # noqa

    product_name: Optional[str] = Field(None, alias="product.name")
    product_vendor: Optional[str] = Field(None, alias="product.vendor")

    product_last_update: Optional[str] = Field(None, alias="product.lifecycle.last_update")  # noqa
    product_last_sale: Optional[str] = Field(None, alias="product.lifecycle.last_sale")  # noqa
    product_end_of_support: Optional[str] = Field(
        None, alias="product.lifecycle.end_of_support"
    )  # noqa

    product_state_current: Optional[str] = Field(
        None, alias="product.lifecycle.state.current"
    )  # noqa
    product_state_3m: Optional[str] = Field(None, alias="product.lifecycle.state.3m")  # noqa
    product_state_6m: Optional[str] = Field(None, alias="product.lifecycle.state.6m")  # noqa
    product_state_12m: Optional[str] = Field(None, alias="product.lifecycle.state.12m")  # noqa
    product_state_18m: Optional[str] = Field(None, alias="product.lifecycle.state.18m")  # noqa
    product_state_24m: Optional[str] = Field(None, alias="product.lifecycle.state.24m")  # noqa

    product_type_name: Optional[str] = Field(None, alias="product.type.name")
    product_type_friendly: Optional[str] = Field(None, alias="product.type.friendly_name")  # noqa

    source_host_hostname: Optional[str] = Field(None, alias="source.host.hostname")  # noqa

    support_model: Optional[str] = Field(None, alias="support.model")
    support_team: Optional[str] = Field(None, alias="support.team")
    support_managed_by: Optional[str] = Field(None, alias="support.managed_by")

    support_ad_group_allowed: Optional[str] = Field(
        None, alias="support.ad_groups.data_access.allowed"
    )

    org: Optional[OrgModel] = None

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
