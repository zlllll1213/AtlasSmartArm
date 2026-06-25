from dataclasses import dataclass, field
from itertools import count
from typing import Callable

from src.backend.errors import ApiError
from src.backend.models.enums import TaskState, TaskType
from src.backend.models.schemas import PickSortRequest, StackRequest
from src.backend.config import Settings
from src.backend.services.board_program_runner import ProgramHandle, ProgramRunner
from src.backend.services.event_bus import EventBus
from src.backend.services.recognition_parser import parse_recognition_log
from src.backend.time_utils import utc_now_iso
from src.integration.task_fsm import TaskStateMachine


STEP_BY_STATE = {
    TaskState.queued: "queued",
    TaskState.detecting: "capturing_frame",
    TaskState.planning: "solving_kinematics",
    TaskState.moving: "moving_to_target",
    TaskState.verifying: "verifying_result",
    TaskState.succeeded: "completed",
    TaskState.failed: "failed",
    TaskState.cancelled: "cancelled",
    TaskState.paused: "paused",
}


@dataclass
class TaskRecord:
    task_id: str
    type: TaskType
    request: dict[str, object]
    fsm: TaskStateMachine = field(default_factory=TaskStateMachine)
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)
    poll_count: int = 0
    result: dict[str, object] | None = None
    program: str | None = None
    pid: int | None = None
    exit_code: int | None = None
    logs: list[str] = field(default_factory=list)
    recognition: dict[str, object] | None = None
    started_at: str | None = None
    ended_at: str | None = None
    handle: ProgramHandle | None = None

    def public(self) -> dict[str, object]:
        return {
            "task_id": self.task_id,
            "type": self.type,
            "state": self.fsm.state,
            "progress": self.fsm.progress,
            "current_step": STEP_BY_STATE[self.fsm.state],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "result": self.result,
            "program": self.program,
            "pid": self.pid,
            "exit_code": self.exit_code,
            "logs": self.logs,
            "recognition": self.recognition,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
        }


