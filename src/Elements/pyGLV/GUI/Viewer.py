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

        #: world units per frame for the WASD/QE fly controls. Not a constant: no single value
        #: suits scenes framed anywhere from 1 to 12 units from their target, so scrolling with the
        #: right button held retunes it live -- see handleScroll()/adjustFlySpeed().
        self.flySpeed = CameraControl.FLY_SPEED
        #: so adjustFlySpeed() reports hitting a bound once instead of once per scroll notch
        self._flySpeedLimitReported = False

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

    def handleScroll(self, x: float, y: float) -> None:
        """
        Scrolling retunes the WASD/QE fly speed and nothing else -- it never moves the camera.

        It used to drive the camera directly (orbit, or pan/zoom with shift/ctrl), which is
        deliberately gone: mixing "move the camera" into the same input as "set how fast the camera
        moves" jolted the view every time the speed was adjusted mid-flight. Camera motion is all
        on the right button now -- drag to look, WASD/QE to fly, shift/ctrl+drag to pan/dolly.

        x is accepted so both backends can pass their event through unchanged, but only the
        vertical axis is used: one axis keeps "scroll up = faster" unambiguous.
        """
        self.adjustFlySpeed(y)

    def adjustFlySpeed(self, notches: float) -> None:
        """
        Scale self.flySpeed by FLY_SPEED_SCROLL_STEP per scroll notch (fractional notches, as
        trackpads report, scale proportionally), clamped to MIN/MAX_FLY_SPEED, and report the new
        value on the terminal so it can actually be dialled in.
        """
        if not notches:
            return

        previous = self.flySpeed
        self.flySpeed = float(np.clip(
            self.flySpeed * (CameraControl.FLY_SPEED_SCROLL_STEP ** notches),
            CameraControl.MIN_FLY_SPEED,
            CameraControl.MAX_FLY_SPEED,
        ))

        if self.flySpeed == previous:
            # Already at a bound. Report it once rather than on every further notch: silence would
            # read as unresponsive, but a line per notch just spams the terminal.
            if not self._flySpeedLimitReported:
                limit = "minimum" if notches < 0 else "maximum"
                print(f"Camera fly speed: {self.flySpeed:.4f} units/frame (at {limit})")
                self._flySpeedLimitReported = True
            return

        self._flySpeedLimitReported = False
        print(f"Camera fly speed: {self.flySpeed:.4f} units/frame")

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
                self.handleScroll(event.wheel.x, event.wheel.y)

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
        poll_camera_fly_keys()/consume_wireframe_toggle_key() by polling, so this needs no backend
        branch."""
        drag = self._wrapeeWindow.poll_right_drag_delta()
        if drag is not None:
            self.freeLookAndFly(drag, width, height)

        # Consumed unconditionally (so the rising edge never goes stale) but acted on only while
        # the right button is held, like the rest of the camera keys -- so SPACE stays free for
        # examples that want it for something else.
        if self._wrapeeWindow.consume_target_reset_key() and self._wrapeeWindow.is_right_mouse_held():
            self.resetTarget()

        if self._wrapeeWindow.consume_wireframe_toggle_key():
            self.toggle_Wireframe()

    def resetTarget(self) -> None:
        """
        Re-aim the camera at the world origin without moving it: the eye and up stay exactly as
        they are, only the target changes, so this recovers a lost view after free-looking around
        rather than restoring some saved camera pose.

        Declines in the two cases where (eye, origin, up) has no lookat basis to build -- the eye
        sitting on the origin, and the eye directly above/below it, where the look direction would
        be parallel to up and cross(forward, up) would collapse to zero.
        """
        if self.cam is not None:
            return  # Entity-based camera moves its own BasicTransform; no eye/target pair here

        eye = np.array(self._eye, dtype=np.float64)
        toOrigin = -eye
        distance = np.linalg.norm(toOrigin)
        if distance < 1e-8:
            print("Camera target unchanged: the camera is sitting on the origin")
            return

        upDot = abs(np.dot(toOrigin / distance, util.normalise(np.array(self._up, dtype=np.float64))))
        if upDot > np.cos(np.radians(CameraControl.MIN_POLAR_ANGLE)):
            print("Camera target unchanged: looking at the origin from here would be straight "
                  "along the up vector")
            return

        self.createViewMatrix(self._eye, (0.0, 0.0, 0.0), self._up)
        if self._wrapeeWindow.eventManager is not None:
            self.wrapeeWindow.eventManager.notify(self, self._updateCamera)
        print("Camera target reset to (0, 0, 0)")

    def freeLookAndFly(self, drag: tuple[float, float], width: int, height: int) -> None:
        """
        Right-button-held navigation for the free eye/target/up camera: the drag swings the look
        direction about a stationary eye (compute_look_step), W/A/S/D move the eye and carry the
        target along so the look direction survives the move (compute_fly_step), and Q/E raise or
        lower the eye against a *fixed* target, tilting the camera (compute_rise_step).

        Holding the right button is what arms those keys, and that is the whole conflict-avoidance
        story: examples that bind W/A/S/D themselves -- the picking ones orbit a selected object
        with them, and keep +/- for its zoom -- stay in sole charge whenever it isn't held.

        Two cases deliberately fall through to the older cameraHandling() path instead:
        shift/ctrl+drag, which keep their existing pan/dolly meaning, and an Entity-based camera
        (self.cam), which has no eye/target pair to swing -- it moves its own BasicTransform.
        """
        shift, ctrl = self._wrapeeWindow.get_modifier_state()
        if shift or ctrl or self.cam is not None:
            self.cameraHandling(drag[0], drag[1], height, width)
            return

        eye, target = self._eye, self._target
        changed = False

        if drag[0] or drag[1]:
            target = CameraControl.compute_look_step(eye, target, self._up, drag[0], drag[1])
            changed = True

        keys = self._wrapeeWindow.poll_camera_fly_keys()
        if keys["forward"] or keys["right"]:
            eye, target = CameraControl.compute_fly_step(
                eye, target, self._up, keys["forward"], keys["right"], 0, self.flySpeed,
            )
            changed = True

        if keys["up"]:
            # Q/E deliberately take the other deal: the eye rises/sinks and the target stays put,
            # so the camera tilts to keep the same point in view. Returns the eye unmoved when the
            # step would reach straight-above/below the target, hence the comparison.
            risen = CameraControl.compute_rise_step(eye, target, self._up, keys["up"], self.flySpeed)
            if not np.allclose(risen, eye):
                eye = risen
                changed = True

        if not changed:
            return  # button held but neither moved nor a key down: leave the camera alone

        self.createViewMatrix(eye, target, self._up)
        if self._wrapeeWindow.eventManager is not None:
            self.wrapeeWindow.eventManager.notify(self, self._updateCamera)

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
        """Scroll wheel for the GLFW backend, reusing the same handleScroll() path SDL2's
        SDL_MOUSEWHEEL event drives."""
        self.handleScroll(xoffset, yoffset)

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
