"""
The EventManager: how a change in one part of the scene reaches another without the two knowing
about each other.

Four dictionaries, all keyed by event name (see Elements.pyECSS.Event.EventManager):

    _events       the Event objects themselves -- name, id, and a `value` carrying the payload
    _publishers   who may raise it (bookkeeping; notify() does not check this)
    _subscribers  the object it is delivered to -- anything with accept(system, event)
    _actuators    the System that actually does the work

eManager.notify(sender, event) looks the name up in _subscribers and _actuators and calls
subscriber.accept(actuator, event). That is the whole mechanism.

This example wires the two built-in events (the GUI's Wireframe checkbox and camera) and then adds
one of its own, OnSpinCube, driven by the R key.
"""

import numpy as np
import sdl2

import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, RenderMesh
from Elements.pyECSS.System import System
from Elements.pyECSS.Event import Event
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GUI.Viewer import RenderGLStateSystem
from Elements.pyGLV.GUI.ImguiDecorator import ImGUIecssDecorator2
from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray

from Elements.utils.terrain import generateTerrain
from Elements.utils.Shortcuts import displayGUI_text
from Elements.definitions import SHADER_DIR

from OpenGL.GL import GL_LINES

example_description = \
"The EventManager, which delivers a change to whoever cares about it.\n\n\
Two built-in events are wired below:\n\
  OnUpdateWireframe   the GUI's Wireframe checkbox\n\
  OnUpdateCamera      the camera, whenever it moves\n\
and one of our own:\n\
  OnSpinCube          press R to turn the cube 15 degrees\n\n\
Each is delivered as subscriber.accept(actuator, event) -- see the terminal,\n\
where eManager.print() lists all four dictionaries at startup.\n\n\
Right mouse button to fly, F for wireframe, ESC to quit."

winWidth = 1024
winHeight = 768

# ---------------- our own event: a subscriber and an actuator ----------------

class SpinSubscriber:
    """A subscriber is any object with accept(system, event): the EventManager hands it the
    actuator System and the Event, and it forwards both on.

    A Component would do as well -- they all have accept() -- except that BasicTransform.accept()
    drops its event argument, so an actuator reached that way cannot see event.value. Taking the
    call here keeps the payload.
    """

    def __init__(self, trans):
        self.trans = trans

    def accept(self, system, event=None):
        system.apply2SpinSubscriber(self, event)


class SpinSystem(System):
    """The actuator: the only place that knows what OnSpinCube actually means. Swap this System for
    another and the same event does something else -- that is the point of the indirection."""

    def apply2SpinSubscriber(self, subscriber, event=None):
        if event is not None:
            subscriber.trans.trs = subscriber.trans.trs @ event.value
            print("OnSpinCube delivered to", subscriber.trans.name)

# ---------------- geometry ----------------

vertexCube = np.array([
    [-0.5, -0.5, 0.5, 1.0],
    [-0.5, 0.5, 0.5, 1.0],
    [0.5, 0.5, 0.5, 1.0],
    [0.5, -0.5, 0.5, 1.0],
    [-0.5, -0.5, -0.5, 1.0],
    [-0.5, 0.5, -0.5, 1.0],
    [0.5, 0.5, -0.5, 1.0],
    [0.5, -0.5, -0.5, 1.0]
],dtype=np.float32)
colorCube = np.array([
    [0.0, 0.0, 0.0, 1.0],
    [1.0, 0.0, 0.0, 1.0],
    [1.0, 1.0, 0.0, 1.0],
    [0.0, 1.0, 0.0, 1.0],
    [0.0, 0.0, 1.0, 1.0],
    [1.0, 0.0, 1.0, 1.0],
    [1.0, 1.0, 1.0, 1.0],
    [0.0, 1.0, 1.0, 1.0]
], dtype=np.float32)
indexCube = np.array((1,0,3, 1,3,2,
                  2,3,7, 2,7,6,
                  3,0,4, 3,4,7,
                  6,5,1, 6,1,2,
                  4,5,6, 4,6,7,
                  5,4,0, 5,0,1), np.uint32)

vertexTerrain, indexTerrain, colorTerrain = generateTerrain(size=4)

# ---------------- the scene: RooT -> cube, terrain ----------------

scene = Scene()
rootEntity = scene.world.createEntity(Entity(name="RooT"))

cube = scene.world.createEntity(Entity(name="cube"))
scene.world.addEntityChild(rootEntity, cube)
cube_trans = scene.world.addComponent(cube, BasicTransform(name="cube_trans", trs=util.translate(0,0.5,0)))
cube_mesh = scene.world.addComponent(cube, RenderMesh(name="cube_mesh"))
cube_mesh.vertex_attributes.append(vertexCube)
cube_mesh.vertex_attributes.append(colorCube)
cube_mesh.vertex_index.append(indexCube)
cube_vArray = scene.world.addComponent(cube, VertexArray())
cube_shader = scene.world.addComponent(cube, ShaderGLDecorator(
    Shader(vertex_import_file=SHADER_DIR / "ColorMVP.vert", fragment_import_file=SHADER_DIR / "Color.frag")))

