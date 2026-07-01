from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
import json
import threading
from typing import Any

try:
    import redis
except Exception:  # pragma: no cover - optional dependency path
    redis = None


@dataclass
class ConversationState:
    session_id: str
    current_run_id: str | None = None
    current_step_id: str | None = None
    current_incident_id: str | None = None
    current_ticket_id: str | None = None
    current_evidence_ids: list[str] = field(default_factory=list)
    last_intent: str | None = None
    last_answer_summary: str | None = None
    last_updated_at: str | None = None


class ConversationStateStore:
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        ttl_seconds: int = 3600,
        use_redis: bool = True,
    ) -> None:
        self._redis_url = redis_url
        self._ttl_seconds = ttl_seconds
        self._memory_store: dict[str, tuple[datetime, str]] = {}
        self._lock = threading.Lock()
        self._redis_client = None

        if use_redis and redis is not None:
            try:
                client = redis.Redis.from_url(redis_url, decode_responses=True)
                client.ping()
                self._redis_client = client
            except Exception:
                self._redis_client = None

    @property
    def backend_name(self) -> str:
        return "redis" if self._redis_client is not None else "memory"

    def load(self, session_id: str) -> ConversationState:
        if self._redis_client is not None:
            return self._load_from_redis(session_id)
        return self._load_from_memory(session_id)

    def save(self, state: ConversationState) -> ConversationState:
        payload = json.dumps(asdict(state))
        if self._redis_client is not None:
            key = self._key(state.session_id)
            self._redis_client.setex(key, self._ttl_seconds, payload)
            return state

        expires_at = datetime.now(timezone.utc) + timedelta(seconds=self._ttl_seconds)
        with self._lock:
            self._memory_store[state.session_id] = (expires_at, payload)
        return state

    def update(self, session_id: str, **patch: Any) -> ConversationState:
        state = self.load(session_id)
        for key, value in patch.items():
            if hasattr(state, key):
                setattr(state, key, value)
        state.last_updated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        return self.save(state)

    def _load_from_redis(self, session_id: str) -> ConversationState:
        key = self._key(session_id)
        payload = self._redis_client.get(key)
        if not payload:
            return ConversationState(session_id=session_id)
        return self._deserialize(session_id, payload)

    def _load_from_memory(self, session_id: str) -> ConversationState:
        with self._lock:
            record = self._memory_store.get(session_id)
            if record is None:
                return ConversationState(session_id=session_id)
            expires_at, payload = record
            if expires_at <= datetime.now(timezone.utc):
                self._memory_store.pop(session_id, None)
                return ConversationState(session_id=session_id)
        return self._deserialize(session_id, payload)

    def _deserialize(self, session_id: str, payload: str) -> ConversationState:
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            return ConversationState(session_id=session_id)
        if not isinstance(data, dict):
            return ConversationState(session_id=session_id)
        return ConversationState(
            session_id=session_id,
            current_run_id=data.get("current_run_id"),
            current_step_id=data.get("current_step_id"),
            current_incident_id=data.get("current_incident_id"),
            current_ticket_id=data.get("current_ticket_id"),
            current_evidence_ids=list(data.get("current_evidence_ids") or []),
            last_intent=data.get("last_intent"),
            last_answer_summary=data.get("last_answer_summary"),
            last_updated_at=data.get("last_updated_at"),
        )

    def _key(self, session_id: str) -> str:
        return f"procedureguard:agent4:session:{session_id}"
