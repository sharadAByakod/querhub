# QueryHub API Usage Guide

This guide is for people who call the QueryHub API.
It explains how to authenticate, how to send search and write requests, and how to
read responses.

## Base URL

Local default:

```text
http://localhost:8001/api/v2
```

Current endpoints:

```text
POST /search/view/vulnitsm
POST /write/view/vulnitsm
POST /update/view/vulnitsm
POST /update/view/vulnitsm/{document_id}
```

Full search URL:

```text
http://localhost:8001/api/v2/search/view/vulnitsm
```

Full write URL:

```text
http://localhost:8001/api/v2/write/view/vulnitsm
```

Full update URLs:

```text
http://localhost:8001/api/v2/update/view/vulnitsm
http://localhost:8001/api/v2/update/view/vulnitsm/{document_id}
```

## Authentication

The API expects a Bearer token.

Headers:

```http
Authorization: Bearer <token>
Content-Type: application/json
```

If the token is missing, invalid, or the client does not have access to the
requested view, the API returns `401` or `403`.

## Search Request Structure

The recommended request format is:

```json
{
  "select": ["host.ip", "vulnerability.summary"],
  "page": 0,
  "size": 10,
  "sort": ["host.ip", "-_score"],
  "where": {
    "all": [
      {"vulnerability.summary": {"match": "kernel"}},
      {"organization.id": {"in": ["ORG-1", "ORG-2"]}}
    ],
    "not": [
      {"host.hostname": {"exists": false}}
    ]
  }
}
```

## Meaning Of The Main Fields

### `select`

Lists the fields to return in each item.

Example:

```json
"select": ["host.ip", "vulnerability.summary"]
```

### `page`

Zero-based page number.

Example:

```json
"page": 0
```

### `size`

Maximum number of items returned for that page.

Example:

```json
"size": 10
```

### `sort`

Sort order for results.

Rules:

- `"field"` means ascending
- `"-field"` means descending

Example:

```json
"sort": ["host.ip", "-_score"]
```

Supported special sort fields:

- `_score`
- `_shard_doc`
- `_doc`
- `_id`

### `where`

Contains all filtering rules.

Logical groups:

- `all` means every condition must match
- `any` means at least one condition must match
- `not` means exclude matching records

Example:

```json
{
  "where": {
    "all": [
      {"ticket.system": "ServiceNow"}
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

That means:

```text
ticket.system = ServiceNow
AND (vulnerability.asi_severity = HIGH OR vulnerability.asi_severity = CRITICAL)
AND NOT host.hostname missing
```

## Write Requests

Use the write endpoint when you want to create a new document or update an existing one.

Recommended request shape:

```json
{
  "document_id": "vuln-123",
  "upsert": true,
  "document": {
    "host.ip": "10.10.1.14",
    "host.count": 3,
    "organization.id": "ORG-1",
    "ticket.system": "ServiceNow",
    "vulnerability.summary": "Kernel patch missing"
  }
}
```

Meaning:

- `document_id` is optional
- if `document_id` is provided, the API updates that document
- if `upsert` is `true`, a missing `document_id` will be created during update
- if `document_id` is omitted, the API creates a new document
- `document` must be a non-empty object
- every field in `document` must be explicitly allowed by the view model

For a single-document update, use:

- `POST /update/view/vulnitsm`

If you already know the document id and want it in the URL, use:

- `POST /update/view/vulnitsm/{document_id}`

For multiple ids, send an `updates` list and give each id its own `document`:

```json
{
  "updates": [
    {
      "document_id": "vuln-123",
      "upsert": true,
      "document": {
        "host.count": 4,
        "vulnerability.summary": "Kernel patch available"
      }
    },
    {
      "document_id": "vuln-456",
      "upsert": false,
      "document": {
        "organization.id": "ORG-2",
        "host.ip": "10.10.1.15"
      }
    }
  ]
}
```

Example cURL:

```bash
curl -X POST "http://localhost:8001/api/v2/write/view/vulnitsm" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "vuln-123",
    "upsert": true,
    "document": {
      "host.ip": "10.10.1.14",
      "host.count": 3,
      "organization.id": "ORG-1",
      "ticket.system": "ServiceNow",
      "vulnerability.summary": "Kernel patch missing"
    }
  }'
