from dataclasses import dataclass

from src.backend.config import Settings
from src.backend.services.arm_service import ArmService
from src.backend.services.calibration_service import CalibrationService
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
    inventory: InventoryService
    tasks: TaskService
    system: SystemService


def create_services(settings: Settings) -> Services:
    event_bus = EventBus()
    arm = ArmService(event_bus)
    calibration = CalibrationService(settings.camera_width, settings.camera_height)
    vision = VisionService(settings)
    inventory = InventoryService(event_bus)
    tasks = TaskService(event_bus)
    system = SystemService(settings, arm, calibration)
    return Services(
        settings=settings,
        event_bus=event_bus,
        arm=arm,
        calibration=calibration,
        vision=vision,
        inventory=inventory,
        tasks=tasks,
        system=system,
    )
