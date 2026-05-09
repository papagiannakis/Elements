"""
Tests for the pure helper functions in mock_ai_contoller:
naming, ordering, colour/shape parsing, node traversal, ID stability,
and action normalisation — no file I/O involved.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from copy import deepcopy
from mock_ai_contoller import (
    make_unique_name,
    next_object_order,
    color_name_from_text,
    shape_from_text,
    normalize_action,
    collect_mesh_objects,
    walk_nodes,
    ensure_stable_object_ids,
    positions_overlap,
    color_matches,
    normalize_group_name,
)

EMPTY_SCENE = {
    "node_type": "scene", "name": "root",
    "window": {"width": 800, "height": 600, "title": "Test"},
    "children": [],
}


def _scene_with_cubes(*names):
    scene = deepcopy(EMPTY_SCENE)
    for i, name in enumerate(names, start=1):
        scene["children"].append({
            "node_type": "mesh_object",
            "name": name, "id": name,
            "created_order": i,
            "shape": "cube",
            "transform": {"position": [float(i), 0.5, 0.0], "scale": [1.0, 1.0, 1.0]},
            "material": {"color": [1.0, 0.0, 0.0]},
        })
    return scene


# ---------------------------------------------------------------------------
# make_unique_name
# ---------------------------------------------------------------------------
class TestMakeUniqueName:
    def test_first_name_has_index_1(self):
        name = make_unique_name(deepcopy(EMPTY_SCENE), "cube")
        assert name == "cube_1"

    def test_increments_when_name_taken(self):
        scene = _scene_with_cubes("cube_1")
        name = make_unique_name(scene, "cube")
        assert name == "cube_2"

    def test_skips_gaps(self):
        scene = _scene_with_cubes("cube_1", "cube_2", "cube_3")
        name = make_unique_name(scene, "cube")
        assert name == "cube_4"

    def test_different_prefix_starts_at_1(self):
        scene = _scene_with_cubes("cube_1")
        name = make_unique_name(scene, "sphere")
        assert name == "sphere_1"


# ---------------------------------------------------------------------------
# next_object_order
# ---------------------------------------------------------------------------
class TestNextObjectOrder:
    def test_empty_scene_returns_1(self):
        assert next_object_order(deepcopy(EMPTY_SCENE)) == 1

    def test_returns_max_plus_one(self):
        scene = _scene_with_cubes("a", "b", "c")  # created_order 1, 2, 3
        assert next_object_order(scene) == 4

    def test_handles_missing_created_order(self):
        scene = deepcopy(EMPTY_SCENE)
        scene["children"].append({"node_type": "mesh_object", "name": "x", "shape": "cube"})
        assert next_object_order(scene) == 1


# ---------------------------------------------------------------------------
# color_name_from_text
# ---------------------------------------------------------------------------
class TestColorNameFromText:
    @pytest.mark.parametrize("text,expected", [
        ("add a red cube", "red"),
        ("blue sphere please", "blue"),
        ("I want a GREEN object", "green"),
        ("yellow pyramid", "yellow"),
        ("white plane", "white"),
    ])
    def test_detects_colour(self, text, expected):
        assert color_name_from_text(text) == expected

    def test_returns_none_when_no_colour(self):
        assert color_name_from_text("add a cube") is None

    def test_returns_none_for_empty_string(self):
        assert color_name_from_text("") is None


# ---------------------------------------------------------------------------
# shape_from_text
# ---------------------------------------------------------------------------
class TestShapeFromText:
    @pytest.mark.parametrize("text,expected", [
        ("add a cube", "cube"),
        ("put a sphere here", "sphere"),
        ("make a cylinder", "cylinder"),
        ("place a pyramid", "pyramid"),
        ("draw a plane", "plane"),
        ("I need a cone", "cone"),
    ])
    def test_detects_shape(self, text, expected):
        assert shape_from_text(text) == expected

    def test_returns_none_when_no_shape(self):
        assert shape_from_text("add something") is None


# ---------------------------------------------------------------------------
# normalize_action
# ---------------------------------------------------------------------------
class TestNormalizeAction:
    def test_renames_object_id_to_id(self):
        action = {"action": "delete_object", "object_id": "cube_1"}
        result = normalize_action(action)
        assert result["id"] == "cube_1"
        assert "object_id" not in result

    def test_renames_name_to_scene_name_for_save(self):
        action = {"action": "save_scene", "name": "my_scene"}
        result = normalize_action(action)
        assert result["scene_name"] == "my_scene"

    def test_renames_name_to_prefab_name_for_add_prefab(self):
        action = {"action": "add_prefab", "name": "house"}
        result = normalize_action(action)
        assert result["prefab_name"] == "house"

    def test_renames_new_position_to_position(self):
        action = {"action": "move_object", "new_position": [1.0, 0.5, 0.0]}
        result = normalize_action(action)
        assert result["position"] == [1.0, 0.5, 0.0]

    @pytest.mark.parametrize("alias,canonical", [
        ("back", "backward"),
        ("front", "forward"),
        ("to the back", "backward"),
        ("to the front", "forward"),
    ])
    def test_normalizes_direction_aliases(self, alias, canonical):
        action = {"action": "move_object", "direction": alias}
        result = normalize_action(action)
        assert result["direction"] == canonical

    def test_does_not_touch_unrelated_fields(self):
        action = {"action": "add_object", "object_type": "cube", "color": "red"}
        result = normalize_action(action)
        assert result["object_type"] == "cube"
        assert result["color"] == "red"

    def test_normalizes_sequence_steps_recursively(self):
        action = {
            "action": "action_sequence",
            "action_sequence": [
                {"action": "save_scene", "name": "demo"},
            ],
        }
        result = normalize_action(action)
        assert result["action_sequence"][0]["scene_name"] == "demo"


# ---------------------------------------------------------------------------
# collect_mesh_objects / walk_nodes
# ---------------------------------------------------------------------------
class TestNodeTraversal:
    def test_collect_mesh_objects_flat(self):
        scene = _scene_with_cubes("a", "b", "c")
        objs = collect_mesh_objects(scene)
        assert len(objs) == 3

    def test_collect_mesh_objects_empty(self):
        assert collect_mesh_objects(deepcopy(EMPTY_SCENE)) == []

    def test_collect_mesh_objects_inside_group(self):
        scene = deepcopy(EMPTY_SCENE)
        scene["children"].append({
            "node_type": "group",
            "name": "g1",
            "transform": {"position": [0.0, 0.0, 0.0], "scale": [1.0, 1.0, 1.0]},
            "children": [
                {
                    "node_type": "mesh_object", "name": "cube_in_group",
                    "shape": "cube",
                    "transform": {"position": [0.0, 0.5, 0.0], "scale": [1.0, 1.0, 1.0]},
                    "material": {"color": [1.0, 0.0, 0.0]},
                }
            ],
        })
        objs = collect_mesh_objects(scene)
        assert len(objs) == 1
        assert objs[0]["name"] == "cube_in_group"

    def test_walk_nodes_visits_scene_and_children(self):
        scene = _scene_with_cubes("cube_1", "cube_2")
        all_nodes = list(walk_nodes(scene))
        node_types = [n.get("node_type") for n in all_nodes]
        assert "scene" in node_types
        assert node_types.count("mesh_object") == 2


# ---------------------------------------------------------------------------
# positions_overlap
# ---------------------------------------------------------------------------
class TestPositionsOverlap:
    def test_identical_positions_overlap(self):
        assert positions_overlap([1.0, 0.5, 0.0], [1.0, 0.5, 0.0])

    def test_close_positions_overlap(self):
        assert positions_overlap([1.0, 0.5, 0.0], [1.02, 0.5, 0.0])

    def test_distant_positions_do_not_overlap(self):
        assert not positions_overlap([0.0, 0.5, 0.0], [1.5, 0.5, 0.0])


# ---------------------------------------------------------------------------
# color_matches
# ---------------------------------------------------------------------------
class TestColorMatches:
    def test_exact_match(self):
        assert color_matches([1.0, 0.0, 0.0], [1.0, 0.0, 0.0])

    def test_close_match_within_tolerance(self):
        assert color_matches([1.0, 0.03, 0.0], [1.0, 0.0, 0.0])

    def test_no_match_when_different(self):
        assert not color_matches([0.0, 1.0, 0.0], [1.0, 0.0, 0.0])

    def test_invalid_input_returns_false(self):
        assert not color_matches("red", [1.0, 0.0, 0.0])


# ---------------------------------------------------------------------------
# normalize_group_name
# ---------------------------------------------------------------------------
class TestNormalizeGroupName:
    def test_lowercases(self):
        assert normalize_group_name("MyGroup") == "mygroup"

    def test_replaces_spaces_with_underscore(self):
        assert normalize_group_name("my group") == "my_group"

    def test_strips_whitespace(self):
        assert normalize_group_name("  buildings  ") == "buildings"


# ---------------------------------------------------------------------------
# ensure_stable_object_ids
# ---------------------------------------------------------------------------
class TestEnsureStableObjectIds:
    def test_assigns_ids_to_nodes_missing_them(self):
        scene = deepcopy(EMPTY_SCENE)
        scene["children"].append({
            "node_type": "mesh_object", "name": "cube_1",
            "shape": "cube",
            "transform": {"position": [0.0, 0.5, 0.0], "scale": [1.0, 1.0, 1.0]},
            "material": {"color": [1.0, 0.0, 0.0]},
        })
        result = ensure_stable_object_ids(scene)
        assert result["children"][0]["id"] == "cube_1"

    def test_deduplicates_conflicting_ids(self):
        scene = deepcopy(EMPTY_SCENE)
        for i in range(3):
            scene["children"].append({
                "node_type": "mesh_object", "name": "cube_1", "id": "cube_1",
                "created_order": i + 1,
                "shape": "cube",
                "transform": {"position": [float(i), 0.5, 0.0], "scale": [1.0, 1.0, 1.0]},
                "material": {"color": [1.0, 0.0, 0.0]},
            })
        result = ensure_stable_object_ids(scene)
        ids = [c["id"] for c in result["children"]]
        assert len(ids) == len(set(ids)), "All IDs must be unique after stabilisation"
