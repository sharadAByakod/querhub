from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class AggregationBase(BaseModel):
    field: str
    name: Optional[str] = None
    # Sub-aggregations support
    aggs: Optional["AggregationRequest"] = None


class TermsAggregation(AggregationBase):
    size: int = 10
    order: Optional[Dict[str, str]] = None


class DateHistogramAggregation(AggregationBase):
    calendar_interval: str = "month"
    format: Optional[str] = None


class RangeAggregation(AggregationBase):
    ranges: List[Dict[str, Any]]


class MetricAggregation(AggregationBase):
    # avg, sum, min, max, cardinality, stats, value_count, percentiles
    type: str
    params: Optional[Dict[str, Any]] = None


class AggregationRequest(BaseModel):
    # Support multiple types of aggregations
    terms: Optional[List[TermsAggregation]] = None
    date_histogram: Optional[List[DateHistogramAggregation]] = None
    range: Optional[List[RangeAggregation]] = None
    metrics: Optional[List[MetricAggregation]] = None


class AggregationQueryParams(BaseModel):
    filters: Optional[List[Any]] = None  # Reuse existing FilterNode/Group
    aggs: AggregationRequest
    where: Optional[Dict[str, Any]] = None  # Support simple 'where' input


# Rebuild recursive models in Pydantic v2
AggregationRequest.model_rebuild()
AggregationBase.model_rebuild()
