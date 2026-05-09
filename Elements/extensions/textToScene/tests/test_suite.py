import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from copy import deepcopy

from mock_ai_contoller import validate_action, apply_action_to_ir
from code_generator import generate_scene_script

BASE_SCENE = {
    "node_type": "scene",
    "name": "root",
    "window": {"width": 800, "height": 600, "title": "Test"},
    "children": []
}


def test_validate_accepts_add_object():
    validate_action({"action": "add_object", "object_type": "cube", "color": "red"})


def test_validate_accepts_add_prefab():
    validate_action({"action": "add_prefab", "prefab_name": "house"})


def test_validate_rejects_unknown_action():
    with pytest.raises(ValueError):
        validate_action({"action": "fly_to_moon"})


def test_add_object_creates_mesh_node():
    result = apply_action_to_ir(deepcopy(BASE_SCENE), {"action": "add_object", "object_type": "cube", "color": "red"})
    assert len(result["children"]) == 1
    assert result["children"][0]["node_type"] == "mesh_object"


def test_add_prefab_house_creates_group():
    result = apply_action_to_ir(deepcopy(BASE_SCENE), {"action": "add_prefab", "prefab_name": "house"})
    assert result["children"][0]["node_type"] == "group"
    assert len(result["children"][0]["children"]) >= 2


def test_add_prefab_tree_creates_group():
    result = apply_action_to_ir(deepcopy(BASE_SCENE), {"action": "add_prefab", "prefab_name": "tree"})
    assert result["children"][0]["node_type"] == "group"
    assert len(result["children"][0]["children"]) >= 2


def test_unknown_prefab_raises():
    with pytest.raises(ValueError):
        apply_action_to_ir(deepcopy(BASE_SCENE), {"action": "add_prefab", "prefab_name": "spaceship"})


def test_code_generator_produces_script():
    result = generate_scene_script(deepcopy(BASE_SCENE))
    assert isinstance(result, str)
    assert len(result) > 0
    assert "import" in result


def test_code_generator_includes_object_name():
    scene = deepcopy(BASE_SCENE)
    scene["children"].append({
        "node_type": "mesh_object",
        "name": "my_cube",
        "shape": "cube",
        "transform": {"position": [0.0, 0.5, 0.0], "scale": [1.0, 1.0, 1.0]},
        "material": {"color": [1.0, 0.0, 0.0]}
    })
    result = generate_scene_script(scene)
    assert "my_cube" in result
