from src.integration.coordinate_transform import PixelToArmTransform


def test_pixel_to_arm_transform_applies_scale_and_offset_with_units():
    transform = PixelToArmTransform(
        image_width_px=640,
        image_height_px=480,
        arm_x_min_m=-0.12,
        arm_x_max_m=0.12,
        arm_y_min_m=0.10,
        arm_y_max_m=0.34,
        z_m=0.0,
        x_offset_m=0.008,
        y_offset_m=-0.002,
    )

    position = transform.pixel_to_arm(pixel_x_px=320, pixel_y_px=240)

    assert round(position.x_m, 3) == 0.008
    assert round(position.y_m, 3) == 0.218
    assert position.z_m == 0.0
