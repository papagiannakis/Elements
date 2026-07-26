"""
Detailed structural tests for every built-in prefab builder.
Checks node types, child counts, shapes, colours, and name namespacing.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from prefabs import build_house, build_tree, build_gift_box, build_street_light


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _flat_mesh_children(node):
    """Return all mesh_object descendants (direct children only here)."""
    return [c for c in node.get("children", []) if c.get("node_type") == "mesh_object"]


# ---------------------------------------------------------------------------
# build_house
# ---------------------------------------------------------------------------
class TestBuildHouse:
    def setup_method(self):
        self.node = build_house("house_a", [1.0, 0.0, 2.0])

    def test_returns_group(self):
        assert self.node["node_type"] == "group"

    def test_name_propagated(self):
        assert self.node["name"] == "house_a"

    def test_position_propagated(self):
        assert self.node["transform"]["position"] == [1.0, 0.0, 2.0]

    def test_has_exactly_two_children(self):
        assert len(self.node["children"]) == 2

    def test_children_are_mesh_objects(self):
        assert all(c["node_type"] == "mesh_object" for c in self.node["children"])

    def test_child_names_contain_parent_name(self):
        for child in self.node["children"]:
            assert child["name"].startswith("house_a")

    def test_body_shape_is_rectangular_prism(self):
        body = next(c for c in self.node["children"] if "body" in c["name"])
        assert body["shape"] == "rectangular_prism"

    def test_roof_shape_is_pyramid(self):
        roof = next(c for c in self.node["children"] if "roof" in c["name"])
        assert roof["shape"] == "pyramid"

    def test_roof_is_above_body(self):
        body = next(c for c in self.node["children"] if "body" in c["name"])
        roof = next(c for c in self.node["children"] if "roof" in c["name"])
        assert roof["transform"]["position"][1] > body["transform"]["position"][1]

    def test_roof_has_reddish_colour(self):
        roof = next(c for c in self.node["children"] if "roof" in c["name"])
        r, g, b = roof["material"]["color"]
        assert r > g and r > b, "Roof should be reddish"


# ---------------------------------------------------------------------------
# build_tree
# ---------------------------------------------------------------------------
class TestBuildTree:
    def setup_method(self):
        self.node = build_tree("oak", [0.0, 0.0, 0.0])

    def test_returns_group(self):
        assert self.node["node_type"] == "group"

    def test_has_exactly_two_children(self):
        assert len(self.node["children"]) == 2

    def test_trunk_shape_is_cylinder(self):
        trunk = next(c for c in self.node["children"] if "trunk" in c["name"])
        assert trunk["shape"] == "cylinder"

    def test_crown_shape_is_sphere(self):
        crown = next(c for c in self.node["children"] if "crown" in c["name"])
        assert crown["shape"] == "sphere"

    def test_crown_is_above_trunk(self):
        trunk = next(c for c in self.node["children"] if "trunk" in c["name"])
        crown = next(c for c in self.node["children"] if "crown" in c["name"])
        assert crown["transform"]["position"][1] > trunk["transform"]["position"][1]

    def test_crown_is_green(self):
        crown = next(c for c in self.node["children"] if "crown" in c["name"])
        r, g, b = crown["material"]["color"]
        assert g > r and g > b, "Crown should be greenish"

    def test_trunk_is_brownish(self):
        trunk = next(c for c in self.node["children"] if "trunk" in c["name"])
        r, g, b = trunk["material"]["color"]
        assert r > b and g > b, "Trunk should be brownish (warm tone)"


# ---------------------------------------------------------------------------
# build_gift_box
# ---------------------------------------------------------------------------
class TestBuildGiftBox:
    def setup_method(self):
        self.node = build_gift_box("gift", [0.0, 0.0, 0.0])

    def test_returns_group(self):
        assert self.node["node_type"] == "group"

    def test_has_exactly_three_children(self):
        assert len(self.node["children"]) == 3

    def test_box_shape_is_cube(self):
        box = next(c for c in self.node["children"] if "box" in c["name"])
        assert box["shape"] == "cube"

    def test_ribbons_are_rectangular_prisms(self):
        ribbons = [c for c in self.node["children"] if "ribbon" in c["name"]]
        assert len(ribbons) == 2
        assert all(r["shape"] == "rectangular_prism" for r in ribbons)

    def test_box_has_reddish_colour(self):
        box = next(c for c in self.node["children"] if "box" in c["name"])
        r, g, b = box["material"]["color"]
        assert r > g and r > b

    def test_ribbons_are_yellowish(self):
        for ribbon in (c for c in self.node["children"] if "ribbon" in c["name"]):
            r, g, b = ribbon["material"]["color"]
            assert r > 0.9 and g > 0.7, "Ribbons should be yellowish"


# ---------------------------------------------------------------------------
# build_street_light
# ---------------------------------------------------------------------------
class TestBuildStreetLight:
    def setup_method(self):
        self.node = build_street_light("street_light", [3.0, 0.0, 0.0])

    def test_returns_group(self):
        assert self.node["node_type"] == "group"

    def test_has_exactly_three_children(self):
        assert len(self.node["children"]) == 3

    def test_pole_shape_is_cylinder(self):
        pole = next(c for c in self.node["children"] if "pole" in c["name"])
        assert pole["shape"] == "cylinder"

    def test_arm_shape_is_rectangular_prism(self):
        arm = next(c for c in self.node["children"] if "arm" in c["name"])
        assert arm["shape"] == "rectangular_prism"

    def test_lamp_shape_is_cube(self):
        lamp = next(c for c in self.node["children"] if "lamp" in c["name"])
        assert lamp["shape"] == "cube"

    def test_lamp_is_yellowish(self):
        lamp = next(c for c in self.node["children"] if "lamp" in c["name"])
        r, g, b = lamp["material"]["color"]
        assert r > 0.9 and g > 0.8, "Lamp should be yellow/white"

    def test_name_propagated(self):
        assert self.node["name"] == "street_light"

    def test_position_propagated(self):
        assert self.node["transform"]["position"] == [3.0, 0.0, 0.0]

    def test_all_children_have_transform(self):
        for child in self.node["children"]:
            assert "transform" in child
            assert "position" in child["transform"]
            assert "scale" in child["transform"]


# ---------------------------------------------------------------------------
# Name uniqueness when building multiple prefabs of same type
# ---------------------------------------------------------------------------
def test_two_houses_with_different_names_have_distinct_child_names():
    h1 = build_house("house_1", [0.0, 0.0, 0.0])
    h2 = build_house("house_2", [5.0, 0.0, 0.0])
    names_1 = {c["name"] for c in h1["children"]}
    names_2 = {c["name"] for c in h2["children"]}
    assert names_1.isdisjoint(names_2), "Children of different prefab instances must not share names"
