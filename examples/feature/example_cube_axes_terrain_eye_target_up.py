"""
Copy of examples/B.Introductory/example_B5_cube_free_fly.py that recreates the Eye/Target/Up
camera sliders that used to be part of every example's default "Elements ImGUI window" panel
(Elements.pyGLV.GUI.ImguiDecorator.ImGUIDecorator.extra()). They were removed from there because
editing them silently did nothing on several examples: whenever a scene has an Entity-based camera
(RenderDecorator.traverseCamera()/self.cam is not None -- examples 7-11, pyJANVRED), that Entity's
own transform drives the view matrix every frame, so the free eye/target/up path the sliders wrote
to was simply never read.

This example has no Entity-based camera (self.cam is None here, exactly like the original
example_4), so the free eye/target/up path IS what's authoritative each frame -- this is the
example where the sliders genuinely do something, which is why the recreated panel lives here
rather than back in the shared default.

`ImGUIecssDecorator2WithEyeTargetUp` below is a small, one-off subclass defined right in this
example file (not added back to the core Elements.pyGLV.GUI.ImguiDecorator module) -- it's a niche
demo feature, not something every example should carry. It reuses the exact same plumbing the old
inline sliders used: `self._eye`/`self._target`/`self._up` (already shared with the mouse-drag
orbit path, via RenderDecorator.__init__) and `self.createViewMatrix(...)` (which pushes the result
to the window and fires the OnUpdateCamera Event) -- just without the "NEW CAMERA VALUE"-per-edit
console spam the original had.
"""

import numpy as np
import imgui

import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, Camera, RenderMesh
from Elements.pyECSS.System import  TransformSystem, CameraSystem
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GUI.Viewer import RenderGLStateSystem
from Elements.pyGLV.GUI.ImguiDecorator import ImGUIecssDecorator2
from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray

from Elements.utils.terrain import generateTerrain

from OpenGL.GL import GL_LINES

from Elements.utils.Shortcuts import displayGUI_text
from Elements.definitions import SHADER_DIR


class ImGUIecssDecorator2WithEyeTargetUp(ImGUIecssDecorator2):
    """ImGUIecssDecorator2 plus a recreated Eye/Target/Up panel -- see this file's docstring."""

    def extra(self):
        super().extra()

        imgui.set_next_window_position(340, 20, imgui.FIRST_USE_EVER)
        imgui.set_next_window_size(320, 220, imgui.FIRST_USE_EVER)
        imgui.begin("Eye / Target / Up (advanced)")
        imgui.text_wrapped(
            "Editing these only takes effect because this scene has no Entity-based camera -- "
            "see this file's docstring."
        )
        imgui.separator()

        changed, self._eye = imgui.drag_float3(
            "Eye", *self._eye, change_speed=0.01, min_value=-10, max_value=10, format="%.3f")
        if changed:
            self.createViewMatrix(self._eye, self._target, self._up)
            if self._wrapeeWindow.eventManager is not None:
                self.wrapeeWindow.eventManager.notify(self, self._updateCamera)

        changed, self._target = imgui.drag_float3(
            "Target", *self._target, change_speed=0.01, min_value=-10, max_value=10, format="%.3f")
        if changed:
            self.createViewMatrix(self._eye, self._target, self._up)
            if self._wrapeeWindow.eventManager is not None:
                self.wrapeeWindow.eventManager.notify(self, self._updateCamera)

        changed, self._up = imgui.drag_float3(
            "Up", *self._up, change_speed=0.01, min_value=-5, max_value=5, format="%.3f")
        if changed:
            self.createViewMatrix(self._eye, self._target, self._up)
            if self._wrapeeWindow.eventManager is not None:
                self.wrapeeWindow.eventManager.notify(self, self._updateCamera)

        imgui.separator()
        imgui.text(f"Up (from gWindow, via the event manager): {np.round(self._wrapeeWindow._cameraUp, 3)}")

        imgui.end()


