"""
Tests for animation (bounce, spin, lerp) and orbit features added in Phase 2.
"""
import sys
import math
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from copy import deepcopy
from mock_ai_contoller import (
    validate_action,
    apply_action_to_ir,
    detect_procedural_action,
)

EMPTY = {
    "node_type": "scene", "name": "root",
    "window": {"width": 800, "height": 600, "title": "Test"},
    "children": [],
}

_CUBE_NODE = {
    "node_type": "mesh_object",
    "name": "orange_cube",
    "shape": "cube",
    "id": "orange_cube",
    "transform": {"position": [2.0, 0.5, 0.0], "scale": [1.0, 1.0, 1.0]},
    "material": {"color": [1.0, 0.5, 0.0]},
}

_SPHERE_NODE = {
    "node_type": "mesh_object",
    "name": "blue_sphere",
    "shape": "sphere",
    "id": "blue_sphere",
    "transform": {"position": [-1.5, 0.5, 0.0], "scale": [1.0, 1.0, 1.0]},
    "material": {"color": [0.0, 0.0, 1.0]},
}

SCENE_WITH_CUBE = {
    "node_type": "scene", "name": "root",
    "window": {"width": 800, "height": 600, "title": "Test"},
    "children": [deepcopy(_CUBE_NODE)],
}

SCENE_WITH_BOTH = {
    "node_type": "scene", "name": "root",
    "window": {"width": 800, "height": 600, "title": "Test"},
    "children": [deepcopy(_CUBE_NODE), deepcopy(_SPHERE_NODE)],
}


# ---------------------------------------------------------------------------
# validate_action — animate_object is an accepted action type
# ---------------------------------------------------------------------------

def test_validate_accepts_animate_bounce():
    validate_action({"action": "animate_object", "target": "cube", "animation_type": "bounce"})


def test_validate_accepts_animate_spin():
    validate_action({"action": "animate_object", "target": "cube", "animation_type": "spin"})


def test_validate_accepts_animate_lerp():
    validate_action({"action": "animate_object", "target": "cube", "animation_type": "lerp"})


# ---------------------------------------------------------------------------
# animate_object — bounce
# ---------------------------------------------------------------------------

class TestAnimateBounce:
    def _apply(self, scene=None, **overrides):
        action = {"action": "animate_object", "target": "cube",
                  "animation_type": "bounce", "amplitude": 0.5, "speed": 2.0}
        action.update(overrides)
        return apply_action_to_ir(deepcopy(scene or SCENE_WITH_CUBE), action)

    def test_bounce_sets_animation_field(self):
        result = self._apply()
        assert "animation" in result["children"][0]

    def test_bounce_type_is_bounce(self):
        result = self._apply()
        assert result["children"][0]["animation"]["type"] == "bounce"

    def test_bounce_has_amplitude(self):
        result = self._apply()
        anim = result["children"][0]["animation"]
        assert "amplitude" in anim
        assert float(anim["amplitude"]) > 0

    def test_bounce_has_speed(self):
        result = self._apply()
        anim = result["children"][0]["animation"]
        assert "speed" in anim
        assert float(anim["speed"]) > 0

    def test_bounce_custom_amplitude(self):
        result = self._apply(amplitude=1.2)
        assert pytest.approx(result["children"][0]["animation"]["amplitude"], abs=0.01) == 1.2

    def test_bounce_custom_speed(self):
        result = self._apply(speed=3.5)
        assert pytest.approx(result["children"][0]["animation"]["speed"], abs=0.01) == 3.5

    def test_bounce_does_not_add_object(self):
        result = self._apply()
        assert len(result["children"]) == 1

    def test_bounce_does_not_mutate_input(self):
        original = deepcopy(SCENE_WITH_CUBE)
        apply_action_to_ir(original, {"action": "animate_object", "target": "cube",
                                       "animation_type": "bounce"})
        assert "animation" not in SCENE_WITH_CUBE["children"][0]

    def test_bounce_target_not_found_raises(self):
        with pytest.raises(Exception):
            apply_action_to_ir(deepcopy(EMPTY), {
                "action": "animate_object", "target": "cube",
                "animation_type": "bounce",
            })


