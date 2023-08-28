import numpy as np
import os
import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, RenderMesh
from Elements.pyECSS.System import  TransformSystem
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GUI.Viewer import RenderGLStateSystem
from Elements.features.Gizmos.Gizmos import Gizmos
from Elements.definitions import TEXTURE_DIR
from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray
from Elements.utils.terrain import generateTerrain
import Elements.utils.normals as norm
from Elements.pyGLV.GL.Textures import get_texture_faces, Texture
from Elements.pyGLV.GL.Textures import get_single_texture_faces
from OpenGL.GL import GL_LINES

#Light
Lposition = util.vec(0.0, 2.5, 1.2) #uniform lightpos
Lambientcolor = util.vec(1.0, 1.0, 1.0) #uniform ambient color
Lambientstr = 0.3 #uniform ambientStr
LviewPos = util.vec(2.5, 2.8, 5.0) #uniform viewpos
Lcolor = util.vec(1.0,1.0,1.0)
Lintensity = 0.9
#Material
Mshininess = 0.4 
Mcolor = util.vec(1.0, 0.0, 0.8)

scene = Scene()    

# Scenegraph with Entities, Components
rootEntity = scene.world.createEntity(Entity(name="RooT"))
entityCam1 = scene.world.createEntity(Entity(name="entityCam1"))
scene.world.addEntityChild(rootEntity, entityCam1)
trans1 = scene.world.addComponent(entityCam1, BasicTransform(name="trans1", trs=util.translate(2.5, 2.5, 2.5)))

skybox = scene.world.createEntity(Entity(name="Skybox"))
scene.world.addEntityChild(rootEntity, skybox)
transSkybox = scene.world.addComponent(skybox, BasicTransform(name="transSkybox", trs=util.identity())) #util.identity()
meshSkybox = scene.world.addComponent(skybox, RenderMesh(name="meshSkybox"))

node4_pink_1 = scene.world.createEntity(Entity(name="node4_pink_1"))
scene.world.addEntityChild(rootEntity, node4_pink_1)
trans4_pink_1 = scene.world.addComponent(node4_pink_1, BasicTransform(name="trans4_pink_1", trs=util.translate(-1.5,0.5,-1.5))) #util.identity()
mesh4_pink_1 = scene.world.addComponent(node4_pink_1, RenderMesh(name="mesh4_pink_1"))

node4_pink_2 = scene.world.createEntity(Entity(name="node4_pink_2"))
scene.world.addEntityChild(node4_pink_1, node4_pink_2)
trans4_pink_2 = scene.world.addComponent(node4_pink_2, BasicTransform(name="trans4_pink_2", trs=util.translate(1.5,0.0,0.0))) #util.identity()
mesh4_pink_2 = scene.world.addComponent(node4_pink_2, RenderMesh(name="mesh4_pink_2"))

node4_pink_3 = scene.world.createEntity(Entity(name="node4_pink_3"))
scene.world.addEntityChild(node4_pink_2, node4_pink_3)
trans4_pink_3 = scene.world.addComponent(node4_pink_3, BasicTransform(name="trans4_pink_3", trs=util.translate(1.5,0.0,0.0))) #util.identity()
mesh4_pink_3 = scene.world.addComponent(node4_pink_3, RenderMesh(name="mesh4_pink_3"))

node4_yellow_1 = scene.world.createEntity(Entity(name="node4_2_yellow_1"))
scene.world.addEntityChild(rootEntity, node4_yellow_1)
trans4_yellow_1 = scene.world.addComponent(node4_yellow_1, BasicTransform(name="trans4_yellow_1", trs=util.translate(-2.0,0.5,0.0))) #util.identity()
mesh4_yellow_1 = scene.world.addComponent(node4_yellow_1, RenderMesh(name="mesh4_yellow_1"))

