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

# pytest tests/test_move_up_down.py -v