# ---------------------------------------------------------------------------
# animate_object — spin
# ---------------------------------------------------------------------------

class TestAnimateSpin:
    def _apply(self, scene=None, **overrides):
        action = {"action": "animate_object", "target": "cube",
                  "animation_type": "spin", "speed": 1.0, "axis": [0, 1, 0]}
        action.update(overrides)
        return apply_action_to_ir(deepcopy(scene or SCENE_WITH_CUBE), action)

    def test_spin_sets_animation_field(self):
        result = self._apply()
        assert "animation" in result["children"][0]

    def test_spin_type_is_spin(self):
        result = self._apply()
        assert result["children"][0]["animation"]["type"] == "spin"

    def test_spin_has_speed(self):
        result = self._apply()
        anim = result["children"][0]["animation"]
        assert "speed" in anim
        assert float(anim["speed"]) > 0

    def test_spin_has_3d_axis(self):
        result = self._apply()
        anim = result["children"][0]["animation"]
        assert "axis" in anim
        assert len(anim["axis"]) == 3

    def test_spin_default_axis_is_y(self):
        result = self._apply()
        axis = result["children"][0]["animation"]["axis"]
        assert axis[1] == 1 and axis[0] == 0 and axis[2] == 0

    def test_spin_custom_x_axis(self):
        result = self._apply(axis=[1, 0, 0])
        axis = result["children"][0]["animation"]["axis"]
        assert axis[0] == 1 and axis[1] == 0

    def test_spin_does_not_add_object(self):
        result = self._apply()
        assert len(result["children"]) == 1

    def test_spin_does_not_mutate_input(self):
        original = deepcopy(SCENE_WITH_CUBE)
        apply_action_to_ir(original, {"action": "animate_object", "target": "cube",
                                       "animation_type": "spin"})
        assert "animation" not in SCENE_WITH_CUBE["children"][0]


# ---------------------------------------------------------------------------
# animate_object — lerp
# ---------------------------------------------------------------------------

class TestAnimateLerp:
    def _apply(self, scene=None, **overrides):
        action = {"action": "animate_object", "target": "cube",
                  "animation_type": "lerp", "direction": "right",
                  "distance": 2.0, "duration": 3.0}
        action.update(overrides)
        return apply_action_to_ir(deepcopy(scene or SCENE_WITH_CUBE), action)

    def test_lerp_sets_animation_field(self):
        result = self._apply()
        assert "animation" in result["children"][0]

    def test_lerp_type_is_lerp(self):
        result = self._apply()
        assert result["children"][0]["animation"]["type"] == "lerp"

    def test_lerp_has_from_and_to(self):
        result = self._apply()
        anim = result["children"][0]["animation"]
        assert "from" in anim and "to" in anim

    def test_lerp_from_and_to_are_3d(self):
        result = self._apply()
        anim = result["children"][0]["animation"]
        assert len(anim["from"]) == 3 and len(anim["to"]) == 3

    def test_lerp_from_matches_object_position(self):
        result = self._apply()
        anim = result["children"][0]["animation"]
        obj_pos = _CUBE_NODE["transform"]["position"]
        assert anim["from"] == pytest.approx(obj_pos, abs=0.01)

    def test_lerp_to_differs_from_from(self):
        result = self._apply()
        anim = result["children"][0]["animation"]
        assert anim["from"] != anim["to"]

    def test_lerp_has_positive_duration(self):
        result = self._apply()
        anim = result["children"][0]["animation"]
        assert "duration" in anim
        assert float(anim["duration"]) > 0

    def test_lerp_direction_right_moves_x(self):
        result = self._apply(direction="right")
        anim = result["children"][0]["animation"]
        assert anim["to"][0] > anim["from"][0]

    def test_lerp_direction_up_moves_y(self):
        result = self._apply(direction="up")
        anim = result["children"][0]["animation"]
        assert anim["to"][1] > anim["from"][1]

    def test_lerp_does_not_mutate_input(self):
        original = deepcopy(SCENE_WITH_CUBE)
        apply_action_to_ir(original, {"action": "animate_object", "target": "cube",
                                       "animation_type": "lerp"})
        assert "animation" not in SCENE_WITH_CUBE["children"][0]

    @pytest.mark.parametrize("direction", ["right", "left", "up", "down", "forward", "backward"])
    def test_lerp_all_directions_valid(self, direction):
        result = self._apply(direction=direction)
        assert "animation" in result["children"][0]


