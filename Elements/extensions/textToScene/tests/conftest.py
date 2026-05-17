"""
Pytest configuration: stubs heavy framework/GL dependencies so the
textToScene unit tests can run without OpenGL, trimesh, or imgui installed.

Executed by pytest before any test module is imported.
"""

import sys
from pathlib import Path
from types import ModuleType

import numpy as np

# ---------------------------------------------------------------------------
# sys.path — make src/ importable
# ---------------------------------------------------------------------------
_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT / "src"))
# Elements repo root (../../../.. relative to this file)
sys.path.insert(0, str(_ROOT.parent.parent.parent))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _stub(name: str) -> ModuleType:
    """Insert an empty stub module into sys.modules and return it."""
    if name in sys.modules:
        return sys.modules[name]
    m = ModuleType(name)
    sys.modules[name] = m
    return m


# ---------------------------------------------------------------------------
# trimesh — only needed transitively by math_utilities; stub the whole thing
# ---------------------------------------------------------------------------
_stub("trimesh")


# ---------------------------------------------------------------------------
# Elements package hierarchy
# ---------------------------------------------------------------------------
_elements = _stub("Elements")

# Elements.pyECSS
_pyecss = _stub("Elements.pyECSS")
_elements.pyECSS = _pyecss

# Elements.pyECSS.math_utilities  (used by Elements.utils.normals)
_mathutil = _stub("Elements.pyECSS.math_utilities")
_mathutil.vec = lambda *args: np.array(list(args), dtype=np.float32)
_mathutil.calculateNormals = lambda v0, v1, v2: np.array([0.0, 1.0, 0.0], dtype=np.float32)
_mathutil.translate = lambda x=0, y=0, z=0: np.eye(4, dtype=np.float32)
_mathutil.identity = lambda: np.eye(4, dtype=np.float32)
_mathutil.scale = lambda s: np.eye(4, dtype=np.float32)
_mathutil.lookat = lambda eye, target, up: np.eye(4, dtype=np.float32)
_mathutil.perspective = lambda fov, asp, near, far: np.eye(4, dtype=np.float32)
_pyecss.math_utilities = _mathutil

# Elements.utils
_utils = _stub("Elements.utils")
_elements.utils = _utils

# Elements.utils.normals  (used by geometry_factory)
def _generateUniqueVertices(vertices, indices, color=None):
    n = len(indices)
    unique_verts = np.array([vertices[i] for i in indices], dtype=np.float32)
    unique_indices = np.arange(n, dtype=np.uint32)
    unique_colors = np.zeros((n, 4), dtype=np.float32)
    return unique_verts, unique_indices, unique_colors

_normals = _stub("Elements.utils.normals")
_normals.generateUniqueVertices = _generateUniqueVertices
_utils.normals = _normals

# Elements.utils.terrain  (imported in code_generator header template — as text, but
# also imported at the top of code_generator.py? No — it only appears in the generated
# string.  Stub anyway for safety.)
_stub("Elements.utils.terrain")
_stub("Elements.utils.Shortcuts")

# Elements.definitions
_defs = _stub("Elements.definitions")
_defs.TEXTURE_DIR = Path(__file__).parent  # dummy path
_elements.definitions = _defs

# Elements.pyECSS sub-modules referenced in the generated script (not at import time,
# but stub to prevent any accidental eager load)
for _sub in (
    "Elements.pyECSS.Entity",
    "Elements.pyECSS.Component",
    "Elements.pyECSS.System",
    "Elements.pyGLV",
    "Elements.pyGLV.GL",
    "Elements.pyGLV.GL.Scene",
    "Elements.pyGLV.GUI",
    "Elements.pyGLV.GUI.Viewer",
    "Elements.pyGLV.GUI.ImguiDecorator",
    "Elements.pyGLV.GL.Shader",
    "Elements.pyGLV.GL.VertexArray",
    "Elements.pyGLV.GL.Textures",
):
    _stub(_sub)

# ---------------------------------------------------------------------------
# Other optional heavy deps (not always installed in test environments)
# ---------------------------------------------------------------------------
for _pkg in ("OpenGL", "OpenGL.GL", "imgui", "openai"):
    _stub(_pkg)

# openai.OpenAI class stub (llm_parser does `from openai import OpenAI`)
import sys as _sys
_openai = _sys.modules["openai"]
class _OpenAI:
    def __init__(self, **kwargs): pass
_openai.OpenAI = _OpenAI
