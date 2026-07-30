import numpy as np
import OpenGL.GL as gl

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

# 1. Import billboard label system
from Elements.extensions.Captions_Screenshot.billboard_label_component import create_billboard_label, BillboardLabelSystem

example_description = \
"This is a scene with a cube, terrain, axes and billboard Labels\n\
The cube and axes are rendered with a simple shader.\n\
Billboard labels always face the camera and follow their objects.\n\n\
A Scenegraph shows the Entities and Components of the scene.\n\
You can move the camera through the Elements GUI or the mouse.\n\
Hit ESC OR Close the window to quit." 

winWidth = 1024
winHeight = 768

scene = Scene()    
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
orthoCam = scene.world.addComponent(entityCam2, Camera(m, "orthoCam", "Camera", "500"))

node4 = scene.world.createEntity(Entity(name="node4"))
scene.world.addEntityChild(rootEntity, node4)
trans4 = scene.world.addComponent(node4, BasicTransform(name="trans4", trs=util.translate(0, 0.5, 0)))
mesh4 = scene.world.addComponent(node4, RenderMesh(name="mesh4"))

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

vertexCube = np.array([
    [-0.5, -0.5, 0.5, 1.0],
    [-0.5, 0.5, 0.5, 1.0],
    [0.5, 0.5, 0.5, 1.0],
    [0.5, -0.5, 0.5, 1.0], 
    [-0.5, -0.5, -0.5, 1.0], 
    [-0.5, 0.5, -0.5, 1.0], 
    [0.5, 0.5, -0.5, 1.0], 
    [0.5, -0.5, -0.5, 1.0]
], dtype=np.float32) 
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

indexAxes = np.array((0, 1, 2, 3, 4, 5), np.uint32)
indexCube = np.array((1, 0, 3, 1, 3, 2, 
                      2, 3, 7, 2, 7, 6,
                      3, 0, 4, 3, 4, 7,
                      6, 5, 1, 6, 1, 2,
                      4, 5, 6, 4, 6, 7,
                      5, 4, 0, 5, 0, 1), np.uint32)


transUpdate = scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
camUpdate = scene.world.createSystem(CameraSystem("camUpdate", "CameraUpdate", "200"))
renderUpdate = scene.world.createSystem(RenderGLShaderSystem())
initUpdate = scene.world.createSystem(InitGLShaderSystem())
labelSystem = scene.world.createSystem(BillboardLabelSystem())

mesh4.vertex_attributes.append(vertexCube)
mesh4.vertex_attributes.append(colorCube)
mesh4.vertex_index.append(indexCube)
vArray4 = scene.world.addComponent(node4, VertexArray())
shaderDec4 = scene.world.addComponent(node4, ShaderGLDecorator(Shader(
    vertex_source=Shader.COLOR_VERT_MVP, 
    fragment_source=Shader.COLOR_FRAG
)))

vertexTerrain, indexTerrain, colorTerrain = generateTerrain(size=4, N=20)
terrain = scene.world.createEntity(Entity(name="terrain"))
scene.world.addEntityChild(rootEntity, terrain)
terrain_trans = scene.world.addComponent(terrain, BasicTransform(name="terrain_trans", trs=util.identity()))
terrain_mesh = scene.world.addComponent(terrain, RenderMesh(name="terrain_mesh"))
terrain_mesh.vertex_attributes.append(vertexTerrain) 
terrain_mesh.vertex_attributes.append(colorTerrain)
terrain_mesh.vertex_index.append(indexTerrain)
terrain_vArray = scene.world.addComponent(terrain, VertexArray(primitive=GL_LINES))
terrain_shader = scene.world.addComponent(terrain, ShaderGLDecorator(Shader(
    vertex_source=Shader.COLOR_VERT_MVP, 
    fragment_source=Shader.COLOR_FRAG
)))

axes = scene.world.createEntity(Entity(name="axes"))
scene.world.addEntityChild(rootEntity, axes)
axes_trans = scene.world.addComponent(axes, BasicTransform(name="axes_trans", trs=util.translate(0.0, 0.001, 0.0)))
axes_mesh = scene.world.addComponent(axes, RenderMesh(name="axes_mesh"))
axes_mesh.vertex_attributes.append(vertexAxes) 
axes_mesh.vertex_attributes.append(colorAxes)
axes_mesh.vertex_index.append(indexAxes)
axes_vArray = scene.world.addComponent(axes, VertexArray(primitive=GL_LINES))
axes_shader = scene.world.addComponent(axes, ShaderGLDecorator(Shader(
    vertex_source=Shader.COLOR_VERT_MVP, 
    fragment_source=Shader.COLOR_FRAG
)))