# ---------------------------------------------------------------------------
# orbit — add_object with orbit
# ---------------------------------------------------------------------------

class TestOrbitObject:
    def _orbit(self, shape="sphere", color="yellow", target="cube"):
        return apply_action_to_ir(deepcopy(SCENE_WITH_CUBE), {
            "action": "add_object",
            "object_type": shape,
            "color": color,
            "orbit": {"target": target, "radius": 3.0, "speed": 0.8},
        })

    def test_orbit_adds_second_object(self):
        result = self._orbit()
        assert len(result["children"]) == 2

    def test_orbit_new_object_has_orbit_field(self):
        result = self._orbit()
        new_obj = result["children"][-1]
        assert "orbit" in new_obj

    def test_orbit_has_center_list(self):
        result = self._orbit()
        center = result["children"][-1]["orbit"]["center"]
        assert isinstance(center, list) and len(center) == 3

    def test_orbit_center_matches_cube_position(self):
        result = self._orbit(target="cube")
        center = result["children"][-1]["orbit"]["center"]
        cube_pos = _CUBE_NODE["transform"]["position"]
        assert center == pytest.approx(cube_pos, abs=0.01)

    def test_orbit_has_positive_radius(self):
        result = self._orbit()
        assert float(result["children"][-1]["orbit"]["radius"]) > 0

    def test_orbit_has_positive_speed(self):
        result = self._orbit()
        assert float(result["children"][-1]["orbit"]["speed"]) > 0

    def test_orbit_shape_is_correct(self):
        result = self._orbit(shape="sphere")
        assert result["children"][-1]["shape"] == "sphere"

    def test_orbit_shape_cone(self):
        result = self._orbit(shape="cone")
        assert result["children"][-1]["shape"] == "cone"

    def test_orbit_unknown_target_defaults_to_origin(self):
        result = self._orbit(target="nonexistent")
        center = result["children"][-1]["orbit"]["center"]
        assert center == pytest.approx([0.0, 0.0, 0.0], abs=0.01)

    def test_orbit_does_not_remove_original(self):
        result = self._orbit()
        assert result["children"][0]["name"] == "orange_cube"

    def test_orbit_does_not_mutate_input(self):
        scene = deepcopy(SCENE_WITH_CUBE)
        apply_action_to_ir(scene, {
            "action": "add_object", "object_type": "sphere",
            "color": "yellow",
            "orbit": {"target": "cube", "radius": 3.0, "speed": 0.8},
        })
        assert "orbit" not in SCENE_WITH_CUBE["children"][0]
        assert len(SCENE_WITH_CUBE["children"]) == 1


# ---------------------------------------------------------------------------
# orbit — add_light with orbit
# ---------------------------------------------------------------------------