node4_yellow_2 = scene.world.createEntity(Entity(name="node4_2_yellow_2"))
scene.world.addEntityChild(node4_yellow_1, node4_yellow_2)
trans4_yellow_2 = scene.world.addComponent(node4_yellow_2, BasicTransform(name="trans4_yellow_2", trs=util.translate(2.0,0.0,0.0))) #util.identity()
mesh4_yellow_2 = scene.world.addComponent(node4_yellow_2, RenderMesh(name="mesh4_yellow_2"))

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
    [1.0, 0.0, 1.0, 1.0],
    [1.0, 0.0, 1.0, 1.0],
    [1.0, 0.0, 1.0, 1.0],
    [1.0, 0.0, 1.0, 1.0],
    [1.0, 0.0, 1.0, 1.0],
    [1.0, 0.0, 1.0, 1.0],
    [1.0, 0.0, 1.0, 1.0],
    [1.0, 0.0, 1.0, 1.0]
], dtype=np.float32)
colorCube2 = np.array([
    [1.0, 1.0, 0.0, 1.0],
    [1.0, 1.0, 0.0, 1.0],
    [1.0, 1.0, 0.0, 1.0],
    [1.0, 1.0, 0.0, 1.0],
    [1.0, 1.0, 0.0, 1.0],
    [1.0, 1.0, 0.0, 1.0],
    [1.0, 1.0, 0.0, 1.0],
    [1.0, 1.0, 0.0, 1.0]
], dtype=np.float32)

#index array for above vertex Arrays
indexCube = np.array((1,0,3, 1,3,2, 
                  2,3,7, 2,7,6,
                  3,0,4, 3,4,7,
                  6,5,1, 6,1,2,
                  4,5,6, 4,6,7,
                  5,4,0, 5,0,1), np.uint32)

#Skybox
minbox = -30
maxbox = 30
vertexSkybox = np.array([
    [minbox, minbox, maxbox, 1.0],
    [minbox, maxbox, maxbox, 1.0],
    [maxbox, maxbox, maxbox, 1.0],
    [maxbox, minbox, maxbox, 1.0], 
    [minbox, minbox, minbox, 1.0], 
    [minbox, maxbox, minbox, 1.0], 
    [maxbox, maxbox, minbox, 1.0], 
    [maxbox, minbox, minbox, 1.0]
],dtype=np.float32)

#index array for Skybox
indexSkybox = np.array((1,0,3, 1,3,2, 
                  2,3,7, 2,7,6,
                  3,0,4, 3,4,7,
                  6,5,1, 6,1,2,
                  4,5,6, 4,6,7,
                  5,4,0, 5,0,1), np.uint32) 

# Systems
transUpdate = scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
# camUpdate = scene.world.createSystem(CameraSystem("camUpdate", "CameraUpdate", "200"))
renderUpdate = scene.world.createSystem(RenderGLShaderSystem())
initUpdate = scene.world.createSystem(InitGLShaderSystem())


vertices_pink, indices_pink, color_pink, normals_pink = norm.generateFlatNormalsMesh(vertexCube,indexCube,colorCube)
vertices_yellow, indices_yellow, color_yellow, normals_yellow = norm.generateFlatNormalsMesh(vertexCube,indexCube,colorCube2)


vertexSkybox, indexSkybox, _ = norm.generateUniqueVertices(vertexSkybox,indexSkybox)

meshSkybox.vertex_attributes.append(vertexSkybox)
meshSkybox.vertex_index.append(indexSkybox)
vArraySkybox = scene.world.addComponent(skybox, VertexArray())
shaderSkybox = scene.world.addComponent(skybox, ShaderGLDecorator(Shader(vertex_source = Shader.STATIC_SKYBOX_VERT, fragment_source=Shader.STATIC_SKYBOX_FRAG)))

