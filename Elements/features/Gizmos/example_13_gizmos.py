import numpy as np
import os
import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, RenderMesh
from Elements.pyECSS.System import  TransformSystem
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GUI.Viewer import RenderGLStateSystem
from Elements.features.Gizmos.Gizmos import Gizmos
from Elements.definitions import TEXTURE_DIR, MODEL_DIR
from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray
import Elements.utils.normals as norm
from Elements.utils.obj_to_mesh import obj_to_mesh
from Elements.pyGLV.GL.Textures import get_texture_faces, Texture
from Elements.pyGLV.GL.Textures import get_single_texture_faces

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


VertexTerrain = np.array(vertexCube,copy=True) @ util.scale(6.0,0.05,6.0)

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

VertexTableTop = np.array(vertexCube,copy=True) @ util.scale(1.5,0.2,1.5)

VertexTableLeg = np.array(vertexCube,copy=True) @ util.scale(0.2,1.2,0.2)

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

scene = Scene()    

# Scenegraph with Entities, Components
rootEntity = scene.world.createEntity(Entity(name="RooT"))
entityCam1 = scene.world.createEntity(Entity(name="entityCam1"))
scene.world.addEntityChild(rootEntity, entityCam1)
trans1 = scene.world.addComponent(entityCam1, BasicTransform(name="trans1", trs=util.translate(2.5, 2.5, 2.5)))

ground = scene.world.createEntity(Entity(name="ground"))
scene.world.addEntityChild(rootEntity, ground)
ground_trans = scene.world.addComponent(ground, BasicTransform(name="ground_trans", trs=util.translate(0.0,-1.1,0.0)))
ground_mesh = scene.world.addComponent(ground, RenderMesh(name="ground_mesh"))

TableTop = scene.world.createEntity(Entity(name="TableTop"))
scene.world.addEntityChild(rootEntity, TableTop)
trans_TableTop = scene.world.addComponent(TableTop, BasicTransform(name="trans_TableTop", trs=util.translate(0.0,0.2,0.0))) #util.identity()
mesh_TableTop = scene.world.addComponent(TableTop, RenderMesh(name="mesh_TableTop"))

TableLeg1 = scene.world.createEntity(Entity(name="TableLeg1"))
scene.world.addEntityChild(TableTop,TableLeg1)
trans_TableLeg1 = scene.world.addComponent(TableLeg1, BasicTransform(name="trans_TableLeg1", trs=util.translate(0.65,-0.7,0.65))) #util.identity()
mesh_TableLeg1 = scene.world.addComponent(TableLeg1, RenderMesh(name="mesh_TableLeg1"))

TableLeg2 = scene.world.createEntity(Entity(name="TableLeg2"))
scene.world.addEntityChild(TableTop,TableLeg2)
trans_TableLeg2 = scene.world.addComponent(TableLeg2, BasicTransform(name="trans_TableLeg2", trs=util.translate(-0.65,-0.7,0.65))) #util.identity()
mesh_TableLeg2 = scene.world.addComponent(TableLeg2, RenderMesh(name="mesh_TableLeg2"))

TableLeg3 = scene.world.createEntity(Entity(name="TableLeg3"))
scene.world.addEntityChild(TableTop,TableLeg3)
trans_TableLeg3 = scene.world.addComponent(TableLeg3, BasicTransform(name="trans_TableLeg3", trs=util.translate(0.65,-0.7,-0.65))) #util.identity()
mesh_TableLeg3 = scene.world.addComponent(TableLeg3, RenderMesh(name="mesh_TableLeg3"))

TableLeg4 = scene.world.createEntity(Entity(name="TableLeg4"))
scene.world.addEntityChild(TableTop,TableLeg4)
trans_TableLeg4 = scene.world.addComponent(TableLeg4, BasicTransform(name="trans_TableLeg4", trs=util.translate(-0.65,-0.7,-0.65))) #util.identity()
mesh_TableLeg4 = scene.world.addComponent(TableLeg4, RenderMesh(name="mesh_TableLeg4"))

teapot = scene.world.createEntity(Entity(name="Teapot"))
scene.world.addEntityChild(rootEntity, teapot)
trans_teapot = scene.world.addComponent(teapot, BasicTransform(name="Teapot_TRS", trs=util.translate(y=0.3) @ util.scale(0.1, 0.1, 0.1) ))
teapot_mesh = scene.world.addComponent(teapot, RenderMesh(name="Teapot_mesh"))

# Systems
transUpdate = scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
# camUpdate = scene.world.createSystem(CameraSystem("camUpdate", "CameraUpdate", "200"))
renderUpdate = scene.world.createSystem(RenderGLShaderSystem())
initUpdate = scene.world.createSystem(InitGLShaderSystem())

vertexground, indexground, _ = norm.generateUniqueVertices(VertexTerrain,indexCube)

