from typing import Any, Dict, List, Type

from pydantic import BaseModel

from es_query_coverter.aggregations.models import (
    AggregationRequest,
    DateHistogramAggregation,
    MetricAggregation,
    RangeAggregation,
    TermsAggregation,
)
from es_query_coverter.utils.query_builder_helpers import QueryBuilderHelpers


class ESAggregationBuilder:
    """
    Translates high-level AggregationRequest into Elasticsearch DSL.
    Includes field validation against the model.
    """

    def __init__(self, model: Type[BaseModel]):
        self.model = model
        self.model_fields = QueryBuilderHelpers.collect_model_fields(model)

    def build(self, request: AggregationRequest) -> Dict[str, Any]:
        es_aggs: Dict[str, Any] = {}

        # 1. Terms Aggregations
        if request.terms:
            for agg in request.terms:
                name = agg.name or f"terms_{agg.field.replace('.', '_')}"
                self._validate_field(agg.field, "terms")
                es_aggs[name] = {"terms": {"field": agg.field, "size": agg.size}}
                if agg.order:
                    es_aggs[name]["terms"]["order"] = agg.order

        # 2. Date Histograms
        if request.date_histogram:
            for agg in request.date_histogram:
                name = agg.name or f"date_hist_{agg.field.replace('.', '_')}"
                self._validate_field(agg.field, "date_histogram")
                es_aggs[name] = {
                    "date_histogram": {
                        "field": agg.field,
                        "calendar_interval": agg.calendar_interval,
                    }
                }
                if agg.format:
                    es_aggs[name]["date_histogram"]["format"] = agg.format

        # 3. Ranges
        if request.range:
            for agg in request.range:
                name = agg.name or f"range_{agg.field.replace('.', '_')}"
                self._validate_field(agg.field, "range")
                es_aggs[name] = {"range": {"field": agg.field, "ranges": agg.ranges}}

        # 4. Metrics (avg, sum, etc.)
        if request.metrics:
            for agg in request.metrics:
                name = agg.name or f"{agg.type}_{agg.field.replace('.', '_')}"
                self._validate_field(agg.field, "metrics")
                if agg.type not in ["avg", "sum", "min", "max", "cardinality"]:
                    from fastapi import HTTPException

                    raise HTTPException(400, f"Unsupported metric type: {agg.type}")
                es_aggs[name] = {agg.type: {"field": agg.field}}

        return es_aggs

    def _validate_field(self, field: str, kind: str):
        QueryBuilderHelpers.validate_field_name(field, self.model_fields, kind)
