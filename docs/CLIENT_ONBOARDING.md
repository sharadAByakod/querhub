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

## 2. Generating a Bearer Token (JWT)

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

## 3. Using the Token

Once you have generated a token, include it in the `Authorization` header of every API request:

```text
Authorization: Bearer <your-generated-jwt-token>
```

---

## 4. Troubleshooting Access

If your token is rejected with a `403 Forbidden` error, verify that:
- Your `sub` claim exactly matches your registered Client ID.
- You are attempting to access a View that was included in your original access request.
- You have the correct permission (e.g., trying to `write` when you only have `read` access).
