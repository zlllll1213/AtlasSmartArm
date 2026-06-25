from fastapi.testclient import TestClient

from src.backend.app import create_app
from src.backend.config import Settings


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
    assert data["program_mode"] == "mock"
    assert data["active_task_id"] is None


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


class FakeProgramHandle:
    def __init__(self, exit_code=None) -> None:
        self.pid = 4242
        self.exit_code = exit_code
        self.interrupted = False

    def poll(self):
        return self.exit_code

    def interrupt(self) -> None:
        self.interrupted = True


class FakeProgramRunner:
    def __init__(self, exit_code=None, output_lines: list[str] | None = None) -> None:
        self.started: list[str] = []
        self.handle = FakeProgramHandle(exit_code=exit_code)
        self.output_lines = output_lines or ["default program started"]

    def start(self, program, on_output):
        self.started.append(program)
        for line in self.output_lines:
            on_output(line)
        return self.handle


class FailingProgramRunner:
    def start(self, program, on_output):
        raise RuntimeError("ros2 launch failed")


class FakeCameraSession:
    def __init__(self, *, stop_after_first_frame: bool = False) -> None:
        self.released = False
        self.read_count = 0
        self.stop_after_first_frame = stop_after_first_frame

    def read_jpeg(self):
        if self.stop_after_first_frame and self.read_count >= 1:
            raise StopIteration
        self.read_count += 1
        return b"\xff\xd8fake-jpeg\xff\xd9", 320, 240

    def release(self) -> None:
        self.released = True


class FakeCameraBackend:
    def __init__(self, *, stop_after_first_frame: bool = False) -> None:
        self.open_calls: list[tuple[int, int, int]] = []
        self.session = FakeCameraSession(stop_after_first_frame=stop_after_first_frame)

    def open(self, *, index: int, width: int, height: int):
        self.open_calls.append((index, width, height))
        return self.session


def test_board_mode_pick_sort_starts_default_ros_program():
    runner = FakeProgramRunner()
    board_client = TestClient(
        create_app(Settings(program_mode="board"), program_runner=runner)
    )

    created = unwrap_ok(
        board_client.post(
            "/api/v1/tasks/pick-sort",
            json={
                "target": {"mode": "auto_detect", "labels": ["insulator"]},
                "destination": {"type": "category_bin", "category": "power_fitting"},
                "options": {"dry_run": False, "max_retry": 1},
            },
        )
    )
    detail = unwrap_ok(board_client.get(f"/api/v1/tasks/{created['task_id']}"))

    assert runner.started == ["pick_sort_default"]
    assert detail["program"] == "pick_sort_default"
    assert detail["pid"] == 4242
    assert detail["started_at"].endswith("Z")
    assert detail["ended_at"] is None
    assert detail["exit_code"] is None
    assert detail["logs"] == ["default program started"]


def test_board_mode_stack_starts_default_ros_program():
    runner = FakeProgramRunner()
    board_client = TestClient(
        create_app(Settings(program_mode="board"), program_runner=runner)
    )

    created = unwrap_ok(
        board_client.post(
            "/api/v1/tasks/stack",
            json={
                "target": {"mode": "auto_detect", "labels": ["red_block"]},
                "stack": {"slot_id": "stack_area_01", "max_layers": 3},
                "options": {"dry_run": False, "max_retry": 1},
            },
        )
    )
    detail = unwrap_ok(board_client.get(f"/api/v1/tasks/{created['task_id']}"))

    assert runner.started == ["stack_default"]
    assert detail["program"] == "stack_default"
    assert detail["pid"] == 4242


def test_board_mode_rejects_second_running_task():
    runner = FakeProgramRunner()
    board_client = TestClient(
        create_app(Settings(program_mode="board"), program_runner=runner)
    )
    unwrap_ok(
        board_client.post(
            "/api/v1/tasks/pick-sort",
            json={
                "target": {"mode": "auto_detect", "labels": ["insulator"]},
                "destination": {"type": "category_bin", "category": "power_fitting"},
                "options": {"dry_run": False, "max_retry": 1},
            },
        )
    )

    error = unwrap_error(
        board_client.post(
            "/api/v1/tasks/stack",
            json={
                "target": {"mode": "auto_detect", "labels": ["red_block"]},
                "stack": {"slot_id": "stack_area_01", "max_layers": 3},
                "options": {"dry_run": False, "max_retry": 1},
            },
        ),
        409,
        "ARM_BUSY",
    )

    assert error["details"]["active_task_id"] == "task_000000000001"


