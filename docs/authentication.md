# VOLTEX Authentication

## 1. Strategy

* **Access tokens**: short-lived JWTs (15 minutes by default) signed with HS256.
* **Refresh tokens**: long-lived opaque tokens (14 days by default), stored server-side as `refresh_tokens.token_hash` (SHA-256 of the actual token). The raw token is returned to the client only at issuance/rotation.
* **Refresh rotation**: every `POST /api/v1/auth/refresh` issues a new refresh token and revokes the old one (`revoked_at = now()`, `replaced_by_id = new.id`). Reuse of a revoked token triggers global revocation of the user's session family (defense against token theft).
* **Logout**: revokes the supplied refresh token. Idempotent.
* **Password hashing**: bcrypt via `passlib[bcrypt]` at cost 12 (default).
* **Email normalization**: `citext` column + `email = email.strip().lower()` at the service layer.

## 2. JWT Claims

```json
{
  "sub": "<user_uuid>",
  "role": "promoter|supervisor|admin",
  "branch_id": "<branch_uuid>",
  "iat": 1700000000,
  "exp": 1700000900,
  "jti": "<random_uuid>",
  "iss": "voltex-backend",
  "aud": "voltex-mobile"
}
```

`jti` is required so logout/blacklist can revoke access tokens (stored in `revoked_access_tokens` if needed; not in v1 minimum scope — short TTL makes this acceptable).

## 3. Endpoints

| Endpoint | Auth | Notes |
|---|---|---|
| `POST /api/v1/auth/login` | none | Returns access+refresh |
| `POST /api/v1/auth/refresh` | none (needs refresh token) | Rotates refresh |
| `POST /api/v1/auth/logout` | bearer (access) + body refresh | Revokes refresh |
| `GET /api/v1/auth/me` | bearer | Returns user |

## 4. Password Policy

* Minimum 8 characters.
* Maximum 128 characters (bcrypt input limit).
* No other composition rules in v1.

## 5. Rate Limiting (future)

The login endpoint should be rate-limited per IP and per email. Out of scope for v1 backend but documented.

## 6. Future: Biometrics

* Biometric unlock is a *client-side* capability that unlocks an existing valid session after enrollment. It does NOT replace password authentication and does NOT verify attendance.
* The backend will support this via a `device_enrollment` table (not in v1).
* No biometric data is sent to or stored on the server.

## 7. Storage of Credentials

* Passwords NEVER stored in plaintext or reversible encryption.
* `password_hash` is the only field that holds credentials.
* Refresh tokens stored as SHA-256 hash only — the raw value is shown to the client once and never recoverable from the DB.

## 9. Configuration (`.env.example`)

```
JWT_SECRET=change-me-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=14
PASSWORD_HASH_ROUNDS=12
ENVIRONMENT=development
```