"""
Viewer classes, part of the Elements.pyGLV

Elements.pyGLV (Computer Graphics for Deep Learning and Scientific Visualization)
@Copyright 2021-2022 Dr. George Papagiannakis

The classes below are all related to the GUI and Display part of the package

Basic design principles are based on the Decorator Design pattern:
	• https://refactoring.guru/design-patterns/decorator
	• https://github.com/faif/python-patterns/blob/master/patterns/structural/decorator.py
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Any

import numpy as np
import sdl2
import sdl2.ext
import OpenGL.GL as gl
import imgui
from imgui.integrations.sdl2 import SDL2Renderer

import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Event import Event
from Elements.pyECSS.System import System


class RenderWindow(ABC):
    """
    The Abstract base class of the Viewer GUI/Display sub-system of pyglGA
    based on the Decorator Pattern, this class is "wrapped" by decorators
    in order to provide extra cpapabilities e.g. SDL2 window, context and ImGUI widgets
    """

    def __init__(self):
        self._eventManager = None
        self._scene = None

    #define properties for EventManager, Scene objects
    @property
    def eventManager(self):
        """  Get RenderWindow's eventManager  """
        return self._eventManager
    @eventManager.setter
    def eventManager(self, value) -> None:
        self._eventManager = value

    @property
    def scene(self):
        """  Get RenderWindow's Scene reference  """
        return self._scene
    @scene.setter
    def scene(self, value) -> None:
        self._scene = value

    @abstractmethod
    def init(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def init_post(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def display(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def display_post(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def shutdown(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def event_input_process(self, running: bool = True) -> bool:
        raise NotImplementedError

    @abstractmethod
    def accept(self, system: System, event: Event | None = None) -> None:
        """
        Accepts a class object to operate on the RenderWindow, based on the Visitor pattern.

        :param system: [a System object]
        :type system: [System]
        """
        raise NotImplementedError

    @classmethod
    def getClassName(cls) -> str:
        return cls.__name__


class SDL2Window(RenderWindow):
    """ The concrete subclass of RenderWindow for the SDL2 GUI API

    :param RenderWindow: [description]
    :type RenderWindow: [type]
    """

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


class RenderDecorator(RenderWindow):
    """
    Main Decorator class that wraps a RenderWindow so that all other Decorator classes can dynamically be
    adding layered functionality on top of the wrapee (RenderWindow) e.g. ImGUI widgets etc.

    :param RenderWindow: the RenderWindow (or another RenderDecorator) being wrapped
    :type RenderWindow: RenderWindow
    """

    #: modifier key that flips a TRS keyboard shortcut / the wireframe shortcut into its negative variant
    _MODIFIER_KEY = sdl2.KMOD_ALT

    #: keydown -> (attribute dict name, axis) bindings for TRS shortcuts applied to a selected scenegraph node
    _TRS_KEY_BINDINGS: dict[int, tuple[str, str]] = {
        sdl2.SDLK_w: ("translation", "x"),
        sdl2.SDLK_e: ("translation", "y"),
        sdl2.SDLK_r: ("translation", "z"),
        sdl2.SDLK_t: ("rotation", "x"),
        sdl2.SDLK_y: ("rotation", "y"),
        sdl2.SDLK_u: ("rotation", "z"),
        sdl2.SDLK_i: ("scale", "x"),
        sdl2.SDLK_o: ("scale", "y"),
        sdl2.SDLK_p: ("scale", "z"),
    }

    def __init__(self, wrapee: RenderWindow):
        super().__init__()

        self._wrapeeWindow = wrapee

        self._eye = (2.5, 2.5, 2.5)
        self._target = (0.0, 0.0, 0.0)
        self._up = (0.0, 1.0, 0.0)

        # TRS shortcuts state, see cameraHandling()/event_input_process()
        self.translation = {"x": 0.0, "y": 0.0, "z": 0.0}
        self.rotation = {"x": 0.0, "y": 0.0, "z": 0.0}
        self.scale = {"x": 0.0, "y": 0.0, "z": 0.0}

        self.traverseCamera()

    @property
    def wrapeeWindow(self):
        return self._wrapeeWindow

    def init(self) -> None:
        """
        Initialise the wrapee window and then this decorator.
        """
        self._wrapeeWindow.init()
        print(f'RenderDecorator: init()')

    def display(self) -> None:
        """
        Main decorator display method
        """
        self._wrapeeWindow.display()

    def shutdown(self) -> None:
        """
        Shutdown the wrapee window and then this decorator.
        """
        self._wrapeeWindow.shutdown()
        print(f'RenderDecorator: shutdown()')

    def traverseCamera(self) -> None:
        """
        Look for an Entity whose name contains "camera" (case-insensitive) directly under the scene root
        and keep a reference to it in self.cam, or None if there isn't one.
        """
        self.cam = None
        scene = self.wrapeeWindow.scene
        if scene is None:
            return
        children = scene.world.root._children
        if not children:
            return
        self.cam = next((child for child in children if "camera" in child.name.lower()), None)

    def createViewMatrix(self, eye: Iterable[float], lookAt: Iterable[float], upVector: Iterable[float]) -> None:
        """
        Build a view matrix from eye/target/up, push it to the wrapee window and the camera Event.
        """
        self._eye = tuple(eye)
        self._target = tuple(lookAt)
        self._up = tuple(upVector)
        view_matrix = util.lookat(eye, lookAt, upVector)
        self.wrapeeWindow._cameraEye = np.array(eye, dtype=np.float32)
        self.wrapeeWindow._cameraTarget = np.array(lookAt, dtype=np.float32)
        self.wrapeeWindow._myCamera = view_matrix
        self._updateCamera.value = view_matrix

    def updateCamera(self, moveX: bool, moveY: bool, moveZ: bool, rotateX: bool, rotateY: bool) -> None:
        """
        Apply one camera move/rotate step, either to an Entity-based camera (self.cam) when the scene
        has one, or to a free eye/target/up camera otherwise.
        """
        if self.cam is not None:
            # camera is an Entity in the scenegraph (examples 7-11 and pyJANVRED)
            cameraspeed = 5
            if rotateX:
                rotMatY = util.rotate((0, 1, 0), self.rotation["x"] * cameraspeed)
                self.cam.trans1.trs = rotMatY @ self.cam.trans1.trs
            elif rotateY:
                rotMatX = util.rotate((1, 0, 0), -self.rotation["y"] * cameraspeed)
                self.cam.trans1.trs = self.cam.trans1.trs @ rotMatX
            if moveX or moveY or moveZ:
                transMat = util.translate(self.translation["x"], self.translation["y"], -self.translation["z"])
                self.cam.trans1.trs = self.cam.trans1.trs @ transMat
        else:
            # free eye/target/up camera, no Entity in the scenegraph (examples 4-6, 8-10)
            cameraspeed = 0.2
            teye = np.array(self._eye)
            ttarget = np.array(self._target)
            tup = np.array(self._up)

            forwardDir = util.normalise(ttarget - teye)
            rightDir = util.normalise(np.cross(forwardDir, tup))

            if rotateX:
                rotMatY = util.rotate(tup, self.rotation["x"] * cameraspeed*15)
                transMatY = util.translate(ttarget) @ rotMatY @ util.translate(-ttarget)
                teye = transMatY @ np.append(teye, [1])
                teye = teye[:-1] / teye[-1]
            elif rotateY:
                rotMatX = util.rotate(rightDir, -self.rotation["y"] * cameraspeed*15)
                transMatX = util.translate(ttarget) @ rotMatX @ util.translate(-ttarget)
                teye = transMatX @ np.append(teye, [1])
                teye = teye[:-1] / teye[-1]
            elif moveX or moveY:
                panX = -cameraspeed * self.translation["x"] * rightDir
                panY = -self.translation["y"] * cameraspeed * tup
                teye += panX + panY
                ttarget += panX + panY
            elif moveZ:
                zoom =  np.sign(self.translation["z"]) * cameraspeed * forwardDir
                teye += zoom
                ttarget += zoom
            self.createViewMatrix(teye, ttarget, tup)

            if self._wrapeeWindow.eventManager is not None:
                self.wrapeeWindow.eventManager.notify(self, self._updateCamera)

    def on_mouse_motion(self, event, x, y, dx, dy) -> None:
        """Called when the mouse is moved.

            event: sdl2.events.SDL_Event,
            x: horiz coord relative to window, y: vert coord relative to window,
            dx: relative horizontal motion, dy: relative vertical motion
        """
        pass

    def on_mouse_press(self, event, x, y, button, dclick) -> None:
        """Called when mouse buttons are pressed.

            event: sdl2.events.SDL_Event,
            x: horiz coord relative to window, y: vert coord relative to window,
            dx: relative horizontal motion, dy: relative vertical motion
            button: RIGHT - MIDDLE - LEFT
            dclick: True - False if button was double click
        """
        pass

    def resetAll(self) -> None:
        """Zero the per-frame translation/rotation deltas and reset scale to identity."""
        self.translation["x"] = self.translation["y"] = self.translation["z"] = 0.0
        self.rotation["x"] = self.rotation["y"] = self.rotation["z"] = 0.0
        self.scale["x"] = self.scale["y"] = self.scale["z"] = 1.0

    def cameraHandling(self, x: float, y: float, height: int, width: int) -> None:
        """Translate a mouse-wheel or right-drag delta into a translate/rotate camera update."""
        keystatus = sdl2.SDL_GetKeyboardState(None)
        self.resetAll()

        if keystatus[sdl2.SDL_SCANCODE_LSHIFT]:
            if abs(x) > abs(y):
                self.translation["x"] = x/width*60 #np.sign(event.wheel.x)
                self.updateCamera(True, False, False, False, False)
            else:
                self.translation["y"] =  y/height*60 #np.sign(event.wheel.y)
                self.updateCamera(False, True, False, False, False)
        elif keystatus[sdl2.SDL_SCANCODE_LCTRL]:
            self.translation["z"] =  y/height*60 #-np.sign(event.wheel.y)
            self.updateCamera(False, False, True, False, False)
        else:
            if abs(x) > abs(y):
                self.rotation["x"] = np.sign(x) #event.wheel.x/height*180
                self.updateCamera(False, False,False, True, False)
            else:
                self.rotation["y"] = np.sign(y) #event.wheel.y/width*180
                self.updateCamera(False, False,False, False, True)

    def toggle_Wireframe(self) -> None:
        """
        Flip wireframe rendering ON/OFF on the underlying window. If this decorator is (or wraps into)
        an ImGUI decorator with its own wireframe checkbox/Event, keep those in sync too, the same way
        createViewMatrix() reaches into ImGUIDecorator's camera Event.
        """
        wireframeMode = not self._wrapeeWindow._wireframeMode
        self._wrapeeWindow._wireframeMode = wireframeMode

        if hasattr(self, "_wireframeMode"):
            self._wireframeMode = wireframeMode
        if getattr(self, "_updateWireframe", None) is not None:
            self._updateWireframe.value = wireframeMode
            if self._wrapeeWindow.eventManager is not None:
                self.wrapeeWindow.eventManager.notify(self, self._updateWireframe)

    def _isNodeShortcutsActive(self) -> bool:
        """
        True when the TRS keyboard shortcuts (W/E/R/T/Y/U/I/O/P) should apply to a selected scenegraph
        node. Only Elements.pyGLV.GUI.ImguiDecorator.ImGUIecssDecorator supports node selection this
        way; its class name is compared as a string here to avoid a circular import between this module
        and ImguiDecorator.py.
        """
        scene = self._wrapeeWindow.scene
        return (
            hasattr(scene, "_gContext")
            and scene._gContext.__class__.__name__ == "ImGUIecssDecorator"
            and bool(self.selected)
        )

    def event_input_process(self) -> bool:
        """
        process SDL2 basic events and input
        """
        running = True
        events = sdl2.ext.get_events()
        width = self.wrapeeWindow._windowWidth
        height = self.wrapeeWindow._windowHeight

        for event in events:
            if event.type == sdl2.SDL_MOUSEWHEEL:
                self.cameraHandling(event.wheel.x, event.wheel.y, height, width)

            elif event.type == sdl2.SDL_MOUSEMOTION:
                if event.motion.state & sdl2.SDL_BUTTON_RMASK:
                    self.cameraHandling(-event.motion.xrel, event.motion.yrel, height, width)

            elif event.type == sdl2.SDL_KEYDOWN:
                ################## toggle the wireframe using the F key #############################
                if event.key.keysym.sym == sdl2.SDLK_f:
                    self.toggle_Wireframe()

                elif event.key.keysym.sym == sdl2.SDLK_ESCAPE:
                    running = False

                ########## shortcuts for selected node from the tree, e.g. W (+alt: -) translates x ###
                elif self._isNodeShortcutsActive():
                    binding = self._TRS_KEY_BINDINGS.get(event.key.keysym.sym)
                    if binding is not None:
                        group, axis = binding
                        step = -0.1 if (sdl2.SDL_GetModState() & self._MODIFIER_KEY) else 0.1
                        getattr(self, group)[axis] += step

            elif event.type == sdl2.SDL_QUIT:
                running = False

            elif event.type == sdl2.SDL_WINDOWEVENT:
                if event.window.event == sdl2.SDL_WINDOWEVENT_RESIZED:
                    print("Window Resized to ", event.window.data1, " X " , event.window.data2)
                    self.wrapeeWindow._windowWidth = event.window.data1
                    self.wrapeeWindow._windowHeight = event.window.data2
                    # new width and height: event.window.data1 and event.window.data2
                    gl.glViewport(0, 0, event.window.data1, event.window.data2)

            #imgui event
            self._imguiRenderer.process_event(event)
        #imgui input
        self._imguiRenderer.process_inputs()
        return running

    def display_post(self) -> None:
        """
        Post diplay method after all other display calls have been issued
        """
        self._wrapeeWindow.display_post()

    def init_post(self) -> None:
        """
        Post init method
        this should be ctypiically alled AFTER all other GL contexts have been created, e.g. ImGUI context
        """
        self._wrapeeWindow.init_post()

    def accept(self, system: System, event: Event | None = None) -> None:
        pass


class RenderGLStateSystem(System):
    """
    System that operates on a RenderDecorator (ImGUIDecorator) and affect GL State

    """

    def __init__(self, name=None, type=None, id=None):
        super().__init__(name, type, id)

    def update(self) -> None:
        """
        method to be subclassed for  behavioral or logic computation

        """
        pass

    def apply2ImGUIDecorator(self, imGUIDecorator, event: Event | None = None) -> None:
        """
        method for  behavioral or logic computation
        when visits Components.

        In this case update GL State from ImGUIDecorator

        """
        pass

    def apply2SDLWindow(self, sdlWindow: SDL2Window, event: Event | None = None) -> None:
        """method for  behavioral or logic computation
        when visits Components.

        In this case update GL State from SDLWindow

        :param sdlWindow: [description]
        :type sdlWindow: [type]
        :param event: [description], defaults to None
        :type event: [type], optional
        """
        if event.name == "OnUpdateWireframe":
            sdlWindow._wireframeMode = event.value

        if event.name == "OnUpdateCamera":
            sdlWindow._myCamera = event.value


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
