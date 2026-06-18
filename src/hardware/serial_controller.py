from src.backend.models.schemas import JointAngles


class SerialArmController:
    def move_joints(self, joints: JointAngles, duration_ms: int) -> None:
        """Placeholder for Arm_serial_servo_write6_array integration.

        The API layer never accepts servo IDs directly; this adapter is where
        low-level servo addressing will be introduced during hardware hookup.
        """
        _ = (joints, duration_ms)
