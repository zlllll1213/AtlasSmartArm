from dataclasses import dataclass, field
from itertools import count

from src.backend.errors import ApiError
from src.backend.models.enums import TaskState, TaskType
from src.backend.models.schemas import PickSortRequest, StackRequest
from src.backend.services.event_bus import EventBus
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
        }


class TaskService:
    def __init__(self, event_bus: EventBus) -> None:
        self.event_bus = event_bus
        self._counter = count(1)
        self._tasks: dict[str, TaskRecord] = {}

    def create_pick_sort(self, request: PickSortRequest) -> dict[str, object]:
        return self._create(TaskType.pick_sort, request.model_dump(mode="json"))

    def create_stack(self, request: StackRequest) -> dict[str, object]:
        return self._create(TaskType.stack, request.model_dump(mode="json"))

    def get(self, task_id: str) -> dict[str, object]:
        task = self._require(task_id)
        self._advance_for_mock(task)
        return task.public()

    def cancel(self, task_id: str) -> dict[str, object]:
        task = self._require(task_id)
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

    def _create(self, task_type: TaskType, request: dict[str, object]) -> dict[str, object]:
        task_id = f"task_{next(self._counter):012d}"
        task = TaskRecord(task_id=task_id, type=task_type, request=request)
        self._tasks[task_id] = task
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
