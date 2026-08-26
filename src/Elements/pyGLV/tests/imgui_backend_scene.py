"""Run one Elements scene for a single (window backend, imgui_bundle) combination.

Spawned as a subprocess by test_imgui_backends.py, because the choice of GUI backend is
process-global and one-shot: a native window library can only be mapped once per process,
``ImguiBundle.native_libraries_ready()`` deliberately refuses to load the bundle once ``sdl2``/
``glfw`` is already imported, ``configure_imgui_backend()`` rewrites ``sys.modules["imgui"]``, and
Scene is a singleton. Four combinations therefore need four interpreters.

Usage::

    python -m Elements.pyGLV.tests.imgui_backend_scene {sdl2|glfw} {bundle|classic}

Prints one ``KEY=value`` line per checked property and exits non-zero on the first failure, so the
parent test can assert on both the exit status and the individual values.

Nothing here may import ``sdl2`` or ``glfw`` at module level: that would defeat the very readiness
check this script exists to exercise.
"""

import sys

import numpy as np

import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Component import RenderMesh
from Elements.pyECSS.Entity import Entity
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GL.Shader import (
    InitGLShaderSystem,
    RenderGLShaderSystem,
    Shader,
    ShaderGLDecorator,
)
from Elements.pyGLV.GL.VertexArray import VertexArray
from Elements.definitions import SHADER_DIR

#: how many frames to render before quitting. Enough that a window that only survives its first
#: frame (the failure mode where begin()'s "opened" return leaks a None) is caught.
FRAMES = 5

example_description = (
    "Backend smoke test: one cube, the decorator's own ImGui window, and this description panel.\n"
    "Closes itself after a few frames."
)

vertexCube = np.array([
    [-0.5, -0.5, 0.5, 1.0], [-0.5, 0.5, 0.5, 1.0], [0.5, 0.5, 0.5, 1.0], [0.5, -0.5, 0.5, 1.0],
    [-0.5, -0.5, -0.5, 1.0], [-0.5, 0.5, -0.5, 1.0], [0.5, 0.5, -0.5, 1.0], [0.5, -0.5, -0.5, 1.0],
], dtype=np.float32)
colorCube = np.array([
    [0.0, 0.0, 0.0, 1.0], [1.0, 0.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [0.0, 1.0, 0.0, 1.0],
    [0.0, 0.0, 1.0, 1.0], [1.0, 0.0, 1.0, 1.0], [1.0, 1.0, 1.0, 1.0], [0.0, 1.0, 1.0, 1.0],
], dtype=np.float32)
indexCube = np.array((1, 0, 3, 1, 3, 2, 2, 3, 7, 2, 7, 6, 3, 0, 4, 3, 4, 7,
                      6, 5, 1, 6, 1, 2, 4, 5, 6, 4, 6, 7, 5, 4, 0, 5, 0, 1), np.uint32)


def build_scene():
    """A single cube, enough to need a live GL context and a real render pass."""
    scene = Scene()
    root = scene.world.createEntity(Entity(name="RooT"))

    cube = scene.world.createEntity(Entity(name="cube"))
    scene.world.addEntityChild(root, cube)
    mesh = scene.world.addComponent(cube, RenderMesh(name="cube_mesh"))
    mesh.vertex_attributes.append(vertexCube)
    mesh.vertex_attributes.append(colorCube)
    mesh.vertex_index.append(indexCube)
    scene.world.addComponent(cube, VertexArray())
    shader = scene.world.addComponent(cube, ShaderGLDecorator(Shader(
        vertex_import_file=SHADER_DIR / "ColorMVP.vert",
        fragment_import_file=SHADER_DIR / "Color.frag")))

    view = util.lookat(util.vec(2.5, 2.5, 2.5), util.vec(0.0, 0.0, 0.0), util.vec(0.0, 1.0, 0.0))
    projection = util.perspective(50.0, 4 / 3, 0.01, 100.0)
    shader.setUniformVariable(key='modelViewProj', value=projection @ view, mat4=True)
    return scene


def main(argv):
    backend, mode = argv[1], argv[2]
    want_bundle = mode == "bundle"

    window_class = None
    if backend == "glfw":
        # Safe before scene.init(): GLFWWindow imports glfw lazily in its own __init__, which runs
        # after the readiness check. (Windows.py does import sdl2 eagerly, which is why the GLFW
        # readiness check looks only at glfw.)
        from Elements.pyGLV.GUI.Windows import GLFWWindow
        window_class = GLFWWindow

    scene = build_scene()
    init_update = scene.world.createSystem(InitGLShaderSystem())
    render_update = scene.world.createSystem(RenderGLShaderSystem())

    scene.init(imgui=True, windowWidth=640, windowHeight=480,
               windowTitle=f"Elements backend test: {backend}/{mode}",
               windowClass=window_class, imgui_bundle=want_bundle)
    scene.world.traverse_visit(init_update, scene.world.root)

    # Imported only now: on the bundle path its module-global `imgui` is rebound by
    # configure_imgui_backend(), and reading the flag afterwards is what proves the description
    # window stayed alive rather than vanishing after frame 0.
    import Elements.utils.Shortcuts as Shortcuts

    # Off by default (the examples toggle it from their menu bar), but worth drawing here: its rows
    # are laid out at runtime with calc_text_size/bullet/same_line/indent, so switching it on is
    # what puts those calls through the bundle's compatibility adapter as well as pyimgui.
    Shortcuts.show_shortcuts_window = True

    decorator = scene.gContext
    results = {
        "backend": decorator.wrapeeWindow.BACKEND_NAME,
        # the whole point: True must mean the bundle really engaged, not that it quietly fell back
        "bundle_active": decorator._imguiBackend is not None,
        "imgui_module": type(Shortcuts.imgui).__name__,
    }

    if want_bundle and decorator._imguiBackend is not None:
        from imgui_bundle import imgui as bundle_imgui
        flags = bundle_imgui.get_io().config_flags
        results["docking_enabled"] = bool(flags & bundle_imgui.ConfigFlags_.docking_enable)

    frames = 0
    while frames < FRAMES:
        scene.render()
        Shortcuts.displayGUI_text(example_description)
        scene.world.traverse_visit(render_update, scene.world.root)
        scene.render_post()
        frames += 1

    results["frames"] = frames
    # False here is the regression that hid the description panel after its first frame.
    results["description_visible"] = Shortcuts.showGUI_text
    results["shortcuts_visible"] = Shortcuts.show_shortcuts_window
    scene.shutdown()

    # Reporting only -- the assertions live in test_imgui_backends.py, so the expectations are
    # written down in exactly one place. A crash or exception here is itself the failure signal.
    for key, value in results.items():
        print(f"{key}={value}")
    print("scene_completed=True")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