verticesTableTop, indicesTableTop, _ = norm.generateUniqueVertices(VertexTableTop,indexCube)
verticesTableLeg, indicesTableLeg, _ = norm.generateUniqueVertices(VertexTableLeg,indexCube)

teapot_obj = MODEL_DIR / "teapot.obj"

#Import Teapot
obj_color = [168/255, 168/255 , 210/255, 1.0]
vert , ind, col = obj_to_mesh(teapot_obj, color=obj_color)
vertices, indices, colors, normals = norm.generateSmoothNormalsMesh(vert , ind, col)

teapot_mesh.vertex_attributes.append(vertices)
teapot_mesh.vertex_attributes.append(colors)
teapot_mesh.vertex_attributes.append(normals)
teapot_mesh.vertex_index.append(indices)
vArray_teapot = scene.world.addComponent(teapot, VertexArray())
ShaderTeapot = scene.world.addComponent(teapot, ShaderGLDecorator(Shader(vertex_source = Shader.VERT_PHONG_MVP, fragment_source=Shader.FRAG_PHONG)))


# Add ground
ground_mesh.vertex_attributes.append(vertexground)
ground_mesh.vertex_attributes.append(Texture.CUBE_TEX_COORDINATES)
ground_mesh.vertex_index.append(indexground)
ground_vArray = scene.world.addComponent(ground, VertexArray())
ground_shader = scene.world.addComponent(ground, ShaderGLDecorator(Shader(vertex_source = Shader.SIMPLE_TEXTURE_VERT, fragment_source=Shader.SIMPLE_TEXTURE_FRAG)))

mesh_TableTop.vertex_attributes.append(verticesTableTop)
mesh_TableTop.vertex_attributes.append(Texture.CUBE_TEX_COORDINATES)
mesh_TableTop.vertex_index.append(indicesTableTop)
vArray_TableTop = scene.world.addComponent(TableTop, VertexArray())
shaderDec_TableTop = scene.world.addComponent(TableTop, ShaderGLDecorator(Shader(vertex_source = Shader.SIMPLE_TEXTURE_VERT, fragment_source=Shader.SIMPLE_TEXTURE_FRAG)))

mesh_TableLeg1.vertex_attributes.append(verticesTableLeg)
mesh_TableLeg1.vertex_attributes.append(Texture.CUBE_TEX_COORDINATES)
mesh_TableLeg1.vertex_index.append(indicesTableLeg)
vArray_TableLeg1 = scene.world.addComponent(TableLeg1, VertexArray())
shaderDec_TableLeg1 = scene.world.addComponent(TableLeg1, ShaderGLDecorator(Shader(vertex_source = Shader.SIMPLE_TEXTURE_VERT, fragment_source=Shader.SIMPLE_TEXTURE_FRAG)))

mesh_TableLeg2.vertex_attributes.append(verticesTableLeg)
mesh_TableLeg2.vertex_attributes.append(Texture.CUBE_TEX_COORDINATES)
mesh_TableLeg2.vertex_index.append(indicesTableLeg)
vArray_TableLeg2 = scene.world.addComponent(TableLeg2, VertexArray())
shaderDec_TableLeg2 = scene.world.addComponent(TableLeg2, ShaderGLDecorator(Shader(vertex_source = Shader.SIMPLE_TEXTURE_VERT, fragment_source=Shader.SIMPLE_TEXTURE_FRAG)))

mesh_TableLeg3.vertex_attributes.append(verticesTableLeg)
mesh_TableLeg3.vertex_attributes.append(Texture.CUBE_TEX_COORDINATES)
mesh_TableLeg3.vertex_index.append(indicesTableLeg)
vArray_TableLeg3 = scene.world.addComponent(TableLeg3, VertexArray())
shaderDec_TableLeg3 = scene.world.addComponent(TableLeg3, ShaderGLDecorator(Shader(vertex_source = Shader.SIMPLE_TEXTURE_VERT, fragment_source=Shader.SIMPLE_TEXTURE_FRAG)))

mesh_TableLeg4.vertex_attributes.append(verticesTableLeg)
mesh_TableLeg4.vertex_attributes.append(Texture.CUBE_TEX_COORDINATES)
mesh_TableLeg4.vertex_index.append(indicesTableLeg)
vArray_TableLeg4 = scene.world.addComponent(TableLeg4, VertexArray())
shaderDec_TableLeg4 = scene.world.addComponent(TableLeg4, ShaderGLDecorator(Shader(vertex_source = Shader.SIMPLE_TEXTURE_VERT, fragment_source=Shader.SIMPLE_TEXTURE_FRAG)))

eye = util.vec(2.5, 2.5, 2.5)
target = util.vec(0.0, 0.0, 0.0)
up = util.vec(0.0, 1.0, 0.0)
view = util.lookat(eye, target, up)
width = 1024.0
height = 768.0
fov = 50.0
aspect_ratio = width/height
near = 0.01
far = 60.0
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

