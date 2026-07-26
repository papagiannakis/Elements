"""
Tests for apply_texture and remove_texture actions.
Self-contained: embeds the conftest stubs so it runs from any location.
"""
import sys
from pathlib import Path
from types import ModuleType

import numpy as np

# ── paths ──────────────────────────────────────────────────────────────────
_SRC  = Path(__file__).resolve().parent.parent / "src"
_REPO = _SRC.parent.parent.parent.parent        # Elements repo root
sys.path.insert(0, str(_SRC))
sys.path.insert(0, str(_REPO))

# ── stubs (mirrors tests/conftest.py) ──────────────────────────────────────
def _stub(name):
    if name in sys.modules:
        return sys.modules[name]
    m = ModuleType(name)
    sys.modules[name] = m
    return m

_stub("trimesh")
_elements = _stub("Elements")
_pyecss   = _stub("Elements.pyECSS")
_elements.pyECSS = _pyecss
_mathutil = _stub("Elements.pyECSS.math_utilities")
_mathutil.vec = lambda *args: np.array(list(args), dtype=np.float32)
_mathutil.calculateNormals = lambda v0, v1, v2: np.array([0., 1., 0.], dtype=np.float32)
_mathutil.translate  = lambda x=0, y=0, z=0: np.eye(4, dtype=np.float32)
_mathutil.identity   = lambda: np.eye(4, dtype=np.float32)
_mathutil.scale      = lambda s: np.eye(4, dtype=np.float32)
_mathutil.lookat     = lambda eye, target, up: np.eye(4, dtype=np.float32)
_mathutil.perspective= lambda fov, asp, near, far: np.eye(4, dtype=np.float32)
_pyecss.math_utilities = _mathutil
_utils   = _stub("Elements.utils")
_elements.utils = _utils
def _generateUniqueVertices(vertices, indices, color=None):
    n = len(indices)
    uv = np.array([vertices[i] for i in indices], dtype=np.float32)
    ui = np.arange(n, dtype=np.uint32)
    uc = np.zeros((n, 4), dtype=np.float32)
    return uv, ui, uc
_normals = _stub("Elements.utils.normals")
_normals.generateUniqueVertices = _generateUniqueVertices
_utils.normals = _normals
_defs = _stub("Elements.definitions")
_defs.TEXTURE_DIR = _SRC
_elements.definitions = _defs
for _s in ("Elements.utils.terrain", "Elements.utils.Shortcuts",
           "Elements.pyECSS.Entity", "Elements.pyECSS.Component",
           "Elements.pyECSS.System", "Elements.pyGLV", "Elements.pyGLV.GL",
           "Elements.pyGLV.GL.Scene", "Elements.pyGLV.GUI",
           "Elements.pyGLV.GUI.Viewer", "Elements.pyGLV.GUI.ImguiDecorator",
           "Elements.pyGLV.GL.Shader", "Elements.pyGLV.GL.VertexArray",
           "Elements.pyGLV.GL.Textures", "OpenGL", "OpenGL.GL", "imgui"):
    _stub(_s)

# ── actual test code ────────────────────────────────────────────────────────
import pytest
from copy import deepcopy
from mock_ai_contoller import apply_action_to_ir, collect_mesh_objects

EMPTY = {
    "node_type": "scene", "name": "root",
    "window": {"width": 800, "height": 600, "title": "Test"},
    "children": [],
}


class TestTextureActions:
    def _cube_scene(self):
        s = deepcopy(EMPTY)
        s["children"].append({
            "node_type": "mesh_object", "name": "cube_1", "id": "cube_1",
            "created_order": 1, "shape": "cube",
            "transform": {"position": [0.0, 0.5, 0.0], "scale": [1.0, 1.0, 1.0]},
            "material": {"color": [1.0, 0.0, 0.0], "texture": {"enabled": False, "path": None}},
        })
        return s

    def test_apply_texture_sets_enabled_true(self):
        result = apply_action_to_ir(self._cube_scene(), {
            "action": "apply_texture", "target": "cube_1", "texture_name": "brick"
        })
        tex = collect_mesh_objects(result)[0]["material"]["texture"]
        assert tex["enabled"] is True

    def test_apply_texture_sets_path(self):
        result = apply_action_to_ir(self._cube_scene(), {
            "action": "apply_texture", "target": "cube_1", "texture_name": "brick"
        })
        tex = collect_mesh_objects(result)[0]["material"]["texture"]
        assert "brick" in tex["path"]

    def test_apply_unknown_texture_raises(self):
        with pytest.raises(ValueError, match="Unknown texture"):
            apply_action_to_ir(self._cube_scene(), {
                "action": "apply_texture", "target": "cube_1", "texture_name": "lava"
            })

    def test_remove_texture_sets_enabled_false(self):
        scene = self._cube_scene()
        scene["children"][0]["material"]["texture"] = {"enabled": True, "path": "/some/brick.jpg"}
        result = apply_action_to_ir(scene, {
            "action": "remove_texture", "target": "cube_1"
        })
        tex = collect_mesh_objects(result)[0]["material"]["texture"]
        assert tex["enabled"] is False
        assert tex["path"] is None

    def test_apply_texture_does_not_mutate_input(self):
        scene = self._cube_scene()
        original_tex = deepcopy(scene["children"][0]["material"]["texture"])
        apply_action_to_ir(scene, {
            "action": "apply_texture", "target": "cube_1", "texture_name": "wood"
        })
        assert scene["children"][0]["material"]["texture"] == original_tex
