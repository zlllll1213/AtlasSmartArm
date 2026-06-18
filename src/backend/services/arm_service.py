from src.backend.errors import ApiError
from src.backend.models.enums import ArmState
from src.backend.models.schemas import ArmPose, JointAngles, MoveRequest
from src.backend.services.event_bus import EventBus


JOINT_RANGES_DEG = {
    "joint1_deg": (0.0, 180.0),
    "joint2_deg": (0.0, 180.0),
    "joint3_deg": (0.0, 180.0),
    "joint4_deg": (0.0, 180.0),
    "joint5_deg": (0.0, 270.0),
    "joint6_deg": (0.0, 180.0),
}


class ArmService:
    def __init__(self, event_bus: EventBus) -> None:
        self.state = ArmState.idle
        self.control_lock: str | None = None
        self.event_bus = event_bus

    def validate_joints(self, joints: JointAngles) -> None:
        values = joints.model_dump()
        for field, value in values.items():
            low, high = JOINT_RANGES_DEG[field]
            if not low <= value <= high:
                raise ApiError(
                    code="OUT_OF_RANGE",
                    message=f"{field} is outside the safe range.",
                    status_code=400,
                    details={"field": field, "min": low, "max": high},
                )

    def validate_pose(self, pose: ArmPose) -> None:
        workspace = {
            "x_m": (-0.25, 0.25),
            "y_m": (0.05, 0.35),
            "z_m": (0.0, 0.25),
            "roll_rad": (-3.1416, 3.1416),
            "pitch_rad": (0.0, 3.1416),
            "yaw_rad": (-3.1416, 3.1416),
        }
        values = pose.model_dump()
        for field, value in values.items():
            low, high = workspace[field]
            if not low <= value <= high:
                raise ApiError(
                    code="OUT_OF_RANGE",
                    message=f"{field} is outside the calibrated workspace.",
                    status_code=400,
                    details={"field": field, "min": low, "max": high},
                )

    def fk(self, joints: JointAngles) -> dict[str, object]:
        self.validate_joints(joints)
        values = joints.model_dump()
        # Mock FK keeps deterministic units for UI and contract testing. The
        # real adapter will call ROS2 and return the same public shape.
        x_m = round((values["joint1_deg"] - 90.0) / 1000.0 + 0.12, 4)
        y_m = round(values["joint2_deg"] / 500.0 + 0.02, 4)
        z_m = round(values["joint3_deg"] / 1000.0, 4)
        return {
            "pose": {
                "x_m": x_m,
                "y_m": y_m,
                "z_m": z_m,
                "roll_rad": 0.0,
                "pitch_rad": 1.57,
                "yaw_rad": 0.0,
            }
        }

    def ik(self, pose: ArmPose) -> dict[str, object]:
        self.validate_pose(pose)
        return {
            "joints": {
                "joint1_deg": 91.2,
                "joint2_deg": 72.4,
                "joint3_deg": 18.5,
                "joint4_deg": 58.9,
                "joint5_deg": 265.0,
                "joint6_deg": 30.0,
            },
            "reachable": True,
        }

    def move(self, request: MoveRequest) -> dict[str, object]:
        if not 100 <= request.duration_ms <= 3000:
            raise ApiError(
                code="OUT_OF_RANGE",
                message="duration_ms must be between 100 and 3000.",
                status_code=400,
                details={"field": "duration_ms", "min": 100, "max": 3000},
            )
        if self.state not in {ArmState.idle, ArmState.planning, ArmState.moving}:
            raise ApiError(
                code="DEVICE_OFFLINE",
                message="Arm is not ready for motion.",
                status_code=503,
                details={"arm_state": self.state},
            )
        if request.target.type == "joints":
            if request.target.joints is None:
                raise ApiError("INVALID_ARGUMENT", "joints target is required.", 400)
            self.validate_joints(request.target.joints)
        if request.target.type == "pose":
            if request.target.pose is None:
                raise ApiError("INVALID_ARGUMENT", "pose target is required.", 400)
            self.validate_pose(request.target.pose)

        if not request.dry_run:
            self.state = ArmState.moving
            self.event_bus.publish("arm.state.changed", {"state": self.state})
            self.state = ArmState.idle
            self.event_bus.publish("arm.state.changed", {"state": self.state})

        return {
            "accepted": True,
            "dry_run": request.dry_run,
            "validated": True,
            "duration_ms": request.duration_ms,
        }

    def emergency_stop(self) -> dict[str, object]:
        self.state = ArmState.stopped
        self.control_lock = None
        self.event_bus.publish("arm.fault.raised", {"state": self.state})
        return {"state": self.state, "message": "Emergency stop accepted."}
