from dataclasses import dataclass

from src.backend.config import Settings
from src.backend.services.arm_service import ArmService
from src.backend.services.board_program_runner import ProgramRunner, SubprocessProgramRunner
from src.backend.services.calibration_service import CalibrationService
from src.backend.services.camera_service import (
    CameraBackend,
    CameraService,
    OpenCVCameraBackend,
    StaticCameraBackend,
)
from src.backend.services.event_bus import EventBus
from src.backend.services.inventory_service import InventoryService
from src.backend.services.system_service import SystemService
from src.backend.services.task_service import TaskService
from src.backend.services.vision_service import VisionService


@dataclass
class Services:
    settings: Settings
    event_bus: EventBus
    arm: ArmService
    calibration: CalibrationService
    vision: VisionService
    camera: CameraService
    inventory: InventoryService
    tasks: TaskService
    system: SystemService


def create_services(
    settings: Settings,
    program_runner: ProgramRunner | None = None,
    camera_backend: CameraBackend | None = None,
) -> Services:
    event_bus = EventBus()
    if settings.program_mode == "board" and program_runner is None:
        program_runner = SubprocessProgramRunner(robot_arm_root=settings.robot_arm_root)
    arm = ArmService(event_bus)
    calibration = CalibrationService(settings.camera_width, settings.camera_height)
    vision = VisionService(settings)
    inventory = InventoryService(event_bus)
    camera: CameraService | None = None

    def camera_in_use() -> bool:
        return camera.preview_active() if camera is not None else False

    tasks = TaskService(event_bus, settings, program_runner, camera_in_use=camera_in_use)
    camera = CameraService(
        settings,
        event_bus,
        active_task_id=tasks.active_task_id,
        backend=camera_backend
        or (OpenCVCameraBackend() if settings.program_mode == "board" else StaticCameraBackend()),
    )
    system = SystemService(settings, arm, calibration, tasks, camera)
    return Services(
        settings=settings,
        event_bus=event_bus,
        arm=arm,
        calibration=calibration,
        vision=vision,
        camera=camera,
        inventory=inventory,
        tasks=tasks,
        system=system,
    )
