from enum import Enum


class EsIndices(str, Enum):

    API_CLIENT = "qh_client"
    VULNIQ_ITSM = "vulniq-itsm"
    VULNIQ = "inventory-vulniq"
    CUSTOMER = "inventory-customer"
    DEVICE = "inventory-device"
    SERVICE = "inventory-service"
    ASSET = "inventory-c16m"