class TestOrbitLight:
    def _orbit_light(self, target="cube"):
        return apply_action_to_ir(deepcopy(SCENE_WITH_CUBE), {
            "action": "add_light",
            "light_type": "point",
            "color": "white",
            "intensity": 1.5,
            "orbit": {"target": target, "radius": 3.0, "speed": 0.8, "height": 2.5},
        })

    def test_orbit_light_adds_light_node(self):
        result = self._orbit_light()
        lights = [c for c in result["children"] if c.get("node_type") == "light"]
        assert len(lights) == 1

    def test_orbit_light_has_orbit_field(self):
        result = self._orbit_light()
        light = next(c for c in result["children"] if c.get("node_type") == "light")
        assert "orbit" in light

    def test_orbit_light_center_matches_target(self):
        result = self._orbit_light(target="cube")
        light = next(c for c in result["children"] if c.get("node_type") == "light")
        center = light["orbit"]["center"]
        cube_pos = _CUBE_NODE["transform"]["position"]
        assert center == pytest.approx(cube_pos, abs=0.01)

    def test_orbit_light_has_height(self):
        result = self._orbit_light()
        light = next(c for c in result["children"] if c.get("node_type") == "light")
        assert "height" in light["orbit"]
        assert float(light["orbit"]["height"]) > 0

    def test_orbit_light_has_radius(self):
        result = self._orbit_light()
        light = next(c for c in result["children"] if c.get("node_type") == "light")
        assert float(light["orbit"]["radius"]) > 0

    def test_orbit_light_preserves_cube(self):
        result = self._orbit_light()
        cubes = [c for c in result["children"] if c.get("shape") == "cube"]
        assert len(cubes) == 1

    def test_orbit_light_does_not_mutate_input(self):
        scene = deepcopy(SCENE_WITH_CUBE)
        apply_action_to_ir(scene, {
            "action": "add_light", "light_type": "point",
            "color": "white", "intensity": 1.5,
            "orbit": {"target": "cube", "radius": 3.0, "speed": 0.8, "height": 2.5},
        })
        assert len(SCENE_WITH_CUBE["children"]) == 1


# ---------------------------------------------------------------------------
# detect_procedural_action — NL command detection
# ---------------------------------------------------------------------------

class TestDetectBounce:
    def test_bounce_word(self):
        a = detect_procedural_action("make the cube bounce")
        assert a is not None and a.get("action") == "animate_object"
        assert a.get("animation_type") == "bounce"

    def test_go_up_and_down(self):
        a = detect_procedural_action("make the sphere go up and down")
        assert a is not None and a.get("animation_type") == "bounce"

    def test_bob(self):
        a = detect_procedural_action("make the sphere bob")
        assert a is not None and a.get("animation_type") == "bounce"

    def test_bob_up_and_down(self):
        a = detect_procedural_action("make it bob up and down")
        assert a is not None and a.get("animation_type") == "bounce"

    def test_jump(self):
        a = detect_procedural_action("make the cube jump")
        assert a is not None and a.get("animation_type") == "bounce"

    def test_move_up_and_down(self):
        a = detect_procedural_action("make the cube move up and down")
        assert a is not None and a.get("animation_type") == "bounce"

    def test_bounce_has_amplitude(self):
        a = detect_procedural_action("make the cube bounce")
        assert a is not None and "amplitude" in a

    def test_bounce_has_speed(self):
        a = detect_procedural_action("make the cube bounce")
        assert a is not None and "speed" in a


class TestDetectSpin:
    def test_spin_word(self):
        a = detect_procedural_action("make the cube spin")
        assert a is not None and a.get("animation_type") == "spin"

    def test_spin_on_axis(self):
        a = detect_procedural_action("make the cube spin on its axis")
        assert a is not None and a.get("animation_type") == "spin"

    def test_rotate_continuously(self):
        a = detect_procedural_action("make the cube rotate continuously")
        assert a is not None and a.get("animation_type") == "spin"

    def test_rotate_forever(self):
        a = detect_procedural_action("make the sphere rotate forever")
        assert a is not None and a.get("animation_type") == "spin"

    def test_keep_spinning(self):
        a = detect_procedural_action("keep spinning the cube")
        assert a is not None and a.get("animation_type") == "spin"

    def test_rotate_on_axis(self):
        a = detect_procedural_action("make the cube rotate on the axis")
        assert a is not None and a.get("animation_type") == "spin"

    def test_spin_has_axis_list(self):
        a = detect_procedural_action("make the cube spin")
        assert a is not None and "axis" in a and len(a["axis"]) == 3

    def test_spin_default_y_axis(self):
        a = detect_procedural_action("make the cube spin")
        assert a is not None and a["axis"][1] == 1


