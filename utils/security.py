import os
from datetime import datetime, timedelta
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

if not SECRET_KEY:
    # In production, this should fail early to prevent insecure defaults
    import logging

    logging.error("SECRET_KEY is not set in environment variables!")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_secret(secret: str) -> str:
    return cast(str, pwd_context.hash(secret))


def verify_secret(plain: str, hashed: str) -> bool:
    return cast(bool, pwd_context.verify(plain, hashed))


def create_access_token(data: dict) -> Any:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Any:
    return jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
