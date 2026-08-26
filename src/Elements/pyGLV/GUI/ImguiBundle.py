"""Optional imgui_bundle integration for the existing Elements GUI lifecycle.

The adapter intentionally covers the classic pyimgui calls used by Elements and its examples.
It is not intended to be a second public ImGui API.
"""

from __future__ import annotations

import ctypes
import importlib
import importlib.machinery
import importlib.util
import os
import re
import sys
import tempfile
from pathlib import Path


def _bundle_package_dir():
    """Locate the imgui_bundle package without executing its ``__init__``."""
    spec = importlib.util.find_spec("imgui_bundle")
    if spec is None:
        return None
    locations = spec.submodule_search_locations or ()
    return Path(next(iter(locations), Path(spec.origin).parent))


def _bundle_linked_library(package_dir: Path, stem: str):
    """Return the ``stem``-prefixed native library that imgui_bundle's extension module links.

    The extension records its dependencies as ``@loader_path/<name>`` strings, so reading them
    straight out of the binary tells us the exact file dyld will map -- which matters because the
    package ships several same-named-but-distinct copies (``libSDL2-2.0.dylib`` next to the
    ``libSDL2-2.0.0.dylib`` actually linked, plus a debug build). Guessing the name instead is how
    a second copy gets loaded.
    """
    suffixes = tuple(importlib.machinery.EXTENSION_SUFFIXES)
    extensions = [p for p in package_dir.glob("_imgui_bundle*") if p.name.endswith(suffixes)]
    # "@loader_path/libSDL2-2.0.0.dylib" on macOS, "$ORIGIN/libSDL2-2.0.so.0" on Linux.
    pattern = re.compile(rb"(?:@[a-z_]+|\$ORIGIN)/(" + re.escape(stem.encode()) + rb"[^\x00/]*)")
    for extension in extensions:
        for name in pattern.findall(extension.read_bytes()):
            candidate = package_dir / name.decode()
            if candidate.is_file():
                return candidate
    return None


def _sole_candidate_dir(library: Path, link_name: str) -> Path:
    """A directory holding nothing but ``link_name`` -> ``library``, reused across runs.

    pysdl2 walks ``PYSDL2_DLL_PATH`` looking for "SDL2", then "SDL2-2.0", then "SDL2-2.0.0" and
    takes the first hit; pointing it at a directory with a single candidate leaves it no choice.
    """
    shared_dir = Path(tempfile.gettempdir()) / "elements_imgui_bundle_native"
    shared_dir.mkdir(exist_ok=True)
    link = shared_dir / link_name
    if not (link.is_symlink() and os.readlink(link) == str(library)):
        if link.is_symlink() or link.exists():
            link.unlink()
        os.symlink(library, link)
    return shared_dir


class _BeginEndResult(int):
    """A bool that also answers ``.opened``, the way pyimgui's begin_*() return values do."""

    @property
    def opened(self) -> bool:
        return bool(self)