class TestDetectLerp:
    def test_back_and_forth(self):
        a = detect_procedural_action("make the cube move back and forth")
        assert a is not None and a.get("animation_type") == "lerp"

    def test_smoothly(self):
        a = detect_procedural_action("make the cube move smoothly to the right")
        assert a is not None and a.get("animation_type") == "lerp"

    def test_interpolate(self):
        a = detect_procedural_action("interpolate the cube position")
        assert a is not None and a.get("animation_type") == "lerp"

    def test_slide(self):
        a = detect_procedural_action("make the cube slide to the left")
        assert a is not None and a.get("animation_type") == "lerp"

    def test_lerp_has_direction(self):
        a = detect_procedural_action("make the cube move back and forth")
        assert a is not None and "direction" in a

    def test_lerp_has_duration(self):
        a = detect_procedural_action("make the cube slide")
        assert a is not None and "duration" in a


class TestDetectOrbit:
    def test_orbits_keyword(self):
        a = detect_procedural_action("add a sphere that orbits the cube")
        assert a is not None and a.get("action") == "add_object"

    def test_rotates_around(self):
        a = detect_procedural_action("add a sphere that rotates around the cube")
        assert a is not None and a.get("action") == "add_object"

    def test_circles(self):
        a = detect_procedural_action("add a sphere that circles the cube")
        assert a is not None and a.get("action") == "add_object"

    def test_revolves_around(self):
        a = detect_procedural_action("add a sphere that revolves around the cube")
        assert a is not None and a.get("action") == "add_object"

    def test_goes_around(self):
        a = detect_procedural_action("add a sphere that goes around the cube")
        assert a is not None

    def test_orbit_shape_is_sphere(self):
        a = detect_procedural_action("add a sphere that orbits the cube")
        assert a is not None and a.get("object_type") == "sphere"

    def test_orbit_target_is_cube(self):
        a = detect_procedural_action("add a sphere that orbits the cube")
        assert a is not None
        orbit = a.get("orbit", {})
        assert orbit.get("target") == "cube"

    def test_orbit_light_add_light(self):
        a = detect_procedural_action("add a light that rotates around the cube")
        assert a is not None and a.get("action") == "add_light"

    def test_orbit_spotlight_add_light(self):
        a = detect_procedural_action("add a spotlight that revolves around the sphere")
        assert a is not None and a.get("action") == "add_light"

    def test_orbit_light_target_is_cube(self):
        a = detect_procedural_action("add a light that orbits the cube")
        orbit = a.get("orbit", {})
        assert orbit.get("target") == "cube"

    def test_orbit_cone_around_sphere(self):
        a = detect_procedural_action("add a cone that orbits the sphere")
        assert a is not None and a.get("object_type") == "cone"
        assert a.get("orbit", {}).get("target") == "sphere"

    def test_orbit_light_has_height(self):
        a = detect_procedural_action("add a light that rotates around the cube")
        assert a is not None
        orbit = a.get("orbit", {})
        assert "height" in orbit


