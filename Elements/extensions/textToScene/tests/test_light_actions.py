"""
Tests for add_light, delete_light, move_light,
change_light_color and change_light_intensity actions.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from copy import deepcopy
from mock_ai_contoller import apply_action_to_ir, collect_lights

EMPTY = {
    "node_type": "scene", "name": "root",
    "window": {"width": 800, "height": 600, "title": "Test"},
    "children": [],
}


class TestAddLight:
    def test_add_point_light_creates_node(self):
        result = apply_action_to_ir(deepcopy(EMPTY), {
            "action": "add_light", "light_type": "point", "color": "white", "intensity": 1.0
        })
        lights = collect_lights(result)
        assert len(lights) == 1
        assert lights[0]["node_type"] == "light"
        assert lights[0]["light_type"] == "point"

    def test_add_directional_light(self):
        result = apply_action_to_ir(deepcopy(EMPTY), {
            "action": "add_light", "light_type": "directional",
            "color": "white", "direction": [1.0, -1.0, 0.0]
        })
        lights = collect_lights(result)
        assert lights[0]["light_type"] == "directional"
        assert lights[0]["properties"]["direction"] == [1.0, -1.0, 0.0]

    def test_add_light_default_type_is_point(self):
        result = apply_action_to_ir(deepcopy(EMPTY), {"action": "add_light"})
        assert collect_lights(result)[0]["light_type"] == "point"

    def test_add_light_invalid_type_raises(self):
        with pytest.raises(ValueError, match="light_type"):
            apply_action_to_ir(deepcopy(EMPTY), {
                "action": "add_light", "light_type": "ambient"
            })

    def test_add_light_sets_position(self):
        result = apply_action_to_ir(deepcopy(EMPTY), {
            "action": "add_light", "light_type": "point",
            "position": [1.0, 2.0, 3.0]
        })
        pos = collect_lights(result)[0]["properties"]["position"]
        assert pos == [1.0, 2.0, 3.0]

    def test_add_light_sets_color(self):
        result = apply_action_to_ir(deepcopy(EMPTY), {
            "action": "add_light", "light_type": "point", "color": "red"
        })
        color = collect_lights(result)[0]["properties"]["color"]
        assert color == [1.0, 0.0, 0.0]

    def test_add_light_sets_intensity(self):
        result = apply_action_to_ir(deepcopy(EMPTY), {
            "action": "add_light", "light_type": "point", "intensity": 0.5
        })
        assert collect_lights(result)[0]["properties"]["intensity"] == 0.5

    def test_add_light_does_not_mutate_input(self):
        scene = deepcopy(EMPTY)
        original = deepcopy(scene)
        apply_action_to_ir(scene, {"action": "add_light"})
        assert scene == original

    def test_add_two_lights_get_unique_names(self):
        scene = deepcopy(EMPTY)
        scene = apply_action_to_ir(scene, {"action": "add_light"})
        scene = apply_action_to_ir(scene, {"action": "add_light"})
        lights = collect_lights(scene)
        assert len(lights) == 2
        assert lights[0]["name"] != lights[1]["name"]


class TestDeleteLight:
    def _scene_with_light(self):
        s = deepcopy(EMPTY)
        s["children"].append({
            "node_type": "light", "name": "light_1", "id": "light_1",
            "light_type": "point",
            "properties": {"position": [2.0, 5.0, 2.0], "color": [1.0, 1.0, 1.0], "intensity": 1.0},
        })
        return s

    def test_delete_light_removes_node(self):
        result = apply_action_to_ir(self._scene_with_light(), {
            "action": "delete_light", "target": "light_1"
        })
        assert collect_lights(result) == []

    def test_delete_light_unknown_target_raises(self):
        with pytest.raises(ValueError, match="Could not resolve"):
            apply_action_to_ir(self._scene_with_light(), {
                "action": "delete_light", "target": "nonexistent"
            })

    def test_delete_light_does_not_mutate_input(self):
        scene = self._scene_with_light()
        original = deepcopy(scene)
        apply_action_to_ir(scene, {"action": "delete_light", "target": "light_1"})
        assert scene == original


class TestModifyLight:
    def _scene_with_light(self):
        s = deepcopy(EMPTY)
        s["children"].append({
            "node_type": "light", "name": "light_1", "id": "light_1",
            "light_type": "point",
            "properties": {
                "position": [2.0, 5.0, 2.0],
                "color": [1.0, 1.0, 1.0],
                "intensity": 1.0,
                "direction": [1.0, -1.0, -1.0],
            },
        })
        return s

    def test_move_light_updates_position(self):
        result = apply_action_to_ir(self._scene_with_light(), {
            "action": "move_light", "target": "light_1", "position": [0.0, 10.0, 0.0]
        })
        pos = collect_lights(result)[0]["properties"]["position"]
        assert pos == [0.0, 10.0, 0.0]

    def test_move_light_invalid_position_raises(self):
        with pytest.raises(ValueError, match="position"):
            apply_action_to_ir(self._scene_with_light(), {
                "action": "move_light", "target": "light_1", "position": [0.0, 1.0]
            })

    def test_change_light_color(self):
        result = apply_action_to_ir(self._scene_with_light(), {
            "action": "change_light_color", "target": "light_1", "color": "red"
        })
        assert collect_lights(result)[0]["properties"]["color"] == [1.0, 0.0, 0.0]

    def test_change_light_intensity(self):
        result = apply_action_to_ir(self._scene_with_light(), {
            "action": "change_light_intensity", "target": "light_1", "intensity": 2.0
        })
        assert collect_lights(result)[0]["properties"]["intensity"] == 2.0

    def test_modify_light_does_not_mutate_input(self):
        scene = self._scene_with_light()
        original = deepcopy(scene)
        apply_action_to_ir(scene, {
            "action": "change_light_intensity", "target": "light_1", "intensity": 99.0
        })
        assert scene == original
