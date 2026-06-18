from fastapi.testclient import TestClient

from src.backend.app import create_app


client = TestClient(create_app())


def unwrap_ok(response, status_code: int = 200):
    assert response.status_code == status_code
    payload = response.json()
    assert payload["success"] is True
    assert payload["request_id"].startswith("req_")
    assert payload["error"] is None
    return payload["data"]


def unwrap_error(response, status_code: int, code: str):
    assert response.status_code == status_code
    payload = response.json()
    assert payload["success"] is False
    assert payload["request_id"].startswith("req_")
    assert payload["data"] is None
    assert payload["error"]["code"] == code
    return payload["error"]


def test_health_uses_unified_response_envelope():
    data = unwrap_ok(client.get("/api/v1/health"))

    assert data["service"] == "atlas-smart-arm-backend"
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"
    assert data["time"].endswith("Z")


def test_system_status_exposes_mock_hardware_boundaries():
    data = unwrap_ok(client.get("/api/v1/system/status"))

    assert data["atlas"]["online"] is True
    assert data["camera"]["width"] == 640
    assert data["camera"]["height"] == 480
    assert data["arm"]["state"] == "idle"
    assert data["calibration"]["ready"] is True


def test_vision_detection_returns_unit_explicit_coordinates():
    data = unwrap_ok(
        client.post(
            "/api/v1/vision/detect",
            json={"source": "camera", "camera_index": 0, "save_frame": False},
        )
    )

    detection = data["detections"][0]
    assert detection["category"] == "power_fitting"
    assert 0 <= detection["confidence"] <= 1
    assert "x_px" in detection["pixel_center"]
    assert "x_m" in detection["arm_position"]


def test_safe_move_rejects_duration_outside_safety_window():
    error = unwrap_error(
        client.post(
            "/api/v1/arm/move",
            json={
                "target": {
                    "type": "joints",
                    "joints": {
                        "joint1_deg": 90,
                        "joint2_deg": 80,
                        "joint3_deg": 50,
                        "joint4_deg": 50,
                        "joint5_deg": 265,
                        "joint6_deg": 30,
                    },
                },
                "duration_ms": 5000,
                "dry_run": True,
            },
        ),
        400,
        "OUT_OF_RANGE",
    )

    assert "duration_ms" in error["details"]["field"]


def test_task_lifecycle_advances_and_can_be_queried():
    created = unwrap_ok(
        client.post(
            "/api/v1/tasks/pick-sort",
            json={
                "target": {"mode": "auto_detect", "labels": ["insulator"]},
                "destination": {"type": "category_bin", "category": "power_fitting"},
                "options": {"dry_run": True, "max_retry": 1},
            },
        )
    )

    assert created["state"] == "queued"
    detail = unwrap_ok(client.get(f"/api/v1/tasks/{created['task_id']}"))
    assert detail["task_id"] == created["task_id"]
    assert detail["state"] in {
        "queued",
        "detecting",
        "planning",
        "moving",
        "verifying",
        "succeeded",
    }
    assert 0 <= detail["progress"] <= 1


def test_inventory_crud_and_stock_movement():
    item = unwrap_ok(
        client.post(
            "/api/v1/inventory/items",
            json={
                "name": "绝缘子",
                "category": "power_fitting",
                "label": "insulator",
                "quantity": 2,
                "location": {"area": "A", "shelf": "A-01", "slot": "A-01-03"},
            },
        )
    )

    inbound = unwrap_ok(
        client.post(
            "/api/v1/inventory/inbound",
            json={
                "item_id": item["item_id"],
                "quantity": 3,
                "operator": "tester",
                "reason": "contract test",
            },
        )
    )
    assert inbound["quantity"] == 5

    outbound = unwrap_ok(
        client.post(
            "/api/v1/inventory/outbound",
            json={
                "item_id": item["item_id"],
                "quantity": 4,
                "operator": "tester",
                "reason": "contract test",
            },
        )
    )
    assert outbound["quantity"] == 1
