
import os
import numpy as np
import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, Camera, RenderMesh
from Elements.pyECSS.System import TransformSystem, CameraSystem
from Elements.pyGLV.GL.GameObject import GameObject
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GUI.Viewer import RenderGLStateSystem
from Elements.pyGLV.GUI.ImguiDecorator import ImGUIecssDecorator2

from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray
from OpenGL.GL import GL_LINES
import OpenGL.GL as gl
from Elements.utils.terrain import generateTerrain
from Elements.definitions import MODEL_DIR, SHADER_DIR

from Elements.utils.Shortcuts import displayGUI_text
example_description = \
"This example demonstrates the ability to import \n\
really complex objects along with their textures. \n\
The scene is being lit using the Blinn-Phong algorithm. \n\
You may move the camera using the mouse or the GUI. \n\
You may see the ECS Scenegraph showing Entities & Components of the scene and \n\
various information about them. Hit ESC OR Close the window to quit." 


#Light
Lposition = util.vec(-1, 1.5, 1.2) #uniform lightpos
Lambientcolor = util.vec(1.0, 1.0, 1.0) #uniform ambient color
Lcolor = util.vec(1.0,1.0,1.0)
Lintensity = 40.0


scene = Scene()    

# Scenegraph with Entities, Components
rootEntity = scene.world.createEntity(Entity(name="RooT"))

eye = util.vec(2.5, 2.5, -2.5)
target = util.vec(0.0, 0.0, 0.0)
up = util.vec(0.0, 1.0, 0.0)
view = util.lookat(eye, target, up)
projMat = util.perspective(50.0, 1.0, 1.0, 10.0)

m = np.linalg.inv(projMat @ view)


light_node = scene.world.createEntity(Entity(name="LightPos"))
scene.world.addEntityChild(rootEntity, light_node)
light_transform = scene.world.addComponent(light_node, BasicTransform(name="Light_TRS",
    trs=util.translate(Lposition[0], Lposition[1], Lposition[2]) @ util.scale(0.05, 0.05, 0.05)))
light_mesh = scene.world.addComponent(light_node, RenderMesh(name="Light_Mesh"))

# Systems
transUpdate = scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
camUpdate = scene.world.createSystem(CameraSystem("camUpdate", "CameraUpdate", "200"))
renderUpdate = scene.world.createSystem(RenderGLShaderSystem())
initUpdate = scene.world.createSystem(InitGLShaderSystem())


# Load Object


obj_to_import = MODEL_DIR / "LivingRoom" / "Lamp" / "Lamp.obj"
model_entity = GameObject.Spawn(scene, obj_to_import, "Lamp", rootEntity, util.translate(-0.2, 0.4, 0.0))


# Light Visualization
# a small cube marking the light's position, TRS-linked to the light itself
light_cube_vertices = np.array([
    [-0.5, -0.5,  0.5, 1.0],
    [-0.5,  0.5,  0.5, 1.0],
    [ 0.5,  0.5,  0.5, 1.0],
    [ 0.5, -0.5,  0.5, 1.0],
    [-0.5, -0.5, -0.5, 1.0],
    [-0.5,  0.5, -0.5, 1.0],
    [ 0.5,  0.5, -0.5, 1.0],
    [ 0.5, -0.5, -0.5, 1.0]
], dtype=np.float32)
light_cube_colors = np.array([[1.0, 1.0, 0.0, 1.0]] * 8, dtype=np.float32)
light_cube_indices = np.array(
    (
        1,0,3, 1,3,2,
        2,3,7, 2,7,6,
        3,0,4, 3,4,7,
        6,5,1, 6,1,2,
        4,5,6, 4,6,7,
        5,4,0, 5,0,1
    ),
    dtype=np.uint32
)

light_mesh.vertex_attributes.append(light_cube_vertices)
light_mesh.vertex_attributes.append(light_cube_colors)
light_mesh.vertex_index.append(light_cube_indices)
light_vArray = scene.world.addComponent(light_node, VertexArray())
light_shader_decorator = scene.world.addComponent(light_node, ShaderGLDecorator(Shader(vertex_import_file=SHADER_DIR / "ColorMVP.vert", fragment_import_file=SHADER_DIR / "Color.frag")))




# Generate terrain
vertexTerrain, indexTerrain, colorTerrain= generateTerrain(size=4,N=20)
# Add terrain
terrain = scene.world.createEntity(Entity(name="terrain"))
scene.world.addEntityChild(rootEntity, terrain)
terrain_trans = scene.world.addComponent(terrain, BasicTransform(name="terrain_trans", trs=util.identity()))
terrain_mesh = scene.world.addComponent(terrain, RenderMesh(name="terrain_mesh"))
terrain_mesh.vertex_attributes.append(vertexTerrain) 
terrain_mesh.vertex_attributes.append(colorTerrain)
terrain_mesh.vertex_index.append(indexTerrain)
terrain_vArray = scene.world.addComponent(terrain, VertexArray(primitive=GL_LINES))
terrain_shader = scene.world.addComponent(terrain, ShaderGLDecorator(Shader(vertex_import_file=SHADER_DIR / "ColorMVP.vert", fragment_import_file=SHADER_DIR / "Color.frag")))
# terrain_shader.setUniformVariable(key='modelViewProj', value=mvpMat, mat4=True)

