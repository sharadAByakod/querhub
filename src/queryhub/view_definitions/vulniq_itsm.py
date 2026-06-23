from queryhub.constants.es_indices import EsIndices
from queryhub.model.vulniqitsm_model import VulniqItsm
from queryhub.view_definitions.base import ViewDefinition


class VulniqItsmViewDefinition(ViewDefinition):
    index_name = EsIndices.VULNIQ_ITSM.value
    model = VulniqItsm
    base_query = None
