import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from copy import deepcopy
from mock_ai_contoller import apply_action_to_ir, collect_mesh_objects, normalize_action, GRID_SPACING

EMPTY = {
    "node_type": "scene", "name": "root",
    "window": {"width": 800, "height": 600, "title": "Test"},
    "children": [],
}

def _cube(position=None):
    s = deepcopy(EMPTY)
    s["children"].append({
        "node_type": "mesh_object", "name": "cube_1", "id": "cube_1",
        "created_order": 1, "shape": "cube",
        "transform": {"position": position or [0.0, 0.5, 0.0], "scale": [1.0, 1.0, 1.0]},
        "material": {"color": [1.0, 0.0, 0.0]},
    })
    return s

def _move(scene, direction):
    return apply_action_to_ir(scene, {"action": "move_object", "target": "cube_1", "direction": direction})

def _y(result):
    return collect_mesh_objects(result)[0]["transform"]["position"][1]


def test_move_up_increases_y():
    assert _y(_move(_cube([0.0, 0.5, 0.0]), "up")) > 0.5

def test_move_down_decreases_y():
    assert _y(_move(_cube([0.0, 3.0, 0.0]), "down")) < 3.0

def test_move_up_step_equals_grid_spacing():
    assert abs(_y(_move(_cube([0.0, 0.5, 0.0]), "up")) - (0.5 + GRID_SPACING)) < 0.01

def test_move_up_preserves_x_z():
    result = _move(_cube([1.5, 0.5, 2.0]), "up")
    pos = collect_mesh_objects(result)[0]["transform"]["position"]
    assert abs(pos[0] - 1.5) < 0.01 and abs(pos[2] - 2.0) < 0.01

def test_up_then_down_returns_to_original_y():
    after = _move(_move(_cube([0.0, 3.0, 0.0]), "up"), "down")
    assert abs(_y(after) - 3.0) < 0.01

def test_move_up_does_not_mutate_input():
    scene = _cube([0.0, 0.5, 0.0])
    _move(scene, "up")
    assert scene["children"][0]["transform"]["position"][1] == 0.5

@pytest.mark.parametrize("alias", ["upward", "upwards", "above", "higher"])
def test_up_aliases_normalize_correctly(alias):
    assert normalize_action({"action": "move_object", "target": "cube_1", "direction": alias})["direction"] == "up"

@pytest.mark.parametrize("alias", ["downward", "downwards", "below", "lower"])
def test_down_aliases_normalize_correctly(alias):
    assert normalize_action({"action": "move_object", "target": "cube_1", "direction": alias})["direction"] == "down"

def test_invalid_direction_raises():
    with pytest.raises(ValueError, match="Unsupported move direction"):
        _move(_cube(), "diagonal")

_scene_with_cube = _cube


class TestScaleObject:
    def test_scale_with_explicit_list(self):
        scene = _scene_with_cube()
        result = apply_action_to_ir(scene, {"action": "scale_object", "target": "cube_1", "scale": [2.0, 3.0, 2.0]})
        scale = collect_mesh_objects(result)[0]["transform"]["scale"]
        assert abs(scale[0] - 2.0) < 0.01 and abs(scale[1] - 3.0) < 0.01

    def test_scale_with_factor(self):
        result = apply_action_to_ir(_scene_with_cube(), {"action": "scale_object", "target": "cube_1", "factor": 2.0})
        assert all(abs(v - 2.0) < 0.01 for v in collect_mesh_objects(result)[0]["transform"]["scale"])

    def test_scale_missing_args_raises(self):
        with pytest.raises(ValueError, match="scale_object requires"):
            apply_action_to_ir(_scene_with_cube(), {"action": "scale_object", "target": "cube_1"})


class TestNormalizeAction:
    @pytest.mark.parametrize("raw,expected", [
        ("upward", "up"), ("above", "up"), ("higher", "up"),
        ("downward", "down"), ("below", "down"),
        ("front", "forward"), ("ahead", "forward"),
        ("back", "backward"), ("behind", "backward"),
    ])
    def test_direction_alias_normalised(self, raw, expected):
        result = normalize_action({"action": "move_object", "target": "cube", "direction": raw})
        assert result["direction"] == expected

    def test_object_id_becomes_id(self):
        result = normalize_action({"action": "delete_object", "object_id": "cube_1"})
        assert result.get("id") == "cube_1" and "object_id" not in result

    def test_non_dict_returns_unchanged(self):
        assert normalize_action("not a dict") == "not a dict"


from mock_ai_contoller import pop_history_state
import mock_ai_contoller as ctrl


class TestUndoEmptyStack:
    def test_pop_history_returns_non_dict_when_empty(self, tmp_path, monkeypatch):
        monkeypatch.setattr(ctrl, "HISTORY_STACK_FILE", tmp_path / "undo_stack.json")
        result = pop_history_state()
        assert not isinstance(result, dict)


class TestActionSequenceFailure:
    def test_sequence_with_unknown_action_raises(self):
        with pytest.raises(Exception):
            apply_action_to_ir(deepcopy(EMPTY), {
                "action": "action_sequence",
                "action_sequence": [
                    {"action": "add_object", "object_type": "cube", "color": "red"},
                    {"action": "teleport_object", "target": "cube_1"},
                ],
            })

    def test_sequence_two_valid_steps_both_applied(self):
        result = apply_action_to_ir(deepcopy(EMPTY), {
            "action": "action_sequence",
            "action_sequence": [
                {"action": "add_object", "object_type": "cube", "color": "red"},
                {"action": "add_object", "object_type": "sphere", "color": "blue"},
            ],
        })
        shapes = {o["shape"] for o in collect_mesh_objects(result)}
        assert shapes == {"cube", "sphere"}