example_description = \
"This is a scene with a cube, a terrain and axes. \n\
The cube and axes are rendered with a simple shader. \n\
that allow camera movement too, via the Elements GUI. \n\n\
A Scenegraph shows the Entities and Components of the \n\
scene, in read only way, i.e., you cannot manipulate  \n\
any information via the Scenegraph GUI. \n\n\
You can move the camera through the Elements GUI \n\
or the mouse. Hit ESC OR Close the window to quit. \n\n\
The 'Eye / Target / Up (advanced)' panel (top) recreates \n\
the camera sliders removed from the default GUI panel -- \n\
see this file's docstring for why they live here instead."

winWidth = 1024
winHeight = 768

scene = Scene()

# Scenegraph with Entities, Components
rootEntity = scene.world.createEntity(Entity(name="RooT"))
entityCam1 = scene.world.createEntity(Entity(name="entityCam1"))
scene.world.addEntityChild(rootEntity, entityCam1)
trans1 = scene.world.addComponent(entityCam1, BasicTransform(name="trans1", trs=util.identity()))

eye = util.vec(1, 0.54, 1.0)
target = util.vec(0.02, 0.14, 0.217)
up = util.vec(0.0, 1.0, 0.0)
view = util.lookat(eye, target, up)
projMat = util.perspective(50.0, 1.0, 1.0, 10.0)
m = np.linalg.inv(projMat @ view)

entityCam2 = scene.world.createEntity(Entity(name="entityCam2"))
scene.world.addEntityChild(entityCam1, entityCam2)
trans2 = scene.world.addComponent(entityCam2, BasicTransform(name="trans2", trs=util.identity()))
orthoCam = scene.world.addComponent(entityCam2, Camera(m, "orthoCam","Camera","500"))

node4 = scene.world.createEntity(Entity(name="node4"))
scene.world.addEntityChild(rootEntity, node4)
trans4 = scene.world.addComponent(node4, BasicTransform(name="trans4", trs=util.translate(0,0.5,0))) #util.identity()
mesh4 = scene.world.addComponent(node4, RenderMesh(name="mesh4"))

#Colored Axes
vertexAxes = np.array([
    [0.0, 0.0, 0.0, 1.0],
    [1.0, 0.0, 0.0, 1.0],
    [0.0, 0.0, 0.0, 1.0],
    [0.0, 1.0, 0.0, 1.0],
    [0.0, 0.0, 0.0, 1.0],
    [0.0, 0.0, 1.0, 1.0]
],dtype=np.float32)
colorAxes = np.array([
    [1.0, 0.0, 0.0, 1.0],
    [1.0, 0.0, 0.0, 1.0],
    [0.0, 1.0, 0.0, 1.0],
    [0.0, 1.0, 0.0, 1.0],
    [0.0, 0.0, 1.0, 1.0],
    [0.0, 0.0, 1.0, 1.0]
], dtype=np.float32)

#Simple Cube
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

#index arrays for above vertex Arrays
indexAxes = np.array((0,1,2,3,4,5), np.uint32) #3 simple colored Axes as R,G,B lines
indexCube = np.array((1,0,3, 1,3,2,
                  2,3,7, 2,7,6,
                  3,0,4, 3,4,7,
                  6,5,1, 6,1,2,
                  4,5,6, 4,6,7,
                  5,4,0, 5,0,1), np.uint32) #rhombus out of two triangles

# Systems
transUpdate = scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
camUpdate = scene.world.createSystem(CameraSystem("camUpdate", "CameraUpdate", "200"))
renderUpdate = scene.world.createSystem(RenderGLShaderSystem())
initUpdate = scene.world.createSystem(InitGLShaderSystem())


## ADD CUBE ##
mesh4.vertex_attributes.append(vertexCube)
mesh4.vertex_attributes.append(colorCube)
mesh4.vertex_index.append(indexCube)
vArray4 = scene.world.addComponent(node4, VertexArray())
shaderDec4 = scene.world.addComponent(node4, ShaderGLDecorator(Shader(vertex_import_file=SHADER_DIR / "ColorMVP.vert", fragment_import_file=SHADER_DIR / "Color.frag")))