class TestDetectModelLoading:
    def test_load_chameleon_if_file_exists(self):
        a = detect_procedural_action("load a chameleon")
        # Returns action if model file exists, else None (graceful degradation)
        if a is not None:
            assert a.get("action") == "add_custom_model"

    def test_add_chameleon_if_file_exists(self):
        a = detect_procedural_action("add a chameleon")
        if a is not None:
            assert a.get("action") == "add_custom_model"

    def test_model_file_extension_detected(self):
        a = detect_procedural_action("load my_model.usdz")
        assert a is not None and a.get("action") == "add_custom_model"
        assert "my_model.usdz" in a.get("model_path", "")

    def test_obj_extension_detected(self):
        a = detect_procedural_action("import scene.obj")
        assert a is not None and a.get("action") == "add_custom_model"

    def test_usd_extension_detected(self):
        a = detect_procedural_action("load assets/building.usd")
        assert a is not None and a.get("action") == "add_custom_model"


# ---------------------------------------------------------------------------
# Code generation — animated objects produce valid Python
# ---------------------------------------------------------------------------

def test_code_gen_bounce_is_valid_python():
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
    from code_generator import generate_scene_script

    ir = {
        "node_type": "scene", "name": "root",
        "window": {"width": 800, "height": 600, "title": "Bounce Test"},
        "children": [
            {
                "node_type": "mesh_object", "name": "bouncer", "shape": "cube",
                "transform": {"position": [0.0, 0.5, 0.0], "scale": [1.0, 1.0, 1.0]},
                "material": {"color": [1.0, 0.0, 0.0]},
                "animation": {"type": "bounce", "amplitude": 0.5, "speed": 2.0},
            }
        ],
    }
    script = generate_scene_script(ir)
    compile(script, "bounce_scene.py", "exec")  # raises SyntaxError if invalid


def test_code_gen_spin_is_valid_python():
    from code_generator import generate_scene_script

    ir = {
        "node_type": "scene", "name": "root",
        "window": {"width": 800, "height": 600, "title": "Spin Test"},
        "children": [
            {
                "node_type": "mesh_object", "name": "spinner", "shape": "sphere",
                "transform": {"position": [0.0, 0.5, 0.0], "scale": [1.0, 1.0, 1.0]},
                "material": {"color": [0.0, 0.5, 1.0]},
                "animation": {"type": "spin", "speed": 1.0, "axis": [0, 1, 0]},
            }
        ],
    }
    script = generate_scene_script(ir)
    compile(script, "spin_scene.py", "exec")


def test_code_gen_lerp_is_valid_python():
    from code_generator import generate_scene_script

    ir = {
        "node_type": "scene", "name": "root",
        "window": {"width": 800, "height": 600, "title": "Lerp Test"},
        "children": [
            {
                "node_type": "mesh_object", "name": "slider", "shape": "cube",
                "transform": {"position": [0.0, 0.5, 0.0], "scale": [1.0, 1.0, 1.0]},
                "material": {"color": [0.0, 1.0, 0.0]},
                "animation": {
                    "type": "lerp",
                    "from": [0.0, 0.5, 0.0],
                    "to":   [3.0, 0.5, 0.0],
                    "duration": 2.0,
                },
            }
        ],
    }
    script = generate_scene_script(ir)
    compile(script, "lerp_scene.py", "exec")


def test_code_gen_orbit_object_is_valid_python():
    from code_generator import generate_scene_script

    ir = {
        "node_type": "scene", "name": "root",
        "window": {"width": 800, "height": 600, "title": "Orbit Test"},
        "children": [
            {
                "node_type": "mesh_object", "name": "cube_1", "shape": "cube",
                "transform": {"position": [0.0, 0.5, 0.0], "scale": [1.0, 1.0, 1.0]},
                "material": {"color": [1.0, 0.0, 0.0]},
            },
            {
                "node_type": "mesh_object", "name": "orbiter", "shape": "sphere",
                "transform": {"position": [3.0, 0.5, 0.0], "scale": [0.5, 0.5, 0.5]},
                "material": {"color": [0.0, 0.5, 1.0]},
                "orbit": {"center": [0.0, 0.0, 0.0], "radius": 3.0, "speed": 0.8},
            },
        ],
    }
    script = generate_scene_script(ir)
    compile(script, "orbit_scene.py", "exec")


