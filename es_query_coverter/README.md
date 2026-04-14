# Query Guide

This document describes the query input accepted by QueryHub and how it is
translated into Elasticsearch clauses.

The current API supports two input styles:

- a simple format designed for normal API consumers
- an advanced format using explicit `filters`, `sort`, `source`, and `pagination`

The simple format is recommended.

## Recommended Query Shape

```json
{
  "select": ["host.ip", "vulnerability.summary"],
  "page": 0,
  "size": 10,
  "sort": ["host.ip", "-_score"],
  "where": {
    "all": [
      {"vulnerability.summary": {"match": "kernel"}},
      {"organization.id": {"in": ["ORG-1", "ORG-2"]}},
      {"vulnerability.cvss_v3.base_score": {"gte": 7, "lte": 10}}
    ],
    "any": [
      {"vulnerability.asi_severity": "HIGH"},
      {"vulnerability.asi_severity": "CRITICAL"}
    ],
    "not": [
      {"host.hostname": {"exists": false}}
    ]
  }
}
```

## Top-Level Fields

### `select`

Controls `_source.includes`.

Examples:

```json
"select": ["host.ip", "vulnerability.summary"]
```

### `page` and `size`

Pagination values used by the route before querying Elasticsearch.

Examples:

```json
"page": 1,
"size": 20
```

This produces:

- `offset = page * size`
- `size = page size`

### `sort`

Accepts either:

- a list of strings in shorthand form
- the older explicit sort object format

String sort rules:

- `"field"` means ascending
- `"-field"` means descending

Examples:

```json
"sort": ["host.ip", "-vulnerability.cvss_v3.base_score", "-_score"]
```

Supported special sort fields:

- `_score`
- `_shard_doc`
- `_doc`
- `_id`

### `where`

The logical filter section.

Logical groups:

- `all` = AND
- `any` = OR
- `not` = NOT

Example:

```json
{
  "where": {
    "all": [
      {"ticket.system": "ServiceNow"},
      {
        "any": [
          {"vulnerability.asi_severity": "HIGH"},
          {"vulnerability.asi_severity": "CRITICAL"}
        ]
      }
    ],
    "not": [
      {"host.hostname": {"exists": false}}
    ]
  }
}
```

Meaning:

```text
ticket.system = ServiceNow
AND (vulnerability.asi_severity = HIGH OR vulnerability.asi_severity = CRITICAL)
AND NOT host.hostname missing
```

## Supported Field Operators

### Scalar value

```json
{"ticket.system": "ServiceNow"}
```

Compiles to:

```json
{"term": {"ticket.system": "ServiceNow"}}
```

### `in`

```json
{"organization.id": {"in": ["ORG-1", "ORG-2"]}}
```

Compiles to:

```json
{"terms": {"organization.id": ["ORG-1", "ORG-2"]}}
```

You can also pass a plain list:

```json
{"organization.id": ["ORG-1", "ORG-2"]}
```

### `neq` / `not_eq`

```json
{"file.size": {"neq": 0}}
```

Compiles to a negated exact match.

### `not_in`

```json
{"organization.id": {"not_in": ["ORG-1", "ORG-2"]}}
```

Compiles to a negated `terms` clause.

### Range operators

Inline form:

```json
{"vulnerability.cvss_v3.base_score": {"gte": 7, "lte": 10}}
```

Nested form:

```json
{"vulnerability.cvss_v3.base_score": {"range": {"gte": 7, "lte": 10}}}
```

Supported range keys:

- `gte`
- `gt`
- `lte`
- `lt`

### `match`

```json
{"vulnerability.summary": {"match": "kernel issue"}}
```

Compiles to:

```json
{"match": {"vulnerability.summary": "kernel issue"}}
```

### `match_phrase` / `phrase`

```json
{"vulnerability.summary": {"match_phrase": "kernel issue"}}
```

### `wildcard`

```json
{"host.hostname": {"wildcard": "srv-*"}}
```

### `regex`

```json
{"host.hostname": {"regex": "srv-[0-9]+"}}
```

### `prefix`

```json
{"host.ip": {"prefix": "10.10."}}
```

### `contains`

```json
{"host.hostname": {"contains": "prod"}}
```

Compiles to a wildcard query:

```json
{"wildcard": {"host.hostname": "*prod*"}}
```

### `starts_with`

```json
{"host.hostname": {"starts_with": "srv-"}}
```

