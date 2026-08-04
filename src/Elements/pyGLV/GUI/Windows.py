"""
Concrete RenderWindow backends, part of Elements.pyGLV -- SDL2Window (the default) and GLFWWindow
(the alternative), kept in one file since both are small, share the exact same RenderWindow
contract (init/init_post/display/display_post/shutdown/event_input_process/accept), and are
selected between via the same `windowClass=` argument to Scene.init().

`glfw` is imported lazily, inside GLFWWindow.__init__ (not at module level), even though it's a
regular install_requires dependency of this project: importing `glfw` loads its native shared
library immediately, and this file is reached just by asking for `SDL2Window` (Elements' default
backend, used by nearly every example) -- a broken/missing GLFW native library on some platform
should not be able to break every example, only the ones that actually opt into
`windowClass=GLFWWindow`.
"""

from __future__ import annotations
from typing import Any, Callable

import numpy as np
import sdl2
import sdl2.ext
import OpenGL.GL as gl

from Elements.pyGLV.GUI.Viewer import RenderWindow
from Elements.pyECSS.Event import Event
from Elements.pyECSS.System import System


class SDL2Window(RenderWindow):
    """ The concrete subclass of RenderWindow for the SDL2 GUI API

    :param RenderWindow: [description]
    :type RenderWindow: [type]
    """

    #: identifies this window's backend to RenderDecorator/ImGUIDecorator, instead of a
    #: `type(window).__name__` string check
    BACKEND_NAME = "SDL2"

    def __init__(
        self,
        windowWidth: int | None = None,
        windowHeight: int | None = None,
        windowTitle: str | None = None,
        scene: Any = None,
        eventManager: Any = None,
        openGLversion: int = 4,
    ):
        """Constructor SDL2Window for basic SDL2 parameters

        :param windowWidth: [description], defaults to None
        :type windowWidth: [type], optional
        :param windowHeight: [description], defaults to None
        :type windowHeight: [type], optional
        :param windowTitle: [description], defaults to None
        :type windowTitle: [type], optional
        """
        super().__init__()

        self._gWindow = None
        self._gContext = None
        self._gVersionLabel = "None"

        self.openGLversion = openGLversion

        self._windowWidth = 1024 if windowWidth is None else windowWidth
        self._windowHeight = 768 if windowHeight is None else windowHeight
        self._windowTitle = "SDL2Window" if windowTitle is None else windowTitle

        if eventManager is not None and scene is None:
            # in case we are testing without a Scene and just an EventManager
            self.eventManager = eventManager

        if scene is not None:
            # set the reference of parent RenderWindow to Scene
            # get the reference to EventManager from Scene.ECSSManager
            self._scene = scene
            self.eventManager = scene.world.eventManager

        #OpenGL state variables
        self._wireframeMode = False
        self._colorEditor = 0.0, 0.0, 0.0
        self._myCamera = np.identity(4)
        self._cameraEye = np.zeros(3, dtype=np.float32)
        self._cameraTarget = np.zeros(3, dtype=np.float32)
        self._cameraUp = np.zeros(3, dtype=np.float32)

    @property
    def gWindow(self):
        return self._gWindow

    @property
    def gContext(self):
        return self._gContext

    def init(self) -> None:
        """
        Initialise an SDL2 RenderWindow, not directly but via the SDL2Decorator
        """
        print(f'{self.getClassName()}: init()')

        #SDL_Init for the window initialization
        sdl_not_initialised = sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO | sdl2.SDL_INIT_TIMER)
        if sdl_not_initialised != 0:
            print("SDL2 could not be initialised! SDL Error: ", sdl2.SDL_GetError())
            exit(1)

        #setting OpenGL attributes for the GL state
        sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_CONTEXT_FLAGS,
                                 sdl2.SDL_GL_CONTEXT_FORWARD_COMPATIBLE_FLAG
                                 )
        sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_CONTEXT_PROFILE_MASK,
                                 sdl2.SDL_GL_CONTEXT_PROFILE_CORE
                                 )
        sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_DOUBLEBUFFER, 1)

        sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_ACCELERATED_VISUAL, 1)

        sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_DEPTH_SIZE, 24)
        sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_STENCIL_SIZE, 8)
        sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_MULTISAMPLEBUFFERS, 1)
        # SDL_GL_MULTISAMPLESAMPLES is intentionally left unset: it does not work
        # reliably on VMs and some Linux systems.

        if self.openGLversion == 3:
            print("=" * 24)
            print("Using OpenGL version 3.2")
            print("="*24)
            sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_CONTEXT_MAJOR_VERSION, 3)
            sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_CONTEXT_MINOR_VERSION, 2)
        else:
            print("="*24)
            print("Using OpenGL version 4.1")
            print("="*24)
            sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_CONTEXT_MAJOR_VERSION, 4)
            sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_CONTEXT_MINOR_VERSION, 1)

        sdl2.SDL_SetHint(sdl2.SDL_HINT_MAC_CTRL_CLICK_EMULATE_RIGHT_CLICK, b"1")
        sdl2.SDL_SetHint(sdl2.SDL_HINT_VIDEO_HIGHDPI_DISABLED, b"1")

        #creating the SDL2 window
        self._gWindow = sdl2.SDL_CreateWindow(self._windowTitle.encode(),
                                              sdl2.SDL_WINDOWPOS_CENTERED,
                                              sdl2.SDL_WINDOWPOS_CENTERED,
                                              self._windowWidth,
                                              self._windowHeight,
                                              sdl2.SDL_WINDOW_OPENGL | sdl2.SDL_WINDOW_RESIZABLE | sdl2.SDL_WINDOW_SHOWN )

        if self._gWindow is None:
            print("Window could not be created! SDL Error: ", sdl2.SDL_GetError())
            exit(1)

        #create the OpenGL context for rendering into the SDL2Window that was constructed just before
        self._gContext = sdl2.SDL_GL_CreateContext(self._gWindow)
        if self._gContext is None:
            print("OpenGL Context could not be created! SDL Error: ", sdl2.SDL_GetError())
            exit(1)
        sdl2.SDL_GL_MakeCurrent(self._gWindow, self._gContext)
        if sdl2.SDL_GL_SetSwapInterval(1) < 0:
            print("Warning: Unable to set VSync! SDL Error: ", sdl2.SDL_GetError())
        #obtain the GL versioning system info
        self._gVersionLabel = f'OpenGL {gl.glGetString(gl.GL_VERSION).decode()} GLSL {gl.glGetString(gl.GL_SHADING_LANGUAGE_VERSION).decode()} Renderer {gl.glGetString(gl.GL_RENDERER).decode()}'
        print(self._gVersionLabel)

    def init_post(self) -> None:
        """
        Post init method for SDL2
        this should be ctypiically alled AFTER all other GL contexts have been created
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
        sdl2.SDL_GL_SwapWindow(self._gWindow)

    def shutdown(self) -> None:
        """
        Shutdown and cleanup SDL2 operations
        """
        print(f'{self.getClassName()}: shutdown()')
        if self._gContext is not None and self._gWindow is not None:
            sdl2.SDL_GL_DeleteContext(self._gContext)
            sdl2.SDL_DestroyWindow(self._gWindow)
            sdl2.SDL_Quit()

    def event_input_process(self, running: bool = True) -> bool:
        """
        process SDL2 basic events and input
        """
        events = sdl2.ext.get_events()
        for event in events:
            if event.type == sdl2.SDL_KEYDOWN:
                if event.key.keysym.sym == sdl2.SDLK_ESCAPE:
                    running = False
            elif event.type == sdl2.SDL_QUIT:
                running = False
            elif event.type == sdl2.SDL_WINDOWEVENT:
                if event.window.event == sdl2.SDL_WINDOWEVENT_RESIZED:
                    print("Window Resized to ", event.window.data1, " X ", event.window.data2)
                    # new width and height: event.window.data1 and event.window.data2
                    self._windowWidth = event.window.data1
                    self._windowHeight = event.window.data2
                    gl.glViewport(0, 0, event.window.data1, event.window.data2)
        return running

    def accept(self, system: System, event: Event | None = None) -> None:
        system.apply2SDLWindow(self, event)


class GLFWWindow(RenderWindow):
    """The concrete subclass of RenderWindow for the GLFW GUI API"""

    #: identifies this window's backend to RenderDecorator/ImGUIDecorator, instead of a
    #: `type(window).__name__` string check
    BACKEND_NAME = "GLFW"

    def __init__(
        self,
        windowWidth: int | None = None,
        windowHeight: int | None = None,
        windowTitle: str | None = None,
        scene: Any = None,
        eventManager: Any = None,
        openGLversion: int = 4,
    ):
        # lazy import -- see this module's docstring for why
        global glfw
        import glfw

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
        self._cameraUp = np.zeros(3, dtype=np.float32)

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


if __name__ == "__main__":
    # The client code.
    gWindow = SDL2Window(openGLversion=3)
    # uses openGL version 3.2 instead of the default 4.1
    gWindow.init()
    gWindow.init_post()
    running = True
    # MAIN RENDERING LOOP
    while running:
        gWindow.display()
        running = gWindow.event_input_process(running)
        gWindow.display_post()
    gWindow.shutdown()
