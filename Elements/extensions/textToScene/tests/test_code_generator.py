"""
Tests for code_generator.generate_scene_script and its normalisation helpers.
No OpenGL / Elements runtime is needed — the conftest stubs those out.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from copy import deepcopy
from code_generator import (
    generate_scene_script,
    normalize_window,
    normalize_transform,
    normalize_material,
    validate_and_normalize_scene_ir,
)

BASE = {
    "node_type": "scene", "name": "root",
    "window": {"width": 800, "height": 600, "title": "Test"},
    "children": [],
}


# ---------------------------------------------------------------------------
# generate_scene_script — output format
# ---------------------------------------------------------------------------
def test_script_is_non_empty_string():
    result = generate_scene_script(deepcopy(BASE))
    assert isinstance(result, str) and len(result) > 0


def test_script_starts_with_import():
    result = generate_scene_script(deepcopy(BASE))
    assert result.lstrip().startswith("import")


def test_script_contains_numpy_import():
    result = generate_scene_script(deepcopy(BASE))
    assert "import numpy" in result


def test_script_contains_window_dimensions():
    result = generate_scene_script(deepcopy(BASE))
    assert "800" in result
    assert "600" in result


def test_script_contains_window_title():
    scene = deepcopy(BASE)
    scene["window"]["title"] = "MySpecialScene"
    result = generate_scene_script(scene)
    assert "MySpecialScene" in result


def test_script_contains_scene_setup():
    result = generate_scene_script(deepcopy(BASE))
    assert "scene = Scene()" in result


def test_object_name_appears_in_script():
    scene = deepcopy(BASE)
    scene["children"].append({
        "node_type": "mesh_object",
        "name": "unique_widget",
        "shape": "cube",
        "transform": {"position": [0.0, 0.5, 0.0], "scale": [1.0, 1.0, 1.0]},
        "material": {"color": [1.0, 0.0, 0.0]},
    })
    result = generate_scene_script(scene)
    assert "unique_widget" in result


def test_multiple_object_names_all_appear():
    scene = deepcopy(BASE)
    for name in ("alpha_cube", "beta_sphere", "gamma_cone"):
        scene["children"].append({
            "node_type": "mesh_object",
            "name": name,
            "shape": "cube",
            "transform": {"position": [0.0, 0.5, 0.0], "scale": [1.0, 1.0, 1.0]},
            "material": {"color": [0.5, 0.5, 0.5]},
        })
    result = generate_scene_script(scene)
    for name in ("alpha_cube", "beta_sphere", "gamma_cone"):
        assert name in result


def test_group_name_appears_in_script():
    scene = deepcopy(BASE)
    scene["children"].append({
        "node_type": "group",
        "name": "my_group",
        "transform": {"position": [0.0, 0.0, 0.0], "scale": [1.0, 1.0, 1.0]},
        "children": [],
    })
    result = generate_scene_script(scene)
    assert "my_group" in result


def test_script_does_not_mutate_input():
    scene = deepcopy(BASE)
    original_children = list(scene["children"])
    generate_scene_script(scene)
    assert scene["children"] == original_children


# ---------------------------------------------------------------------------
# normalize_window
# ---------------------------------------------------------------------------
class TestNormalizeWindow:
    def test_valid_window(self):
        w = normalize_window({"width": 1280, "height": 720, "title": "Hi"})
        assert w["width"] == 1280
        assert w["height"] == 720
        assert w["title"] == "Hi"

    def test_missing_keys_use_defaults(self):
        w = normalize_window({})
        assert w["width"] > 0
        assert w["height"] > 0

    def test_none_uses_defaults(self):
        w = normalize_window(None)
        assert isinstance(w["width"], int)

    def test_zero_width_raises(self):
        with pytest.raises(ValueError):
            normalize_window({"width": 0, "height": 600})

    def test_negative_height_raises(self):
        with pytest.raises(ValueError):
            normalize_window({"width": 800, "height": -1})

    def test_non_dict_raises(self):
        with pytest.raises(TypeError):
            normalize_window("800x600")


# ---------------------------------------------------------------------------
# normalize_transform
# ---------------------------------------------------------------------------
class TestNormalizeTransform:
    def test_valid_transform(self):
        t = normalize_transform({"position": [1.0, 2.0, 3.0], "scale": [1.0, 1.0, 1.0]})
        assert t["position"] == pytest.approx([1.0, 2.0, 3.0])

    def test_missing_fields_use_defaults(self):
        t = normalize_transform({})
        assert len(t["position"]) == 3
        assert len(t["scale"]) == 3

    def test_none_uses_defaults(self):
        t = normalize_transform(None)
        assert isinstance(t["position"], list)

    def test_wrong_length_raises(self):
        with pytest.raises((ValueError, TypeError)):
            normalize_transform({"position": [1.0, 2.0]})

    def test_non_dict_raises(self):
        with pytest.raises(TypeError):
            normalize_transform("bad")


# ---------------------------------------------------------------------------
# normalize_material
# ---------------------------------------------------------------------------
class TestNormalizeMaterial:
    def test_valid_material(self):
        m = normalize_material({"color": [1.0, 0.0, 0.0]})
        assert m["color"][0] == pytest.approx(1.0)

    def test_clamps_colour_above_1(self):
        m = normalize_material({"color": [2.0, 0.0, 0.0]})
        assert m["color"][0] == pytest.approx(1.0)

    def test_clamps_colour_below_0(self):
        m = normalize_material({"color": [-0.5, 0.0, 0.0]})
        assert m["color"][0] == pytest.approx(0.0)

    def test_none_uses_defaults(self):
        m = normalize_material(None)
        assert len(m["color"]) == 3

    def test_non_dict_raises(self):
        with pytest.raises(TypeError):
            normalize_material("red")

    def test_texture_enabled_flag(self):
        m = normalize_material({"texture": {"enabled": True, "path": "/tmp/tex.png"}})
        assert m["texture"]["enabled"] is True
        assert m["texture"]["path"] == "/tmp/tex.png"


# ---------------------------------------------------------------------------
# validate_and_normalize_scene_ir
# ---------------------------------------------------------------------------
class TestValidateAndNormalizeSceneIR:
    def test_valid_scene_passes(self):
        result = validate_and_normalize_scene_ir(deepcopy(BASE))
        assert result["node_type"] == "scene"

    def test_non_dict_raises(self):
        with pytest.raises(TypeError):
            validate_and_normalize_scene_ir("not a dict")

    def test_wrong_top_level_node_type_raises(self):
        bad = deepcopy(BASE)
        bad["node_type"] = "mesh_object"
        with pytest.raises(ValueError):
            validate_and_normalize_scene_ir(bad)

    def test_child_missing_shape_raises(self):
        scene = deepcopy(BASE)
        scene["children"].append({"node_type": "mesh_object", "name": "bad"})
        with pytest.raises(ValueError):
            validate_and_normalize_scene_ir(scene)

    def test_unsupported_child_node_type_raises(self):
        scene = deepcopy(BASE)
        scene["children"].append({"node_type": "camera", "name": "cam"})
        with pytest.raises(ValueError):
            validate_and_normalize_scene_ir(scene)