skybox_texture_locations = TEXTURE_DIR /  "Skyboxes" / "Sea"
front_img = skybox_texture_locations /  "front.jpg"
right_img = skybox_texture_locations / "right.jpg"
left_img = skybox_texture_locations / "left.jpg"
back_img = skybox_texture_locations / "back.jpg"
bottom_img = skybox_texture_locations / "bottom.jpg"
top_img = skybox_texture_locations / "top.jpg"

face_data = get_texture_faces(front_img,back_img,top_img,bottom_img,left_img,right_img)

texturePath_Ground = TEXTURE_DIR /  "Texture_Grass.png"
texture = Texture(texturePath_Ground)
ground_shader.setUniformVariable(key='ImageTexture', value=texture, texture=True)

texturePath_Wood_Material = TEXTURE_DIR /  "dark_wood_texture.jpg"
texture_Wood = Texture(texturePath_Wood_Material)

shaderDec_TableTop.setUniformVariable(key='ImageTexture', value=texture_Wood, texture=True)
shaderDec_TableLeg1.setUniformVariable(key='ImageTexture', value=texture_Wood, texture=True)
shaderDec_TableLeg2.setUniformVariable(key='ImageTexture', value=texture_Wood, texture=True)
shaderDec_TableLeg3.setUniformVariable(key='ImageTexture', value=texture_Wood, texture=True)
shaderDec_TableLeg4.setUniformVariable(key='ImageTexture', value=texture_Wood, texture=True)


ShaderTeapot.setUniformVariable(key='ambientColor',value=Lambientcolor,float3=True)
ShaderTeapot.setUniformVariable(key='ambientStr',value=Lambientstr,float1=True)
ShaderTeapot.setUniformVariable(key='viewPos',value=LviewPos,float3=True)
ShaderTeapot.setUniformVariable(key='lightPos',value=Lposition,float3=True)
ShaderTeapot.setUniformVariable(key='lightColor',value=Lcolor,float3=True)
ShaderTeapot.setUniformVariable(key='lightIntensity',value=Lintensity,float1=True)
ShaderTeapot.setUniformVariable(key='shininess',value=Mshininess,float1=True)
ShaderTeapot.setUniformVariable(key='matColor',value=Mcolor,float3=True)

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
    model_ground = ground.getChild(0).l2world

    model_TableTop = trans_TableTop.l2world
    model_TableLeg1 = trans_TableLeg1.l2world
    model_TableLeg2 = trans_TableLeg2.l2world
    model_TableLeg3 = trans_TableLeg3.l2world
    model_TableLeg4 = trans_TableLeg4.l2world

    mvp_teapot = projMat @ view @ trans_teapot.trs

    #Update Ground Variables
    ground_shader.setUniformVariable(key='Proj', value=projMat, mat4=True)
    ground_shader.setUniformVariable(key='View', value=view, mat4=True)
    ground_shader.setUniformVariable(key='model', value=model_ground, mat4=True)

    #Update Table Variables
    shaderDec_TableTop.setUniformVariable(key='Proj', value=projMat, mat4=True)
    shaderDec_TableTop.setUniformVariable(key='View', value=view, mat4=True)
    shaderDec_TableTop.setUniformVariable(key='model', value=model_TableTop, mat4=True)

    shaderDec_TableLeg1.setUniformVariable(key='Proj', value=projMat, mat4=True)
    shaderDec_TableLeg1.setUniformVariable(key='View', value=view, mat4=True)
    shaderDec_TableLeg1.setUniformVariable(key='model', value=model_TableLeg1, mat4=True)

    shaderDec_TableLeg2.setUniformVariable(key='Proj', value=projMat, mat4=True)
    shaderDec_TableLeg2.setUniformVariable(key='View', value=view, mat4=True)
    shaderDec_TableLeg2.setUniformVariable(key='model', value=model_TableLeg2, mat4=True)

    shaderDec_TableLeg3.setUniformVariable(key='Proj', value=projMat, mat4=True)
    shaderDec_TableLeg3.setUniformVariable(key='View', value=view, mat4=True)
    shaderDec_TableLeg3.setUniformVariable(key='model', value=model_TableLeg3, mat4=True)

    shaderDec_TableLeg4.setUniformVariable(key='Proj', value=projMat, mat4=True)
    shaderDec_TableLeg4.setUniformVariable(key='View', value=view, mat4=True)
    shaderDec_TableLeg4.setUniformVariable(key='model', value=model_TableLeg4, mat4=True)

    #Update Teapot Uniform Variables
    ShaderTeapot.setUniformVariable(key='modelViewProj', value=mvp_teapot, mat4=True)
    ShaderTeapot.setUniformVariable(key='model',value=trans_teapot.trs,mat4=True)

    scene.render_post()
    
scene.shutdown()