from dataclasses import dataclass

from src.backend.models.enums import TaskState


ALLOWED_TRANSITIONS: dict[TaskState, set[TaskState]] = {
    TaskState.queued: {TaskState.detecting, TaskState.cancelled, TaskState.failed},
    TaskState.detecting: {TaskState.planning, TaskState.cancelled, TaskState.failed},
    TaskState.planning: {TaskState.moving, TaskState.paused, TaskState.cancelled, TaskState.failed},
    TaskState.moving: {TaskState.verifying, TaskState.paused, TaskState.failed},
    TaskState.verifying: {TaskState.succeeded, TaskState.failed},
    TaskState.paused: {TaskState.planning, TaskState.cancelled, TaskState.failed},
    TaskState.succeeded: set(),
    TaskState.failed: set(),
    TaskState.cancelled: set(),
}

PROGRESS_BY_STATE: dict[TaskState, float] = {
    TaskState.queued: 0.0,
    TaskState.detecting: 0.18,
    TaskState.planning: 0.36,
    TaskState.moving: 0.62,
    TaskState.verifying: 0.86,
    TaskState.succeeded: 1.0,
    TaskState.failed: 1.0,
    TaskState.cancelled: 1.0,
    TaskState.paused: 0.4,
}


@dataclass
class TaskStateMachine:
    state: TaskState = TaskState.queued
    progress: float = 0.0

    def transition_to(self, next_state: str | TaskState) -> None:
        target_state = TaskState(next_state)
        if target_state not in ALLOWED_TRANSITIONS[self.state]:
            raise ValueError(f"Invalid task transition: {self.state} -> {target_state}")
        self.state = target_state
        self.progress = PROGRESS_BY_STATE[target_state]
