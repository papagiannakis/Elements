import sys
from copy import deepcopy
from pathlib import Path
from types import ModuleType

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

if "openai" not in sys.modules:
    openai_stub = ModuleType("openai")
    openai_stub.OpenAI = object
    sys.modules["openai"] = openai_stub

import mock_ai_contoller as controller


EMPTY = {
    "node_type": "scene",
    "name": "root",
    "window": {"width": 800, "height": 600, "title": "Test"},
    "children": [],
}


def _scene_with_cube(rotation=None):
    scene = deepcopy(EMPTY)
    transform = {
        "position": [0.0, 0.5, 0.0],
        "scale": [1.0, 1.0, 1.0],
    }
    if rotation is not None:
        transform["rotation"] = list(rotation)

    scene["children"].append({
        "node_type": "mesh_object",
        "name": "cube_1",
        "id": "cube_1",
        "created_order": 1,
        "shape": "cube",
        "transform": transform,
        "material": {"color": [1.0, 0.0, 0.0]},
    })
    return scene


def _cube_rotation(scene):
    return scene["children"][0]["transform"]["rotation"]


def test_validate_action_accepts_rotate_object():
    controller.validate_action({
        "action": "rotate_object",
        "target": "red cube",
        "axis": "y",
        "degrees": 45,
    })


def test_validate_action_rejects_invalid_rotate_axis():
    with pytest.raises(ValueError, match="axis must be one of"):
        controller.validate_action({
            "action": "rotate_object",
            "target": "red cube",
            "axis": "q",
            "degrees": 45,
        })


def test_apply_action_to_ir_initializes_missing_rotation():
    scene = _scene_with_cube(rotation=None)

    result = controller.apply_action_to_ir(scene, {
        "action": "rotate_object",
        "target": "cube",
        "axis": "y",
        "degrees": 45,
    })

    assert _cube_rotation(result) == [0.0, 45.0, 0.0]
    assert "rotation" not in scene["children"][0]["transform"]


def test_apply_action_to_ir_adds_degrees_to_correct_axis():
    scene = _scene_with_cube(rotation=[10.0, 20.0, 30.0])

    result = controller.apply_action_to_ir(scene, {
        "action": "rotate_object",
        "target": "cube",
        "axis": "x",
        "degrees": 15,
    })

    assert _cube_rotation(result) == [25.0, 20.0, 30.0]


def test_save_load_preserves_rotation_field(tmp_path, monkeypatch):
    saved_scenes_dir = tmp_path / "saved_scenes"
    saved_scenes_dir.mkdir()
    official_scene_file = tmp_path / "scene_ir.json"
    official_script_file = tmp_path / "scene_out.py"

    monkeypatch.setattr(controller, "SAVED_SCENES_DIR", saved_scenes_dir)
    monkeypatch.setattr(controller, "SCENE_IR_FILE", official_scene_file)
    monkeypatch.setattr(controller, "SCENE_OUT_FILE", official_script_file)
    monkeypatch.setattr(controller, "generate_scene_script", lambda scene_ir: "# test scene\n")
    monkeypatch.setattr(controller, "clear_preview_files", lambda: None)
    monkeypatch.setattr(controller, "clear_history_files", lambda: None)
    monkeypatch.setattr(controller, "reset_request_and_ui_files", lambda *args, **kwargs: None)
    monkeypatch.setattr(controller, "write_scene_state", lambda *args, **kwargs: None)

    scene = _scene_with_cube(rotation=[0.0, 45.0, 0.0])
    controller.save_named_scene(scene, "rot_scene")
    controller.initialize_load_scene("rot_scene")

    loaded = controller.read_json(official_scene_file, default=None)
    assert loaded is not None
    assert loaded["children"][0]["transform"]["rotation"] == [0.0, 45.0, 0.0]
