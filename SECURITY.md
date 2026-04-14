# Security Architecture: QueryHub

QueryHub employs a multi-layered security model designed to protect Elasticsearch from unauthorized access and malicious querying.

## 1. Authentication (Identity)
The application uses **Bearer Token Authentication** powered by JWT (JSON Web Tokens).
- **Standards:** HS256/RS256 algorithms.
- **Verification:** Every request is decoded using a secure `SECRET_KEY`.
- **Identity Check:** The `sub` (subject) claim in the token must match a record in the `qh_client` Elasticsearch index.

## 2. Authorization (RBAC)
We implement strict **Role-Based Access Control** at two levels:
- **View Level:** Users can only query specific "Views" (e.g., `vulnitsm`) that are explicitly assigned to their client profile.
- **Action Level:** Separate permissions are required for `read` (search) and `write` (create/update) operations.

## 3. Defense-In-Depth (Gatekeeping)

### Field-Level Protection
The API never exposes raw Elasticsearch indices. Instead:
- **Query Allowlist:** Users can only search, sort, or select fields defined in the Pydantic model.
- **Write Allowlist:** Only fields listed in `WRITABLE_FIELDS` on the model can be modified. This prevents "Mass Assignment" attacks.

### Resource Protection (DoS Prevention)
- **Pagination Limits:** The API enforces a hard maximum `size` of **1000** records per request to prevent resource exhaustion on the ES cluster.
- **Rate Limiting:** Built-in middleware limits requests per IP (Default: 100 req / 60 sec) using a sliding window.
- **Query Validation:** Wildcard queries are validated against known fields before execution.

## 4. Operational Security
- **Secure Transport:** Always deploy behind a TLS-terminating reverse proxy (Nginx, Traefik).
- **Credential Handling:** Secrets are managed via environment variables and should be injected using a secure secret manager (e.g., Kubernetes Secrets, AWS Vault) in production.
- **Audit Logs:** Security events (Auth failures, Permission denials) are logged with a severity of `WARNING` or `ERROR`.

## 5. Security Scanning
Run the following tools regularly:
- `pip-audit`: Scans dependencies for known vulnerabilities.
- `mypy`: Ensures type safety to prevent common coding errors.
- `pytest`: Validates that security logic (auth/authz) remains intact.