## ADD CUBE ##
# attach a simple cube in a RenderMesh so that VertexArray can pick it up
mesh4_pink_1.vertex_attributes.append(vertices_pink)
mesh4_pink_1.vertex_attributes.append(color_pink)
mesh4_pink_1.vertex_attributes.append(normals_pink)
mesh4_pink_1.vertex_index.append(indices_pink)
vArray4_pink_1 = scene.world.addComponent(node4_pink_1, VertexArray())
shaderDec4_pink_1 = scene.world.addComponent(node4_pink_1, ShaderGLDecorator(Shader(vertex_source = Shader.VERT_PHONG_MVP, fragment_source=Shader.FRAG_PHONG)))

mesh4_pink_2.vertex_attributes.append(vertices_pink)
mesh4_pink_2.vertex_attributes.append(color_pink)
mesh4_pink_2.vertex_attributes.append(normals_pink)
mesh4_pink_2.vertex_index.append(indices_pink)
vArray4_pink_2 = scene.world.addComponent(node4_pink_2, VertexArray())
shaderDec4_pink_2 = scene.world.addComponent(node4_pink_2, ShaderGLDecorator(Shader(vertex_source = Shader.VERT_PHONG_MVP, fragment_source=Shader.FRAG_PHONG)))

mesh4_pink_3.vertex_attributes.append(vertices_pink)
mesh4_pink_3.vertex_attributes.append(color_pink)
mesh4_pink_3.vertex_attributes.append(normals_pink)
mesh4_pink_3.vertex_index.append(indices_pink)
vArray4_pink_3 = scene.world.addComponent(node4_pink_3, VertexArray())
shaderDec4_pink_3 = scene.world.addComponent(node4_pink_3, ShaderGLDecorator(Shader(vertex_source = Shader.VERT_PHONG_MVP, fragment_source=Shader.FRAG_PHONG)))

mesh4_yellow_1.vertex_attributes.append(vertices_yellow)
mesh4_yellow_1.vertex_attributes.append(color_yellow)
mesh4_yellow_1.vertex_attributes.append(normals_yellow)
mesh4_yellow_1.vertex_index.append(indices_yellow)
vArray4_yellow_1 = scene.world.addComponent(node4_yellow_1, VertexArray())
shaderDec4_yellow_1 = scene.world.addComponent(node4_yellow_1, ShaderGLDecorator(Shader(vertex_source = Shader.VERT_PHONG_MVP, fragment_source=Shader.FRAG_PHONG)))

mesh4_yellow_2.vertex_attributes.append(vertices_yellow)
mesh4_yellow_2.vertex_attributes.append(color_yellow)
mesh4_yellow_2.vertex_attributes.append(normals_yellow)
mesh4_yellow_2.vertex_index.append(indices_yellow)
vArray4_yellow_2 = scene.world.addComponent(node4_yellow_2, VertexArray())
shaderDec4_yellow_2 = scene.world.addComponent(node4_yellow_2, ShaderGLDecorator(Shader(vertex_source = Shader.VERT_PHONG_MVP, fragment_source=Shader.FRAG_PHONG)))

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

eye = util.vec(2.5, 2.5, 2.5)
target = util.vec(0.0, 0.0, 0.0)
up = util.vec(0.0, 1.0, 0.0)
view = util.lookat(eye, target, up)
width = 1024.0
height = 768.0
fov = 50.0
aspect_ratio = width/height
near = 0.01
far = 10.0
projMat = util.perspective(fov, aspect_ratio, near, far)

gizmos = Gizmos(rootEntity)
gizmos.set_camera_in_use("entityCam1")
gizmos.update_projection(projMat)
gizmos.update_view(view)
gizmos.update_screen_dimensions(window_width=width,window_height=height)

# MAIN RENDERING LOOP

running = True
scene.init(imgui=True, windowWidth = 1024, windowHeight = 768, windowTitle = "Elements: An Example with Gizmos", openGLversion = 4)

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

gWindow._myCamera = view # otherwise, an imgui slider must be moved to properly update