running = True
scene.init(imgui=True, windowWidth=winWidth, windowHeight=winHeight, 
          windowTitle="Elements: Terrain & Cube with Billboard Labels", 
          customImGUIdecorator=ImGUIecssDecorator2, openGLversion=4)

# 2. Enable blending for labels
gl.glEnable(gl.GL_BLEND)
gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)


# 3. create cube label
label_cube, comp_cube = create_billboard_label(
    scene=scene,
    parent_entity=node4,
    text="CUBE",
    bg_rgba=(0.9, 0.6, 0.2, 0.9),
    fg_rgba=(1.0, 1.0, 1.0, 1.0),
    world_height=0.2,
    offset_local=(0.0, 0.8, 0.0),
    padding_px=14,
    font_size=15
)

# terrain label
label_terrain, comp_terrain = create_billboard_label(
    scene=scene,
    parent_entity=terrain,
    text="TERRAIN",
    bg_rgba=(0.3, 0.6, 0.3, 0.9),
    fg_rgba=(1.0, 1.0, 1.0, 1.0),
    world_height=0.3,
    offset_local=(0.0, 0.3, 0.0),
    padding_px=16,
    font_size=15
)

# axes labels
label_x_axis, comp_x = create_billboard_label(
    scene=scene,
    parent_entity=axes,
    text="X",
    bg_rgba=(0.9, 0.2, 0.2, 0.9),
    fg_rgba=(1.0, 1.0, 1.0, 1.0),
    world_height=0.15,
    offset_local=(1.1, 0.0, 0.0),
    padding_px=8,
    font_size=12
)

label_y_axis, comp_y = create_billboard_label(
    scene=scene,
    parent_entity=axes,
    text="Y",
    bg_rgba=(0.2, 0.9, 0.2, 0.9),
    fg_rgba=(1.0, 1.0, 1.0, 1.0),
    world_height=0.15,
    offset_local=(0.0, 1.1, 0.0),
    padding_px=8,
    font_size=12
)

label_z_axis, comp_z = create_billboard_label(
    scene=scene,
    parent_entity=axes,
    text="Z",
    bg_rgba=(0.2, 0.2, 0.9, 0.9),
    fg_rgba=(1.0, 1.0, 1.0, 1.0),
    world_height=0.15,
    offset_local=(0.0, 0.0, 1.1),
    padding_px=8,
    font_size=12
)

# 4. Store billboard components for updating
billboard_labels = [
    (comp_cube, trans4),
    (comp_terrain, terrain_trans),
    (comp_x, axes_trans),
    (comp_y, axes_trans),
    (comp_z, axes_trans)
]
scene.world.traverse_visit(initUpdate, scene.world.root)

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
gWindow._myCamera = view

model_cube = trans4.trs
model_terrain = terrain.getChild(0).trs
model_axes = axes_trans.trs

while running:
    running = scene.render()
    displayGUI_text(example_description)
    
    scene.world.traverse_visit(renderUpdate, scene.world.root)
    scene.world.traverse_visit_pre_camera(camUpdate, orthoCam)
    scene.world.traverse_visit(camUpdate, scene.world.root)

    # Update view from imgui camera
    view = gWindow._myCamera
    
    # Calculate MVP matrices
    mvp_cube = projMat @ view @ model_cube
    mvp_terrain = projMat @ view @ model_terrain
    mvp_axes = projMat @ view @ model_axes
    
    # Update shaders
    axes_shader.setUniformVariable(key='modelViewProj', value=mvp_axes, mat4=True)
    terrain_shader.setUniformVariable(key='modelViewProj', value=mvp_terrain, mat4=True)
    shaderDec4.setUniformVariable(key='modelViewProj', value=mvp_cube, mat4=True)

    #5. update me loop gia na paei se ola ta labels 
    # gia na einai billboard dld na koitane thn kamera
    view_inv = np.linalg.inv(view)
    cam_right = view_inv[:3, 0]
    cam_up = view_inv[:3, 1]
    
    for billboard_comp, parent_transform in billboard_labels:
        if billboard_comp.shader:
            offset_world = parent_transform.trs @ util.vec(*billboard_comp.offset_local, 1.0)
            center = offset_world[:3]
            
            billboard_comp.shader.setUniformVariable(key='View', value=view, mat4=True)
            billboard_comp.shader.setUniformVariable(key='Proj', value=projMat, mat4=True)
            billboard_comp.shader.setUniformVariable(key='center', value=center, float3=True)
            billboard_comp.shader.setUniformVariable(key='camRight', value=cam_right, float3=True)
            billboard_comp.shader.setUniformVariable(key='camUp', value=cam_up, float3=True)
            billboard_comp.shader.setUniformVariable(
                key='size',
                value=util.vec(billboard_comp.world_width, billboard_comp.world_height, 0.0),
                float3=True
            )

    scene.render_post()
    
scene.shutdown()