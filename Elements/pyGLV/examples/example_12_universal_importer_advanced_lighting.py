
import os
import numpy as np

import Elements.pyECSS.utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, Camera, RenderMesh
from Elements.pyECSS.System import TransformSystem, CameraSystem
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GL.Textures import Texture
from Elements.pyGLV.GUI.Viewer import RenderGLStateSystem, ImGUIecssDecorator

from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray

from OpenGL.GL import GL_LINES
import OpenGL.GL as gl

import Elements.pyGLV.utils.normals as norm
from Elements.pyGLV.utils.terrain import generateTerrain

from Elements.pyGLV.utils.objimporter.wavefront import Wavefront


#Light
Lposition = util.vec(0, 1.0, 1.0) #uniform lightpos
Lambientcolor = util.vec(1.0, 1.0, 1.0) #uniform ambient color
Lcolor = util.vec(1.0,1.0,1.0)
Lintensity = 10.0

scene = Scene()    

# Scenegraph with Entities, Components
rootEntity = scene.world.createEntity(Entity(name="RooT"))
entityCam1 = scene.world.createEntity(Entity(name="Entity1"))
scene.world.addEntityChild(rootEntity, entityCam1)
trans1 = scene.world.addComponent(entityCam1, BasicTransform(name="Entity1_TRS", trs=util.translate(0,0,-8)))

eye = util.vec(2.5, 2.5, -2.5)
target = util.vec(0.0, 0.0, 0.0)
up = util.vec(0.0, 1.0, 0.0)
view = util.lookat(eye, target, up)
# projMat = util.ortho(-10.0, 10.0, -10.0, 10.0, -1.0, 10.0) ## WORKING
# projMat = util.perspective(90.0, 1.33, 0.1, 100) ## WORKING
projMat = util.perspective(50.0, 1.0, 1.0, 10.0) ## WORKING 

m = np.linalg.inv(projMat @ view)


entityCam2 = scene.world.createEntity(Entity(name="Entity_Camera"))
scene.world.addEntityChild(entityCam1, entityCam2)
trans2 = scene.world.addComponent(entityCam2, BasicTransform(name="Camera_TRS", trs=util.identity()))
# orthoCam = scene.world.addComponent(entityCam2, Camera(util.ortho(-100.0, 100.0, -100.0, 100.0, 1.0, 100.0), "orthoCam","Camera","500"))
orthoCam = scene.world.addComponent(entityCam2, Camera(m, "orthoCam","Camera","500"))

object_node = scene.world.createEntity(Entity(name="Object"))
scene.world.addEntityChild(rootEntity, object_node)
object_transform = scene.world.addComponent(object_node, BasicTransform(name="Object_TRS", trs=util.scale(10.0, 10.0, 10.0) ))
object_mesh = scene.world.addComponent(object_node, RenderMesh(name="Object_mesh"))


light_node = scene.world.createEntity(Entity(name="LightPos"))
scene.world.addEntityChild(rootEntity, light_node)
light_transform = scene.world.addComponent(light_node, BasicTransform(name="Light_TRS", trs=util.scale(1.0, 1.0, 1.0) ))
light_mesh = scene.world.addComponent(light_node, RenderMesh(name="Light_Mesh"))

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


# Systems
transUpdate = scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
camUpdate = scene.world.createSystem(CameraSystem("camUpdate", "CameraUpdate", "200"))
renderUpdate = scene.world.createSystem(RenderGLShaderSystem())
initUpdate = scene.world.createSystem(InitGLShaderSystem())



## object load 
dirname = os.path.dirname(__file__)
# obj_to_import = os.path.join(dirname, 'models','cow.obj')
# obj_to_import = os.path.join(dirname, 'models','sphere.obj')
obj_to_import = os.path.join(dirname, 'models','bowel/bowel.obj')

imported_obj = Wavefront(obj_to_import, calculate_smooth_normals=True)

mesh_from_obj = imported_obj.mesh_list[0]

# print(mesh_from_obj.vertices)
# print(mesh_from_obj.uv)
# print(mesh_from_obj.normals)
# print(mesh_from_obj.indices)
# exit()

object_mesh.vertex_attributes.append(mesh_from_obj.vertices)
object_mesh.vertex_attributes.append(mesh_from_obj.normals)
# If imported object has uv data, pass them or create all zeros array
if mesh_from_obj.has_uv: 
    object_mesh.vertex_attributes.append(mesh_from_obj.uv)