terrain = scene.world.createEntity(Entity(name="terrain"))
scene.world.addEntityChild(rootEntity, terrain)
terrain_trans = scene.world.addComponent(terrain, BasicTransform(name="terrain_trans", trs=util.identity()))
terrain_mesh = scene.world.addComponent(terrain, RenderMesh(name="terrain_mesh"))
terrain_mesh.vertex_attributes.append(vertexTerrain)
terrain_mesh.vertex_attributes.append(colorTerrain)
terrain_mesh.vertex_index.append(indexTerrain)
terrain_vArray = scene.world.addComponent(terrain, VertexArray(primitive=GL_LINES))
terrain_shader = scene.world.addComponent(terrain, ShaderGLDecorator(
    Shader(vertex_import_file=SHADER_DIR / "ColorMVP.vert", fragment_import_file=SHADER_DIR / "Color.frag")))

# ---------------- systems ----------------

initUpdate = scene.world.createSystem(InitGLShaderSystem())
renderUpdate = scene.world.createSystem(RenderGLShaderSystem())

# MAIN RENDERING LOOP

running = True
scene.init(imgui=True, windowWidth = winWidth, windowHeight = winHeight,
           windowTitle = "The EventManager", customImGUIdecorator = ImGUIecssDecorator2,
           openGLversion = 4)

scene.world.traverse_visit(initUpdate, scene.world.root)

# ---------------- the event manager ----------------
# After scene.init(): the ImGUI decorator registers OnUpdateWireframe/OnUpdateCamera in _events and
# _publishers during its own init(), so those entries only exist from here on.

eManager = scene.world.eventManager
gWindow = scene.renderWindow
gGUI = scene.gContext

# The two built-in events. Subscriber: the window, whose accept() forwards to
# system.apply2SDLWindow(). Actuator: RenderGLStateSystem, which sets _wireframeMode / _myCamera on
# it. Both of those are also written directly nowadays, so an example can skip this wiring
# entirely -- it is the mechanism that matters here, not the effect.
renderGLEventActuator = RenderGLStateSystem()
eManager._subscribers['OnUpdateWireframe'] = gWindow
eManager._actuators['OnUpdateWireframe'] = renderGLEventActuator
eManager._subscribers['OnUpdateCamera'] = gWindow
eManager._actuators['OnUpdateCamera'] = renderGLEventActuator

# Our own event, registered in all four dictionaries by hand. `value` is filled in just before each
# notify() -- it is the payload, here the matrix to apply.
spinCubeEvent = Event(name="OnSpinCube", id=400, value=util.identity())
spinSubscriber = SpinSubscriber(cube_trans)

eManager._events['OnSpinCube'] = spinCubeEvent
eManager._publishers['OnSpinCube'] = gWindow          # what raises it: the R key, read below
eManager._subscribers['OnSpinCube'] = spinSubscriber  # what it is delivered to
eManager._actuators['OnSpinCube'] = SpinSystem()      # what acts on it

eManager.print()   # the four dictionaries, on the terminal

eye = util.vec(2.5, 2.5, 2.5)
target = util.vec(0.0, 0.0, 0.0)
up = util.vec(0.0, 1.0, 0.0)
gGUI.createViewMatrix(eye, target, up)

projMat = util.perspective(50.0, winWidth/winHeight, 0.01, 100.0)

rKeyWasPressed = False   # so one press raises one event, instead of one per frame

while running:
    running = scene.render()
    displayGUI_text(example_description)
    scene.world.traverse_visit(renderUpdate, scene.world.root)

    # raise OnSpinCube on the rising edge of R
    keys = sdl2.SDL_GetKeyboardState(None)
    rPressed = bool(keys[sdl2.SDL_SCANCODE_R])
    if rPressed and not rKeyWasPressed:
        spinCubeEvent.value = util.rotate((0.0, 1.0, 0.0), 15.0)
        eManager.notify(gWindow, spinCubeEvent)
    rKeyWasPressed = rPressed

    view = gWindow._myCamera
    # cube_trans.trs is read here, not cached before the loop: the actuator replaces it on every
    # event, and a cached reference would still point at the matrix from before the first press
    cube_shader.setUniformVariable(key='modelViewProj', value=projMat @ view @ cube_trans.trs, mat4=True)
    terrain_shader.setUniformVariable(key='modelViewProj', value=projMat @ view @ terrain_trans.trs, mat4=True)

    scene.render_post()

scene.shutdown()
