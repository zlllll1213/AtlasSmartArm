from dataclasses import dataclass, field
from itertools import count

from src.backend.time_utils import utc_now_iso


@dataclass
class EventBus:
    _events: list[dict[str, object]] = field(default_factory=list)
    _counter: count = field(default_factory=lambda: count(1))

    def publish(self, event_type: str, data: dict[str, object]) -> dict[str, object]:
        event = {
            "event_id": f"evt_{next(self._counter):012d}",
            "type": event_type,
            "time": utc_now_iso(),
            "data": data,
        }
        self._events.append(event)
        return event

    def latest(self, limit: int = 50) -> list[dict[str, object]]:
        return self._events[-limit:]
