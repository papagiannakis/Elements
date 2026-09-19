"""
Unit tests for the four supported GUI combinations: {SDL2, GLFW} x {imgui_bundle, classic pyimgui}.

Each combination opens a real Elements scene containing a cube, the ImGUIDecorator's own ImGui
window, an example-description panel and the shortcuts panel, renders a handful of frames and
shuts down.

Each runs in its own interpreter, via imgui_backend_scene.py. That is not incidental: picking a GUI
backend mutates process-global, one-shot state -- a native window library can only be mapped once
per process, Scene is a singleton, and Elements.pyGLV.GUI.ImguiDecorator.configure_imgui_backend()
rewrites sys.modules["imgui"]. Four combinations in one interpreter would silently test whichever
one happened to win the race, which is precisely the bug class these tests exist to catch.

Elements.pyGLV (Computer Graphics for Deep Learning and Scientific Visualization)
"""

import importlib.util
import subprocess
import sys
import unittest

#: run as `python -m`, so the child resolves Elements the same way the parent did
CHILD_MODULE = "Elements.pyGLV.tests.imgui_backend_scene"

#: generous -- a child creates a window, compiles shaders and renders a few frames
CHILD_TIMEOUT_SECONDS = 180

#: what dyld prints when the same library is mapped twice under different paths. Harmless-looking,
#: but it means two SDL2s (or two GLFWs) are live in one process, which is a real crash source.
DUPLICATE_LIBRARY_MARKER = "is implemented in both"


def _installed(package):
    return importlib.util.find_spec(package) is not None


class TestImguiBackends(unittest.TestCase):
    """One test per (window backend, imgui implementation) combination."""

    def _run_scene(self, backend, mode):
        """Run one combination in a subprocess and return its reported facts as a dict."""
        completed = subprocess.run(
            [sys.executable, "-u", "-m", CHILD_MODULE, backend, mode],
            capture_output=True, text=True, timeout=CHILD_TIMEOUT_SECONDS,
        )
        report = (f"\n----- {backend}/{mode} stdout -----\n{completed.stdout}"
                  f"\n----- {backend}/{mode} stderr -----\n{completed.stderr}")

        self.assertEqual(completed.returncode, 0,
                         f"scene process exited with {completed.returncode}{report}")

        facts = {}
        for line in completed.stdout.splitlines():
            key, separator, value = line.partition("=")
            if separator and key.isidentifier():
                facts[key] = value

        self.assertEqual(facts.get("scene_completed"), "True",
                         f"scene did not reach the end of its render loop{report}")
        self.assertEqual(facts.get("backend"), "SDL2" if backend == "sdl2" else "GLFW",
                         f"wrong window backend{report}")
        self.assertEqual(facts.get("frames"), "5", f"scene rendered too few frames{report}")

        # The regression that made the description panel vanish after its first frame: begin()
        # returned None for "opened" on the bundle path, which callers read as "window closed".
        self.assertEqual(facts.get("description_visible"), "True",
                         f"the example-description window stopped being drawn{report}")

        # The shortcuts panel lays its rows out at runtime instead of padding strings, so it calls
        # more of the ImGui surface than the rest of the scene does -- and on the bundle path every
        # one of those calls has to exist in the compatibility adapter.
        self.assertEqual(facts.get("shortcuts_visible"), "True",
                         f"the shortcuts window stopped being drawn{report}")

        # Two copies of SDL2/GLFW in one process. This is the failure the bundle integration is
        # built to avoid, and it only ever shows up on stderr -- never as a non-zero exit.
        self.assertNotIn(DUPLICATE_LIBRARY_MARKER, completed.stderr,
                         f"a native library was loaded twice{report}")
        return facts, report

    @unittest.skipUnless(_installed("imgui_bundle"), "imgui_bundle is not installed")
    def test_sdl2_with_imgui_bundle(self):
        """SDL2 window, docking-capable imgui_bundle."""
        print("TestImguiBackends:test_sdl2_with_imgui_bundle START".center(100, '-'))
        facts, report = self._run_scene("sdl2", "bundle")
        # Guards the silent-fallback path: native_libraries_ready() declining the bundle would
        # otherwise leave this test quietly asserting nothing about imgui_bundle at all.
        self.assertEqual(facts.get("bundle_active"), "True",
                         f"imgui_bundle was requested but fell back to classic pyimgui{report}")
        self.assertEqual(facts.get("docking_enabled"), "True", f"docking was not enabled{report}")
        print("TestImguiBackends:test_sdl2_with_imgui_bundle END".center(100, '-'))

    @unittest.skipUnless(_installed("imgui_bundle"), "imgui_bundle is not installed")
    @unittest.skipUnless(_installed("glfw"), "glfw is not installed")
    def test_glfw_with_imgui_bundle(self):
        """GLFW window, docking-capable imgui_bundle."""
        print("TestImguiBackends:test_glfw_with_imgui_bundle START".center(100, '-'))
        facts, report = self._run_scene("glfw", "bundle")
        self.assertEqual(facts.get("bundle_active"), "True",
                         f"imgui_bundle was requested but fell back to classic pyimgui{report}")
        self.assertEqual(facts.get("docking_enabled"), "True", f"docking was not enabled{report}")
        print("TestImguiBackends:test_glfw_with_imgui_bundle END".center(100, '-'))

    def test_sdl2_with_classic_imgui(self):
        """SDL2 window, classic pyimgui -- the pre-imgui_bundle behaviour."""
        print("TestImguiBackends:test_sdl2_with_classic_imgui START".center(100, '-'))
        facts, report = self._run_scene("sdl2", "classic")
        self.assertEqual(facts.get("bundle_active"), "False",
                         f"imgui_bundle=False still activated the bundle{report}")
        self.assertEqual(facts.get("imgui_module"), "module",
                         f"expected the real pyimgui module, not the bundle adapter{report}")
        print("TestImguiBackends:test_sdl2_with_classic_imgui END".center(100, '-'))

    @unittest.skipUnless(_installed("glfw"), "glfw is not installed")
    def test_glfw_with_classic_imgui(self):
        """GLFW window, classic pyimgui."""
        print("TestImguiBackends:test_glfw_with_classic_imgui START".center(100, '-'))
        facts, report = self._run_scene("glfw", "classic")
        self.assertEqual(facts.get("bundle_active"), "False",
                         f"imgui_bundle=False still activated the bundle{report}")
        self.assertEqual(facts.get("imgui_module"), "module",
                         f"expected the real pyimgui module, not the bundle adapter{report}")
        print("TestImguiBackends:test_glfw_with_classic_imgui END".center(100, '-'))


if __name__ == "__main__":
    unittest.main()
