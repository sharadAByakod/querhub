# Client Onboarding: Access & Token Generation

This guide explains how to gain access to QueryHub and how to generate the Bearer Token (JWT) required for API communication.

---

## 1. Requesting Access (Registration)

To register a new client or service with QueryHub, you must **request access from the ASI Team**. 

Please provide the following information in your request:
- **Client ID:** A unique name for your service (e.g., `service-inventory-prod`).
- **Owner:** The team or individual responsible for the client.
- **Requested Views:** Which data views you need to access (e.g., `vulnitsm`).
- **Permissions:** Whether you need `read` access, `write` access, or both.

Once the ASI Team approves your request, your Client ID will be activated in the system.

---

## 2. Elasticsearch Client Record

QueryHub authenticates clients from an Elasticsearch document stored in the **`qh_client`** index.

### Index And Document ID

- **Index name:** `qh_client`
- **Document ID:** must be the same value as `client_id`

Example:

```text
Index: qh_client
Document ID: service-inventory-prod
```

If the Elasticsearch document ID and the `client_id` value do not match, token-based lookup can fail because QueryHub loads clients by document ID.

### Required Document Shape

Recommended document to add in Elasticsearch:

```json
{
  "client_id": "service-inventory-prod",
  "client_secret": "$2b$12$replace-with-bcrypt-hash",
  "permissions": {
    "vulnitsm": ["read", "write"]
  },
  "status": "active",
  "owner": "Inventory Platform",
  "created_at": "2026-06-20T10:30:00Z",
  "approved_by": "asi-team",
  "approved_at": "2026-06-20T10:30:00Z",
  "last_used": null
}
```

### Field / Column Details

| Field | Type | Required | Notes |
| :--- | :--- | :--- | :--- |
| `client_id` | `string` | Yes | Unique client name. Should also be used as the Elasticsearch document ID. |
| `client_secret` | `string` | Yes | Must be a **bcrypt hash**, not plain text. QueryHub verifies it using `bcrypt`. |
| `permissions` | `object` | Yes | Map of view name to allowed actions. Example: `{"vulnitsm": ["read", "write"]}` |
| `status` | `string` | Yes | Must be `active` for token generation to succeed. |
| `owner` | `string` | Recommended | Team or individual who owns the client. |
| `created_at` | `date` | Recommended | ISO-8601 timestamp for when the record was created. |
| `approved_by` | `string` | Optional | Approver name or team. |
| `approved_at` | `date` | Optional | ISO-8601 approval timestamp. |
| `last_used` | `date/null` | Optional | Updated by QueryHub after successful requests. You can leave this as `null` when onboarding. |

### Permissions Format

Use the view name as the key and lowercase actions in the value array.

Current recommended format:

```json
{
  "permissions": {
    "vulnitsm": ["read"]
  }
}
```

Notes:

- `read` allows search and aggregations.
- `write` allows write and update endpoints.
- `vulnitsm` is the current supported view name.

### Minimal Working Document

If you only want the minimum fields needed for a working client, this is enough:

```json
{
  "client_id": "service-inventory-prod",
  "client_secret": "$2b$12$replace-with-bcrypt-hash",
  "permissions": {
    "vulnitsm": ["read"]
  },
  "status": "active"
}
```

### Example Elasticsearch Insert

```http
PUT qh_client/_doc/service-inventory-prod
{
  "client_id": "service-inventory-prod",
  "client_secret": "$2b$12$replace-with-bcrypt-hash",
  "permissions": {
    "vulnitsm": ["read", "write"]
  },
  "status": "active",
  "owner": "Inventory Platform",
  "created_at": "2026-06-20T10:30:00Z",
  "approved_by": "asi-team",
  "approved_at": "2026-06-20T10:30:00Z",
  "last_used": null
}
```

### Hashing The Secret

Do not store the raw client password in Elasticsearch. Store the bcrypt hash.

If you need to generate a hash from the repo code, use the helper in `utils/security.py`:

```bash
python3 -c 'from utils.security import hash_secret; print(hash_secret("replace-with-plain-secret"))'
```

Copy the printed hash into the `client_secret` field.

---

## 3. Generating a Bearer Token (JWT)

QueryHub provides an automated endpoint to exchange your credentials for a short-lived access token.

**Endpoint:** `POST /api/v2/token`

### **Request Body**
```json
{
  "client_id": "your-client-id",
  "client_secret": "your-password"
}
```

### **Successful Response**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 30
}
```

> **Security Note:** You should only call this endpoint over a secure HTTPS connection. The `access_token` is valid for 30 minutes. Your application should be programmed to request a new token automatically if it receives a `401 Unauthorized` response.

---

## 4. Using the Token

Once you have generated a token, include it in the `Authorization` header of every API request:

```text
Authorization: Bearer <your-generated-jwt-token>
```

---

## 5. Troubleshooting Access

If your token is rejected with a `403 Forbidden` error, verify that:
- Your `sub` claim exactly matches your registered Client ID.
- You are attempting to access a View that was included in your original access request.
- You have the correct permission (e.g., trying to `write` when you only have `read` access).

If token generation fails with `401 Unauthorized`, verify that:
- The document exists in the `qh_client` index.
- The Elasticsearch document ID matches `client_id`.
- `status` is set to `active`.
- `client_secret` is stored as a bcrypt hash, not plain text.
