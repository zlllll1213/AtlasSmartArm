from dataclasses import dataclass


@dataclass(frozen=True)
class ArmCartesianPosition:
    x_m: float
    y_m: float
    z_m: float


@dataclass(frozen=True)
class PixelToArmTransform:
    image_width_px: int
    image_height_px: int
    arm_x_min_m: float
    arm_x_max_m: float
    arm_y_min_m: float
    arm_y_max_m: float
    z_m: float
    x_offset_m: float = 0.0
    y_offset_m: float = 0.0

    def pixel_to_arm(self, *, pixel_x_px: int, pixel_y_px: int) -> ArmCartesianPosition:
        if not 0 <= pixel_x_px <= self.image_width_px:
            raise ValueError("pixel_x_px is outside image width")
        if not 0 <= pixel_y_px <= self.image_height_px:
            raise ValueError("pixel_y_px is outside image height")

        # Keep the unit conversion in one place: pixels are normalized first,
        # then mapped into the calibrated mechanical-arm workspace in meters.
        x_ratio = pixel_x_px / self.image_width_px
        y_ratio = pixel_y_px / self.image_height_px
        x_m = self.arm_x_min_m + (self.arm_x_max_m - self.arm_x_min_m) * x_ratio
        y_m = self.arm_y_min_m + (self.arm_y_max_m - self.arm_y_min_m) * y_ratio
        return ArmCartesianPosition(
            x_m=x_m + self.x_offset_m,
            y_m=y_m + self.y_offset_m,
            z_m=self.z_m,
        )
