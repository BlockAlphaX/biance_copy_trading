"""Authentication utilities for the web API."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Any, Dict, List, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

try:
    from jose import JWTError, jwt  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - fallback when python-jose is unavailable
    import base64
    import hashlib
    import hmac
    import json

    class JWTError(Exception):
        """Fallback JWT error when python-jose is not installed."""

    class _MiniJWT:
        """Minimal HS256 JWT implementation used as a fallback."""

        @staticmethod
        def _b64encode(data: bytes) -> str:
            return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")

        @staticmethod
        def _b64decode(data: str) -> bytes:
            padding = "=" * (-len(data) % 4)
            return base64.urlsafe_b64decode(data + padding)

        @classmethod
        def encode(cls, payload: Dict[str, Any], key: str, algorithm: str = "HS256") -> str:
            if algorithm != "HS256":
                raise JWTError(f"Unsupported algorithm: {algorithm}")
            header = {"alg": algorithm, "typ": "JWT"}
            header_segment = cls._b64encode(
                json.dumps(header, separators=(",", ":"), sort_keys=True).encode("utf-8")
            )
            payload_segment = cls._b64encode(
                json.dumps(payload, separators=(",", ":"), default=str).encode("utf-8")
            )
            signing_input = f"{header_segment}.{payload_segment}".encode("utf-8")
            signature = hmac.new(key.encode("utf-8"), signing_input, hashlib.sha256).digest()
            signature_segment = cls._b64encode(signature)
            return f"{header_segment}.{payload_segment}.{signature_segment}"

        @classmethod
        def decode(
            cls,
            token: str,
            key: str,
            algorithms: List[str],
            audience: Optional[str] = None,
            issuer: Optional[str] = None,
        ) -> Dict[str, Any]:
            try:
                header_segment, payload_segment, signature_segment = token.split(".")
            except ValueError as exc:
                raise JWTError("Invalid token format") from exc

            header_data = json.loads(cls._b64decode(header_segment).decode("utf-8"))
            algorithm = header_data.get("alg")
            if algorithm not in algorithms:
                raise JWTError("Unexpected signing algorithm")

            signing_input = f"{header_segment}.{payload_segment}".encode("utf-8")
            expected_signature = hmac.new(
                key.encode("utf-8"), signing_input, hashlib.sha256
            ).digest()
            provided_signature = cls._b64decode(signature_segment)
            if not hmac.compare_digest(expected_signature, provided_signature):
                raise JWTError("Signature verification failed")

            payload = json.loads(cls._b64decode(payload_segment).decode("utf-8"))

            if audience:
                aud_claim = payload.get("aud")
                if isinstance(aud_claim, list):
                    if audience not in aud_claim:
                        raise JWTError("Invalid audience")
                elif aud_claim != audience:
                    raise JWTError("Invalid audience")

            if issuer and payload.get("iss") != issuer:
                raise JWTError("Invalid issuer")

            return payload

    class _FallbackJWTModule:
        """Wrapper mimicking python-jose API."""

        @staticmethod
        def encode(payload: Dict[str, Any], key: str, algorithm: str = "HS256") -> str:
            return _MiniJWT.encode(payload, key, algorithm)

        @staticmethod
        def decode(
            token: str,
            key: str,
            algorithms: List[str],
            audience: Optional[str] = None,
            issuer: Optional[str] = None,
        ) -> Dict[str, Any]:
            return _MiniJWT.decode(token, key, algorithms, audience=audience, issuer=issuer)

    jwt = _FallbackJWTModule()


class AuthSettings(BaseSettings):
    """Runtime configuration for API authentication."""

    jwt_secret: str = Field(default="dev-secret-change-me", alias="JWT_SECRET")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    jwt_audience: Optional[str] = None
    jwt_issuer: str = "binance-copy-trading"

    model_config = SettingsConfigDict(
        env_prefix="API_",
        env_file=".env",
        env_file_encoding="utf-8",
    )


class TokenPayload(BaseModel):
    """Token payload representation."""

    sub: str
    exp: Optional[int] = None
    scopes: List[str] = Field(default_factory=list)
    iss: Optional[str] = None
    aud: Optional[str | List[str]] = None


@lru_cache(maxsize=1)
def get_auth_settings() -> AuthSettings:
    """Return cached authentication settings."""
    return AuthSettings()


security_scheme = HTTPBearer(auto_error=False)


def create_access_token(
    subject: str,
    *,
    expires_delta: Optional[timedelta] = None,
    scopes: Optional[List[str]] = None,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """Create a signed JWT for a subject."""
    settings = get_auth_settings()
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))

    payload: Dict[str, Any] = {
        "sub": subject,
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "iss": settings.jwt_issuer,
    }

    if settings.jwt_audience:
        payload["aud"] = settings.jwt_audience
    if scopes:
        payload["scopes"] = scopes
    if extra_claims:
        payload.update(extra_claims)

    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token


def _decode_token(token: str) -> TokenPayload:
    """Decode and validate a JWT, returning the payload."""
    settings = get_auth_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
        )
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        ) from exc

    try:
        token_payload = TokenPayload.model_validate(payload)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed authentication payload",
        ) from exc

    if token_payload.exp and datetime.now(timezone.utc).timestamp() > token_payload.exp:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token expired",
        )

    return token_payload


def reset_auth_settings_cache() -> None:
    """Clear cached auth settings (primarily for tests)."""
    get_auth_settings.cache_clear()


async def get_current_subject(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
) -> TokenPayload:
    """Resolve the authenticated subject from an Authorization header."""
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
        )
    return _decode_token(credentials.credentials)


def verify_token(token: str) -> TokenPayload:
    """Validate a raw JWT string."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
        )
    return _decode_token(token)