#Set Uniform Variables for Light and material
shaderDec4_pink_1.setUniformVariable(key='ambientColor',value=Lambientcolor,float3=True)
shaderDec4_pink_1.setUniformVariable(key='ambientStr',value=Lambientstr,float1=True)
shaderDec4_pink_1.setUniformVariable(key='viewPos',value=LviewPos,float3=True)
shaderDec4_pink_1.setUniformVariable(key='lightPos',value=Lposition,float3=True)
shaderDec4_pink_1.setUniformVariable(key='lightColor',value=Lcolor,float3=True)
shaderDec4_pink_1.setUniformVariable(key='lightIntensity',value=Lintensity,float1=True)
shaderDec4_pink_1.setUniformVariable(key='shininess',value=Mshininess,float1=True)
shaderDec4_pink_1.setUniformVariable(key='matColor',value=Mcolor,float3=True)
##
shaderDec4_pink_2.setUniformVariable(key='ambientColor',value=Lambientcolor,float3=True)
shaderDec4_pink_2.setUniformVariable(key='ambientStr',value=Lambientstr,float1=True)
shaderDec4_pink_2.setUniformVariable(key='viewPos',value=LviewPos,float3=True)
shaderDec4_pink_2.setUniformVariable(key='lightPos',value=Lposition,float3=True)
shaderDec4_pink_2.setUniformVariable(key='lightColor',value=Lcolor,float3=True)
shaderDec4_pink_2.setUniformVariable(key='lightIntensity',value=Lintensity,float1=True)
shaderDec4_pink_2.setUniformVariable(key='shininess',value=Mshininess,float1=True)
shaderDec4_pink_2.setUniformVariable(key='matColor',value=Mcolor,float3=True)
##
shaderDec4_pink_3.setUniformVariable(key='ambientColor',value=Lambientcolor,float3=True)
shaderDec4_pink_3.setUniformVariable(key='ambientStr',value=Lambientstr,float1=True)
shaderDec4_pink_3.setUniformVariable(key='viewPos',value=LviewPos,float3=True)
shaderDec4_pink_3.setUniformVariable(key='lightPos',value=Lposition,float3=True)
shaderDec4_pink_3.setUniformVariable(key='lightColor',value=Lcolor,float3=True)
shaderDec4_pink_3.setUniformVariable(key='lightIntensity',value=Lintensity,float1=True)
shaderDec4_pink_3.setUniformVariable(key='shininess',value=Mshininess,float1=True)
shaderDec4_pink_3.setUniformVariable(key='matColor',value=Mcolor,float3=True)
##
shaderDec4_yellow_1.setUniformVariable(key='ambientColor',value=Lambientcolor,float3=True)
shaderDec4_yellow_1.setUniformVariable(key='ambientStr',value=Lambientstr,float1=True)
shaderDec4_yellow_1.setUniformVariable(key='viewPos',value=LviewPos,float3=True)
shaderDec4_yellow_1.setUniformVariable(key='lightPos',value=Lposition,float3=True)
shaderDec4_yellow_1.setUniformVariable(key='lightColor',value=Lcolor,float3=True)
shaderDec4_yellow_1.setUniformVariable(key='lightIntensity',value=Lintensity,float1=True)
shaderDec4_yellow_1.setUniformVariable(key='shininess',value=Mshininess,float1=True)
shaderDec4_yellow_1.setUniformVariable(key='matColor',value=Mcolor,float3=True)
##
shaderDec4_yellow_2.setUniformVariable(key='ambientColor',value=Lambientcolor,float3=True)
shaderDec4_yellow_2.setUniformVariable(key='ambientStr',value=Lambientstr,float1=True)
shaderDec4_yellow_2.setUniformVariable(key='viewPos',value=LviewPos,float3=True)
shaderDec4_yellow_2.setUniformVariable(key='lightPos',value=Lposition,float3=True)
shaderDec4_yellow_2.setUniformVariable(key='lightColor',value=Lcolor,float3=True)
shaderDec4_yellow_2.setUniformVariable(key='lightIntensity',value=Lintensity,float1=True)
shaderDec4_yellow_2.setUniformVariable(key='shininess',value=Mshininess,float1=True)
shaderDec4_yellow_2.setUniformVariable(key='matColor',value=Mcolor,float3=True)

