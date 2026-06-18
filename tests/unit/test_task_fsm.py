import pytest

from src.integration.task_fsm import TaskStateMachine


def test_task_state_machine_allows_expected_happy_path():
    fsm = TaskStateMachine()

    for state in ["detecting", "planning", "moving", "verifying", "succeeded"]:
        fsm.transition_to(state)

    assert fsm.state == "succeeded"
    assert fsm.progress == 1.0


def test_task_state_machine_rejects_invalid_transition():
    fsm = TaskStateMachine()

    with pytest.raises(ValueError, match="Invalid task transition"):
        fsm.transition_to("moving")