def test_board_mode_maps_program_exit_to_task_result():
    board_client = TestClient(
        create_app(Settings(program_mode="board"), program_runner=FakeProgramRunner(exit_code=0))
    )
    created = unwrap_ok(
        board_client.post(
            "/api/v1/tasks/pick-sort",
            json={
                "target": {"mode": "auto_detect", "labels": ["insulator"]},
                "destination": {"type": "category_bin", "category": "power_fitting"},
                "options": {"dry_run": False, "max_retry": 1},
            },
        )
    )

    detail = unwrap_ok(board_client.get(f"/api/v1/tasks/{created['task_id']}"))

    assert detail["state"] == "succeeded"
    assert detail["exit_code"] == 0
    assert detail["ended_at"].endswith("Z")
    assert detail["result"] == {"message": "Default board program completed."}


def test_board_mode_maps_program_failure_to_task_result():
    board_client = TestClient(
        create_app(Settings(program_mode="board"), program_runner=FakeProgramRunner(exit_code=2))
    )
    created = unwrap_ok(
        board_client.post(
            "/api/v1/tasks/stack",
            json={
                "target": {"mode": "auto_detect", "labels": ["red_block"]},
                "stack": {"slot_id": "stack_area_01", "max_layers": 3},
                "options": {"dry_run": False, "max_retry": 1},
            },
        )
    )

    detail = unwrap_ok(board_client.get(f"/api/v1/tasks/{created['task_id']}"))

    assert detail["state"] == "failed"
    assert detail["exit_code"] == 2
    assert detail["result"] == {"message": "Default board program failed.", "exit_code": 2}


def test_board_mode_cancel_interrupts_running_program_without_emergency_stop_claim():
    runner = FakeProgramRunner()
    board_client = TestClient(
        create_app(Settings(program_mode="board"), program_runner=runner)
    )
    created = unwrap_ok(
        board_client.post(
            "/api/v1/tasks/pick-sort",
            json={
                "target": {"mode": "auto_detect", "labels": ["insulator"]},
                "destination": {"type": "category_bin", "category": "power_fitting"},
                "options": {"dry_run": False, "max_retry": 1},
            },
        )
    )

    detail = unwrap_ok(board_client.post(f"/api/v1/tasks/{created['task_id']}/cancel"))

    assert runner.handle.interrupted is True
    assert detail["state"] == "cancelled"
    assert detail["result"] == {
        "message": "Default board program interrupted; this is not an emergency stop."
    }


def test_board_mode_program_output_is_published_as_event():
    runner = FakeProgramRunner()
    app = create_app(Settings(program_mode="board"), program_runner=runner)
    board_client = TestClient(app)

    created = unwrap_ok(
        board_client.post(
            "/api/v1/tasks/pick-sort",
            json={
                "target": {"mode": "auto_detect", "labels": ["insulator"]},
                "destination": {"type": "category_bin", "category": "power_fitting"},
                "options": {"dry_run": False, "max_retry": 1},
            },
        )
    )

    events = app.state.services.event_bus.latest(limit=10)
    log_events = [event for event in events if event["type"] == "task.log.created"]

    assert log_events[-1]["data"] == {
        "task_id": created["task_id"],
        "program": "pick_sort_default",
        "line": "default program started",
    }


def test_board_mode_parses_pick_sort_recognition_from_default_program_output():
    runner = FakeProgramRunner(
        output_lines=[
            "msg is: {'Book': (0.012, 0.321), 'Syringe': (-0.01, 0.4)}",
        ]
    )
    app = create_app(Settings(program_mode="board"), program_runner=runner)
    board_client = TestClient(app)

    created = unwrap_ok(
        board_client.post(
            "/api/v1/tasks/pick-sort",
            json={
                "target": {"mode": "auto_detect", "labels": ["Book"]},
                "destination": {"type": "category_bin", "category": "power_fitting"},
                "options": {"dry_run": False, "max_retry": 1},
            },
        )
    )
    detail = unwrap_ok(board_client.get(f"/api/v1/tasks/{created['task_id']}"))
    recognition_events = [
        event for event in app.state.services.event_bus.latest(limit=10)
        if event["type"] == "task.recognition.updated"
    ]

    assert detail["recognition"]["latest_label"] == "Book"
    assert detail["recognition"]["latest_category"] == "recyclable"
    assert detail["recognition"]["updated_at"].endswith("Z")
    assert detail["recognition"]["detections"] == [
        {
            "label": "Book",
            "category": "recyclable",
            "x_m": 0.012,
            "y_m": 0.321,
            "source": "msg",
        },
        {
            "label": "Syringe",
            "category": "hazardous",
            "x_m": -0.01,
            "y_m": 0.4,
            "source": "msg",
        },
    ]
    assert recognition_events[-1]["data"]["recognition"]["latest_label"] == "Book"