```

Example response:

```json
{
  "view": "vulnitsm",
  "action": "write",
  "document_id": "vuln-123",
  "result": "updated",
  "written_fields": [
    "host.count",
    "host.ip",
    "organization.id",
    "ticket.system",
    "vulnerability.summary"
  ],
  "allowed_fields": [
    "event.provider",
    "event.updated",
    "host.count",
    "host.hostname",
    "host.id",
    "host.ip",
    "host.name",
    "host.state",
    "organization.contract.id",
    "organization.id",
    "organization.name",
    "ticket.system",
    "vulnerability.asi_severity",
    "vulnerability.changeType",
    "vulnerability.cisa.ransomware_use",
    "vulnerability.cvss_v3.base_score",
    "vulnerability.cvss_v3.base_severity",
    "vulnerability.cwes",
    "vulnerability.id",
    "vulnerability.last_update",
    "vulnerability.nist.base_score",
    "vulnerability.nist.base_severity",
    "vulnerability.publish_date",
    "vulnerability.source.cisa",
    "vulnerability.source.created_date",
    "vulnerability.source.cve",
    "vulnerability.source.enabled_vendor",
    "vulnerability.source.updated_date",
    "vulnerability.source.vendor",
    "vulnerability.summary",
    "vulnerability.url",
    "file.size"
  ],
  "client": "client-1"
}
```

Example update by id:

```bash
curl -X POST "http://localhost:8001/api/v2/update/view/vulnitsm/vuln-123" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "upsert": true,
    "document": {
      "host.count": 4,
      "vulnerability.summary": "Kernel patch available"
    }
  }'
```

Example update with multiple ids:

```bash
curl -X POST "http://localhost:8001/api/v2/update/view/vulnitsm" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "updates": [
      {
        "document_id": "vuln-123",
        "upsert": true,
        "document": {
          "host.count": 4,
          "vulnerability.summary": "Kernel patch available"
        }
      },
      {
        "document_id": "vuln-456",
        "upsert": false,
        "document": {
          "organization.id": "ORG-2",
          "host.ip": "10.10.1.15"
        }
      }
    ]
  }'
```

Example bulk response:

```json
{
  "view": "vulnitsm",
  "action": "update",
  "count": 2,
  "results": [
    {
      "document_id": "vuln-123",
      "result": "updated",
      "written_fields": ["host.count", "vulnerability.summary"]
    },
    {
      "document_id": "vuln-456",
      "result": "updated",
      "written_fields": ["host.ip", "organization.id"]
    }
  ],
  "allowed_fields": ["host.count", "host.ip", "organization.id", "vulnerability.summary"],
  "client": "client-1"
}
```

Rules for the path-id update endpoint:

- the `document_id` comes from the URL
- the body may omit `document_id`
- if the body also sends `document_id`, it must match the URL value

Rules for the body update endpoint:

- for one document, send `document_id` and `document`
- for multiple documents, send `updates`
- each item in `updates` must contain its own `document_id` and `document`
- do not mix single-update fields with `updates` in the same request

## Writable Fields

Writable fields are defined in code on the view models using `WRITABLE_FIELDS`.
The API collects them from the selected model and all inherited parent models.

For `vulnitsm`, the current writable fields are:

- `event.provider`
- `event.updated`
- `file.size`
- `host.count`
- `host.hostname`
- `host.id`
- `host.ip`
- `host.name`
- `host.state`
- `organization.contract.id`
- `organization.id`
- `organization.name`
- `ticket.system`
- `vulnerability.asi_severity`
- `vulnerability.changeType`
- `vulnerability.cisa.ransomware_use`
- `vulnerability.cvss_v3.base_score`
- `vulnerability.cvss_v3.base_severity`
- `vulnerability.cwes`
- `vulnerability.id`
- `vulnerability.last_update`
- `vulnerability.nist.base_score`
- `vulnerability.nist.base_severity`
- `vulnerability.publish_date`
- `vulnerability.source.cisa`
- `vulnerability.source.created_date`
- `vulnerability.source.cve`
- `vulnerability.source.enabled_vendor`
- `vulnerability.source.updated_date`
- `vulnerability.source.vendor`
- `vulnerability.summary`
- `vulnerability.url`

Write validation rules:

- use alias names like `host.ip`, not internal Python field names
- unknown fields fail with `400 Bad Request`
- known but non-writable fields fail with `400 Bad Request`
- values are validated against the model field type before write
- path-id updates fail with `400 Bad Request` if path and body ids do not match

## Supported Operators

### Exact value

```json
{"ticket.system": "ServiceNow"}
```

### `in`

```json
{"organization.id": {"in": ["ORG-1", "ORG-2"]}}
```

You can also use a plain list:

```json
{"organization.id": ["ORG-1", "ORG-2"]}
```

### `neq` / `not_eq`

```json
{"file.size": {"neq": 0}}
```

### `not_in`

```json
{"organization.id": {"not_in": ["ORG-1", "ORG-2"]}}
```

### Range

```json
{"vulnerability.cvss_v3.base_score": {"gte": 7, "lte": 10}}
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

