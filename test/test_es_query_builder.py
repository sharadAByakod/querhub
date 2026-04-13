import pytest
from pydantic import BaseModel, Field

from es_query_coverter.filters.filter_group import FilterGroup
from es_query_coverter.model.es_query import QueryParams
from es_query_coverter.model.es_sort import SortRequest
from es_query_coverter.model.filter_request import FilterRequest
from es_query_coverter.model.pagination import PaginationRequest
from es_query_coverter.model.source_filter import SourceFilter
from es_query_coverter.utils.es_query_builder import ESQueryBuilder


# -----------------------------------------------------
# SAMPLE MODEL
# -----------------------------------------------------
class HostModel(BaseModel):
    ip: str
    hostname: str


class OrgModel(BaseModel):
    org_id: str
    org_name: str


class VulnerabilityModel(BaseModel):
    cve_id: str
    severity: str


class FullModel(BaseModel):
    host: HostModel
    org: OrgModel
    vuln: VulnerabilityModel
    timestamp: str
    score: int


class AliasedModel(BaseModel):
    host_ip: str = Field(alias="host.ip")
    severity: str = Field(alias="vulnerability.severity")


# -----------------------------------------------------
# FIXTURE
# -----------------------------------------------------
@pytest.fixture
def builder():
    return ESQueryBuilder(FullModel)


# =====================================================
# BASE TESTS
# =====================================================
def test_build_sort(builder):
    sort_items = [
        SortRequest(field="timestamp", order="asc"),
        SortRequest(field="vuln.severity", order="desc"),
    ]

    result = builder.build_sort(sort_items)

    assert result == [
        {"timestamp": {"order": "asc"}},
        {"vuln.severity": {"order": "desc"}},
    ]


def test_build_sort_allows_special_meta_fields(builder):
    result = builder.build_sort([SortRequest(field="_score", order="desc")])
    assert result == [{"_score": {"order": "desc"}}]


def test_build_pagination(builder):
    pagination = PaginationRequest(page=2, size=50)
    size, offset = builder.build_pagination(pagination)
    assert size == 50
    assert offset == 100


def test_build_source(builder):
    source = SourceFilter(includes=["host.ip", "vuln.*"], excludes="org.org_name")

    result = builder.build_source(source)

    assert result == {
        "_source": {
            "includes": ["host.ip", "vuln.*"],
            "excludes": ["org.org_name"],
        }
    }


def test_builder_prefers_alias_names_for_flat_models():
    builder = ESQueryBuilder(AliasedModel)

    assert builder.model_fields == ["host.ip", "vulnerability.severity"]
    assert builder.build_sort([SortRequest(field="host.ip", order="asc")]) == [
        {"host.ip": {"order": "asc"}}
    ]
    assert builder.build_source(SourceFilter(includes="host.ip")) == {
        "_source": {"includes": ["host.ip"]}
    }


def test_query_params_support_simple_input_shape():
    params = QueryParams.model_validate(
        {
            "select": ["host.ip", "vuln.severity"],
            "page": 1,
            "size": 20,
            "sort": ["host.ip", "-_score"],
            "where": {
                "all": [
                    {"vuln.severity": "HIGH"},
                    {"score": {"gte": 50, "lt": 90}},
                    {
                        "any": [
                            {"host.hostname": {"contains": "srv"}},
                            {"host.ip": {"starts_with": "10.10."}},
                        ]
                    },
                ],
                "not": [
                    {"org.org_name": {"regex": ".*lab.*"}},
                ],
            },
        }
    )

    assert params.source == SourceFilter(includes=["host.ip", "vuln.severity"])
    assert params.pagination == PaginationRequest(page=1, size=20)
    assert params.sort == [
        SortRequest(field="host.ip", order="asc"),
        SortRequest(field="_score", order="desc"),
    ]

    builder = ESQueryBuilder(FullModel)
    result = builder.build_filters(params.filters)

    assert result == {
        "bool": {
            "must": [
                {
                    "bool": {
                        "must": [
                            {"term": {"vuln.severity": "HIGH"}},
                            {"range": {"score": {"gte": 50, "lt": 90}}},
                            {
                                "bool": {
                                    "should": [
                                        {"wildcard": {"host.hostname": "*srv*"}},
                                        {"prefix": {"host.ip": "10.10."}},
                                    ]
                                }
                            },
                        ],
                        "must_not": [
                            {"regexp": {"org.org_name": ".*lab.*"}},
                        ]
                    }
                }
            ]
        }
    }


