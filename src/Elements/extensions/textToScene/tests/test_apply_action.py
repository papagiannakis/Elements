"""
Tests for apply_action_to_ir covering the full range of action types,
positioning, colours, deletion, and immutability of the input scene.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from copy import deepcopy
from mock_ai_contoller import apply_action_to_ir, collect_mesh_objects

EMPTY = {
    "node_type": "scene", "name": "root",
    "window": {"width": 800, "height": 600, "title": "Test"},
    "children": [],
}


def _add_cube(scene, name="cube_1", color=None, position=None):
    """Helper: inject a mesh_object child directly."""
    scene = deepcopy(scene)
    scene["children"].append({
        "node_type": "mesh_object",
        "name": name,
        "id": name,
        "created_order": 1,
        "shape": "cube",
        "transform": {"position": position or [0.0, 0.5, 0.0], "scale": [1.0, 1.0, 1.0]},
        "material": {"color": color or [1.0, 0.0, 0.0]},
    })
    return scene


# ---------------------------------------------------------------------------
# add_object — shape, colour, node_type
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("shape", ["cube", "sphere", "cylinder", "cone", "pyramid", "plane"])
def test_add_object_various_shapes(shape):
    result = apply_action_to_ir(deepcopy(EMPTY), {"action": "add_object", "object_type": shape})
    added = result["children"][0]
    assert added["node_type"] == "mesh_object"
    assert added["shape"] == shape


@pytest.mark.parametrize("color_name,expected_r", [
    ("red",    1.0),
    ("green",  0.0),
    ("blue",   0.0),
    ("yellow", 1.0),
    ("white",  1.0),
])
def test_add_object_colour_is_applied(color_name, expected_r):
    result = apply_action_to_ir(deepcopy(EMPTY), {"action": "add_object", "object_type": "cube", "color": color_name})
    rgb = result["children"][0]["material"]["color"]
    assert abs(rgb[0] - expected_r) < 0.05


def test_add_two_objects_different_positions():
    s = deepcopy(EMPTY)
    s = apply_action_to_ir(s, {"action": "add_object", "object_type": "cube", "color": "red"})
    s = apply_action_to_ir(s, {"action": "add_object", "object_type": "cube", "color": "blue"})
    pos0 = s["children"][0]["transform"]["position"]
    pos1 = s["children"][1]["transform"]["position"]
    assert pos0 != pos1, "Two objects must not share the same position"


def test_add_object_does_not_mutate_input():
    original = deepcopy(EMPTY)
    apply_action_to_ir(original, {"action": "add_object", "object_type": "cube"})
    assert original["children"] == [], "Input scene must not be modified"


# ---------------------------------------------------------------------------
# delete_object
# ---------------------------------------------------------------------------
def test_delete_object_by_id():
    scene = _add_cube(EMPTY, name="cube_x")
    result = apply_action_to_ir(scene, {"action": "delete_object", "object_id": "cube_x"})
    assert result["children"] == []


def test_delete_object_by_target_text():
    scene = _add_cube(EMPTY, name="cube_1", color=[1.0, 0.0, 0.0])
    result = apply_action_to_ir(scene, {"action": "delete_object", "target": "red cube"})
    assert result["children"] == []


def test_delete_nonexistent_target_raises():
    with pytest.raises(ValueError):
        apply_action_to_ir(deepcopy(EMPTY), {"action": "delete_object", "target": "purple sphere"})


# ---------------------------------------------------------------------------
# recolor_object
# ---------------------------------------------------------------------------
def test_recolor_changes_material_color():
    scene = _add_cube(EMPTY, name="cube_1", color=[1.0, 0.0, 0.0])
    result = apply_action_to_ir(scene, {
        "action": "recolor_object",
        "target": "cube",
        "color": "blue",
    })
    rgb = result["children"][0]["material"]["color"]
    assert abs(rgb[2] - 1.0) < 0.05  # blue channel
    assert abs(rgb[0] - 0.0) < 0.05  # red channel now zero


def test_recolor_nonexistent_target_raises():
    with pytest.raises(ValueError):
        apply_action_to_ir(deepcopy(EMPTY), {"action": "recolor_object", "target": "cube", "color": "red"})


# ---------------------------------------------------------------------------
# scale_object
# ---------------------------------------------------------------------------
def test_scale_object_with_factor():
    scene = _add_cube(EMPTY, name="cube_1")
    result = apply_action_to_ir(scene, {
        "action": "scale_object",
        "target": "cube",
        "factor": 2.0,
    })
    scale = result["children"][0]["transform"]["scale"]
    assert all(abs(v - 2.0) < 0.001 for v in scale)


def test_scale_object_with_explicit_scale():
    scene = _add_cube(EMPTY, name="cube_1")
    result = apply_action_to_ir(scene, {
        "action": "scale_object",
        "target": "cube",
        "scale": [1.0, 3.0, 1.0],
    })
    scale = result["children"][0]["transform"]["scale"]
    assert abs(scale[1] - 3.0) < 0.001


def test_scale_object_missing_factor_and_scale_raises():
    scene = _add_cube(EMPTY, name="cube_1")
    with pytest.raises(ValueError):
        apply_action_to_ir(scene, {"action": "scale_object", "target": "cube"})


# ---------------------------------------------------------------------------
# move_object
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("direction", ["right", "left", "forward", "backward", "up", "down"])
def test_move_object_valid_directions(direction):
    scene = _add_cube(EMPTY, name="cube_1", position=[0.0, 0.5, 0.0])
    result = apply_action_to_ir(scene, {
        "action": "move_object",
        "target": "cube",
        "direction": direction,
    })
    pos_before = [0.0, 0.5, 0.0]
    pos_after = result["children"][0]["transform"]["position"]
    assert pos_before != pos_after, f"Object should have moved ({direction})"


def test_move_object_invalid_direction_raises():
    scene = _add_cube(EMPTY, name="cube_1")
    with pytest.raises(ValueError):
        apply_action_to_ir(scene, {"action": "move_object", "target": "cube", "direction": "diagonal"})


def test_move_object_no_direction_raises():
    scene = _add_cube(EMPTY, name="cube_1")
    with pytest.raises(ValueError):
        apply_action_to_ir(scene, {"action": "move_object", "target": "cube"})


# ---------------------------------------------------------------------------
# action_sequence
# ---------------------------------------------------------------------------
def test_action_sequence_executes_all_steps():
    result = apply_action_to_ir(deepcopy(EMPTY), {
        "action": "action_sequence",
        "action_sequence": [
            {"action": "add_object", "object_type": "cube", "color": "red"},
            {"action": "add_object", "object_type": "sphere", "color": "blue"},
            {"action": "add_object", "object_type": "cylinder", "color": "green"},
        ],
    })
    assert len(result["children"]) == 3


def test_action_sequence_order_matters():
    """Add a cube then delete it — scene should be empty."""
    result = apply_action_to_ir(deepcopy(EMPTY), {
        "action": "action_sequence",
        "action_sequence": [
            {"action": "add_object", "object_type": "cube", "color": "red"},
            {"action": "delete_object", "target": "red cube"},
        ],
    })
    assert result["children"] == []


# ---------------------------------------------------------------------------
# Unsupported action type
# ---------------------------------------------------------------------------
def test_unsupported_action_raises():
    with pytest.raises(ValueError):
        apply_action_to_ir(deepcopy(EMPTY), {"action": "paint_scene"})
