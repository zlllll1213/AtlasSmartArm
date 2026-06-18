from src.backend.config import Settings
from src.backend.models.schemas import VisionDetectRequest
from src.integration.coordinate_transform import PixelToArmTransform


class VisionService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.transform = PixelToArmTransform(
            image_width_px=settings.camera_width,
            image_height_px=settings.camera_height,
            arm_x_min_m=-0.12,
            arm_x_max_m=0.12,
            arm_y_min_m=0.10,
            arm_y_max_m=0.34,
            z_m=0.0,
            x_offset_m=0.008,
            y_offset_m=0.0,
        )

    def detect(self, request: VisionDetectRequest) -> dict[str, object]:
        center = {"x_px": 326, "y_px": 226}
        position = self.transform.pixel_to_arm(
            pixel_x_px=center["x_px"], pixel_y_px=center["y_px"]
        )
        return {
            "frame_id": "frame_mock_20260618_000001",
            "image": {
                "width": self.settings.camera_width,
                "height": self.settings.camera_height,
            },
            "detections": [
                {
                    "object_id": "det_mock_001",
                    "label": "insulator",
                    "category": "power_fitting",
                    "confidence": 0.93,
                    "bbox_norm": {"cx": 0.51, "cy": 0.47, "w": 0.12, "h": 0.10},
                    "pixel_center": center,
                    "arm_position": {
                        "x_m": round(position.x_m, 4),
                        "y_m": round(position.y_m, 4),
                        "z_m": position.z_m,
                    },
                }
            ],
        }