# Generate terrain
vertexTerrain, indexTerrain, colorTerrain= generateTerrain(size=4,N=20)
terrain = scene.world.createEntity(Entity(name="terrain"))
scene.world.addEntityChild(rootEntity, terrain)
terrain_trans = scene.world.addComponent(terrain, BasicTransform(name="terrain_trans", trs=util.identity()))
terrain_mesh = scene.world.addComponent(terrain, RenderMesh(name="terrain_mesh"))
terrain_mesh.vertex_attributes.append(vertexTerrain)
terrain_mesh.vertex_attributes.append(colorTerrain)
terrain_mesh.vertex_index.append(indexTerrain)
terrain_vArray = scene.world.addComponent(terrain, VertexArray(primitive=GL_LINES))
terrain_shader = scene.world.addComponent(terrain, ShaderGLDecorator(Shader(vertex_import_file=SHADER_DIR / "ColorMVP.vert", fragment_import_file=SHADER_DIR / "Color.frag")))

## ADD AXES ##
axes = scene.world.createEntity(Entity(name="axes"))
scene.world.addEntityChild(rootEntity, axes)
axes_trans = scene.world.addComponent(axes, BasicTransform(name="axes_trans", trs=util.translate(0.0, 0.001, 0.0)))
axes_mesh = scene.world.addComponent(axes, RenderMesh(name="axes_mesh"))
axes_mesh.vertex_attributes.append(vertexAxes)
axes_mesh.vertex_attributes.append(colorAxes)
axes_mesh.vertex_index.append(indexAxes)
axes_vArray = scene.world.addComponent(axes, VertexArray(primitive=GL_LINES)) # note the primitive change
axes_shader = scene.world.addComponent(axes, ShaderGLDecorator(Shader(vertex_import_file=SHADER_DIR / "ColorMVP.vert", fragment_import_file=SHADER_DIR / "Color.frag")))


# MAIN RENDERING LOOP

running = True
scene.init(imgui=True, windowWidth = winWidth, windowHeight = winHeight,
           windowTitle = "Elements: A Working Event Manager (Eye/Target/Up)",
           customImGUIdecorator = ImGUIecssDecorator2WithEyeTargetUp, openGLversion = 4)

# pre-pass scenegraph to initialise all GL context dependent geometry, shader classes
# needs an active GL context
scene.world.traverse_visit(initUpdate, scene.world.root)

################### EVENT MANAGER ###################

eManager = scene.world.eventManager
gWindow = scene.renderWindow
gGUI = scene.gContext

renderGLEventActuator = RenderGLStateSystem()

eManager._subscribers['OnUpdateWireframe'] = gWindow
eManager._actuators['OnUpdateWireframe'] = renderGLEventActuator
eManager._subscribers['OnUpdateCamera'] = gWindow
eManager._actuators['OnUpdateCamera'] = renderGLEventActuator

eye = util.vec(2.5, 2.5, 2.5)
target = util.vec(0.0, 0.0, 0.0)
up = util.vec(0.0, 1.0, 0.0)
view = util.lookat(eye, target, up)

projMat = util.perspective(50.0, 1.0, 0.01, 10.0)

gWindow._myCamera = view # otherwise, an imgui slider must be moved to properly update

model_cube = trans4.trs
model_terrain = terrain.getChild(0).trs # notice that terrain.getChild(0) == terrain_trans
model_axes = axes_trans.trs

while running:
    running = scene.render()
    displayGUI_text(example_description)
    scene.world.traverse_visit(renderUpdate, scene.world.root)
    scene.world.traverse_visit_pre_camera(camUpdate, orthoCam)
    scene.world.traverse_visit(camUpdate, scene.world.root)

    view =  gWindow._myCamera # updates view via the imgui
    mvp_cube = projMat @ view @ model_cube
    mvp_terrain = projMat @ view @ model_terrain
    mvp_axes = projMat @ view @ model_axes
    axes_shader.setUniformVariable(key='modelViewProj', value=mvp_axes, mat4=True)
    terrain_shader.setUniformVariable(key='modelViewProj', value=mvp_terrain, mat4=True)
    shaderDec4.setUniformVariable(key='modelViewProj', value=mvp_cube, mat4=True)
    scene.render_post()

scene.shutdown()
