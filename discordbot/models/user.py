from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    id: str
    nick: str
    status: str
    price: int
    buyer: Optional[str]
    reason_inactive: Optional[str]
    discord_channel_id: int
    created_at: str