else:
    object_uvs = np.array([[1.0, 1.0]] * len(mesh_from_obj.vertices))
    object_mesh.vertex_attributes.append(object_uvs)

object_mesh.vertex_index.append(mesh_from_obj.indices)
object_vertex_array = scene.world.addComponent(object_node, VertexArray())
object_shader_decorator = scene.world.addComponent(object_node, ShaderGLDecorator(Shader(vertex_import_file=os.path.join(os.path.dirname(__file__), "shaders/lit/ComplexLit.vert"), fragment_import_file= os.path.join(os.path.dirname(__file__), "shaders/lit/ComplexLit.frag"))))


# Light Visualization
# a simple tetrahedron
tetrahedron_vertices = np.array([
    [  1.0,  1.0,  1.0, 1.0 ], 
    [ -1.0, -1.0,  1.0, 1.0 ], 
    [ -1.0,  1.0, -1.0, 1.0 ], 
    [  1.0, -1.0, -1.0, 1.0 ]
],dtype=np.float32) 
tetrahedron_colors = np.array([
    [  1.0,  0.0,  0.0, 1.0 ],
    [  0.0,  1.0,  0.0, 1.0 ],  
    [  0.0,  0.0,  1.0, 1.0 ], 
    [  1.0,  1.0,  1.0, 1.0 ]
])
tetrahedron_indices = np.array([0, 2, 1, 0, 1, 3, 2, 3, 1, 3, 2, 0])

light_mesh.vertex_attributes.append(tetrahedron_vertices)
light_mesh.vertex_attributes.append(tetrahedron_colors)
light_mesh.vertex_index.append(tetrahedron_indices)
light_vArray = scene.world.addComponent(light_node, VertexArray())
light_shader_decorator = scene.world.addComponent(light_node, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))




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
terrain_shader = scene.world.addComponent(terrain, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))
# terrain_shader.setUniformVariable(key='modelViewProj', value=mvpMat, mat4=True)

## ADD AXES ##
axes = scene.world.createEntity(Entity(name="axes"))
scene.world.addEntityChild(rootEntity, axes)
axes_trans = scene.world.addComponent(axes, BasicTransform(name="axes_trans", trs=  util.translate(0.0, 0.00001, 0.0))) #util.identity()
axes_mesh = scene.world.addComponent(axes, RenderMesh(name="axes_mesh"))
axes_mesh.vertex_attributes.append(vertexAxes) 
axes_mesh.vertex_attributes.append(colorAxes)
axes_mesh.vertex_index.append(indexAxes)
axes_vArray = scene.world.addComponent(axes, VertexArray(primitive=gl.GL_LINES)) # note the primitive change

# shaderDec_axes = scene.world.addComponent(axes, Shader())
# OR
axes_shader = scene.world.addComponent(axes, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))
# axes_shader.setUniformVariable(key='modelViewProj', value=mvpMat, mat4=True)


# MAIN RENDERING LOOP

running = True
scene.init(imgui=True, windowWidth = 1200, windowHeight = 800, windowTitle = "Elements: Import wavefront .obj example", openGLversion = 4, customImGUIdecorator = ImGUIecssDecorator)

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
# MANOS END
# Add RenderWindow to the EventManager publishers
# eManager._publishers[updateBackground.name] = gGUI


eye = util.vec(2.5, 2.5, 2.5)
target = util.vec(0.0, 0.0, 0.0)
up = util.vec(0.0, 1.0, 0.0)
view = util.lookat(eye, target, up)
# projMat = util.ortho(-10.0, 10.0, -10.0, 10.0, -1.0, 10.0) ## WORKING
# projMat = util.perspective(90.0, 1.33, 0.1, 100) ## WORKING
projMat = util.perspective(50.0, 1200/800, 0.01, 100.0) ## WORKING 

gWindow._myCamera = view # otherwise, an imgui slider must be moved to properly update

model_terrain_axes = util.translate(0.0,0.0,0.0)

