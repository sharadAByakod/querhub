# QueryHub

QueryHub is a FastAPI service that exposes view-based search and controlled write APIs
on top of Elasticsearch. It validates incoming query parameters and write payloads
against the view model, applies client authorization, executes the request, and returns
responses using the Elasticsearch field aliases.

## What The App Does

- exposes authenticated search endpoints under `/api/v2`
- exposes authenticated write endpoints under `/api/v2`
- authorizes access per client and per view
- validates sort fields, selected fields, and filter fields against the target view model
- validates write payload fields against model-defined allowlists
- compiles high-level query input into Elasticsearch query clauses
- fetches a single page of results and returns pagination metadata
- creates or updates documents using alias-based field names

## Current API Surface

Current endpoints:

```text
POST /api/v2/search/view/{view_name}
POST /api/v2/write/view/{view_name}
POST /api/v2/update/view/{view_name}
POST /api/v2/update/view/{view_name}/{document_id}
```

Currently supported view names:

- `vulnitsm`

The route is implemented in `routers/view_router.py` and is registered in `main.py`
with the `/api/v2` prefix.

## Project Layout

```text
config/                Runtime settings from environment variables
constants/             Enumerations for actions, indices, and views
database/              Elasticsearch client and fetch helpers
es_query_coverter/     Query models, parser, DSLs, and builder logic
model/                 Response/view Pydantic models
routers/               FastAPI route handlers
service/               Client lookup/update services
test/                  Query builder and route tests
utils/                 Authentication, authorization, and support helpers
```

## Requirements

- Python 3.12 recommended
- Elasticsearch reachable from the app
- client auth records in the `qh_client` index

Core dependencies are listed in `requirements.txt`, including:

- `fastapi`
- `uvicorn`
- `elasticsearch`
- `pydantic`
- `python-jose`

## Configuration

The app reads configuration from environment variables in `config/settings.py`.
Important values:

```text
LOG_LEVEL=INFO
ES_HOST=http://localhost:9200
ES_USER=elastic
ES_PASS=abc
ES_CA_PATH=ca.crt
ES_CLIENT_CERT=client.crt
ES_CLIENT_KEY=client.key
SECRET_KEY=<jwt-secret>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE=30
```

Notes:

- the Elasticsearch client is created on app startup
- TLS certificate paths default to local files, so set them explicitly if needed
- JWT decoding depends on `SECRET_KEY` and `ALGORITHM`

## Running Locally

Install dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Start the API:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

The service will be available at:

```text
http://localhost:8001/api/v2
```

## Authentication And Authorization

Every request to the view API uses Bearer token authentication.

Request flow:

1. `utils.auth_dependency.get_current_client()` reads the Bearer token.
2. `utils.security.decode_token()` extracts the `sub` claim.
3. `service.client_service.get_client()` loads the client from Elasticsearch.
4. `utils.authorization.authorize()` checks the client permission for the requested view.

If the client is missing, inactive, or unauthorized, the route returns `401` or `403`.

## Example Search Request

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
        {"organization.id": {"in": ["ORG-1", "ORG-2"]}},
        {"host.ip": {"starts_with": "10.10."}}
      ],
      "not": [
        {"host.hostname": {"exists": false}}
      ]
    }
  }'
```

Example response shape:

```json
{
  "view": "vulnitsm",
  "count": 10,
  "data": [
    {
      "host.ip": "10.10.1.14",
      "vulnerability.summary": "Kernel issue"
    }
  ],
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

## Example Write Request

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

Example response shape:

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

## Example Update Requests

Update using `document_id` in the body:

```bash
curl -X POST "http://localhost:8001/api/v2/update/view/vulnitsm" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "vuln-123",
    "upsert": true,
    "document": {
      "host.count": 4,
      "vulnerability.summary": "Kernel patch available"
    }
  }'
```

Update multiple ids, where each id has its own document:

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

Update using `document_id` in the path:

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

## Model-Based Write Allowlists

The write API does not accept arbitrary Elasticsearch fields.

Each model can declare a `WRITABLE_FIELDS` set using Elasticsearch field aliases:

```python
class HostModel(BaseModel):
    WRITABLE_FIELDS = {
        "host.hostname",
        "host.id",
        "host.ip",
        "host.name",
        "host.state",
    }
```

The route collects writable fields from the selected view model and its parent models.
That means a view like `vulnitsm` inherits writable fields from `OrgModel`,
`HostModel`, `VulnerabilityModel`, and `VulniqItsm`.

Write rules:

- send writable fields inside `document`
- use the Elasticsearch alias names such as `host.ip`
- unknown fields are rejected
- known but non-writable fields are rejected
- values are type-checked before Elasticsearch is called
- `/write/view/{view_name}` stays available as the generic create/update route
- `/update/view/{view_name}` accepts either one `document_id` or an `updates` list
- `/update/view/{view_name}/{document_id}` lets callers pass the id in the URL
- multi-id updates are sent to Elasticsearch in one bulk request

## Query Documentation

The query input format, supported operators, and advanced examples are documented in:

- `es_query_coverter/README.md`
- `docs/API_USAGE.md`

## Query Builder Explanation

The query builder is the layer that turns an API request into an Elasticsearch
query for the selected view.

In simple terms, it does five things:

1. reads the incoming request fields like `select`, `sort`, `page`, `size`, and `where`
2. validates that the requested fields exist on the view model
3. converts the high-level query operators into Elasticsearch clauses
4. builds the final `bool` query used for search
5. returns only the requested page of data with pagination metadata

What this means for API users:

- you do not need to send raw Elasticsearch JSON
- you can use the simpler `where.all` / `where.any` / `where.not` structure
- field names must match the API field aliases such as `host.ip` or `vulnerability.summary`
- unsupported fields or operators return validation errors before the query runs

Quick example:

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

This means:

- return only `host.ip` and `vulnerability.summary`
- search the first page with 10 results
- sort by `host.ip` ascending and score descending
- include records matching `kernel`
- keep only organization IDs `ORG-1` or `ORG-2`
- exclude records where `host.hostname` is missing

For the consumer-facing version of this documentation, use:

- `docs/API_USAGE.md`

## Development

Run the focused test suite:

```bash
python3 -m pytest -q test/test_es_query_builder.py test/test_view_router.py test/test_write_helpers.py
```

Run the full suite:

```bash
pytest -q
```
