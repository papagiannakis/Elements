"""
GLFWWindow, an alternative to Elements.pyGLV.GUI.Viewer.SDL2Window, part of Elements.pyGLV

Same RenderWindow contract as SDL2Window (init/init_post/display/display_post/shutdown/
event_input_process/accept), so it's a drop-in `windowClass=` for Scene.init(). Nothing outside
this file imports `glfw` -- Viewer.py's RenderDecorator drives this window's camera-orbit/
wireframe-toggle input through the duck-typed helper methods below instead, and
ImguiDecorator.py's GLFW branch imports imgui.integrations.glfw lazily -- so environments without
`glfw` installed are unaffected unless they explicitly opt into this window class.
"""

from __future__ import annotations
from typing import Any, Callable

import glfw
import numpy as np
import OpenGL.GL as gl

from Elements.pyGLV.GUI.Viewer import RenderWindow
from Elements.pyECSS.Event import Event
from Elements.pyECSS.System import System


class GLFWWindow(RenderWindow):
    """The concrete subclass of RenderWindow for the GLFW GUI API"""

    def __init__(
        self,
        windowWidth: int | None = None,
        windowHeight: int | None = None,
        windowTitle: str | None = None,
        scene: Any = None,
        eventManager: Any = None,
        openGLversion: int = 4,
    ):
        super().__init__()

        self._gWindow = None
        self._gVersionLabel = "None"

        self.openGLversion = openGLversion

        self._windowWidth = 1024 if windowWidth is None else windowWidth
        self._windowHeight = 768 if windowHeight is None else windowHeight
        self._windowTitle = "GLFWWindow" if windowTitle is None else windowTitle

        if eventManager is not None and scene is None:
            self.eventManager = eventManager

        if scene is not None:
            self._scene = scene
            self.eventManager = scene.world.eventManager

        #OpenGL state variables -- same fields as SDL2Window so ImGUIDecorator's generic code
        #(which pokes these directly) works unchanged regardless of backend
        self._wireframeMode = False
        self._colorEditor = 0.0, 0.0, 0.0
        self._myCamera = np.identity(4)
        self._cameraEye = np.zeros(3, dtype=np.float32)
        self._cameraTarget = np.zeros(3, dtype=np.float32)

        #GLFW-only polling state, for the duck-typed helpers below
        self._lastCursorX = 0.0
        self._lastCursorY = 0.0
        self._fKeyWasPressed = False

    @property
    def gWindow(self):
        return self._gWindow

    def init(self) -> None:
        """
        Initialise a GLFW RenderWindow, not directly but via the ImGUIDecorator
        """
        print(f'{self.getClassName()}: init()')

        if not glfw.init():
            print("GLFW could not be initialised!")
            exit(1)

        #setting OpenGL attributes for the GL state, mirroring SDL2Window's choices
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, glfw.TRUE)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.DOUBLEBUFFER, glfw.TRUE)
        glfw.window_hint(glfw.DEPTH_BITS, 24)
        glfw.window_hint(glfw.STENCIL_BITS, 8)
        glfw.window_hint(glfw.RESIZABLE, glfw.TRUE)

        if self.openGLversion == 3:
            print("=" * 24)
            print("Using OpenGL version 3.2")
            print("=" * 24)
            glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
            glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 2)
        else:
            print("=" * 24)
            print("Using OpenGL version 4.1")
            print("=" * 24)
            glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 4)
            glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 1)

        #creating the GLFW window
        self._gWindow = glfw.create_window(self._windowWidth, self._windowHeight, self._windowTitle, None, None)
        if self._gWindow is None:
            print("Window could not be created! GLFW Error: ", glfw.get_error())
            glfw.terminate()
            exit(1)

        glfw.make_context_current(self._gWindow)
        glfw.swap_interval(1)

        #GLFW enables Retina/HiDPI framebuffers by default (unlike SDL2Window, which explicitly
        #disables HiDPI) -- re-seed our stored size from the actual framebuffer, or the first
        #glViewport call below would only cover a quarter of the real window on a Retina display
        self._windowWidth, self._windowHeight = glfw.get_framebuffer_size(self._gWindow)
        gl.glViewport(0, 0, self._windowWidth, self._windowHeight)

        #obtain the GL versioning system info
        self._gVersionLabel = f'OpenGL {gl.glGetString(gl.GL_VERSION).decode()} GLSL {gl.glGetString(gl.GL_SHADING_LANGUAGE_VERSION).decode()} Renderer {gl.glGetString(gl.GL_RENDERER).decode()}'
        print(self._gVersionLabel)

    def init_post(self) -> None:
        """
        Post init method for GLFW
        this should be typically called AFTER all other GL contexts have been created
        """
        pass

    def display(self) -> None:
        """
        Main display window method to be called standalone or from within a concrete Decorator
        """
        gl.glClearColor(*self._colorEditor, 1.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        gl.glDisable(gl.GL_CULL_FACE)
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glDepthFunc(gl.GL_LESS)

        gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_LINE if self._wireframeMode else gl.GL_FILL)

    def display_post(self) -> None:
        """
        To be called at the end of each drawn frame to swap double buffers
        """
        glfw.swap_buffers(self._gWindow)

    def shutdown(self) -> None:
        """
        Shutdown and cleanup GLFW operations
        """
        print(f'{self.getClassName()}: shutdown()')
        if self._gWindow is not None:
            glfw.destroy_window(self._gWindow)
            glfw.terminate()

    def event_input_process(self, running: bool = True) -> bool:
        """
        process GLFW basic events and input
        """
        glfw.poll_events()

        if glfw.window_should_close(self._gWindow):
            running = False
        if glfw.get_key(self._gWindow, glfw.KEY_ESCAPE) == glfw.PRESS:
            running = False

        fbWidth, fbHeight = glfw.get_framebuffer_size(self._gWindow)
        if fbWidth != self._windowWidth or fbHeight != self._windowHeight:
            print("Window Resized to ", fbWidth, " X ", fbHeight)
            self._windowWidth, self._windowHeight = fbWidth, fbHeight
            gl.glViewport(0, 0, fbWidth, fbHeight)

        return running

    def accept(self, system: System, event: Event | None = None) -> None:
        system.apply2GLFWWindow(self, event)

    # ---- duck-typed helpers, called only from Viewer.py's RenderDecorator GLFW branch --------
    # kept here so Viewer.py never needs `import glfw`

    def poll_right_drag_delta(self) -> tuple[float, float] | None:
        """None unless the right mouse button is held, in which case the cursor-position delta
        since the last call (sign-matched to SDL2Window's own (-xrel, yrel) convention)."""
        x, y = glfw.get_cursor_pos(self._gWindow)
        dx, dy = x - self._lastCursorX, y - self._lastCursorY
        self._lastCursorX, self._lastCursorY = x, y
        if glfw.get_mouse_button(self._gWindow, glfw.MOUSE_BUTTON_RIGHT) == glfw.PRESS:
            return (-dx, dy)
        return None

    def get_modifier_state(self) -> tuple[bool, bool]:
        """(shift_held, ctrl_held), the GLFW equivalent of SDL2Window's SDL_GetKeyboardState scan."""
        shift = glfw.get_key(self._gWindow, glfw.KEY_LEFT_SHIFT) == glfw.PRESS
        ctrl = glfw.get_key(self._gWindow, glfw.KEY_LEFT_CONTROL) == glfw.PRESS
        return shift, ctrl

    def consume_wireframe_toggle_key(self) -> bool:
        """True exactly once per F keypress (rising edge), since GLFW has no keydown event queue
        to check "was this key just pressed" against, unlike SDL2's SDL_KEYDOWN."""
        pressed = glfw.get_key(self._gWindow, glfw.KEY_F) == glfw.PRESS
        edge = pressed and not self._fKeyWasPressed
        self._fKeyWasPressed = pressed
        return edge

    def register_scroll_callback(self, handler: Callable[[float, float], None]) -> None:
        """Chains `handler` onto whatever scroll callback is already installed (GlfwRenderer's,
        for ImGui's own scroll handling), instead of replacing it -- GLFW only allows one callback
        per window per event type."""
        previous = None

        def combined(window, xoffset, yoffset):
            if previous is not None:
                previous(window, xoffset, yoffset)
            handler(xoffset, yoffset)

        previous = glfw.set_scroll_callback(self._gWindow, combined)
