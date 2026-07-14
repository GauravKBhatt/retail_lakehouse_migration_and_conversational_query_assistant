import os
import json
from typing import List

import redis

MAX_TURNS = 10
TTL_SECONDS = 3600

_redis = redis.Redis(
    host=os.environ.get("REDIS_HOST", "localhost"),
    port=int(os.environ.get("REDIS_PORT", "6379")),
    decode_responses=True,
)


def _key(session_id: str) -> str:
    return f"chat:history:{session_id}"


def get_history(session_id: str) -> List[dict]:
    raw = _redis.lrange(_key(session_id), 0, -1)
    return [json.loads(m) for m in raw]


def save_history(session_id: str, messages: List[dict]) -> None:
    key = _key(session_id)
    _redis.delete(key)
    for msg in messages[-MAX_TURNS * 2:]:
        _redis.rpush(key, json.dumps(msg))
    _redis.expire(key, TTL_SECONDS)
