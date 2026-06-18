from typing import Protocol

from src.backend.models.schemas import ArmPose, JointAngles


class ArmAdapter(Protocol):
    """Stable hardware boundary hidden behind backend services.

    Real implementations must wrap ROS2, serial, and device exceptions before
    they cross into the API layer.
    """

    def solve_fk(self, joints: JointAngles) -> ArmPose:
        ...

    def solve_ik(self, pose: ArmPose) -> JointAngles:
        ...

    def move_joints(self, joints: JointAngles, duration_ms: int) -> None:
        ...
