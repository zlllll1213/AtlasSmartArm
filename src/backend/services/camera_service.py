from __future__ import annotations

import base64
import json
import re
import threading
import time
from pathlib import Path
from typing import Callable, Iterator, Protocol
from uuid import uuid4

from src.backend.config import Settings
from src.backend.errors import ApiError
from src.backend.services.event_bus import EventBus
from src.backend.time_utils import utc_now_iso


class CameraSession(Protocol):
    def read_jpeg(self) -> tuple[bytes, int, int]:
        ...

    def release(self) -> None:
        ...


class CameraBackend(Protocol):
    def open(self, *, index: int, width: int, height: int) -> CameraSession:
        ...


class OpenCVCameraSession:
    def __init__(self, *, index: int, width: int, height: int) -> None:
        try:
            import cv2  # type: ignore[import-not-found]
        except ImportError as exc:
            raise ApiError(
                "VISION_UNAVAILABLE",
                "OpenCV is not available on this backend.",
                503,
                {},
            ) from exc

        self._cv2 = cv2
        self._capture = cv2.VideoCapture(index)
        if not self._capture.isOpened():
            raise ApiError(
                "DEVICE_OFFLINE",
                "Camera device could not be opened.",
                503,
                {"camera_index": index},
            )
        self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    def read_jpeg(self) -> tuple[bytes, int, int]:
        ok, frame = self._capture.read()
        if not ok or frame is None:
            raise ApiError("VISION_UNAVAILABLE", "Camera frame could not be read.", 503, {})
        height, width = frame.shape[:2]
        ok, encoded = self._cv2.imencode(".jpg", frame)
        if not ok:
            raise ApiError("VISION_UNAVAILABLE", "Camera frame could not be encoded.", 503, {})
        return encoded.tobytes(), int(width), int(height)

    def release(self) -> None:
        self._capture.release()


class OpenCVCameraBackend:
    def open(self, *, index: int, width: int, height: int) -> CameraSession:
        return OpenCVCameraSession(index=index, width=width, height=height)


class StaticCameraSession:
    _JPEG = base64.b64decode(
        "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////"
        "2wBDAf//////////////////////////////////////////////////////////////////////////////////////wAARCAABAAEDASIAAhEBAxEB"
        "/8QAFQABAQAAAAAAAAAAAAAAAAAAAAX/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIQAxAAAAH/xAAUEAEAAAAAAAAAAAAAAAAAAAAA"
        "/9oACAEBAAEFAqf/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oACAEDAQE/ASP/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oACAECAQE/ASP/"
        "xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oACAEBAAY/Al//xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oACAEBAAE/IV//2gAMAwEAAgADAAAA"
        "EP/EABQRAQAAAAAAAAAAAAAAAAAAABD/2gAIAQMBAT8QH//EABQRAQAAAAAAAAAAAAAAAAAAABD/2gAIAQIBAT8QH//EABQQAQAAAAAA"
        "AAAAAAAAAAAAABD/2gAIAQEAAT8QH//Z"
    )

    def read_jpeg(self) -> tuple[bytes, int, int]:
        return self._JPEG, 1, 1

    def release(self) -> None:
        return None


class StaticCameraBackend:
    def open(self, *, index: int, width: int, height: int) -> CameraSession:
        return StaticCameraSession()


_SAFE_LABEL = re.compile(r"[^A-Za-z0-9_.-]+")
_CAPTURE_ID = re.compile(r"^cap_[A-Za-z0-9]{1,64}$")


