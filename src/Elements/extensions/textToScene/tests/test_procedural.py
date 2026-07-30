"""
Tests for the procedural generation actions:
  generate_pattern (ring)
  generate_composite (tree, table, lamp, open-ended with parts)
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
    build_ring_pattern,
    build_tree_composite,
    build_table_composite,
    build_lamp_composite,
    build_open_composite,
    validate_composite_parts,
    resolve_composite_overlaps,
    collect_mesh_objects,
)

EMPTY = {
    "node_type": "scene", "name": "root",
    "window": {"width": 800, "height": 600, "title": "Test"},
    "children": [],
}


# ---------------------------------------------------------------------------
# validate_action — new action types accepted
# ---------------------------------------------------------------------------
def test_validate_accepts_generate_pattern():
    validate_action({
        "action": "generate_pattern",
        "pattern": "ring",
        "object_type": "cube",
        "count": 8,
        "radius": 2.5,
        "color": "red",
    })


def test_validate_accepts_generate_composite():
    validate_action({
        "action": "generate_composite",
        "composite": "tree",
        "object_type": "sphere",
        "color": "green",
    })


# ---------------------------------------------------------------------------
# generate_pattern — ring
# ---------------------------------------------------------------------------
class TestRingPattern:
    def _ring(self, count=8, radius=2.5, object_type="cube", color="red"):
        return apply_action_to_ir(deepcopy(EMPTY), {
            "action": "generate_pattern",
            "pattern": "ring",
            "object_type": object_type,
            "count": count,
            "radius": radius,
            "color": color,
        })

    def test_ring_creates_one_group(self):
        result = self._ring()
        assert len(result["children"]) == 1
        assert result["children"][0]["node_type"] == "group"

    def test_ring_group_has_correct_child_count(self):
        for count in (4, 8, 12):
            result = self._ring(count=count)
            assert len(result["children"][0]["children"]) == count

    @pytest.mark.parametrize("shape", ["cube", "sphere", "cylinder", "cone"])
    def test_ring_children_have_correct_shape(self, shape):
        result = self._ring(object_type=shape)
        for child in result["children"][0]["children"]:
            assert child["shape"] == shape

    def test_ring_children_colour_applied(self):
        result = self._ring(color="blue")
        for child in result["children"][0]["children"]:
            r, g, b = child["material"]["color"]
            assert abs(b - 1.0) < 0.05

    def test_ring_positions_are_on_circle(self):
        radius = 3.0
        count = 8
        result = self._ring(count=count, radius=radius)
        for child in result["children"][0]["children"]:
            x, _y, z = child["transform"]["position"]
            dist = math.sqrt(x ** 2 + z ** 2)
            assert abs(dist - radius) < 0.01, f"Child not on circle: dist={dist}"

    def test_ring_positions_are_evenly_spaced(self):
        count = 8
        result = self._ring(count=count)
        children = result["children"][0]["children"]
        angles = []
        for child in children:
            x, _y, z = child["transform"]["position"]
            angles.append(math.atan2(z, x))
        angles.sort()
        diffs = [angles[i + 1] - angles[i] for i in range(len(angles) - 1)]
        diffs.append(angles[0] + 2 * math.pi - angles[-1])
        expected = 2 * math.pi / count
        for d in diffs:
            assert abs(d - expected) < 0.01, f"Uneven spacing: {d} vs {expected}"

    def test_ring_all_child_names_unique(self):
        result = self._ring(count=12)
        names = [c["name"] for c in result["children"][0]["children"]]
        assert len(names) == len(set(names))

    def test_ring_does_not_mutate_input(self):
        scene = deepcopy(EMPTY)
        apply_action_to_ir(scene, {
            "action": "generate_pattern", "pattern": "ring",
            "object_type": "cube", "count": 6, "radius": 2.0, "color": "red",
        })
        assert scene["children"] == []

    def test_ring_count_clamped_to_minimum_2(self):
        result = self._ring(count=0)
        assert len(result["children"][0]["children"]) >= 2

    def test_ring_count_clamped_to_maximum_32(self):
        result = self._ring(count=100)
        assert len(result["children"][0]["children"]) <= 32

    def test_ring_unknown_pattern_raises(self):
        with pytest.raises(ValueError, match="Unknown pattern"):
            apply_action_to_ir(deepcopy(EMPTY), {
                "action": "generate_pattern",
                "pattern": "spiral",
                "object_type": "cube",
            })


# ---------------------------------------------------------------------------
# generate_composite — tree
# ---------------------------------------------------------------------------
class TestTreeComposite:
    def _tree(self, object_type="cube", color="green"):
        return apply_action_to_ir(deepcopy(EMPTY), {
            "action": "generate_composite",
            "composite": "tree",
            "object_type": object_type,
            "color": color,
        })

    def test_tree_creates_one_group(self):
        result = self._tree()
        assert len(result["children"]) == 1
        assert result["children"][0]["node_type"] == "group"

    def test_tree_has_enough_children(self):
        result = self._tree()
        # trunk (1) + canopy1 (6) + canopy2 (4) + top (1) = 12
        assert len(result["children"][0]["children"]) == 12

    @pytest.mark.parametrize("shape", ["cube", "sphere", "cylinder", "cone", "pyramid"])
    def test_tree_respects_object_type(self, shape):
        result = self._tree(object_type=shape)
        for child in result["children"][0]["children"]:
            assert child["shape"] == shape

    def test_tree_colour_applied_to_all_children(self):
        result = self._tree(color="red")
        for child in result["children"][0]["children"]:
            r, _g, _b = child["material"]["color"]
            assert abs(r - 1.0) < 0.05

    def test_tree_trunk_is_taller_than_wide(self):
        result = self._tree()
        trunk = next(c for c in result["children"][0]["children"] if "trunk" in c["name"])
        sx, sy, sz = trunk["transform"]["scale"]
        assert sy > sx and sy > sz

    def test_tree_trunk_is_lowest_part(self):
        result = self._tree()
        children = result["children"][0]["children"]
        trunk_y = next(c for c in children if "trunk" in c["name"])["transform"]["position"][1]
        for child in children:
            if "trunk" not in child["name"]:
                assert child["transform"]["position"][1] >= trunk_y

    def test_tree_top_is_highest_part(self):
        result = self._tree()
        children = result["children"][0]["children"]
        top_y = next(c for c in children if "top" in c["name"])["transform"]["position"][1]
        for child in children:
            assert child["transform"]["position"][1] <= top_y + 0.01

    def test_tree_all_child_names_unique(self):
        result = self._tree()
        names = [c["name"] for c in result["children"][0]["children"]]
        assert len(names) == len(set(names))

    def test_tree_does_not_mutate_input(self):
        scene = deepcopy(EMPTY)
        apply_action_to_ir(scene, {
            "action": "generate_composite", "composite": "tree",
            "object_type": "cube", "color": "green",
        })
        assert scene["children"] == []

    def test_tree_unknown_composite_raises(self):
        with pytest.raises(ValueError, match="Unknown composite"):
            apply_action_to_ir(deepcopy(EMPTY), {
                "action": "generate_composite",
                "composite": "castle",
                "object_type": "cube",
            })


# ---------------------------------------------------------------------------
# Integration — mixed scene (ring + tree + regular objects)
# ---------------------------------------------------------------------------
def test_ring_and_tree_coexist_in_same_scene():
    scene = deepcopy(EMPTY)
    scene = apply_action_to_ir(scene, {"action": "add_object", "object_type": "cube", "color": "red"})
    scene = apply_action_to_ir(scene, {
        "action": "generate_pattern", "pattern": "ring",
        "object_type": "sphere", "count": 6, "radius": 2.0, "color": "blue",
    })
    scene = apply_action_to_ir(scene, {
        "action": "generate_composite", "composite": "tree",
        "object_type": "cube", "color": "green",
    })
    assert len(scene["children"]) == 3
    node_types = {c["node_type"] for c in scene["children"]}
    assert "mesh_object" in node_types
    assert "group" in node_types


def test_all_mesh_objects_reachable_via_collect():
    scene = deepcopy(EMPTY)
    scene = apply_action_to_ir(scene, {
        "action": "generate_pattern", "pattern": "ring",
        "object_type": "cube", "count": 8, "radius": 2.0, "color": "red",
    })
    scene = apply_action_to_ir(scene, {
        "action": "generate_composite", "composite": "tree",
        "object_type": "sphere", "color": "green",
    })
    all_meshes = collect_mesh_objects(scene)
    # ring: 8, tree: 12
    assert len(all_meshes) == 20


# ---------------------------------------------------------------------------
# generate_composite — table (deterministic)
# ---------------------------------------------------------------------------
class TestTableComposite:
    def _table(self, object_type="cube", color="white"):
        return apply_action_to_ir(deepcopy(EMPTY), {
            "action": "generate_composite",
            "composite": "table",
            "object_type": object_type,
            "color": color,
        })

    def test_table_creates_one_group(self):
        result = self._table()
        assert len(result["children"]) == 1
        assert result["children"][0]["node_type"] == "group"

    def test_table_has_five_children(self):
        result = self._table()
        assert len(result["children"][0]["children"]) == 5

    def test_table_top_is_highest(self):
        result = self._table()
        children = result["children"][0]["children"]
        top = next(c for c in children if "top" in c["name"])
        for child in children:
            if "leg" in child["name"]:
                assert top["transform"]["position"][1] >= child["transform"]["position"][1]

    def test_table_has_four_legs(self):
        result = self._table()
        legs = [c for c in result["children"][0]["children"] if "leg" in c["name"]]
        assert len(legs) == 4

    def test_table_top_is_wider_than_tall(self):
        result = self._table()
        children = result["children"][0]["children"]
        top = next(c for c in children if "top" in c["name"])
        sx, sy, sz = top["transform"]["scale"]
        assert sx > sy

    def test_table_does_not_mutate_input(self):
        scene = deepcopy(EMPTY)
        apply_action_to_ir(scene, {
            "action": "generate_composite", "composite": "table",
            "object_type": "cube", "color": "white",
        })
        assert scene["children"] == []


# ---------------------------------------------------------------------------
# generate_composite — lamp (deterministic)
# ---------------------------------------------------------------------------
class TestLampComposite:
    def _lamp(self, object_type="cube", color="yellow"):
        return apply_action_to_ir(deepcopy(EMPTY), {
            "action": "generate_composite",
            "composite": "lamp",
            "object_type": object_type,
            "color": color,
        })

    def test_lamp_creates_one_group(self):
        result = self._lamp()
        assert len(result["children"]) == 1
        assert result["children"][0]["node_type"] == "group"

    def test_lamp_has_three_children(self):
        result = self._lamp()
        assert len(result["children"][0]["children"]) == 3

    def test_lamp_has_base_pole_shade(self):
        result = self._lamp()
        names = [c["name"] for c in result["children"][0]["children"]]
        name_str = " ".join(names)
        assert "base" in name_str
        assert "pole" in name_str
        assert "shade" in name_str

    def test_lamp_shade_is_highest(self):
        result = self._lamp()
        children = result["children"][0]["children"]
        shade = next(c for c in children if "shade" in c["name"])
        base = next(c for c in children if "base" in c["name"])
        assert shade["transform"]["position"][1] > base["transform"]["position"][1]

    def test_lamp_pole_is_taller_than_wide(self):
        result = self._lamp()
        children = result["children"][0]["children"]
        pole = next(c for c in children if "pole" in c["name"])
        sx, sy, sz = pole["transform"]["scale"]
        assert sy > sx

    def test_lamp_does_not_mutate_input(self):
        scene = deepcopy(EMPTY)
        apply_action_to_ir(scene, {
            "action": "generate_composite", "composite": "lamp",
            "object_type": "cube", "color": "yellow",
        })
        assert scene["children"] == []


# ---------------------------------------------------------------------------
# validate_composite_parts
# ---------------------------------------------------------------------------
class TestValidateCompositeParts:
    _GOOD_PART = {"name": "body", "shape": "cube", "position": [0.0, 0.5, 0.0], "scale": [1.0, 1.0, 1.0]}

    def _good(self, n=1):
        return [{"name": "part_{}".format(i), "shape": "cube",
                 "position": [0.0, 0.5, 0.0], "scale": [1.0, 1.0, 1.0]} for i in range(n)]

    def test_valid_single_part_passes(self):
        validate_composite_parts([self._GOOD_PART])

    def test_empty_list_raises(self):
        with pytest.raises(ValueError, match="non-empty"):
            validate_composite_parts([])

    def test_non_list_raises(self):
        with pytest.raises(ValueError):
            validate_composite_parts("bad")

    def test_too_many_parts_raises(self):
        with pytest.raises(ValueError, match="too long"):
            validate_composite_parts(self._good(21))

    def test_non_dict_part_raises(self):
        with pytest.raises(ValueError):
            validate_composite_parts(["not a dict"])

    def test_missing_name_raises(self):
        with pytest.raises(ValueError, match="name"):
            validate_composite_parts([{"shape": "cube", "position": [0,0,0], "scale": [1,1,1]}])

    def test_duplicate_name_raises(self):
        parts = [
            {"name": "x", "shape": "cube", "position": [0,0,0], "scale": [1,1,1]},
            {"name": "x", "shape": "sphere", "position": [0,1,0], "scale": [1,1,1]},
        ]
        with pytest.raises(ValueError, match="Duplicate"):
            validate_composite_parts(parts)

    def test_invalid_shape_raises(self):
        with pytest.raises(ValueError, match="shape"):
            validate_composite_parts([
                {"name": "b", "shape": "rectangular_prism", "position": [0,0,0], "scale": [1,1,1]}
            ])

    def test_wrong_position_length_raises(self):
        with pytest.raises(ValueError, match="position"):
            validate_composite_parts([
                {"name": "b", "shape": "cube", "position": [0,0], "scale": [1,1,1]}
            ])

    def test_wrong_scale_length_raises(self):
        with pytest.raises(ValueError, match="scale"):
            validate_composite_parts([
                {"name": "b", "shape": "cube", "position": [0,0,0], "scale": [1,1]}
            ])

    def test_zero_scale_raises(self):
        with pytest.raises(ValueError, match="positive"):
            validate_composite_parts([
                {"name": "b", "shape": "cube", "position": [0,0,0], "scale": [0,1,1]}
            ])

    def test_negative_scale_raises(self):
        with pytest.raises(ValueError, match="positive"):
            validate_composite_parts([
                {"name": "b", "shape": "cube", "position": [0,0,0], "scale": [1,-1,1]}
            ])

    @pytest.mark.parametrize("shape", ["cube", "sphere", "cylinder", "cone", "pyramid", "plane"])
    def test_all_valid_shapes_pass(self, shape):
        validate_composite_parts([
            {"name": "p", "shape": shape, "position": [0,0,0], "scale": [1,1,1]}
        ])


# ---------------------------------------------------------------------------
# build_open_composite
# ---------------------------------------------------------------------------
class TestOpenComposite:
    _PARTS = [
        {"name": "body", "shape": "cylinder", "position": [0.0, 0.75, 0.0], "scale": [0.5, 1.5, 0.5]},
        {"name": "neck", "shape": "cylinder", "position": [0.0, 1.8,  0.0], "scale": [0.25, 0.6, 0.25]},
        {"name": "cap",  "shape": "cube",     "position": [0.0, 2.2,  0.0], "scale": [0.3,  0.15, 0.3]},
    ]

    def _build(self, object_name="bottle", parts=None, primitive_type="cylinder", color="white"):
        scene = deepcopy(EMPTY)
        return build_open_composite(scene, object_name, parts or self._PARTS, primitive_type, color)

    def test_creates_one_group(self):
        result = self._build()
        assert len(result["children"]) == 1
        assert result["children"][0]["node_type"] == "group"

    def test_group_child_count_matches_parts(self):
        result = self._build()
        assert len(result["children"][0]["children"]) == len(self._PARTS)

    def test_child_shapes_match_parts(self):
        result = self._build()
        for child, part in zip(result["children"][0]["children"], self._PARTS):
            assert child["shape"] == part["shape"]

    def test_child_positions_match_parts(self):
        result = self._build()
        for child, part in zip(result["children"][0]["children"], self._PARTS):
            assert child["transform"]["position"] == pytest.approx(part["position"])

    def test_child_scales_match_parts(self):
        result = self._build()
        for child, part in zip(result["children"][0]["children"], self._PARTS):
            assert child["transform"]["scale"] == pytest.approx(part["scale"])

    def test_color_applied_to_all_children(self):
        result = self._build(color="red")
        for child in result["children"][0]["children"]:
            r, g, b = child["material"]["color"]
            assert abs(r - 1.0) < 0.05

    def test_child_names_prefixed_with_group_name(self):
        result = self._build(object_name="bottle")
        group_name = result["children"][0]["name"]
        for child in result["children"][0]["children"]:
            assert child["name"].startswith(group_name)

    def test_does_not_mutate_input(self):
        scene = deepcopy(EMPTY)
        apply_action_to_ir(scene, {
            "action": "generate_composite",
            "composite": "open",
            "object_name": "bottle",
            "primitive_type": "cylinder",
            "color": "white",
            "parts": self._PARTS,
        })
        assert scene["children"] == []

    def test_apply_action_routes_parts_to_open_composite(self):
        scene = deepcopy(EMPTY)
        result = apply_action_to_ir(scene, {
            "action": "generate_composite",
            "composite": "open",
            "object_name": "bottle",
            "primitive_type": "cylinder",
            "color": "white",
            "parts": self._PARTS,
        })
        assert len(result["children"]) == 1
        assert result["children"][0]["node_type"] == "group"
        assert len(result["children"][0]["children"]) == 3

    def test_apply_action_open_composite_missing_parts_raises(self):
        with pytest.raises(ValueError):
            apply_action_to_ir(deepcopy(EMPTY), {
                "action": "generate_composite",
                "composite": "open",
                "object_name": "bottle",
            })

    def test_apply_action_open_composite_invalid_parts_raises(self):
        with pytest.raises(ValueError):
            apply_action_to_ir(deepcopy(EMPTY), {
                "action": "generate_composite",
                "composite": "open",
                "object_name": "bottle",
                "parts": [{"name": "bad", "shape": "INVALID", "position": [0,0,0], "scale": [1,1,1]}],
            })


# ---------------------------------------------------------------------------
# resolve_composite_overlaps
# ---------------------------------------------------------------------------
def _part(name, pos, scale, shape="cube"):
    return {"name": name, "shape": shape, "position": list(pos), "scale": list(scale)}


def _boxes_overlap(a, b):
    """Return True if the two part bounding boxes intersect (with tolerance)."""
    for ax in range(3):
        a_lo = a["position"][ax] - a["scale"][ax] / 2.0
        a_hi = a["position"][ax] + a["scale"][ax] / 2.0
        b_lo = b["position"][ax] - b["scale"][ax] / 2.0
        b_hi = b["position"][ax] + b["scale"][ax] / 2.0
        if min(a_hi, b_hi) - max(a_lo, b_lo) > 1e-4:
            continue
        return False
    return True


class TestResolveCompositeOverlaps:
    def test_non_overlapping_parts_unchanged(self):
        parts = [
            _part("body", [0.0, 0.75, 0.0], [0.5, 1.5, 0.5]),
            _part("neck", [0.0, 1.80, 0.0], [0.25, 0.6, 0.25]),
        ]
        result = resolve_composite_overlaps(parts)
        assert result[0]["position"] == pytest.approx(parts[0]["position"], abs=0.01)
        assert result[1]["position"] == pytest.approx(parts[1]["position"], abs=0.01)

    def test_overlapping_parts_are_separated(self):
        parts = [
            _part("a", [0.0, 0.5, 0.0], [1.0, 1.0, 1.0]),
            _part("b", [0.0, 0.5, 0.0], [1.0, 1.0, 1.0]),
        ]
        result = resolve_composite_overlaps(parts)
        assert not _boxes_overlap(result[0], result[1])

    def test_vertical_overlap_resolved(self):
        parts = [
            _part("a", [0.0, 0.5, 0.0], [1.0, 1.0, 1.0]),
            _part("b", [0.0, 0.8, 0.0], [1.0, 1.0, 1.0]),
        ]
        result = resolve_composite_overlaps(parts)
        assert not _boxes_overlap(result[0], result[1])

    def test_horizontal_overlap_resolved(self):
        parts = [
            _part("a", [0.0, 0.5, 0.0], [1.0, 1.0, 1.0]),
            _part("b", [0.4, 0.5, 0.0], [1.0, 1.0, 1.0]),
        ]
        result = resolve_composite_overlaps(parts)
        assert not _boxes_overlap(result[0], result[1])

    def test_ground_clamp_applied(self):
        parts = [
            _part("a", [0.0, 0.5, 0.0], [1.0, 1.0, 1.0]),
            _part("b", [0.0, 0.3, 0.0], [1.0, 1.0, 1.0]),
        ]
        result = resolve_composite_overlaps(parts)
        for part in result:
            half_y = part["scale"][1] / 2.0
            assert part["position"][1] >= half_y - 1e-4, "Part below ground after resolve"

    def test_three_overlapping_parts_all_separated(self):
        parts = [
            _part("a", [0.0, 0.5, 0.0], [1.0, 1.0, 1.0]),
            _part("b", [0.0, 0.9, 0.0], [1.0, 1.0, 1.0]),
            _part("c", [0.0, 1.3, 0.0], [1.0, 1.0, 1.0]),
        ]
        result = resolve_composite_overlaps(parts)
        for i in range(len(result)):
            for j in range(i + 1, len(result)):
                assert not _boxes_overlap(result[i], result[j]), (
                    "Parts {} and {} still overlap".format(result[i]["name"], result[j]["name"])
                )

    def test_scales_never_changed(self):
        parts = [
            _part("a", [0.0, 0.5, 0.0], [1.0, 2.0, 0.5]),
            _part("b", [0.0, 0.5, 0.0], [0.5, 1.0, 0.5]),
        ]
        result = resolve_composite_overlaps(parts)
        assert result[0]["scale"] == pytest.approx([1.0, 2.0, 0.5])
        assert result[1]["scale"] == pytest.approx([0.5, 1.0, 0.5])

    def test_does_not_mutate_input(self):
        parts = [
            _part("a", [0.0, 0.5, 0.0], [1.0, 1.0, 1.0]),
            _part("b", [0.0, 0.5, 0.0], [1.0, 1.0, 1.0]),
        ]
        original_pos_a = list(parts[0]["position"])
        resolve_composite_overlaps(parts)
        assert parts[0]["position"] == original_pos_a
