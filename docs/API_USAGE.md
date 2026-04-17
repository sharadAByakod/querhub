# QueryHub API Usage Guide (Server-to-Server)

QueryHub is a high-performance, secure gateway for Elasticsearch. This guide explains how to authenticate, search, and update data using machine-to-machine (M2M) communication.

---

## 1. Authentication

QueryHub uses **Bearer Token Authentication (JWT)**. 

### **Step 1: Obtain a Token**
Your client server should first request a JWT from your identity provider (e.g., Auth0, Okta, or a custom internal service). 

### **Step 2: Include the Token in Requests**
All requests to QueryHub must include the `Authorization` header:

```bash
curl -X POST "https://queryhub.your-domain.com/api/v2/search/view/vulnitsm" \
  -H "Authorization: Bearer <your-jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{ ... }'
```

> **Note:** Tokens should be short-lived. Your client code should automatically refresh the token if QueryHub returns a `401 Unauthorized` status.

---

## 2. Searching Data

Search requests are sent to `/api/v2/search/view/{view_name}`.

### **The Recommended Query Shape**

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

### **Logical Groups (`where`)**
- `all`: All conditions must match (Elasticsearch `must`).
- `any`: At least one condition must match (Elasticsearch `should`).
- `not`: Conditions must NOT match (Elasticsearch `must_not`).

### **Supported Field Operators**

| Operator | Example | Description |
| :--- | :--- | :--- |
| **Scalar** | `{"ticket.system": "ServiceNow"}` | Exact match (`term`). |
| **`in`** | `{"org.id": {"in": ["A", "B"]}}` | Match any value in list (`terms`). |
| **`range`** | `{"score": {"gte": 7}}` | Supports `gte`, `gt`, `lte`, `lt`. |
| **`match`** | `{"summary": {"match": "kernel"}}` | Full-text search. |
| **`wildcard`** | `{"host": {"wildcard": "srv-*"}}` | Standard wildcard search. |
| **`exists`** | `{"host": {"exists": true}}` | Check if field exists. |
| **`starts_with`**| `{"ip": {"starts_with": "10."}}` | Prefix search. |
| **`contains`** | `{"name": {"contains": "prod"}}` | Match substring. |

---

## 3. Aggregating Data

Aggregation requests are sent to `/api/v2/aggs/view/{view_name}`. They allow you to calculate metrics (averages, sums) and buckets (terms, date histograms) while optionally filtering the dataset.

### **The Aggregation Request Shape**

```json
{
  "where": {
    "all": [{"organization.id": "ORG-1"}]
  },
  "aggs": {
    "terms": [
      {
        "field": "vulnerability.asi_severity",
        "name": "severity_counts",
        "size": 10
      }
    ],
    "metrics": [
      {
        "field": "vulnerability.cvss_v3.base_score",
        "name": "average_cvss",
        "type": "avg"
      }
    ],
    "date_histogram": [
      {
        "field": "event.updated",
        "name": "updates_over_time",
        "calendar_interval": "month"
      }
    ]
  }
}
```

### **Sub-Aggregations (Nesting)**

QueryHub supports nesting aggregations within buckets (like `terms`, `date_histogram`, or `range`). This allows you to calculate metrics for each bucket.

```json
{
  "aggs": {
    "terms": [
      {
        "field": "vulnerability.asi_severity",
        "name": "severity_buckets",
        "aggs": {
          "metrics": [
            {
              "field": "vulnerability.cvss_v3.base_score",
              "name": "avg_score",
              "type": "avg"
            }
          ]
        }
      }
    ]
  }
}
```

### **Supported Aggregation Types**

| Type | Fields | Description |
| :--- | :--- | :--- |
| **`terms`** | `field`, `name`, `size`, `order`, `aggs` | Group by exact values. |
| **`metrics`** | `field`, `name`, `type` | `avg`, `sum`, `min`, `max`, `cardinality`, `stats`, `value_count`. |
| **`date_histogram`** | `field`, `name`, `calendar_interval`, `format`, `aggs` | Bucket by time intervals. |
| **`range`** | `field`, `name`, `ranges`, `aggs` | Bucket by numeric ranges. |

---

## 4. Writing & Updating Data

QueryHub enforces **field-level allowlists**. You can only write to fields defined in the view's `WRITABLE_FIELDS` configuration.

### **Single Write (Create or Upsert)**
**Endpoint:** `POST /api/v2/write/view/{view_name}`

```json
{
  "document_id": "vuln-123",
  "upsert": true,
  "document": {
    "host.ip": "10.10.1.14",
    "vulnerability.summary": "Kernel patch missing"
  }
}
```

### **Single Update**
**Endpoints:** `POST /api/v2/update/view/{view_name}` or `POST /api/v2/update/view/{view_name}/{document_id}`

Use the body-id form when you want to send the id in JSON, or the path-id form when
the id is already part of the URL.

```json
{
  "document_id": "vuln-123",
  "upsert": true,
  "document": {
    "host.count": 4
  }
}
```

### **Bulk Update**
**Endpoint:** `POST /api/v2/update/view/{view_name}`

QueryHub sends this multi-document update to Elasticsearch as a single bulk request.

```json
{
  "updates": [
    {
      "document_id": "vuln-123",
      "upsert": true,
      "document": { "host.count": 4 }
    },
    {
      "document_id": "vuln-456",
      "upsert": false,
      "document": { "organization.id": "ORG-2" }
    }
  ]
}
```

---

## 5. Best Practices for Server Clients

1.  **Enforce Timeouts:** Your client should set a timeout (e.g., 5-10 seconds) for all QueryHub requests to prevent hanging connections.
2.  **Handle Rate Limiting:** If QueryHub returns `429 Too Many Requests`, your client should implement a backoff-and-retry strategy.
3.  **Validate Field Names:** Use the `allowed_fields` list returned in write responses to ensure your client is only sending authorized fields.
4.  **Pick The Right Update Shape:** Use body-id or path-id for one document, and `updates` for many documents.

---

## 6. Error Codes

| Status Code | Description |
| :--- | :--- |
| **200 OK** | Request successful. |
| **400 Bad Request** | Validation error (e.g., invalid field name, missing required parameter). |
| **401 Unauthorized** | Missing or invalid JWT token. |
| **403 Forbidden** | Client does not have permission for the requested View or Action. |
| **429 Too Many Requests** | Rate limit exceeded. |
| **500 Internal Server Error** | Unexpected server-side failure. |