### `match_phrase`

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

### `starts_with`

```json
{"host.hostname": {"starts_with": "srv-"}}
```

### `ends_with`

```json
{"host.hostname": {"ends_with": ".prod"}}
```

### `exists`

```json
{"host.hostname": {"exists": true}}
```

or:

```json
{"host.hostname": {"exists": false}}
```

## Examples

### Example 1: Basic query

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

### Example 2: Text search with OR conditions

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

### Example 3: Mixed filtering

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

## Example cURL

```bash
curl -X POST "http://localhost:8001/api/v2/search/view/vulnitsm" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "select": ["host.ip", "vulnerability.summary"],
    "page": 0,
    "size": 10,
    "sort": ["host.ip", "-_score"],
    "where": {
      "all": [
        {"vulnerability.summary": {"match": "kernel"}},
        {"organization.id": {"in": ["ORG-1", "ORG-2"]}}
      ],
      "not": [
        {"host.hostname": {"exists": false}}
      ]
    }
  }'
```

## Response Structure

Example response:

```json
{
  "view": "vulnitsm",
  "count": 2,
  "data": [
    {
      "host.ip": "10.10.1.14",
      "vulnerability.summary": "Kernel issue"
    },
    {
      "host.ip": "10.10.1.15",
      "vulnerability.summary": "Kernel patch missing"
    }
  ],
  "pagination": {
    "page": 0,
    "size": 10,
    "offset": 0,
    "returned": 2,
    "total": 124
  },
  "client": "client-1"
}
```

Meaning:

- `view` is the selected view
- `count` is the number of items in this page
- `data` is the current page of records
- `pagination.total` is the total number of matched records
- `pagination.returned` is the number of items in this response

## Common Errors

### `400 Bad Request`

Usually means:

- field name is invalid
- operator is unsupported
- sort format is invalid
- a range or `exists` value is malformed
- a write field is unknown
- a write field is not allowed
- a write value has the wrong type

### `401 Unauthorized`

Usually means:

- token is missing
- token is invalid
- client record is missing

### `403 Forbidden`

Usually means:

- the client is not active
- the client does not have permission for the requested view

## Notes For API Consumers

- use field aliases like `host.ip` and `vulnerability.summary`
- prefer the simple request format instead of raw `filters`
- use `match` for text search and `in` for exact multi-value filters
- use `page` and `size` for paging instead of requesting everything at once
- use `select` to keep the response small
- for writes, only send fields that are part of the writable allowlist

## Related Docs

- root app guide: `README.md`
- query internals and advanced notes: `es_query_coverter/README.md`