class _ImguiBundleAdapter:
    """Small compatibility surface for the pyimgui calls used by Elements."""

    _CONSTANTS = {
        "FIRST_USE_EVER": ("Cond_", "first_use_ever"),
        "TREE_NODE_BULLET": ("TreeNodeFlags_", "bullet"),
        "TREE_NODE_OPEN_ON_ARROW": ("TreeNodeFlags_", "open_on_arrow"),
        "TREE_NODE_SELECTED": ("TreeNodeFlags_", "selected"),
        "WINDOW_NO_MOVE": ("WindowFlags_", "no_move"),
        "WINDOW_NO_RESIZE": ("WindowFlags_", "no_resize"),
        "WINDOW_NO_SCROLLBAR": ("WindowFlags_", "no_scrollbar"),
        "WINDOW_NO_TITLE_BAR": ("WindowFlags_", "no_title_bar"),
        "INPUT_TEXT_ENTER_RETURNS_TRUE": ("InputTextFlags_", "enter_returns_true"),
        "COLOR_TEXT": ("Col_", "text"),
        "TITLE_BG": ("Col_", "title_bg"),
        "TITLE_BG_ACTIVE": ("Col_", "title_bg_active"),
        "TITLE_BG_COLLAPSED": ("Col_", "title_bg_collapsed"),
    }

    def __init__(self, bundle_imgui):
        self._imgui = bundle_imgui

    def __getattr__(self, name):
        if name == "core":
            return self
        constant = self._CONSTANTS.get(name)
        if constant is not None:
            enum = getattr(self._imgui, constant[0])
            return getattr(enum, constant[1])
        return getattr(self._imgui, name)

    def begin(self, name, closable=False, *args, **kwargs):
        """pyimgui's ``begin(label, closable, flags) -> (expanded, opened)``.

        The bundle instead takes ``p_open`` and returns it back, so a caller unpacking two values
        gets ``None`` for ``opened`` unless a bool went in -- and callers treat that ``None`` as
        "window was closed", hiding it after one frame. Pass a real bool when the window is meant
        to be closable, and report ``opened`` as True when it is not.
        """
        expanded, opened = self._imgui.begin(name, True if closable else None, *args, **kwargs)
        return expanded, True if opened is None else opened

    def begin_menu(self, label, enabled=True, *args, **kwargs):
        return _BeginEndResult(self._imgui.begin_menu(label, enabled, *args, **kwargs))

    def begin_main_menu_bar(self, *args, **kwargs):
        return _BeginEndResult(self._imgui.begin_main_menu_bar(*args, **kwargs))

    def begin_menu_bar(self, *args, **kwargs):
        return _BeginEndResult(self._imgui.begin_menu_bar(*args, **kwargs))

    def tree_node(self, label, flags=None, *args, **kwargs):
        if flags is None or isinstance(flags, str):
            return self._imgui.tree_node(label, *(() if flags is None else (flags,)), *args, **kwargs)
        return self._imgui.tree_node_ex(label, flags, *args, **kwargs)

    def _vec2(self, x, y):
        """pyimgui takes two floats where the bundle takes one ImVec2."""
        return x if y is None else self._imgui.ImVec2(x, y)

    def set_next_window_size(self, width, height=None, *args, **kwargs):
        return self._imgui.set_next_window_size(self._vec2(width, height), *args, **kwargs)

    def set_next_window_pos(self, x, y=None, *args, **kwargs):
        return self._imgui.set_next_window_pos(self._vec2(x, y), *args, **kwargs)

    set_next_window_position = set_next_window_pos

    def set_window_position(self, x, y=None, *args, **kwargs):
        # pyimgui's set_window_position is the bundle's set_window_pos.
        return self._imgui.set_window_pos(self._vec2(x, y), *args, **kwargs)

    set_window_pos = set_window_position

    def get_content_region_available(self):
        # pyimgui's name for what the bundle calls get_content_region_avail().
        return self._imgui.get_content_region_avail()

    def get_content_region_available_width(self):
        return self._imgui.get_content_region_avail().x

    def push_style_color(self, color, *values):
        values = values[0] if len(values) == 1 and isinstance(values[0], (list, tuple)) else values
        return self._imgui.push_style_color(color, self._imgui.ImVec4(*values))

    def color_edit3(self, label, *values, **kwargs):
        values = values[0] if len(values) == 1 and isinstance(values[0], (list, tuple)) else values
        return self._imgui.color_edit3(label, list(values), **kwargs)

    def _vector_widget(self, function_name, label, values, args, kwargs):
        function = getattr(self._imgui, function_name)
        return function(label, list(values), *args, **kwargs)

    def drag_float3(self, label, x, y=None, z=None, *args, **kwargs):
        values = x if y is None and z is None else (x, y, z)
        return self._vector_widget("drag_float3", label, values, args, kwargs)

    def input_float3(self, label, x, y=None, z=None, *args, **kwargs):
        values = x if y is None and z is None else (x, y, z)
        return self._vector_widget("input_float3", label, values, args, kwargs)

    def input_float4(self, label, x, y=None, z=None, w=None, *args, **kwargs):
        values = x if y is None and z is None and w is None else (x, y, z, w)
        return self._vector_widget("input_float4", label, values, args, kwargs)

    def drag_int3(self, label, x, y=None, z=None, *args, **kwargs):
        values = x if y is None and z is None else (x, y, z)
        return self._vector_widget("drag_int3", label, values, args, kwargs)