def test_board_mode_parses_sorted_recognition_output_and_unknown_labels():
    runner = FakeProgramRunner(
        output_lines=[
            "new msg is [('Custom_object', (0.05, -0.02))]",
        ]
    )
    board_client = TestClient(
        create_app(Settings(program_mode="board"), program_runner=runner)
    )

    created = unwrap_ok(
        board_client.post(
            "/api/v1/tasks/pick-sort",
            json={
                "target": {"mode": "auto_detect", "labels": ["Custom_object"]},
                "destination": {"type": "category_bin", "category": "power_fitting"},
                "options": {"dry_run": False, "max_retry": 1},
            },
        )
    )
    detail = unwrap_ok(board_client.get(f"/api/v1/tasks/{created['task_id']}"))

    assert detail["recognition"]["latest_label"] == "Custom_object"
    assert detail["recognition"]["latest_category"] == "unknown"
    assert detail["recognition"]["detections"][0]["source"] == "new_msg"


def test_board_mode_unstructured_logs_do_not_create_fake_recognition():
    board_client = TestClient(
        create_app(Settings(program_mode="board"), program_runner=FakeProgramRunner())
    )

    created = unwrap_ok(
        board_client.post(
            "/api/v1/tasks/pick-sort",
            json={
                "target": {"mode": "auto_detect", "labels": ["Book"]},
                "destination": {"type": "category_bin", "category": "power_fitting"},
                "options": {"dry_run": False, "max_retry": 1},
            },
        )
    )
    detail = unwrap_ok(board_client.get(f"/api/v1/tasks/{created['task_id']}"))

    assert detail["recognition"] is None


def test_board_mode_default_program_does_not_mutate_inventory():
    board_client = TestClient(
        create_app(Settings(program_mode="board"), program_runner=FakeProgramRunner(exit_code=0))
    )
    before = unwrap_ok(board_client.get("/api/v1/inventory/items"))
    created = unwrap_ok(
        board_client.post(
            "/api/v1/tasks/pick-sort",
            json={
                "target": {"mode": "auto_detect", "labels": ["insulator"]},
                "destination": {"type": "category_bin", "category": "power_fitting"},
                "options": {"dry_run": False, "max_retry": 1},
            },
        )
    )
    unwrap_ok(board_client.get(f"/api/v1/tasks/{created['task_id']}"))

    after = unwrap_ok(board_client.get("/api/v1/inventory/items"))

    assert after["items"] == before["items"]


def test_board_mode_system_status_exposes_active_task_and_camera_policy():
    board_client = TestClient(
        create_app(Settings(program_mode="board"), program_runner=FakeProgramRunner())
    )
    created = unwrap_ok(
        board_client.post(
            "/api/v1/tasks/pick-sort",
            json={
                "target": {"mode": "auto_detect", "labels": ["insulator"]},
                "destination": {"type": "category_bin", "category": "power_fitting"},
                "options": {"dry_run": False, "max_retry": 1},
            },
        )
    )

    status = unwrap_ok(board_client.get("/api/v1/system/status"))

    assert status["program_mode"] == "board"
    assert status["active_task_id"] == created["task_id"]
    assert status["camera_policy"] == "idle_only"


def test_board_mode_failed_program_start_does_not_leave_active_task():
    board_client = TestClient(
        create_app(Settings(program_mode="board"), program_runner=FailingProgramRunner())
    )

    unwrap_error(
        board_client.post(
            "/api/v1/tasks/pick-sort",
            json={
                "target": {"mode": "auto_detect", "labels": ["insulator"]},
                "destination": {"type": "category_bin", "category": "power_fitting"},
                "options": {"dry_run": False, "max_retry": 1},
            },
        ),
        500,
        "INTERNAL",
    )
    status = unwrap_ok(board_client.get("/api/v1/system/status"))

    assert status["active_task_id"] is None