Compiles to a prefix query.

### `ends_with`

```json
{"host.hostname": {"ends_with": ".prod"}}
```

Compiles to a wildcard query ending in the provided suffix.

### `exists`

```json
{"host.hostname": {"exists": true}}
```

or:

```json
{"host.hostname": {"exists": false}}
```

`true` compiles to an `exists` query.
`false` compiles to a negated `exists` query.

## Example Queries

### Exact filter + paging

```json
{
  "select": ["host.ip", "organization.id"],
  "page": 0,
  "size": 25,
  "where": {
    "all": [
      {"organization.id": "ORG-1"},
      {"ticket.system": "ServiceNow"}
    ]
  }
}
```

### Full-text + OR group

```json
{
  "select": ["host.ip", "vulnerability.summary"],
  "sort": ["-vulnerability.cvss_v3.base_score", "-_score"],
  "where": {
    "all": [
      {"vulnerability.summary": {"match": "kernel"}},
      {
        "any": [
          {"vulnerability.asi_severity": "HIGH"},
          {"vulnerability.asi_severity": "CRITICAL"}
        ]
      }
    ]
  }
}
```

### Mixed ranges and exclusions

```json
{
  "where": {
    "all": [
      {"vulnerability.cvss_v3.base_score": {"gte": 7, "lte": 10}},
      {"file.size": {"gt": 0}},
      {"host.ip": {"starts_with": "10.10."}}
    ],
    "not": [
      {"organization.name": {"regex": ".*lab.*"}},
      {"host.hostname": {"exists": false}}
    ]
  }
}
```

## Advanced Format

The older format still works and is useful if you want to send the internal
query-builder structures directly.

Example:

```json
{
  "source": {
    "includes": ["host.ip", "vulnerability.summary"]
  },
  "pagination": {
    "page": 0,
    "size": 10
  },
  "sort": [
    {"field": "host.ip", "order": "asc"},
    {"field": "_score", "order": "desc"}
  ],
  "filters": [
    {
      "field": "vulnerability.summary",
      "dsl": "match",
      "value": "kernel",
      "operation": "AND"
    }
  ]
}
```

## Aggregation DSL

QueryHub supports a structured aggregation DSL via the `/aggs/view/{view_name}` endpoint.

### Request Structure

```json
{
  "where": { ... },
  "aggs": {
    "terms": [...],
    "metrics": [...],
    "date_histogram": [...],
    "range": [...]
  }
}
```

### 1. Terms Aggregation

Group documents by a specific field.

```json
{
  "field": "vulnerability.asi_severity",
  "name": "severity_buckets",
  "size": 10,
  "order": {"_count": "desc"}
}
```

### 2. Metric Aggregation

Calculate a single value across a set of documents.

```json
{
  "field": "vulnerability.cvss_v3.base_score",
  "name": "avg_score",
  "type": "avg"
}
```

Supported types: `avg`, `sum`, `min`, `max`, `cardinality`.

### 3. Date Histogram

Bucket documents by time intervals.

```json
{
  "field": "event.updated",
  "name": "monthly_updates",
  "calendar_interval": "month"
}
```

### 4. Range Aggregation

Bucket documents by numeric ranges.

```json
{
  "field": "vulnerability.cvss_v3.base_score",
  "name": "score_ranges",
  "ranges": [
    {"to": 4},
    {"from": 4, "to": 7},
    {"from": 7}
  ]
}
```

## How It Maps To Elasticsearch

The builder validates field names using the view model aliases and compiles the
simple query structure into Elasticsearch `bool` queries.

Mapping summary:

- `all` -> `bool.must`
- `any` -> nested `bool.should`
- `not` -> `bool.must_not`
- scalar -> `term`
- `in` -> `terms`
- range operators -> `range`
- text operators -> `match`, `match_phrase`, `wildcard`, `regexp`, `prefix`

## Validation Notes

- only fields declared on the target view model are allowed
- wildcard field names must match at least one known field
- `range` on wildcard field names is rejected
- `sort` shorthand accepts `-field` for descending order
- `exists` must be `true` or `false`
- unsupported operators return `400`

## Response Shape

The view route returns:

```json
{
  "view": "vulnitsm",
  "count": 10,
  "data": [],
  "pagination": {
    "page": 0,
    "size": 10,
    "offset": 0,
    "returned": 10,
    "total": 124
  },
  "client": "client-1"
}
```
