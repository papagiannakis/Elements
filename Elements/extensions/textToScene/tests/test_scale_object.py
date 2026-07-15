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

def _cube():
    s = deepcopy(EMPTY)
    s["children"].append({
        "node_type": "mesh_object", "name": "cube_1", "id": "cube_1",
        "created_order": 1, "shape": "cube",
        "transform": {"position": [0.0, 0.5, 0.0], "scale": [1.0, 1.0, 1.0]},
        "material": {"color": [1.0, 0.0, 0.0]},
    })
    return s

def _scale(scene, **kwargs):
    return apply_action_to_ir(scene, {"action": "scale_object", "target": "cube_1", **kwargs})

def _s(result):
    return collect_mesh_objects(result)[0]["transform"]["scale"]

def test_scale_with_factor():
    assert all(abs(v - 2.0) < 0.01 for v in _s(_scale(_cube(), factor=2.0)))

def test_scale_with_list():
    s = _s(_scale(_cube(), scale=[2.0, 3.0, 0.5]))
    assert abs(s[0]-2.0) < 0.01 and abs(s[1]-3.0) < 0.01 and abs(s[2]-0.5) < 0.01

def test_scale_half():
    assert all(abs(v - 0.5) < 0.01 for v in _s(_scale(_cube(), factor=0.5)))

def test_scale_missing_args_raises():
    with pytest.raises(ValueError, match="scale_object requires"):
        _scale(_cube())

def test_scale_does_not_mutate_input():
    scene = _cube()
    _scale(scene, factor=3.0)
    assert scene["children"][0]["transform"]["scale"] == [1.0, 1.0, 1.0]

def test_scale_preserves_position():
    result = _scale(_cube(), factor=2.0)
    pos = collect_mesh_objects(result)[0]["transform"]["position"]
    assert abs(pos[1] - 0.5) < 0.01
