import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from mock_ai_contoller import validate_action, apply_action_to_ir
BASE_SCENE = {
    "node_type": "scene", "name": "root",
    "window": {"width": 800, "height": 600, "title": "Test"},
    "children": []
}

def test_validate_accepts_add_prefab():
    validate_action({"action": "add_prefab", "prefab_name": "house"})

def test_house_creates_group():
    result = apply_action_to_ir(BASE_SCENE, {"action": "add_prefab", "prefab_name": "house"})
    child = result["children"][0]
    assert child["node_type"] == "group"
    assert len(child["children"]) >= 2  # body + roof

def test_tree_creates_group():
    result = apply_action_to_ir(BASE_SCENE, {"action": "add_prefab", "prefab_name": "tree"})
    child = result["children"][0]
    assert child["node_type"] == "group"

def test_unknown_prefab_raises():
    with pytest.raises(ValueError, match="Unknown prefab"):
        apply_action_to_ir(BASE_SCENE, {"action": "add_prefab", "prefab_name": "spaceship"})