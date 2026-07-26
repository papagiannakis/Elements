"""Tests for extended COLOR_TABLE entries."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from mock_ai_contoller import COLOR_TABLE, color_name_to_rgb, apply_action_to_ir, collect_mesh_objects
from copy import deepcopy

EMPTY = {
    "node_type": "scene", "name": "root",
    "window": {"width": 800, "height": 600, "title": "Test"},
    "children": [],
}

class TestExtendedColors:
    @pytest.mark.parametrize("name", ["orange", "cyan", "pink", "brown", "gray", "grey"])
    def test_extended_color_in_table(self, name):
        assert name in COLOR_TABLE

    @pytest.mark.parametrize("name", ["orange", "cyan", "pink", "brown", "gray"])
    def test_color_name_to_rgb_extended(self, name):
        rgb = color_name_to_rgb(name)
        assert isinstance(rgb, list) and len(rgb) == 3
        assert all(0.0 <= c <= 1.0 for c in rgb)

    def test_gray_and_grey_are_identical(self):
        assert color_name_to_rgb("gray") == color_name_to_rgb("grey")

    def test_unknown_color_returns_purple_fallback(self):
        assert color_name_to_rgb("ultraviolet") == [0.8, 0.0, 0.8]