def test_camera_capture_saves_labeled_photo(tmp_path):
    camera_backend = FakeCameraBackend()
    camera_client = TestClient(
        create_app(
            Settings(program_mode="board", capture_dir=str(tmp_path)),
            camera_backend=camera_backend,
        )
    )

    capture = unwrap_ok(
        camera_client.post("/api/v1/camera/captures", json={"label": "new_part"})
    )
    image = camera_client.get(capture["image_url"])

    assert capture["label"] == "new_part"
    assert capture["width"] == 320
    assert capture["height"] == 240
    assert capture["captured_at"].endswith("Z")
    assert capture["image_url"].startswith("/api/v1/camera/captures/")
    assert image.status_code == 200
    assert image.content == b"\xff\xd8fake-jpeg\xff\xd9"
    assert camera_backend.open_calls == [(0, 640, 480)]
    assert camera_backend.session.released is True


def test_camera_preview_stream_releases_camera_when_stream_ends(tmp_path):
    camera_backend = FakeCameraBackend(stop_after_first_frame=True)
    camera_client = TestClient(
        create_app(
            Settings(program_mode="board", capture_dir=str(tmp_path)),
            camera_backend=camera_backend,
        )
    )

    response = camera_client.get("/api/v1/camera/preview.mjpg")
    status = unwrap_ok(camera_client.get("/api/v1/camera/status"))

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("multipart/x-mixed-replace")
    assert b"fake-jpeg" in response.content
    assert camera_backend.session.released is True
    assert status["preview_active"] is False
    assert status["preview_clients"] == 0


def test_camera_preview_stop_releases_active_session(tmp_path):
    camera_backend = FakeCameraBackend()
    app = create_app(
        Settings(program_mode="board", capture_dir=str(tmp_path)),
        camera_backend=camera_backend,
    )
    camera_client = TestClient(app)
    stream = app.state.services.camera.preview_stream()
    next(stream)

    stopped = unwrap_ok(camera_client.post("/api/v1/camera/preview/stop"))

    assert stopped["preview_active"] is False
    assert stopped["preview_clients"] == 0
    assert camera_backend.session.released is True
    stream.close()


def test_board_mode_camera_capture_is_rejected_while_task_is_running(tmp_path):
    camera_backend = FakeCameraBackend()
    board_client = TestClient(
        create_app(
            Settings(program_mode="board", capture_dir=str(tmp_path)),
            program_runner=FakeProgramRunner(),
            camera_backend=camera_backend,
        )
    )
    created = unwrap_ok(
        board_client.post(
            "/api/v1/tasks/pick-sort",
            json={
                "target": {"mode": "auto_detect", "labels": ["insulator"]},
                "destination": {"type": "category_bin", "category": "power_fitting"},
                "options": {"dry_run": False, "max_retry": 1},
            },
        )
    )

    error = unwrap_error(
        board_client.post("/api/v1/camera/captures", json={"label": "blocked"}),
        409,
        "ARM_BUSY",
    )

    assert error["details"]["active_task_id"] == created["task_id"]
    assert camera_backend.open_calls == []


def test_board_mode_task_is_rejected_while_camera_preview_is_active(tmp_path):
    camera_backend = FakeCameraBackend()
    app = create_app(
        Settings(program_mode="board", capture_dir=str(tmp_path)),
        program_runner=FakeProgramRunner(),
        camera_backend=camera_backend,
    )
    board_client = TestClient(app)
    stream = app.state.services.camera.preview_stream()
    next(stream)

    try:
        error = unwrap_error(
            board_client.post(
                "/api/v1/tasks/pick-sort",
                json={
                    "target": {"mode": "auto_detect", "labels": ["insulator"]},
                    "destination": {"type": "category_bin", "category": "power_fitting"},
                    "options": {"dry_run": False, "max_retry": 1},
                },
            ),
            409,
            "CAMERA_BUSY",
        )
    finally:
        stream.close()

    assert error["message"] == (
        "Camera preview is active; close the preview page before starting a board task."
    )


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
