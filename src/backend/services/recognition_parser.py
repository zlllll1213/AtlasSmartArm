from ast import literal_eval
from collections.abc import Iterable, Mapping, Sequence
from typing import Any


_LABEL_CATEGORIES = {
    "syringe": "hazardous",
    "used_batteries": "hazardous",
    "expired_cosmetics": "hazardous",
    "expired_tablets": "hazardous",
    "zip_top_can": "recyclable",
    "newspaper": "recyclable",
    "old_school_bag": "recyclable",
    "book": "recyclable",
    "fish_bone": "kitchen",
    "watermelon_rind": "kitchen",
    "apple_core": "kitchen",
    "egg_shell": "kitchen",
    "peach_pit": "kitchen",
    "cigarette_butts": "other",
    "toilet_paper": "other",
    "disposable_chopsticks": "other",
}


def category_for_label(label: str) -> str:
    return _LABEL_CATEGORIES.get(label.strip().lower(), "unknown")


def parse_recognition_log(line: str) -> list[dict[str, object]]:
    """Parse stable recognition logs emitted by the board default pick-sort program."""
    source, payload = _extract_payload(line)
    if source is None:
        return []
    try:
        parsed = literal_eval(payload)
    except (SyntaxError, ValueError):
        return []
    return [
        detection
        for detection in (
            _detection_from_item(label, position, source)
            for label, position in _iter_label_positions(parsed)
        )
        if detection is not None
    ]


def _extract_payload(line: str) -> tuple[str | None, str]:
    if "new msg is" in line:
        return "new_msg", line.split("new msg is", 1)[1].strip()
    if "msg is:" in line:
        return "msg", line.split("msg is:", 1)[1].strip()
    return None, ""


def _iter_label_positions(parsed: Any) -> Iterable[tuple[Any, Any]]:
    if isinstance(parsed, Mapping):
        return parsed.items()
    if isinstance(parsed, Sequence) and not isinstance(parsed, (str, bytes)):
        return (
            (item[0], item[1])
            for item in parsed
            if isinstance(item, Sequence)
            and not isinstance(item, (str, bytes))
            and len(item) >= 2
        )
    return []


def _detection_from_item(label: Any, position: Any, source: str) -> dict[str, object] | None:
    if not isinstance(label, str):
        return None
    if not isinstance(position, Sequence) or isinstance(position, (str, bytes)) or len(position) < 2:
        return None
    try:
        x_m = float(position[0])
        y_m = float(position[1])
    except (TypeError, ValueError):
        return None
    cleaned_label = label.strip()
    if not cleaned_label:
        return None
    return {
        "label": cleaned_label,
        "category": category_for_label(cleaned_label),
        "x_m": x_m,
        "y_m": y_m,
        "source": source,
    }