# Set object mesh shader static data
# Light
object_shader_decorator.setUniformVariable(key='lightPos', value=Lposition, float3=True)
object_shader_decorator.setUniformVariable(key='lightColor', value=Lcolor, float3=True)
object_shader_decorator.setUniformVariable(key='lightIntensity', value=Lintensity, float1=True)
# Material
# Albedo
object_shader_decorator.setUniformVariable(key='albedoColor', value=np.array([1.0, 1.0, 1.0]), float3=True)
texturePath = os.path.join(os.path.dirname(__file__), "textures/white1x1.png")#"models/bowel/albedo.png")
texture = Texture(texturePath, 0)
object_shader_decorator.setUniformVariable(key='albedoMap', value=texture, texture=True)
# Normal map
object_shader_decorator.setUniformVariable(key='normalMapIntensity', value=1.0, float1=True)
texturePath = os.path.join(os.path.dirname(__file__), "models/bowel/normal.png")
texture = Texture(texturePath, 1)
object_shader_decorator.setUniformVariable(key='normalMap', value=texture, texture=True)
# Metallic map
texturePath = os.path.join(os.path.dirname(__file__), "models/bowel/metallic.png")
texture = Texture(texturePath, 2)
object_shader_decorator.setUniformVariable(key='metallicMap', value=texture, texture=True)
# Roughness
texturePath = os.path.join(os.path.dirname(__file__), "textures/black1x1.png")
texture = Texture(texturePath, 3)
object_shader_decorator.setUniformVariable(key='roughnessMap', value=texture, texture=True)
# Ambient Occlusion
texturePath = os.path.join(os.path.dirname(__file__), "textures/black1x1.png")
texture = Texture(texturePath, 4)
object_shader_decorator.setUniformVariable(key='aoMap', value=texture, texture=True)

def find_cam_position_from_view_matrix(view_matrix, projection_matrix, up, target):
    # Extract the camera orientation from the view matrix
    cam_rot = view_matrix[:3, :3]

    # Calculate the camera direction vector
    cam_dir = target - view_matrix[:3, 3]
    cam_dir /= np.linalg.norm(cam_dir)

    # Calculate the camera's right vector
    cam_right = np.cross(cam_dir, up)
    cam_right /= np.linalg.norm(cam_right)

    # Calculate the camera's up vector
    cam_up = np.cross(cam_right, cam_dir)

    # Invert the projection matrix to obtain the camera's view frustum
    view_frustum = np.linalg.inv(projection_matrix)

    # Calculate the distance from the camera to the near plane
    near_dist = view_frustum[2, 3] / view_frustum[0, 0]

    # Calculate the camera's position
    cam_pos = target - cam_dir * near_dist

    return cam_pos

while running:
    running = scene.render(running)
    scene.world.traverse_visit(renderUpdate, scene.world.root)
    scene.world.traverse_visit_pre_camera(camUpdate, orthoCam)
    scene.world.traverse_visit(camUpdate, scene.world.root)
    view =  gWindow._myCamera # updates view via the imgui
    # mvp_cube = projMat @ view @ model_cube
    light_shader_decorator.setUniformVariable(key="modelViewProj", value= projMat @ view @ (util.translate(Lposition[0], Lposition[1], Lposition[2]) @ util.scale(0.05, 0.05, 0.05)), mat4=True)
    mvp_terrain = projMat @ view @ terrain_trans.trs
    mvp_axes = projMat @ view @ axes_trans.trs
    axes_shader.setUniformVariable(key='modelViewProj', value=mvp_axes, mat4=True)
    terrain_shader.setUniformVariable(key='modelViewProj', value=mvp_terrain, mat4=True)

    # Set Object's Shader Realtime Dynamic Data
    object_mvp = projMat @ view @ object_transform.trs

    # --- Set vertex shader data ---
    object_shader_decorator.setUniformVariable(key='projection', value=projMat, mat4=True)
    object_shader_decorator.setUniformVariable(key='view', value=view, mat4=True)
    object_shader_decorator.setUniformVariable(key='model', value=object_transform.trs, mat4=True)
    # Calculate normal matrix
    normalMatrix = np.transpose(util.inverse(object_transform.trs))
    object_shader_decorator.setUniformVariable(key='normalMatrix', value=normalMatrix, mat4=True)
    
    # --- Set fragment shader data ---
    # # Camera position
    object_shader_decorator.setUniformVariable(key='camPos', value=eye, float3=True)

    # object_shader_decorator.setUniformVariable(key='modelViewProj', value=object_mvp, mat4=True)
    # object_shader_decorator.setUniformVariable(key='model',value=object_transform.trs,mat4=True)
    # object_shader_decorator.setUniformVariable(key='ambientColor',value=Lambientcolor,float3=True)
    # object_shader_decorator.setUniformVariable(key='ambientStr',value=Lambientstr,float1=True)
    # object_shader_decorator.setUniformVariable(key='shininess',value=Mshininess,float1=True)
    # object_shader_decorator.setUniformVariable(key='matColor',value=Mcolor,float3=True)


    scene.render_post()
    
scene.shutdown()

