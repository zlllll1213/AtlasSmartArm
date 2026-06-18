from src.backend.config import Settings
from src.backend.services.arm_service import ArmService
from src.backend.services.calibration_service import CalibrationService


class SystemService:
    def __init__(
        self,
        settings: Settings,
        arm_service: ArmService,
        calibration_service: CalibrationService,
    ) -> None:
        self.settings = settings
        self.arm_service = arm_service
        self.calibration_service = calibration_service

    def status(self) -> dict[str, object]:
        return {
            "atlas": {
                "online": self.settings.atlas_mock,
                "host": self.settings.atlas_host,
                "network": {
                    "iface": self.settings.atlas_net_iface,
                    "ip_address": self.settings.atlas_host,
                    "netmask": self.settings.atlas_netmask,
                    "gateway": self.settings.atlas_gateway,
                    "dns": [self.settings.atlas_dns_primary, self.settings.atlas_dns_secondary],
                },
                "os": "ubuntu-22.04",
                "npu_available": self.settings.atlas_mock,
            },
            "camera": {
                "online": self.settings.vision_mock,
                "index": self.settings.camera_index,
                "width": self.settings.camera_width,
                "height": self.settings.camera_height,
            },
            "arm": {
                "online": self.settings.arm_mock,
                "state": self.arm_service.state,
                "control_lock": self.arm_service.control_lock,
            },
            "vision": {"model_loaded": self.settings.vision_mock, "model_name": "yolov5s_bs1.om"},
            "calibration": {
                "ready": self.calibration_service.ready,
                "version": self.calibration_service.version,
            },
        }
