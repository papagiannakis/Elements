"""
Viewer classes, part of the Elements.pyGLV

Elements.pyGLV (Computer Graphics for Deep Learning and Scientific Visualization)
@Copyright 2021-2022 Dr. George Papagiannakis

The classes below are all related to the GUI and Display part of the package. The concrete window
backends (SDL2Window, GLFWWindow) live in Elements.pyGLV.GUI.Windows -- this module holds only the
backend-agnostic core: the RenderWindow ABC every backend implements, the RenderDecorator base all
ImGUI decorators build on, and RenderGLStateSystem.

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

import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Event import Event
from Elements.pyECSS.System import System
from Elements.pyGLV.GUI import CameraControl


class RenderWindow(ABC):
    """
    The Abstract base class of the Viewer GUI/Display sub-system of pyglGA
    based on the Decorator Pattern, this class is "wrapped" by decorators
    in order to provide extra cpapabilities e.g. SDL2 window, context and ImGUI widgets
    """

    #: identifies this window's backend (e.g. "SDL2", "GLFW") to RenderDecorator/ImGUIDecorator,
    #: instead of a `type(window).__name__` string check -- every concrete subclass overrides this
    BACKEND_NAME: str = "Unknown"

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


class RenderDecorator(RenderWindow):
    """
    Main Decorator class that wraps a RenderWindow so that all other Decorator classes can dynamically be
    adding layered functionality on top of the wrapee (RenderWindow) e.g. ImGUI widgets etc.

    :param RenderWindow: the RenderWindow (or another RenderDecorator) being wrapped
    :type RenderWindow: RenderWindow
    """

    def __init__(self, wrapee: RenderWindow):
        super().__init__()

        self._wrapeeWindow = wrapee

        self._eye = (2.5, 2.5, 2.5)
        self._target = (0.0, 0.0, 0.0)
        self._up = (0.0, 1.0, 0.0)

        # per-frame camera translate/rotate deltas, see cameraHandling()/resetAll()
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
        self.wrapeeWindow._cameraUp = np.array(upVector, dtype=np.float32)
        self.wrapeeWindow._myCamera = view_matrix
        self._updateCamera.value = view_matrix

    def updateCamera(self, moveX: bool, moveY: bool, moveZ: bool, rotateX: bool, rotateY: bool) -> None:
        """
        Apply one camera move/rotate step, either to an Entity-based camera (self.cam) when the scene
        has one, or to a free eye/target/up camera otherwise. The actual math lives in
        Elements.pyGLV.GUI.CameraControl, as plain functions with no window/event coupling.
        """
        if self.cam is not None:
            # camera is an Entity in the scenegraph (examples 7-11 and pyJANVRED)
            self.cam.trans1.trs = CameraControl.compute_entity_camera_step(
                self.cam.trans1.trs, self.translation, self.rotation, moveX, moveY, moveZ, rotateX, rotateY,
            )
        else:
            # free eye/target/up camera, no Entity in the scenegraph (examples 4-6, 8-10)
            new_eye, new_target = CameraControl.compute_free_camera_step(
                self._eye, self._target, self._up, self.translation, self.rotation, moveX, moveY, moveZ, rotateX, rotateY,
            )
            self.createViewMatrix(new_eye, new_target, self._up)

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
        self.resetAll()

        shift, ctrl = self._wrapeeWindow.get_modifier_state()

        if shift:
            if abs(x) > abs(y):
                self.translation["x"] = x/width*60 #np.sign(event.wheel.x)
                self.updateCamera(True, False, False, False, False)
            else:
                self.translation["y"] =  y/height*60 #np.sign(event.wheel.y)
                self.updateCamera(False, True, False, False, False)
        elif ctrl:
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

    def event_input_process(self) -> bool:
        """
        process backend input. SDL2 needs its own per-event loop here: QUIT/resize/ESC only ever
        arrive as events, and classic-pyimgui's SDL2Renderer is fed per-event (process_event()),
        unlike GLFW's callback-based integration -- see _event_input_process_glfw(). Camera-drag
        and wireframe-toggle detection, though, are backend-agnostic polling calls either way
        (poll_right_drag_delta()/consume_wireframe_toggle_key(), implemented by both SDL2Window
        and GLFWWindow) -- see _poll_camera_and_wireframe().
        """
        if self._wrapeeWindow.BACKEND_NAME == "GLFW":
            return self._event_input_process_glfw()

        running = True
        events = sdl2.ext.get_events()
        width = self.wrapeeWindow._windowWidth
        height = self.wrapeeWindow._windowHeight

        for event in events:
            if event.type == sdl2.SDL_MOUSEWHEEL:
                self.cameraHandling(event.wheel.x, event.wheel.y, height, width)

            elif event.type == sdl2.SDL_KEYDOWN:
                if event.key.keysym.sym == sdl2.SDLK_ESCAPE:
                    running = False

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

        self._poll_camera_and_wireframe(width, height)

        #imgui input
        self._imguiRenderer.process_inputs()
        return running

    def _event_input_process_glfw(self) -> bool:
        """
        process GLFW basic events and input -- GlfwRenderer (unlike SDL2Renderer) has no
        process_event(), since GLFW feeds ImGui through callbacks attached at its own
        construction time instead of a polled event queue, so there's no per-event loop here.
        """
        window = self._wrapeeWindow
        running = window.event_input_process(True)

        self._poll_camera_and_wireframe(window._windowWidth, window._windowHeight)

        self._imguiRenderer.process_inputs()
        return running

    def _poll_camera_and_wireframe(self, width: int, height: int) -> None:
        """Backend-agnostic: both SDL2Window and GLFWWindow implement poll_right_drag_delta()/
        consume_wireframe_toggle_key() by polling, so this needs no backend branch."""
        drag = self._wrapeeWindow.poll_right_drag_delta()
        if drag is not None:
            self.cameraHandling(drag[0], drag[1], height, width)

        if self._wrapeeWindow.consume_wireframe_toggle_key():
            self.toggle_Wireframe()

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
        if self._wrapeeWindow.BACKEND_NAME == "GLFW":
            self._wrapeeWindow.register_scroll_callback(self._on_glfw_scroll)

    def _on_glfw_scroll(self, xoffset: float, yoffset: float) -> None:
        """Scroll-wheel zoom for the GLFW backend, reusing the same cameraHandling() path SDL2's
        SDL_MOUSEWHEEL event drives."""
        width = self.wrapeeWindow._windowWidth
        height = self.wrapeeWindow._windowHeight
        self.cameraHandling(xoffset, yoffset, height, width)

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

    def apply2SDLWindow(self, sdlWindow, event: Event | None = None) -> None:
        """method for  behavioral or logic computation
        when visits Components.

        In this case update GL State from SDLWindow (Elements.pyGLV.GUI.Windows.SDL2Window)

        :param sdlWindow: [description]
        :type sdlWindow: [type]
        :param event: [description], defaults to None
        :type event: [type], optional
        """
        if event.name == "OnUpdateWireframe":
            sdlWindow._wireframeMode = event.value

        if event.name == "OnUpdateCamera":
            sdlWindow._myCamera = event.value

    def apply2GLFWWindow(self, glfwWindow, event: Event | None = None) -> None:
        """method for  behavioral or logic computation
        when visits Components.

        In this case update GL State from a GLFWWindow (Elements.pyGLV.GUI.Windows.GLFWWindow)

        :param glfwWindow: [description]
        :type glfwWindow: [type]
        :param event: [description], defaults to None
        :type event: [type], optional
        """
        if event.name == "OnUpdateWireframe":
            glfwWindow._wireframeMode = event.value

        if event.name == "OnUpdateCamera":
            glfwWindow._myCamera = event.value
