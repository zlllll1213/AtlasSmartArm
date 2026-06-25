from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from src.backend.models.enums import MaterialCategory


class BBoxNorm(BaseModel):
    cx: float = Field(ge=0, le=1)
    cy: float = Field(ge=0, le=1)
    w: float = Field(gt=0, le=1)
    h: float = Field(gt=0, le=1)


class PixelCenter(BaseModel):
    x_px: int = Field(ge=0)
    y_px: int = Field(ge=0)


class ArmPosition(BaseModel):
    x_m: float
    y_m: float
    z_m: float


class ArmPose(BaseModel):
    x_m: float
    y_m: float
    z_m: float
    roll_rad: float
    pitch_rad: float
    yaw_rad: float


class JointAngles(BaseModel):
    joint1_deg: float
    joint2_deg: float
    joint3_deg: float
    joint4_deg: float
    joint5_deg: float
    joint6_deg: float


class VisionDetectRequest(BaseModel):
    source: Literal["camera", "sample"] = "camera"
    camera_index: int = 0
    save_frame: bool = False


class CameraCaptureRequest(BaseModel):
    label: str | None = Field(default=None, min_length=1, max_length=80)

    model_config = ConfigDict(extra="forbid")


class FKRequest(BaseModel):
    joints: JointAngles


class IKRequest(BaseModel):
    pose: ArmPose


class MoveTarget(BaseModel):
    type: Literal["joints", "pose"]
    joints: JointAngles | None = None
    pose: ArmPose | None = None


class MoveRequest(BaseModel):
    target: MoveTarget
    duration_ms: int = 1000
    dry_run: bool = False


class TaskTarget(BaseModel):
    mode: Literal["auto_detect", "manual_select"] = "auto_detect"
    labels: list[str] = Field(default_factory=list)


class PickDestination(BaseModel):
    type: Literal["category_bin", "location"] = "category_bin"
    category: MaterialCategory = MaterialCategory.unknown


class TaskOptions(BaseModel):
    dry_run: bool = False
    max_retry: int = Field(default=1, ge=0, le=5)


class PickSortRequest(BaseModel):
    target: TaskTarget
    destination: PickDestination
    options: TaskOptions = Field(default_factory=TaskOptions)


class StackSpec(BaseModel):
    slot_id: str
    max_layers: int = Field(default=3, ge=1, le=8)


class StackRequest(BaseModel):
    target: TaskTarget
    stack: StackSpec
    options: TaskOptions = Field(default_factory=TaskOptions)


class InventoryLocation(BaseModel):
    area: str
    shelf: str
    slot: str


class InventoryItemCreate(BaseModel):
    name: str = Field(min_length=1)
    category: MaterialCategory
    label: str = Field(min_length=1)
    quantity: int = Field(default=0, ge=0)
    location: InventoryLocation


class InventoryItemUpdate(BaseModel):
    name: str | None = None
    category: MaterialCategory | None = None
    label: str | None = None
    quantity: int | None = Field(default=None, ge=0)
    location: InventoryLocation | None = None


class StockMovementRequest(BaseModel):
    item_id: str
    quantity: int = Field(gt=0)
    operator: str = Field(min_length=1)
    reason: str = Field(min_length=1)


class AuditRequest(BaseModel):
    item_id: str
    counted_quantity: int = Field(ge=0)
    operator: str = Field(min_length=1)
    reason: str = Field(min_length=1)


class CalibrationOffsetRequest(BaseModel):
    x_offset_m: float = Field(ge=-0.05, le=0.05)
    y_offset_m: float = Field(ge=-0.05, le=0.05)
    reason: str = Field(min_length=1)

    model_config = ConfigDict(extra="forbid")
