import pytest
from pydantic import BaseModel, Field
from typing import Optional

from es_query_coverter.aggregations.agg_builder import ESAggregationBuilder
from es_query_coverter.aggregations.models import (
    AggregationRequest,
    TermsAggregation,
    MetricAggregation,
    DateHistogramAggregation,
    RangeAggregation,
)

class MockModel(BaseModel):
    host_ip: str = Field("1.2.3.4", alias="host.ip")
    vuln_score: float = Field(5.0, alias="vulnerability.score")
    event_date: str = Field("2023-01-01", alias="event.date")

def test_agg_builder_builds_terms_aggregation():
    builder = ESAggregationBuilder(MockModel)
    request = AggregationRequest(
        terms=[
            TermsAggregation(field="host.ip", name="ips", size=5)
        ]
    )

    result = builder.build(request)

    assert result == {
        "ips": {
            "terms": {
                "field": "host.ip",
                "size": 5
            }
        }
    }

def test_agg_builder_builds_metrics_aggregation():
    builder = ESAggregationBuilder(MockModel)
    request = AggregationRequest(
        metrics=[
            MetricAggregation(field="vulnerability.score", name="avg_score", type="avg")
        ]
    )

    result = builder.build(request)

    assert result == {
        "avg_score": {
            "avg": {
                "field": "vulnerability.score"
            }
        }
    }

def test_agg_builder_builds_date_histogram_aggregation():
    builder = ESAggregationBuilder(MockModel)
    request = AggregationRequest(
        date_histogram=[
            DateHistogramAggregation(
                field="event.date",
                name="monthly",
                calendar_interval="month",
                format="yyyy-MM"
            )
        ]
    )

    result = builder.build(request)

    assert result == {
        "monthly": {
            "date_histogram": {
                "field": "event.date",
                "calendar_interval": "month",
                "format": "yyyy-MM"
            }
        }
    }

def test_agg_builder_builds_range_aggregation():
    builder = ESAggregationBuilder(MockModel)
    ranges = [{"to": 5}, {"from": 5, "to": 8}, {"from": 8}]
    request = AggregationRequest(
        range=[
            RangeAggregation(field="vulnerability.score", name="score_ranges", ranges=ranges)
        ]
    )

    result = builder.build(request)

    assert result == {
        "score_ranges": {
            "range": {
                "field": "vulnerability.score",
                "ranges": ranges
            }
        }
    }

def test_agg_builder_validates_field_names():
    builder = ESAggregationBuilder(MockModel)
    request = AggregationRequest(
        terms=[TermsAggregation(field="invalid.field")]
    )

    from fastapi import HTTPException
    with pytest.raises(HTTPException) as excinfo:
        builder.build(request)

    assert excinfo.value.status_code == 400
    assert "Invalid terms field 'invalid.field'" in str(excinfo.value.detail)

def test_agg_builder_rejects_unsupported_metric_types():
    builder = ESAggregationBuilder(MockModel)
    request = AggregationRequest(
        metrics=[MetricAggregation(field="vulnerability.score", type="unsupported")]
    )

    from fastapi import HTTPException
    with pytest.raises(HTTPException) as excinfo:
        builder.build(request)

    assert excinfo.value.status_code == 400
    assert "Unsupported metric type" in str(excinfo.value.detail)