skybox_texture_locations = os.path.join(TEXTURE_DIR, "Skyboxes", "Day_Sunless")
#skybox_texture_locations = os.path.join(TEXTURE_DIR, "Skyboxes", "Meadow")
front_img = os.path.join(skybox_texture_locations, "front.png")
right_img = os.path.join(skybox_texture_locations,"right.png")
left_img = os.path.join(skybox_texture_locations,"left.png")
back_img = os.path.join(skybox_texture_locations,"back.png")
bottom_img = os.path.join(skybox_texture_locations,"bottom.png")
top_img = os.path.join(skybox_texture_locations,"top.png")

face_data = get_texture_faces(front_img,back_img,top_img,bottom_img,left_img,right_img)

while running:
    running = scene.render()
    scene.world.traverse_visit(transUpdate, scene.world.root) 
    scene.world.traverse_visit(renderUpdate, scene.world.root)
    view =  gWindow._myCamera # updates view via the imgui
    height = scene.renderWindow._windowHeight
    width = scene.renderWindow._windowWidth
    
    gizmos.update_screen_dimensions(window_width=width,window_height=height)
    gizmos.update_view(view)
    gizmos.update_ray_start()
    gizmos.get_Event()
    gizmos.update_imgui()

    model_cube_pink_1 = trans4_pink_1.l2world
    model_cube_pink_2 = trans4_pink_2.l2world
    model_cube_pink_3 = trans4_pink_3.l2world
    model_terrain = terrain.getChild(0).l2world
    model_cube_yellow_1 = trans4_yellow_1.l2world
    model_cube_yellow_2 = trans4_yellow_2.l2world
    
    mvp_cube_pink_1 = projMat @ view @ model_cube_pink_1
    mvp_cube_pink_2 = projMat @ view @ model_cube_pink_2
    mvp_cube_pink_3 = projMat @ view @ model_cube_pink_3
    mvp_cube_yellow_1 = projMat @ view @ model_cube_yellow_1
    mvp_cube_yellow_2 = projMat @ view @ model_cube_yellow_2
    mvp_terrain = projMat @ view @ model_terrain

    shaderSkybox.setUniformVariable(key='Proj', value=projMat, mat4=True)
    shaderSkybox.setUniformVariable(key='View', value=view, mat4=True)

    terrain_shader.setUniformVariable(key='modelViewProj', value=mvp_terrain, mat4=True)
    shaderDec4_pink_1.setUniformVariable(key='modelViewProj', value=mvp_cube_pink_1, mat4=True)
    shaderDec4_pink_2.setUniformVariable(key='modelViewProj', value=mvp_cube_pink_2, mat4=True)
    shaderDec4_pink_3.setUniformVariable(key='modelViewProj', value=mvp_cube_pink_3, mat4=True)
    shaderDec4_yellow_1.setUniformVariable(key='modelViewProj', value=mvp_cube_yellow_1, mat4=True)
    shaderDec4_yellow_2.setUniformVariable(key='modelViewProj', value=mvp_cube_yellow_2, mat4=True)
    shaderDec4_pink_1.setUniformVariable(key='model', value=model_cube_pink_1, mat4=True)
    shaderDec4_pink_2.setUniformVariable(key='model', value=model_cube_pink_2, mat4=True)
    shaderDec4_pink_3.setUniformVariable(key='model', value=model_cube_pink_3, mat4=True)
    shaderDec4_yellow_1.setUniformVariable(key='model', value=model_cube_yellow_1, mat4=True)
    shaderDec4_yellow_2.setUniformVariable(key='model', value=model_cube_yellow_2, mat4=True)
    scene.render_post()
    
scene.shutdown()