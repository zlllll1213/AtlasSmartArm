from typing import Protocol


class Detector(Protocol):
    """Vision detector boundary for future OpenCV/OM model implementations."""

    def detect(self, frame: object) -> list[dict[str, object]]:
        ...
