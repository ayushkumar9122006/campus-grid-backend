from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

import bcrypt
from fastapi import Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from campus_grid.core.config import configs
from campus_grid.core.exceptions import AuthError

ALGORITHM = "HS256"


def get_password_hash(password: str) -> str:
    """Generate secure bcrypt password hash."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def create_access_token(subject: dict, expires_delta: Optional[timedelta] = None) -> Tuple[str, str]:
    """Create signed JWT access token and return token string and formatted expiry."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=configs.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = subject.copy()
    to_encode.update({"exp": int(expire.timestamp())})
    encoded_jwt = jwt.encode(to_encode, configs.SECRET_KEY, algorithm=ALGORITHM)
    expiration_datetime = expire.strftime(configs.DATETIME_FORMAT)
    return encoded_jwt, expiration_datetime


def decode_jwt(token: str) -> Optional[dict]:
    """Decode and validate JWT token signature and expiration."""
    try:
        decoded_token = jwt.decode(token, configs.SECRET_KEY, algorithms=[ALGORITHM])
        now_ts = int(datetime.now(timezone.utc).timestamp())
        if decoded_token.get("exp", 0) < now_ts:
            return None
        return decoded_token
    except (JWTError, Exception):
        return None


class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> Optional[str]:
        credentials: Optional[HTTPAuthorizationCredentials] = await super(JWTBearer, self).__call__(request)
        if credentials:
            if credentials.scheme != "Bearer":
                raise AuthError(detail="Invalid authentication scheme. Expected Bearer token.")
            payload = decode_jwt(credentials.credentials)
            if not payload:
                raise AuthError(detail="Invalid or expired access token.")
            return credentials.credentials
        else:
            raise AuthError(detail="Authorization credentials required.")