class CameraService:
    def __init__(
        self,
        settings: Settings,
        event_bus: EventBus,
        active_task_id: Callable[[], str | None],
        backend: CameraBackend,
    ) -> None:
        self.settings = settings
        self.event_bus = event_bus
        self._active_task_id = active_task_id
        self._backend = backend
        self._lock = threading.RLock()
        self._session: CameraSession | None = None
        self._preview_clients = 0
        self._capture_dir = Path(settings.capture_dir)
        self._capture_dir.mkdir(parents=True, exist_ok=True)

    def preview_active(self) -> bool:
        with self._lock:
            return self._preview_clients > 0 and self._session is not None

    def status(self) -> dict[str, object]:
        with self._lock:
            return {
                "preview_active": self.preview_active(),
                "preview_clients": self._preview_clients,
                "capture_dir": str(self._capture_dir),
            }

    def preview_stream(self) -> Iterator[bytes]:
        self._ensure_camera_available()
        self._acquire_preview_client()
        return self._stream_frames()

    def capture(self, label: str | None = None) -> dict[str, object]:
        self._ensure_camera_available()
        jpeg, width, height = self._read_capture_frame()
        capture_id = f"cap_{uuid4().hex[:12]}"
        captured_at = utc_now_iso()
        display_label = (label or "unlabeled").strip() or "unlabeled"
        safe_label = _SAFE_LABEL.sub("_", display_label).strip("._-") or "unlabeled"
        file_name = f"{captured_at.replace(':', '').replace('-', '')}_{safe_label}_{capture_id}.jpg"
        image_path = self._capture_dir / file_name
        image_path.write_bytes(jpeg)
        metadata = {
            "capture_id": capture_id,
            "label": display_label,
            "file_name": file_name,
            "path": str(image_path),
            "width": width,
            "height": height,
            "captured_at": captured_at,
            "image_url": f"/api/v1/camera/captures/{capture_id}/image",
        }
        self._metadata_path(capture_id).write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self.event_bus.publish("camera.capture.created", metadata)
        return metadata

    def image_path_for(self, capture_id: str) -> Path:
        metadata_path = self._metadata_path(capture_id)
        if not metadata_path.exists():
            raise ApiError("NOT_FOUND", "Camera capture not found.", 404, {"capture_id": capture_id})
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        image_path = (self._capture_dir / metadata["file_name"]).resolve()
        if self._capture_dir.resolve() not in image_path.parents:
            raise ApiError("NOT_FOUND", "Camera capture not found.", 404, {"capture_id": capture_id})
        if not image_path.exists():
            raise ApiError("NOT_FOUND", "Camera capture image not found.", 404, {"capture_id": capture_id})
        return image_path

    def _ensure_camera_available(self) -> None:
        active_task_id = self._active_task_id()
        if self.settings.program_mode == "board" and active_task_id is not None:
            raise ApiError(
                "ARM_BUSY",
                "Camera preview and capture are disabled while a board task is running.",
                409,
                {"active_task_id": active_task_id},
            )

    def _acquire_preview_client(self) -> None:
        with self._lock:
            if self._session is None:
                self._session = self._backend.open(
                    index=self.settings.camera_index,
                    width=self.settings.camera_width,
                    height=self.settings.camera_height,
                )
            self._preview_clients += 1

    def _stream_frames(self) -> Iterator[bytes]:
        try:
            while True:
                try:
                    jpeg, _, _ = self._read_jpeg_locked()
                except StopIteration:
                    break
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n"
                    + f"Content-Length: {len(jpeg)}\r\n\r\n".encode("ascii")
                    + jpeg
                    + b"\r\n"
                )
                time.sleep(max(0.02, 1 / 15))
        finally:
            self._release_preview_client()

    def _read_capture_frame(self) -> tuple[bytes, int, int]:
        with self._lock:
            if self._session is not None:
                return self._session.read_jpeg()
            session = self._backend.open(
                index=self.settings.camera_index,
                width=self.settings.camera_width,
                height=self.settings.camera_height,
            )
            try:
                return session.read_jpeg()
            finally:
                session.release()

    def _read_jpeg_locked(self) -> tuple[bytes, int, int]:
        with self._lock:
            if self._session is None:
                raise StopIteration
            return self._session.read_jpeg()

    def _release_preview_client(self) -> None:
        with self._lock:
            self._preview_clients = max(0, self._preview_clients - 1)
            if self._preview_clients == 0 and self._session is not None:
                self._session.release()
                self._session = None

    def _metadata_path(self, capture_id: str) -> Path:
        if not _CAPTURE_ID.fullmatch(capture_id):
            raise ApiError("NOT_FOUND", "Camera capture not found.", 404, {"capture_id": capture_id})
        return self._capture_dir / f"{capture_id}.json"
