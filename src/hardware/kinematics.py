from src.backend.models.schemas import ArmPose, JointAngles


def mock_inverse_kinematics(_pose: ArmPose) -> JointAngles:
    """Return a deterministic IK solution until ROS2 Kinemarics is connected."""
    return JointAngles(
        joint1_deg=91.2,
        joint2_deg=72.4,
        joint3_deg=18.5,
        joint4_deg=58.9,
        joint5_deg=265.0,
        joint6_deg=30.0,
    )
