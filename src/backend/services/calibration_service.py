from src.backend.models.schemas import CalibrationOffsetRequest
from src.backend.time_utils import utc_now_iso


class CalibrationService:
    def __init__(self, width: int = 640, height: int = 480) -> None:
        self.ready = True
        self.version = "calib_mock_20260618_001"
        self.x_offset_m = 0.008
        self.y_offset_m = 0.0
        self.width = width
        self.height = height
        self.updated_at = utc_now_iso()

    def status(self) -> dict[str, object]:
        return {
            "ready": self.ready,
            "version": self.version,
            "files": {"dp_bin": True, "xyt_config": True, "offset": True},
            "image": {"width": self.width, "height": self.height},
            "updated_at": self.updated_at,
        }

    def update_offset(self, request: CalibrationOffsetRequest) -> dict[str, object]:
        self.x_offset_m = request.x_offset_m
        self.y_offset_m = request.y_offset_m
        self.version = f"calib_mock_{utc_now_iso().replace(':', '').replace('-', '')}"
        self.updated_at = utc_now_iso()
        return {
            "version": self.version,
            "x_offset_m": self.x_offset_m,
            "y_offset_m": self.y_offset_m,
            "reason": request.reason,
            "updated_at": self.updated_at,
        }
