from dataclasses import dataclass
import os
from typing import Literal


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def _program_mode(value: str | None) -> Literal["mock", "board"]:
    return "board" if value == "board" else "mock"


@dataclass(frozen=True)
class Settings:
    app_env: str = os.getenv("APP_ENV", "development")
    app_port: int = int(os.getenv("APP_PORT", "8080"))
    app_version: str = "0.1.0"
    atlas_net_iface: str = os.getenv("ATLAS_NET_IFACE", "ETH1")
    atlas_host: str = os.getenv("ATLAS_HOST", "192.168.137.100")
    atlas_netmask: str = os.getenv("ATLAS_NETMASK", "255.255.255.0")
    atlas_gateway: str | None = os.getenv("ATLAS_GATEWAY") or None
    atlas_dns_primary: str = os.getenv("ATLAS_DNS_PRIMARY", "8.8.8.8")
    atlas_dns_secondary: str = os.getenv("ATLAS_DNS_SECONDARY", "114.114.114.114")
    camera_index: int = int(os.getenv("CAMERA_INDEX", "0"))
    camera_width: int = int(os.getenv("CAMERA_WIDTH", "640"))
    camera_height: int = int(os.getenv("CAMERA_HEIGHT", "480"))
    vision_model_path: str = os.getenv(
        "VISION_MODEL_PATH", "/opt/atlas-smart-arm/models/yolov5s_bs1.om"
    )
    calibration_dir: str = os.getenv(
        "CALIBRATION_DIR", "/opt/atlas-smart-arm/calibration"
    )
    capture_dir: str = os.getenv("CAPTURE_DIR", "data/captures")
    program_mode: Literal["mock", "board"] = _program_mode(os.getenv("PROGRAM_MODE"))
    robot_arm_root: str = os.getenv(
        "ROBOT_ARM_ROOT",
        "/home/HwHiAiUser/E2ESamples/src/E2E-Sample/ros2_robot_arm",
    )
    atlas_mock: bool = _as_bool(os.getenv("ATLAS_MOCK"), True)
    vision_mock: bool = _as_bool(os.getenv("VISION_MOCK"), True)
    arm_mock: bool = _as_bool(os.getenv("ARM_MOCK"), True)


def get_settings() -> Settings:
    return Settings()