def test_query_params_support_negative_simple_operators():
    params = QueryParams.model_validate(
        {
            "where": {
                "all": [
                    {"org.org_name": ["Org-1", "Org-2"]},
                    {"score": {"neq": 0}},
                    {"host.hostname": {"exists": False}},
                ]
            }
        }
    )

    builder = ESQueryBuilder(FullModel)
    result = builder.build_filters(params.filters)

    assert result == {
        "bool": {
            "must": [
                {
                    "bool": {
                        "must": [
                            {"terms": {"org.org_name": ["Org-1", "Org-2"]}},
                        ],
                        "must_not": [
                            {"term": {"score": 0}},
                            {"exists": {"field": "host.hostname"}},
                        ],
                    }
                }
            ]
        }
    }


# =====================================================
# END‑TO‑END DSL TESTS (USING QueryBuilder)
# =====================================================


# ------------------------------
# DSL: is  → term
# ------------------------------
def test_dsl_is(builder):
    filters = [
        FilterRequest(field="vuln.severity", dsl="is", value="HIGH", operation="AND")
    ]

    result = builder.build_filters(filters)

    assert result == {"bool": {"must": [{"term": {"vuln.severity": "HIGH"}}]}}


# ------------------------------
# DSL: one_of → terms
# ------------------------------
def test_dsl_one_of(builder):
    filters = [
        FilterRequest(
            field="vuln.cve_id",
            dsl="one_of",
            value=["CVE-1", "CVE-2"],
            operation="AND",
        )
    ]

    result = builder.build_filters(filters)

    assert result == {
        "bool": {"must": [{"terms": {"vuln.cve_id": ["CVE-1", "CVE-2"]}}]}
    }


def test_dsl_in_alias(builder):
    filters = [
        FilterRequest(
            field="vuln.cve_id",
            dsl="in",
            value=["CVE-1", "CVE-2"],
            operation="AND",
        )
    ]

    result = builder.build_filters(filters)

    assert result == {
        "bool": {"must": [{"terms": {"vuln.cve_id": ["CVE-1", "CVE-2"]}}]}
    }


# ------------------------------
# DSL: regex → regexp
# ------------------------------
def test_dsl_regex(builder):
    filters = [
        FilterRequest(
            field="host.hostname",
            dsl="regex",
            value=".*server.*",
            operation="AND",
        )
    ]

    result = builder.build_filters(filters)

    assert result == {"bool": {"must": [{"regexp": {"host.hostname": ".*server.*"}}]}}


# ------------------------------
# DSL: wildcard → wildcard
# ------------------------------
def test_dsl_wildcard(builder):
    filters = [
        FilterRequest(
            field="org.org_name",
            dsl="wildcard",
            value="tech*",
            operation="AND",
        )
    ]

    result = builder.build_filters(filters)

    assert result == {"bool": {"must": [{"wildcard": {"org.org_name": "tech*"}}]}}


def test_dsl_match(builder):
    filters = [
        FilterRequest(
            field="host.hostname",
            dsl="match",
            value="database server",
            operation="AND",
        )
    ]

    result = builder.build_filters(filters)

    assert result == {
        "bool": {"must": [{"match": {"host.hostname": "database server"}}]}
    }


def test_dsl_match_phrase(builder):
    filters = [
        FilterRequest(
            field="host.hostname",
            dsl="match_phrase",
            value="database server",
            operation="AND",
        )
    ]

    result = builder.build_filters(filters)

    assert result == {
        "bool": {
            "must": [{"match_phrase": {"host.hostname": "database server"}}]
        }
    }


def test_dsl_prefix(builder):
    filters = [
        FilterRequest(
            field="org.org_name",
            dsl="prefix",
            value="tech",
            operation="AND",
        )
    ]

    result = builder.build_filters(filters)

    assert result == {"bool": {"must": [{"prefix": {"org.org_name": "tech"}}]}}


def test_dsl_contains(builder):
    filters = [
        FilterRequest(
            field="host.hostname",
            dsl="contains",
            value="server",
            operation="AND",
        )
    ]

    result = builder.build_filters(filters)

    assert result == {
        "bool": {"must": [{"wildcard": {"host.hostname": "*server*"}}]}
    }


