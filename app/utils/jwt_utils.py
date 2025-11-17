from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import jwt

from app.config import settings


def create_jwt_token(
    payload: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT token with the provided payload.

    Args:
        payload: Data to encode inside the token.
        expires_delta: Optional custom expiration timedelta.

    Returns:
        Encoded JWT token as a string.
    """
    if expires_delta is None:
        expires_delta = timedelta(days=settings.JWT_EXPIRY_DAYS)

    now = datetime.now(timezone.utc)
    to_encode = payload.copy()
    to_encode.update(
        {
            "iat": now,
            "exp": now + expires_delta,
        }
    )

    token = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return token


def decode_jwt_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate a JWT token.

    Args:
        token: JWT token string.

    Returns:
        Decoded payload.
    """
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )

