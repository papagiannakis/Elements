import numpy as np

import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, Camera, RenderMesh
from Elements.pyECSS.System import TransformSystem, CameraSystem
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GUI.Viewer import RenderGLStateSystem
from Elements.pyGLV.GUI.ImguiDecorator import ImGUIecssDecorator2
from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray

from Elements.utils.terrain import generateTerrain

from OpenGL.GL import GL_LINES

from Elements.utils.Shortcuts import displayGUI_text

from Elements.extensions.Normals_USDimporter_BSP.BSPTree import BSPTree


example_description = \
"This is a scene with triangles (instead of cubes), a terrain and axes. \n\
The triangles and axes are rendered with a simple shader. \n\
that allow camera movement too, via the Elements GUI. \n\n\
An ECSS Graph shows the Entities and Components of the \n\
scene, in read only way, i.e., you cannot manipulate  \n\
any information via the ECSS Graph GUI. \n\n\
You can move the camera through the Elements GUI \n\
or the mouse. Hit ESC OR Close the window to quit."

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
# orthoCam = scene.world.addComponent(entityCam2, Camera(util.ortho(-100.0, 100.0, -100.0, 100.0, 1.0, 100.0), "orthoCam","Camera","500"))
orthoCam = scene.world.addComponent(entityCam2, Camera(m, "orthoCam", "Camera", "500"))

node4 = scene.world.createEntity(Entity(name="node4"))
scene.world.addEntityChild(rootEntity, node4)
trans4 = scene.world.addComponent(node4, BasicTransform(name="trans4", trs=util.translate(0, 0.5, 0)))
mesh4 = scene.world.addComponent(node4, RenderMesh(name="mesh4"))

node5 = scene.world.createEntity(Entity(name="node5"))
scene.world.addEntityChild(rootEntity, node5)
trans5 = scene.world.addComponent(node5, BasicTransform(name="trans5", trs=util.translate(2, 0.5, 2)))
mesh5 = scene.world.addComponent(node5, RenderMesh(name="mesh5"))

node6 = scene.world.createEntity(Entity(name="node6"))
scene.world.addEntityChild(rootEntity, node6)
trans6 = scene.world.addComponent(node6, BasicTransform(name="trans6", trs=util.translate(-2, 0.5, 2)))
mesh6 = scene.world.addComponent(node6, RenderMesh(name="mesh6"))

node7 = scene.world.createEntity(Entity(name="node7"))
scene.world.addEntityChild(rootEntity, node7)
trans7 = scene.world.addComponent(node7, BasicTransform(name="trans7", trs=util.translate(2, 0.5, -2)))
mesh7 = scene.world.addComponent(node7, RenderMesh(name="mesh7"))

node8 = scene.world.createEntity(Entity(name="node8"))
scene.world.addEntityChild(rootEntity, node8)
trans8 = scene.world.addComponent(node8, BasicTransform(name="trans8", trs=util.translate(-2, 0.5, -2)))
mesh8 = scene.world.addComponent(node8, RenderMesh(name="mesh8"))

# Colored Axes
vertexAxes = np.array([
    [0.0, 0.0, 0.0, 1.0],
    [1.0, 0.0, 0.0, 1.0],
    [0.0, 0.0, 0.0, 1.0],
    [0.0, 1.0, 0.0, 1.0],
    [0.0, 0.0, 0.0, 1.0],
    [0.0, 0.0, 1.0, 1.0]
], dtype=np.float32)
colorAxes = np.array([
    [1.0, 0.0, 0.0, 1.0],
    [1.0, 0.0, 0.0, 1.0],
    [0.0, 1.0, 0.0, 1.0],
    [0.0, 1.0, 0.0, 1.0],
    [0.0, 0.0, 1.0, 1.0],
    [0.0, 0.0, 1.0, 1.0]
], dtype=np.float32)

vertexTri = np.array([
    [-0.5, 0.0,  0.0, 1.0],
    [ 0.5, 0.0,  0.0, 1.0],
    [ 0.0, 0.9,  0.0, 1.0]
], dtype=np.float32)

colorTri = np.array([
    [1.0, 0.2, 0.2, 1.0],
    [0.2, 1.0, 0.2, 1.0],
    [0.2, 0.2, 1.0, 1.0]
], dtype=np.float32)

# index arrays
index = np.array((0, 1, 2), np.uint32)          # simple triangle
indexAxes = np.array((0, 1, 2, 3, 4, 5), np.uint32)
indexTri = np.array((0, 1, 2), np.uint32)       # scene triangles


# Systems
transUpdate = scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
camUpdate = scene.world.createSystem(CameraSystem("camUpdate", "CameraUpdate", "200"))
renderUpdate = scene.world.createSystem(RenderGLShaderSystem())
initUpdate = scene.world.createSystem(InitGLShaderSystem())


mesh4.vertex_attributes.clear()
mesh4.vertex_index.clear()
mesh4.vertex_attributes.append(vertexTri)
mesh4.vertex_attributes.append(colorTri)
mesh4.vertex_index.append(indexTri)
vArray4 = scene.world.addComponent(node4, VertexArray())
shaderDec4 = scene.world.addComponent(
    node4,
    ShaderGLDecorator(Shader(vertex_source=Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG))
)

mesh5.vertex_attributes.clear()
mesh5.vertex_index.clear()
mesh5.vertex_attributes.append(vertexTri)
mesh5.vertex_attributes.append(colorTri)
mesh5.vertex_index.append(indexTri)
vArray5 = scene.world.addComponent(node5, VertexArray())
shaderDec5 = scene.world.addComponent(
    node5,
    ShaderGLDecorator(Shader(vertex_source=Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG))
)

mesh6.vertex_attributes.clear()
mesh6.vertex_index.clear()
mesh6.vertex_attributes.append(vertexTri)
mesh6.vertex_attributes.append(colorTri)
mesh6.vertex_index.append(indexTri)
vArray6 = scene.world.addComponent(node6, VertexArray())
shaderDec6 = scene.world.addComponent(
    node6,
    ShaderGLDecorator(Shader(vertex_source=Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG))
)

mesh7.vertex_attributes.clear()
mesh7.vertex_index.clear()
mesh7.vertex_attributes.append(vertexTri)
mesh7.vertex_attributes.append(colorTri)
mesh7.vertex_index.append(indexTri)
vArray7 = scene.world.addComponent(node7, VertexArray())
shaderDec7 = scene.world.addComponent(
    node7,
    ShaderGLDecorator(Shader(vertex_source=Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG))
)

mesh8.vertex_attributes.clear()
mesh8.vertex_index.clear()
mesh8.vertex_attributes.append(vertexTri)
mesh8.vertex_attributes.append(colorTri)
mesh8.vertex_index.append(indexTri)
vArray8 = scene.world.addComponent(node8, VertexArray())
shaderDec8 = scene.world.addComponent(
    node8,
    ShaderGLDecorator(Shader(vertex_source=Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG))
)


# Generate terrain
vertexTerrain, indexTerrain, colorTerrain = generateTerrain(size=4, N=20)

# Add terrain
terrain = scene.world.createEntity(Entity(name="terrain"))
scene.world.addEntityChild(rootEntity, terrain)
terrain_trans = scene.world.addComponent(terrain, BasicTransform(name="terrain_trans", trs=util.identity()))
terrain_mesh = scene.world.addComponent(terrain, RenderMesh(name="terrain_mesh"))
terrain_mesh.vertex_attributes.append(vertexTerrain)
terrain_mesh.vertex_attributes.append(colorTerrain)
terrain_mesh.vertex_index.append(indexTerrain)
terrain_vArray = scene.world.addComponent(terrain, VertexArray(primitive=GL_LINES))
terrain_shader = scene.world.addComponent(
    terrain, ShaderGLDecorator(Shader(vertex_source=Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG))
)

# ADD AXES
axes = scene.world.createEntity(Entity(name="axes"))
scene.world.addEntityChild(rootEntity, axes)
axes_trans = scene.world.addComponent(axes, BasicTransform(name="axes_trans", trs=util.translate(0.0, 0.001, 0.0)))
axes_mesh = scene.world.addComponent(axes, RenderMesh(name="axes_mesh"))
axes_mesh.vertex_attributes.append(vertexAxes)
axes_mesh.vertex_attributes.append(colorAxes)
axes_mesh.vertex_index.append(indexAxes)
axes_vArray = scene.world.addComponent(axes, VertexArray(primitive=GL_LINES))
axes_shader = scene.world.addComponent(
    axes, ShaderGLDecorator(Shader(vertex_source=Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG))
)


# MAIN RENDERING LOOP
running = True
scene.init(
    imgui=True,
    windowWidth=winWidth,
    windowHeight=winHeight,
    windowTitle="Elements: A Working Event Manager",
    customImGUIdecorator=ImGUIecssDecorator2,
    openGLversion=4
)

# pre-pass scenegraph to initialise all GL context dependent geometry, shader classes
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

gWindow._myCamera = view  # otherwise, an imgui slider must be moved to properly update


# Models for the 5 triangles
model_tri1 = trans4.trs
model_tri2 = trans5.trs
model_tri3 = trans6.trs
model_tri4 = trans7.trs
model_tri5 = trans8.trs

# BSP input: transform each triangle's vertices to world and stack
T1 = (model_tri1 @ vertexTri.T).T[:, :3]
T2 = (model_tri2 @ vertexTri.T).T[:, :3]
T3 = (model_tri3 @ vertexTri.T).T[:, :3]
T4 = (model_tri4 @ vertexTri.T).T[:, :3]
T5 = (model_tri5 @ vertexTri.T).T[:, :3]
vertices = np.vstack([T1, T2, T3, T4, T5]).astype(np.float32)


V = vertexTri.shape[0]  # 3 vertices per triangle
i0 = indexTri + 0 * V
i1 = indexTri + 1 * V
i2 = indexTri + 2 * V
i3 = indexTri + 3 * V
i4 = indexTri + 4 * V
indexes = np.concatenate([i0, i1, i2, i3, i4]).astype(np.int32)
BSP = BSPTree(vertices, indexes)
BSP.build()

print()
print("---- BSP Tree ----")
BSP.print_by_depth()

print()
print("---- Search path traversal (for a non-intersected triangle) ----")
BSP.search(1)

print()
print("---- Search path traversal (for a intersected triangle) ----")

BSP.search(0)

model_terrain = terrain.getChild(0).trs
model_axes = axes_trans.trs

while running:
    running = scene.render()
    displayGUI_text(example_description)
    scene.world.traverse_visit(renderUpdate, scene.world.root)
    scene.world.traverse_visit_pre_camera(camUpdate, orthoCam)
    scene.world.traverse_visit(camUpdate, scene.world.root)

    view = gWindow._myCamera  # updates view via the imgui

    mvp_tri1 = projMat @ view @ model_tri1
    mvp_tri2 = projMat @ view @ model_tri2
    mvp_tri3 = projMat @ view @ model_tri3
    mvp_tri4 = projMat @ view @ model_tri4
    mvp_tri5 = projMat @ view @ model_tri5

    mvp_terrain = projMat @ view @ model_terrain
    mvp_axes = projMat @ view @ model_axes

    axes_shader.setUniformVariable(key='modelViewProj', value=mvp_axes, mat4=True)
    terrain_shader.setUniformVariable(key='modelViewProj', value=mvp_terrain, mat4=True)

    shaderDec4.setUniformVariable(key='modelViewProj', value=mvp_tri1, mat4=True)
    shaderDec5.setUniformVariable(key='modelViewProj', value=mvp_tri2, mat4=True)
    shaderDec6.setUniformVariable(key='modelViewProj', value=mvp_tri3, mat4=True)
    shaderDec7.setUniformVariable(key='modelViewProj', value=mvp_tri4, mat4=True)
    shaderDec8.setUniformVariable(key='modelViewProj', value=mvp_tri5, mat4=True)

    scene.render_post()

scene.shutdown()
