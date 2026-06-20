import os
from datetime import datetime, timedelta, timezone
from typing import Any, cast

from jose import jwt
from passlib.context import CryptContext


def _load_access_token_expire() -> int:
    raw_value = os.getenv("ACCESS_TOKEN_EXPIRE", "30")

    try:
        return int(raw_value)
    except ValueError as exc:
        raise RuntimeError(
            "ACCESS_TOKEN_EXPIRE must be an integer number of minutes"
        ) from exc


ACCESS_TOKEN_EXPIRE = _load_access_token_expire()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_secret(secret: str) -> str:
    return cast(str, pwd_context.hash(secret))


def verify_secret(plain: str, hashed: str) -> bool:
    return cast(bool, pwd_context.verify(plain, hashed))


def _require_secret_key() -> str:
    if not SECRET_KEY:
        raise RuntimeError("SECRET_KEY must be set to create or decode JWTs")
    return SECRET_KEY


def create_access_token(data: dict) -> Any:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, _require_secret_key(), algorithm=ALGORITHM)


def decode_token(token: str) -> Any:
    return jwt.decode(token, _require_secret_key(), algorithms=[ALGORITHM])