class TaskService:
    def __init__(
        self,
        event_bus: EventBus,
        settings: Settings,
        program_runner: ProgramRunner | None = None,
        camera_in_use: Callable[[], bool] | None = None,
    ) -> None:
        self.event_bus = event_bus
        self.settings = settings
        self.program_runner = program_runner
        self.camera_in_use = camera_in_use or (lambda: False)
        self._counter = count(1)
        self._tasks: dict[str, TaskRecord] = {}

    def create_pick_sort(self, request: PickSortRequest) -> dict[str, object]:
        return self._create(
            TaskType.pick_sort,
            request.model_dump(mode="json"),
            board_program="pick_sort_default",
        )

    def create_stack(self, request: StackRequest) -> dict[str, object]:
        return self._create(
            TaskType.stack,
            request.model_dump(mode="json"),
            board_program="stack_default",
        )

    def get(self, task_id: str) -> dict[str, object]:
        task = self._require(task_id)
        if self.settings.program_mode == "board":
            self._advance_for_board(task)
        else:
            self._advance_for_mock(task)
        return task.public()

    def cancel(self, task_id: str) -> dict[str, object]:
        task = self._require(task_id)
        if self.settings.program_mode == "board" and task.handle is not None:
            if task.fsm.state in {TaskState.succeeded, TaskState.failed, TaskState.cancelled}:
                raise ApiError(
                    "OUT_OF_RANGE",
                    "Finished board tasks cannot be cancelled.",
                    400,
                    {"task_id": task_id, "state": task.fsm.state},
                )
            task.handle.interrupt()
            task.fsm.transition_to(TaskState.cancelled)
            task.ended_at = utc_now_iso()
            task.updated_at = task.ended_at
            task.result = {
                "message": "Default board program interrupted; this is not an emergency stop."
            }
            self.event_bus.publish(
                "task.state.changed", {"task_id": task_id, "state": task.fsm.state}
            )
            return task.public()
        if task.fsm.state not in {TaskState.queued, TaskState.detecting, TaskState.planning}:
            raise ApiError(
                "OUT_OF_RANGE",
                "Only queued, detecting, or planning tasks can be cancelled safely.",
                400,
                {"task_id": task_id, "state": task.fsm.state},
            )
        task.fsm.transition_to(TaskState.cancelled)
        task.updated_at = utc_now_iso()
        self.event_bus.publish("task.state.changed", {"task_id": task_id, "state": task.fsm.state})
        return task.public()

    def active_task_id(self) -> str | None:
        for task in self._tasks.values():
            if task.fsm.state not in {TaskState.succeeded, TaskState.failed, TaskState.cancelled}:
                return task.task_id
        return None

    def _create(
        self,
        task_type: TaskType,
        request: dict[str, object],
        *,
        board_program: str,
    ) -> dict[str, object]:
        if self.settings.program_mode == "board":
            active_task_id = self.active_task_id()
            if active_task_id is not None:
                raise ApiError(
                    "ARM_BUSY",
                    "A board default program task is already running.",
                    409,
                    {"active_task_id": active_task_id},
                )
            if self.camera_in_use():
                raise ApiError(
                    "CAMERA_BUSY",
                    "Camera preview is active; close the preview page before starting a board task.",
                    409,
                    {},
                )
        task_id = f"task_{next(self._counter):012d}"
        task = TaskRecord(task_id=task_id, type=task_type, request=request)
        self._tasks[task_id] = task
        if self.settings.program_mode == "board":
            try:
                self._start_board_program(task, board_program)
            except ApiError:
                self._tasks.pop(task_id, None)
                raise
            except Exception as exc:
                self._tasks.pop(task_id, None)
                raise ApiError(
                    "INTERNAL",
                    "Failed to start board default program.",
                    500,
                    {"program": board_program},
                ) from exc
        self.event_bus.publish("task.state.changed", {"task_id": task_id, "state": task.fsm.state})
        return {"task_id": task_id, "type": task_type, "state": task.fsm.state}

    def _require(self, task_id: str) -> TaskRecord:
        try:
            return self._tasks[task_id]
        except KeyError as exc:
            raise ApiError("NOT_FOUND", "Task not found.", 404, {"task_id": task_id}) from exc

    def _advance_for_mock(self, task: TaskRecord) -> None:
        if task.fsm.state in {TaskState.succeeded, TaskState.failed, TaskState.cancelled}:
            return
        task.poll_count += 1
        sequence = [
            TaskState.detecting,
            TaskState.planning,
            TaskState.moving,
            TaskState.verifying,
            TaskState.succeeded,
        ]
        next_index = min(task.poll_count - 1, len(sequence) - 1)
        target = sequence[next_index]
        if target != task.fsm.state:
            task.fsm.transition_to(target)
            task.updated_at = utc_now_iso()
            self.event_bus.publish(
                "task.progress.updated",
                {"task_id": task.task_id, "state": task.fsm.state, "progress": task.fsm.progress},
            )
        if task.fsm.state == TaskState.succeeded:
            task.result = {"message": "Mock task completed.", "handled_objects": 1}

    def _start_board_program(self, task: TaskRecord, program: str) -> None:
        if self.program_runner is None:
            raise ApiError(
                "INTERNAL",
                "Board program runner is not configured.",
                500,
                {"program": program},
            )
        task.program = program
        task.started_at = utc_now_iso()
        task.fsm.transition_to(TaskState.detecting)
        task.fsm.transition_to(TaskState.planning)
        task.fsm.transition_to(TaskState.moving)

        def remember_log(line: str) -> None:
            task.logs.append(line)
            del task.logs[:-200]
            task.updated_at = utc_now_iso()
            self.event_bus.publish(
                "task.log.created",
                {"task_id": task.task_id, "program": task.program, "line": line},
            )
            self._remember_recognition_from_log(task, line)

        task.handle = self.program_runner.start(program, remember_log)
        task.pid = task.handle.pid
        task.updated_at = utc_now_iso()

    def _remember_recognition_from_log(self, task: TaskRecord, line: str) -> None:
        if task.type != TaskType.pick_sort:
            return
        detections = parse_recognition_log(line)
        if not detections:
            return
        updated_at = utc_now_iso()
        latest = detections[0]
        task.recognition = {
            "latest_label": latest["label"],
            "latest_category": latest["category"],
            "detections": detections,
            "updated_at": updated_at,
        }
        task.updated_at = updated_at
        self.event_bus.publish(
            "task.recognition.updated",
            {
                "task_id": task.task_id,
                "program": task.program,
                "recognition": task.recognition,
            },
        )

    def _advance_for_board(self, task: TaskRecord) -> None:
        if task.handle is None or task.fsm.state in {
            TaskState.succeeded,
            TaskState.failed,
            TaskState.cancelled,
        }:
            return
        exit_code = task.handle.poll()
        if exit_code is None:
            return
        task.exit_code = exit_code
        task.ended_at = utc_now_iso()
        task.updated_at = task.ended_at
        if exit_code == 0:
            task.fsm.transition_to(TaskState.verifying)
            task.fsm.transition_to(TaskState.succeeded)
            task.result = {"message": "Default board program completed."}
        else:
            task.fsm.transition_to(TaskState.failed)
            task.result = {"message": "Default board program failed.", "exit_code": exit_code}
