from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from constants.actions import Actions


class Client(BaseModel):
    client_id: str
    client_secrest: str
    permissions: Dict[str, List[str]] = Field(default_factory=dict)
    status: str = "pending"
    owner: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    last_used: Optional[datetime] = None


class ClientCreateRequest(BaseModel):
    owner: str
    permissions: Dict[str, List[Actions]]