def test_code_gen_orbit_contains_cos_sin():
    from code_generator import generate_scene_script

    ir = {
        "node_type": "scene", "name": "root",
        "window": {"width": 800, "height": 600, "title": "Orbit Test"},
        "children": [
            {
                "node_type": "mesh_object", "name": "orbiter", "shape": "sphere",
                "transform": {"position": [3.0, 0.5, 0.0], "scale": [0.5, 0.5, 0.5]},
                "material": {"color": [0.0, 0.5, 1.0]},
                "orbit": {"center": [0.0, 0.0, 0.0], "radius": 3.0, "speed": 0.8},
            },
        ],
    }
    script = generate_scene_script(ir)
    assert "np.cos" in script or "cos(" in script
    assert "np.sin" in script or "sin(" in script


def test_code_gen_bounce_contains_sin():
    from code_generator import generate_scene_script

    ir = {
        "node_type": "scene", "name": "root",
        "window": {"width": 800, "height": 600, "title": "Bounce Test"},
        "children": [
            {
                "node_type": "mesh_object", "name": "bouncer", "shape": "cube",
                "transform": {"position": [0.0, 0.5, 0.0], "scale": [1.0, 1.0, 1.0]},
                "material": {"color": [1.0, 0.0, 0.0]},
                "animation": {"type": "bounce", "amplitude": 0.5, "speed": 2.0},
            }
        ],
    }
    script = generate_scene_script(ir)
    assert "np.sin" in script or "sin(" in script
    assert "time.time()" in script


def test_code_gen_spin_contains_rotate():
    from code_generator import generate_scene_script

    ir = {
        "node_type": "scene", "name": "root",
        "window": {"width": 800, "height": 600, "title": "Spin Test"},
        "children": [
            {
                "node_type": "mesh_object", "name": "spinner", "shape": "cube",
                "transform": {"position": [0.0, 0.5, 0.0], "scale": [1.0, 1.0, 1.0]},
                "material": {"color": [1.0, 0.0, 0.0]},
                "animation": {"type": "spin", "speed": 1.5, "axis": [0, 1, 0]},
            }
        ],
    }
    script = generate_scene_script(ir)
    assert "util.rotate" in script
    assert "time.time()" in script


# ---------------------------------------------------------------------------
# IR round-trip: orbit and animation fields survive normalize_node
# ---------------------------------------------------------------------------

def test_orbit_field_survives_code_generator_normalize():
    from code_generator import generate_scene_script

    ir = {
        "node_type": "scene", "name": "root",
        "window": {"width": 800, "height": 600, "title": "Test"},
        "children": [
            {
                "node_type": "mesh_object", "name": "orbiter", "shape": "sphere",
                "transform": {"position": [3.0, 0.5, 0.0], "scale": [0.5, 0.5, 0.5]},
                "material": {"color": [0.0, 0.5, 1.0]},
                "orbit": {"center": [1.0, 0.0, 0.0], "radius": 4.0, "speed": 1.2},
            },
        ],
    }
    script = generate_scene_script(ir)
    # The custom radius and speed should appear in the generated code
    assert "4.0" in script
    assert "1.2" in script


def test_animation_field_survives_code_generator_normalize():
    from code_generator import generate_scene_script

    ir = {
        "node_type": "scene", "name": "root",
        "window": {"width": 800, "height": 600, "title": "Test"},
        "children": [
            {
                "node_type": "mesh_object", "name": "bouncer", "shape": "cube",
                "transform": {"position": [0.0, 0.5, 0.0], "scale": [1.0, 1.0, 1.0]},
                "material": {"color": [1.0, 0.0, 0.0]},
                "animation": {"type": "bounce", "amplitude": 1.7, "speed": 3.3},
            }
        ],
    }
    script = generate_scene_script(ir)
    assert "1.7" in script
    assert "3.3" in script
