"""
Thorough tests for validate_action — all valid action types,
action_sequence nesting rules, and rejection of invalid schemas.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from mock_ai_contoller import validate_action


# ---------------------------------------------------------------------------
# All supported single-action names must be accepted
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("action_name", [
    "add_object",
    "move_object",
    "delete_object",
    "recolor_object",
    "scale_object",
    "new_scene",
    "save_scene",
    "load_scene",
    "add_prefab",
    "undo",
])
def test_validate_accepts_all_single_actions(action_name):
    validate_action({"action": action_name})


# ---------------------------------------------------------------------------
# action_sequence
# ---------------------------------------------------------------------------
def test_validate_accepts_action_sequence():
    validate_action({
        "action": "action_sequence",
        "action_sequence": [
            {"action": "add_object", "object_type": "cube", "color": "red"},
            {"action": "add_object", "object_type": "sphere", "color": "blue"},
        ],
    })


def test_validate_rejects_empty_action_sequence():
    with pytest.raises(ValueError):
        validate_action({"action": "action_sequence", "action_sequence": []})


def test_validate_rejects_action_sequence_missing_list():
    with pytest.raises(ValueError):
        validate_action({"action": "action_sequence"})


def test_validate_rejects_nested_action_sequence():
    with pytest.raises(ValueError):
        validate_action({
            "action": "action_sequence",
            "action_sequence": [
                {
                    "action": "action_sequence",
                    "action_sequence": [{"action": "add_object"}],
                }
            ],
        })


def test_validate_rejects_sequence_step_not_dict():
    with pytest.raises(ValueError):
        validate_action({
            "action": "action_sequence",
            "action_sequence": ["add_object"],
        })


# ---------------------------------------------------------------------------
# Structural errors
# ---------------------------------------------------------------------------
def test_validate_rejects_missing_action_key():
    with pytest.raises(ValueError):
        validate_action({"object_type": "cube"})


def test_validate_rejects_non_dict():
    with pytest.raises(ValueError):
        validate_action("add_object")


def test_validate_rejects_none():
    with pytest.raises(ValueError):
        validate_action(None)


def test_validate_rejects_unknown_action_name():
    with pytest.raises(ValueError):
        validate_action({"action": "teleport_object"})


def test_validate_rejects_empty_dict():
    with pytest.raises(ValueError):
        validate_action({})