## ADD AXES ##
#Colored Axes
vertexAxes = np.array([
    [0.0, 0.0, 0.0, 1.0],
    [1.5, 0.0, 0.0, 1.0],
    [0.0, 0.0, 0.0, 1.0],
    [0.0, 1.5, 0.0, 1.0],
    [0.0, 0.0, 0.0, 1.0],
    [0.0, 0.0, 1.5, 1.0]
],dtype=np.float32) 
colorAxes = np.array([
    [1.0, 0.0, 0.0, 1.0],
    [1.0, 0.0, 0.0, 1.0],
    [0.0, 1.0, 0.0, 1.0],
    [0.0, 1.0, 0.0, 1.0],
    [0.0, 0.0, 1.0, 1.0],
    [0.0, 0.0, 1.0, 1.0]
], dtype=np.float32)


#index arrays for above vertex Arrays
index = np.array((0,1,2), np.uint32) #simple triangle
indexAxes = np.array((0,1,2,3,4,5), np.uint32) #3 simple colored Axes as R,G,B lines

axes = scene.world.createEntity(Entity(name="axes"))
scene.world.addEntityChild(rootEntity, axes)
axes_trans = scene.world.addComponent(axes, BasicTransform(name="axes_trans", trs=  util.translate(0.0, 0.00001, 0.0))) #util.identity()
axes_mesh = scene.world.addComponent(axes, RenderMesh(name="axes_mesh"))
axes_mesh.vertex_attributes.append(vertexAxes) 
axes_mesh.vertex_attributes.append(colorAxes)
axes_mesh.vertex_index.append(indexAxes)
axes_vArray = scene.world.addComponent(axes, VertexArray(primitive=gl.GL_LINES)) # note the primitive change

axes_shader = scene.world.addComponent(axes, ShaderGLDecorator(Shader(vertex_import_file=SHADER_DIR / "ColorMVP.vert", fragment_import_file=SHADER_DIR / "Color.frag")))



# MAIN RENDERING LOOP
running = True
scene.init(imgui=True, windowWidth = 1200, windowHeight = 800, windowTitle = "Elements: Import wavefront .obj example", openGLversion = 4, customImGUIdecorator = ImGUIecssDecorator2)

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
projMat = util.perspective(50.0, 1200/800, 0.01, 100.0) ## WORKING 

gWindow._myCamera = view # otherwise, an imgui slider must be moved to properly update

model_terrain_axes = util.translate(0.0,0.0,0.0)

# Initialize mesh GL depended components
model_entity.initialize_gl(Lposition, Lcolor, Lintensity)

model_entity.transform_component.trs = util.scale(1.0, 1.0, 1.0)

while running:
    running = scene.render()
    displayGUI_text(example_description)
    scene.world.traverse_visit(renderUpdate, scene.world.root)
    scene.world.traverse_visit(transUpdate, scene.world.root)

    view =  gWindow._myCamera # updates view via the imgui
    # mvp_cube = projMat @ view @ model_cube
    light_shader_decorator.setUniformVariable(key="modelViewProj", value= projMat @ view @ light_transform.trs, mat4=True)
    mvp_terrain = projMat @ view @ terrain_trans.trs
    mvp_axes = projMat @ view @ axes_trans.trs
    axes_shader.setUniformVariable(key='modelViewProj', value=mvp_axes, mat4=True)
    terrain_shader.setUniformVariable(key='modelViewProj', value=mvp_terrain, mat4=True)

    # Set Object Real Time Shader Data
    for mesh_entity in model_entity.mesh_entities:
        # --- Set vertex shader data ---
        mesh_entity.shader_decorator_component.setUniformVariable(key='projection', value=projMat, mat4=True)
        mesh_entity.shader_decorator_component.setUniformVariable(key='view', value=view, mat4=True)
        mesh_entity.shader_decorator_component.setUniformVariable(key='model', value=mesh_entity.transform_component.l2world, mat4=True)
        # Calculate normal matrix
        normalMatrix = np.transpose(util.inverse(mesh_entity.transform_component.l2world))
        mesh_entity.shader_decorator_component.setUniformVariable(key='normalMatrix', value=normalMatrix, mat4=True)

        # --- Set fragment shader data ---
        # Light position, driven by the light cube's own TRS so moving it via the ECSS GUI moves the light
        mesh_entity.shader_decorator_component.setUniformVariable(key='lightPos', value=light_transform.trs[:3, 3], float3=True)
        # Camera position
        mesh_entity.shader_decorator_component.setUniformVariable(key='camPos', value=eye, float3=True)

    scene.render_post()
    
scene.shutdown()
