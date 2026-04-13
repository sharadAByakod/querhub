import time
from typing import Dict, List, Optional

from fastapi import HTTPException

RATE_LIMIT = 100
RATE_WINDOW = 60

rate_table: Dict[str, List[float]] = {}


def rate_limit(ip: str) -> None:
    now = time.time()

    if ip not in rate_table:
        rate_table[ip] = []

    rate_table[ip] = [t for t in rate_table[ip] if now - t < RATE_WINDOW]

    if len(rate_table[ip]) >= RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Too many requests")

    rate_table[ip].append(now)


def _csv_to_list(val: Optional[str]) -> Optional[List[str]]:
    if not val:
        return None
    return [x.strip() for x in val.split(",") if x.strip()]