def test_dsl_starts_with(builder):
    filters = [
        FilterRequest(
            field="host.hostname",
            dsl="starts_with",
            value="srv-",
            operation="AND",
        )
    ]

    result = builder.build_filters(filters)

    assert result == {"bool": {"must": [{"prefix": {"host.hostname": "srv-"}}]}}


def test_dsl_ends_with(builder):
    filters = [
        FilterRequest(
            field="host.hostname",
            dsl="ends_with",
            value=".prod",
            operation="AND",
        )
    ]

    result = builder.build_filters(filters)

    assert result == {
        "bool": {"must": [{"wildcard": {"host.hostname": "*.prod"}}]}
    }


def test_dsl_exists(builder):
    filters = [
        FilterRequest(
            field="host.hostname",
            dsl="exists",
            value=True,
            operation="AND",
        )
    ]

    result = builder.build_filters(filters)

    assert result == {"bool": {"must": [{"exists": {"field": "host.hostname"}}]}}


# =====================================================
# RANGE DSL END‑TO‑END TESTS
# =====================================================


def test_range_gte_only(builder):
    filters = [FilterRequest(field="score", dsl="range", gte=10, operation="AND")]
    result = builder.build_filters(filters)
    assert result == {"bool": {"must": [{"range": {"score": {"gte": 10}}}]}}


def test_range_lte_only(builder):
    filters = [FilterRequest(field="score", dsl="range", lte=50, operation="AND")]
    result = builder.build_filters(filters)
    assert result == {"bool": {"must": [{"range": {"score": {"lte": 50}}}]}}


def test_range_gt_only(builder):
    filters = [FilterRequest(field="score", dsl="range", gt=5, operation="AND")]
    result = builder.build_filters(filters)
    assert result == {"bool": {"must": [{"range": {"score": {"gt": 5}}}]}}


def test_range_lt_only(builder):
    filters = [FilterRequest(field="score", dsl="range", lt=99, operation="AND")]
    result = builder.build_filters(filters)
    assert result == {"bool": {"must": [{"range": {"score": {"lt": 99}}}]}}


def test_range_gte_lte(builder):
    filters = [
        FilterRequest(field="timestamp", dsl="range", gte=100, lte=200, operation="AND")
    ]
    result = builder.build_filters(filters)
    assert result == {
        "bool": {"must": [{"range": {"timestamp": {"gte": 100, "lte": 200}}}]}
    }


def test_range_gt_lt(builder):
    filters = [FilterRequest(field="score", dsl="range", gt=10, lt=20, operation="AND")]
    result = builder.build_filters(filters)
    assert result == {"bool": {"must": [{"range": {"score": {"gt": 10, "lt": 20}}}]}}


def test_range_gte_lt(builder):
    filters = [FilterRequest(field="score", dsl="range", gte=1, lt=10, operation="AND")]
    result = builder.build_filters(filters)
    assert result == {"bool": {"must": [{"range": {"score": {"gte": 1, "lt": 10}}}]}}


def test_range_gt_lte(builder):
    filters = [FilterRequest(field="score", dsl="range", gt=1, lte=10, operation="AND")]
    result = builder.build_filters(filters)
    assert result == {"bool": {"must": [{"range": {"score": {"gt": 1, "lte": 10}}}]}}


def test_range_all_params(builder):
    filters = [
        FilterRequest(field="host.ip", dsl="range", gte=1, lte=10, operation="AND")
    ]
    result = builder.build_filters(filters)
    assert result == {
        "bool": {
            "must": [
                {
                    "range": {
                        "host.ip": {
                            "gte": 1,
                            "lte": 10,
                        }
                    }
                }
            ]
        }
    }


def test_range_invalid_no_values(builder):
    filters = [FilterRequest(field="score", dsl="range", operation="AND")]
    with pytest.raises(Exception):
        builder.build_filters(filters)


