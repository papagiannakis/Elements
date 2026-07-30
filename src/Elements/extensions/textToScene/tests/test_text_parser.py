"""
Tests for text_parser.text_to_ir — the simple line-based scene description parser.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from text_parser import text_to_ir


# ---------------------------------------------------------------------------
# Window parsing
# ---------------------------------------------------------------------------
def test_window_width_and_height():
    ir = text_to_ir("window 1280 720")
    assert ir["window"]["width"] == 1280
    assert ir["window"]["height"] == 720


def test_window_wrong_arg_count_raises():
    with pytest.raises(ValueError, match="Window"):
        text_to_ir("window 800")


def test_window_extra_args_raises():
    with pytest.raises(ValueError, match="Window"):
        text_to_ir("window 800 600 extra")


# ---------------------------------------------------------------------------
# Object parsing
# ---------------------------------------------------------------------------
def test_object_minimal():
    ir = text_to_ir("object cube MyCube")
    assert len(ir["objects"]) == 1
    obj = ir["objects"][0]
    assert obj["type"] == "cube"
    assert obj["name"] == "MyCube"


def test_object_defaults():
    ir = text_to_ir("object sphere Ball")
    obj = ir["objects"][0]
    assert obj["position"] == [0, 0, 0]
    assert obj["scale"] == [1, 1, 1]
    assert obj["color"] == [1, 1, 1]


def test_object_with_position():
    ir = text_to_ir("object cube Box position=1.0,2.0,3.0")
    obj = ir["objects"][0]
    assert obj["position"] == pytest.approx([1.0, 2.0, 3.0])


def test_object_with_scale():
    ir = text_to_ir("object cube Box scale=2.0,2.0,2.0")
    obj = ir["objects"][0]
    assert obj["scale"] == pytest.approx([2.0, 2.0, 2.0])


def test_object_with_color():
    ir = text_to_ir("object cube Box color=1.0,0.0,0.0")
    obj = ir["objects"][0]
    assert obj["color"] == pytest.approx([1.0, 0.0, 0.0])


def test_object_all_properties():
    ir = text_to_ir(
        "object cube Crate position=1.0,0.5,2.0 scale=1.5,1.5,1.5 color=0.8,0.4,0.0"
    )
    obj = ir["objects"][0]
    assert obj["position"] == pytest.approx([1.0, 0.5, 2.0])
    assert obj["scale"] == pytest.approx([1.5, 1.5, 1.5])
    assert obj["color"] == pytest.approx([0.8, 0.4, 0.0])


def test_object_missing_args_raises():
    with pytest.raises(ValueError, match="Object definition"):
        text_to_ir("object cube")


def test_object_unknown_property_raises():
    with pytest.raises(ValueError, match="Unknown object property"):
        text_to_ir("object cube Box shininess=high")


# ---------------------------------------------------------------------------
# Multiple objects
# ---------------------------------------------------------------------------
def test_multiple_objects():
    ir = text_to_ir(
        "object cube A\n"
        "object sphere B\n"
        "object cylinder C"
    )
    assert len(ir["objects"]) == 3
    types = [o["type"] for o in ir["objects"]]
    assert types == ["cube", "sphere", "cylinder"]


# ---------------------------------------------------------------------------
# Unknown line type
# ---------------------------------------------------------------------------
def test_unknown_line_raises():
    with pytest.raises(ValueError, match="Unknown line type"):
        text_to_ir("light point sun")


# ---------------------------------------------------------------------------
# Empty / whitespace input
# ---------------------------------------------------------------------------
def test_empty_input_returns_empty_ir():
    ir = text_to_ir("")
    assert ir["objects"] == []
    assert ir["window"] == {}


def test_whitespace_only_input_returns_empty_ir():
    ir = text_to_ir("   \n   \n   ")
    assert ir["objects"] == []


# ---------------------------------------------------------------------------
# Window + objects together
# ---------------------------------------------------------------------------
def test_window_and_objects_combined():
    ir = text_to_ir(
        "window 1920 1080\n"
        "object cube Floor\n"
        "object sphere Ball position=0.0,1.0,0.0"
    )
    assert ir["window"]["width"] == 1920
    assert ir["window"]["height"] == 1080
    assert len(ir["objects"]) == 2