class ImguiBundleBackend:
    """Native backend and frame lifecycle for an Elements SDL2 or GLFW window."""

    def __init__(self, window_backend):
        self.window_backend = window_backend
        self._bundle = importlib.import_module("imgui_bundle")
        self.imgui = _ImguiBundleAdapter(self._bundle.imgui)
        self._callbacks = []
        self._patched_modules = []
        self._sdl2_watch = None

    @staticmethod
    def native_libraries_ready(window_backend: str) -> bool:
        """Return whether the bundle can be loaded without creating a native-library conflict.

        Both SDL2 *and* GLFW matter regardless of which window backend is in play: the bundle's
        extension links both, so importing it maps both. If either is already mapped from somewhere
        else, that copy can no longer be redirected and loading the bundle would duplicate it.
        open3d is the unfixable case -- its GLFW is compiled into its own extension, so there is no
        library path to redirect.
        """
        if sys.platform != "darwin":
            return True
        return not any(name in sys.modules for name in ("open3d", "sdl2", "glfw"))

    @staticmethod
    def is_available() -> bool:
        return importlib.util.find_spec("imgui_bundle") is not None

    @staticmethod
    def prepare_native_libraries(window_backend: str) -> None:
        """Bind pysdl2/pyglfw to the very same native library imgui_bundle's extension links.

        The window library must be loaded exactly once per process. imgui_bundle ships its own
        SDL2/GLFW beside its extension module and loads them through ``@loader_path``; pysdl2 and
        pyglfw load theirs by name. When those resolve to two different files -- pysdl2-dll's
        ``SDL2.framework``, or even the bundle's own spare ``libSDL2-2.0.dylib`` next to the
        ``libSDL2-2.0.0.dylib`` its extension actually links -- both copies define the same
        Objective-C classes, which is the "Class SDLWindow is implemented in both ..." storm and
        the crashes behind it.

        Note ``imgui_bundle/__init__.py`` sets ``PYSDL2_DLL_PATH`` to its own directory and then
        imports ``sdl2`` itself, where pysdl2 picks the wrong one of the two -- so we cannot repair
        this after the fact. We have to resolve the path and get ``sdl2`` imported first; the
        bundle's own import then finds it already in ``sys.modules`` and dyld reuses the mapping.
        """
        if not ImguiBundleBackend.is_available() or not ImguiBundleBackend.native_libraries_ready(window_backend):
            return

        package_dir = _bundle_package_dir()
        if package_dir is None:
            return

        # Pin both, not just the backend in use: the extension links both, so both get mapped when
        # it loads. Pinning only SDL2 while running on GLFW still leaves pyglfw free to load a
        # second GLFW, and vice versa.
        linked = _bundle_linked_library(package_dir, "libSDL2")
        if linked is not None and importlib.util.find_spec("sdl2") is not None:
            # Overwrite rather than setdefault: on macOS a stale value points at a second copy.
            os.environ["PYSDL2_DLL_PATH"] = str(_sole_candidate_dir(linked, "libSDL2.dylib"))
            importlib.import_module("sdl2")

        linked = _bundle_linked_library(package_dir, "libglfw") or _bundle_linked_library(package_dir, "glfw3")
        if linked is not None and importlib.util.find_spec("glfw") is not None:
            os.environ["PYGLFW_LIBRARY"] = str(linked)
            importlib.import_module("glfw")

    def patch_imported_imgui_modules(self, classic_imgui) -> None:
        """Route every ``import imgui`` in the process to the bundle instead.

        Only one ImGui context exists once the bundle is active, and it belongs to the bundle;
        classic pyimgui would dereference a null ``GImGui`` and take the process down with it. So
        both halves matter: rebinding the ``imgui`` global of modules already imported, *and*
        standing in for the module in ``sys.modules`` so modules imported later -- e.g. a GUI helper
        a scene pulls in after ``Scene.init()`` -- resolve to the bundle too.
        """
        for module in list(sys.modules.values()):
            namespace = getattr(module, "__dict__", None)
            if namespace is not None and namespace.get("imgui") is classic_imgui:
                self._patched_modules.append((namespace, classic_imgui))
                namespace["imgui"] = self.imgui
        sys.modules["imgui"] = self.imgui
        self._patched_modules.append((sys.modules, classic_imgui))

    def restore_imported_imgui_modules(self) -> None:
        for namespace, classic_imgui in self._patched_modules:
            if namespace.get("imgui") is self.imgui:
                namespace["imgui"] = classic_imgui
        self._patched_modules.clear()

    def init(self, window) -> None:
        bundle_imgui = self._bundle.imgui
        backends = self._bundle.imgui.backends
        window_address = ctypes.cast(window._gWindow, ctypes.c_void_p).value

        # ImGUIDecorator.__init__ already created one through the adapter; creating a second here
        # would leak it and leave its font atlas unbuilt.
        if bundle_imgui.get_current_context() is None:
            bundle_imgui.create_context()
        if self.window_backend == "SDL2":
            backends.sdl2_init_for_opengl(window_address, window._gContext)
        else:
            backends.glfw_init_for_open_gl(window_address, False)
            self._chain_glfw_callbacks(window, backends)
        backends.opengl3_init("#version 410")
        bundle_imgui.get_io().config_flags |= bundle_imgui.ConfigFlags_.docking_enable

        if self.window_backend == "SDL2":
            self._install_sdl2_event_watch()

    def _install_sdl2_event_watch(self) -> None:
        import sdl2

        def event_watch(_, event_ptr):
            event_address = ctypes.cast(event_ptr, ctypes.c_void_p).value
            self._bundle.imgui.backends.sdl2_process_event(event_address)
            return 1

        self._sdl2_watch = sdl2.SDL_EventFilter(event_watch)
        sdl2.SDL_AddEventWatch(self._sdl2_watch, None)

    def _chain_glfw_callbacks(self, window, backends) -> None:
        import glfw

        address = ctypes.cast(window._gWindow, ctypes.c_void_p).value
        callback_pairs = (
            (glfw.set_mouse_button_callback, backends.glfw_mouse_button_callback),
            (glfw.set_cursor_pos_callback, backends.glfw_cursor_pos_callback),
            (glfw.set_scroll_callback, backends.glfw_scroll_callback),
            (glfw.set_key_callback, backends.glfw_key_callback),
            (glfw.set_char_callback, backends.glfw_char_callback),
        )

        for setter, forwarder in callback_pairs:
            previous = setter(window._gWindow, None)

            def combined(native_window, *args, previous=previous, forwarder=forwarder):
                if previous is not None:
                    previous(native_window, *args)
                forwarder(address, *args)

            setter(window._gWindow, combined)
            self._callbacks.append(combined)

    def process_event(self, event) -> None:
        # SDL2 input is forwarded by SDL_AddEventWatch, so it is not sent a second time by the
        # existing RenderDecorator event loop.
        pass

    def process_inputs(self) -> None:
        pass

    def new_frame(self) -> None:
        backends = self._bundle.imgui.backends
        backends.opengl3_new_frame()
        if self.window_backend == "SDL2":
            backends.sdl2_new_frame()
        else:
            backends.glfw_new_frame()

    def render(self, draw_data) -> None:
        self._bundle.imgui.backends.opengl3_render_draw_data(draw_data)

    def shutdown(self) -> None:
        if self.window_backend == "SDL2" and self._sdl2_watch is not None:
            import sdl2
            sdl2.SDL_DelEventWatch(self._sdl2_watch, None)
        backends = self._bundle.imgui.backends
        backends.opengl3_shutdown()
        if self.window_backend == "SDL2":
            backends.sdl2_shutdown()
        else:
            backends.glfw_shutdown()
        self._bundle.imgui.destroy_context()
        self.restore_imported_imgui_modules()


def create_imgui_bundle_backend(window_backend: str):
    """Return the optional backend, or ``None`` when imgui_bundle is not installed."""
    if not ImguiBundleBackend.is_available():
        return None
    try:
        return ImguiBundleBackend(window_backend)
    except (ImportError, OSError) as error:
        print(f"imgui_bundle could not be loaded ({error}); falling back to classic pyimgui")
        return None