# =====================================================
# Nested / Group Test
# =====================================================
def test_nested_groups(builder):
    filters = [
        FilterRequest(field="vuln.severity", dsl="is", value="HIGH", operation="AND"),
        FilterGroup(
            operation="AND",
            conditions=[
                FilterRequest(
                    field="org.org_id", dsl="is", value="ORG-1", operation="OR"
                ),
                FilterRequest(
                    field="org.org_id", dsl="is", value="ORG-2", operation="OR"
                ),
            ]
        ),
    ]

    result = builder.build_filters(filters)

    assert result == {
        "bool": {
            "must": [
                {"term": {"vuln.severity": "HIGH"}},
                {
                    "bool": {
                        "should": [
                            {"term": {"org.org_id": "ORG-1"}},
                            {"term": {"org.org_id": "ORG-2"}},
                        ]
                    }
                }
            ],
        }
    }


def test_nested_groups_can_be_optional(builder):
    filters = [
        FilterRequest(field="vuln.severity", dsl="is", value="HIGH", operation="AND"),
        FilterGroup(
            operation="OR",
            conditions=[
                FilterRequest(
                    field="org.org_id", dsl="is", value="ORG-1", operation="OR"
                ),
                FilterRequest(
                    field="org.org_id", dsl="is", value="ORG-2", operation="OR"
                ),
            ],
        ),
    ]

    result = builder.build_filters(filters)

    assert result == {
        "bool": {
            "must": [{"term": {"vuln.severity": "HIGH"}}],
            "should": [
                {
                    "bool": {
                        "should": [
                            {"term": {"org.org_id": "ORG-1"}},
                            {"term": {"org.org_id": "ORG-2"}},
                        ]
                    }
                }
            ],
        }
    }


# =====================================================
# NEGATIVE TEST CASES
# =====================================================


# ------------------------------
# Unsupported DSL
# ------------------------------
def test_invalid_dsl(builder):
    filters = [
        FilterRequest(field="vuln.severity", dsl="unknown", value="X", operation="AND")
    ]
    with pytest.raises(Exception):
        builder.build_filters(filters)


# ------------------------------
# Wildcard not allowed for range
# ------------------------------
def test_range_with_wildcard_field(builder):
    filters = [FilterRequest(field="score.*", dsl="range", gte=10, operation="AND")]
    with pytest.raises(Exception):
        builder.build_filters(filters)


# ------------------------------
# Invalid boolean operator
# ------------------------------
def test_invalid_boolean_operator(builder):
    filters = [
        FilterRequest(
            field="vuln.severity", dsl="is", value="HIGH", operation="INVALID"
        )
    ]
    with pytest.raises(Exception):
        builder.build_filters(filters)


# ------------------------------
# Invalid field name
# ------------------------------
def test_invalid_field_name(builder):
    filters = [
        FilterRequest(field="invalid.field", dsl="is", value="HIGH", operation="AND")
    ]
    with pytest.raises(Exception):
        builder.build_filters(filters)


# ------------------------------
# one_of DSL requires non‑empty list
# ------------------------------
def test_one_of_empty_list(builder):
    filters = [
        FilterRequest(field="vuln.cve_id", dsl="one_of", value=[], operation="AND")
    ]
    with pytest.raises(Exception):
        builder.build_filters(filters)


# ------------------------------
# Missing value for term/is DSL
# ------------------------------
def test_is_missing_value(builder):
    filters = [FilterRequest(field="vuln.severity", dsl="is", operation="AND")]
    with pytest.raises(Exception):
        builder.build_filters(filters)


# ------------------------------
# Invalid regex value type
# ------------------------------
def test_regex_invalid_value_type(builder):
    filters = [
        FilterRequest(field="host.hostname", dsl="regex", value=123, operation="AND")
    ]
    with pytest.raises(Exception):
        builder.build_filters(filters)


# ------------------------------
# Range DSL must have at least one operator
# ------------------------------
def test_range_missing_operators(builder):
    filters = [FilterRequest(field="score", dsl="range", operation="AND")]
    with pytest.raises(Exception):
        builder.build_filters(filters)


# ------------------------------
# Nested group with an invalid filter
# ------------------------------
def test_nested_group_invalid_filter(builder):
    filters = [
        FilterGroup(
            conditions=[
                FilterRequest(
                    field="vuln.cve_id", dsl="is", value="CVE-1", operation="AND"
                ),
                FilterRequest(field="bad.field", dsl="is", value="X", operation="AND"),
            ]
        )
    ]
    with pytest.raises(Exception):
        builder.build_filters(filters)
