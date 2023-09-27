import numpy as np
import os
import time
import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, RenderMesh
from Elements.pyECSS.System import  TransformSystem
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray
import Elements.utils.normals as norm
from OpenGL.GL import GL_LINES
from Elements.pyGLV.GL.Textures import Texture, get_texture_faces
from Elements.utils.obj_to_mesh import obj_to_mesh
from Elements.definitions import TEXTURE_DIR, MODEL_DIR
from Elements.features.XR.ElementsXR import ElementsXR_program
from Elements.definitions import TEXTURE_DIR
from Elements.features.Gizmos.Gizmos import Gizmos_XR

"""
Note: Before running this example open steamVR, go to Settings -> OpenXR and press "SET STEAMVR AS OPENXR RUNTIME"
      Otherwise the graphics plugin will not find the OpenGL plugin.
      Tested with Windows Mixed Reality
"""

#Light
Lposition = util.vec(2.0, 5.5, 2.0) #uniform lightpos
Lambientcolor = util.vec(1.0, 1.0, 1.0) #uniform ambient color
Lambientstr = 0.3 #uniform ambientStr
LviewPos = util.vec(2.5, 2.8, 5.0) #uniform viewpos
Lcolor = util.vec(1.0,1.0,1.0)
Lintensity = 0.8
#Material
Mshininess = 0.4 
Mcolor = util.vec(0.8, 0.0, 0.8)

scene = Scene()

# Scenegraph with Entities, Components
rootEntity = scene.world.createEntity(Entity(name="RooT"))

skybox = scene.world.createEntity(Entity(name="Skybox"))
scene.world.addEntityChild(rootEntity, skybox)
transSkybox = scene.world.addComponent(skybox, BasicTransform(name="transSkybox", trs=util.identity())) 
meshSkybox = scene.world.addComponent(skybox, RenderMesh(name="meshSkybox"))

teapot = scene.world.createEntity(Entity(name="Teapot"))
scene.world.addEntityChild(rootEntity, teapot)
trans_teapot = scene.world.addComponent(teapot, BasicTransform(name="Teapot_TRS", trs= util.scale(0.1,0.1,0.1) @ util.translate(y=3.0)))
teapot_mesh = scene.world.addComponent(teapot, RenderMesh(name="Teapot_mesh"))

ground = scene.world.createEntity(Entity(name="ground"))
scene.world.addEntityChild(rootEntity, ground)
ground_trans = scene.world.addComponent(ground, BasicTransform(name="ground_trans", trs=util.translate(0.0,-1.1,0.0) @ util.scale(10.0,1.0,10.0)))
ground_mesh = scene.world.addComponent(ground, RenderMesh(name="ground_mesh"))

Table = scene.world.createEntity(Entity(name="Table"))
scene.world.addEntityChild(rootEntity, Table)
trans_TableTop = scene.world.addComponent(Table, BasicTransform(name="trans_Table", trs=util.identity()))

TableTop = scene.world.createEntity(Entity(name="TableTop"))
scene.world.addEntityChild(Table,TableTop)
trans_TableTop = scene.world.addComponent(TableTop, BasicTransform(name="trans_TableTop", trs=util.translate(0.0,0.2,0.0)))
mesh_TableTop = scene.world.addComponent(TableTop, RenderMesh(name="mesh_TableTop"))

TableLeg1 = scene.world.createEntity(Entity(name="TableLeg1"))
scene.world.addEntityChild(Table,TableLeg1)
trans_TableLeg1 = scene.world.addComponent(TableLeg1, BasicTransform(name="trans_TableLeg1", trs=util.translate(0.65,-0.5,0.65)))
mesh_TableLeg1 = scene.world.addComponent(TableLeg1, RenderMesh(name="mesh_TableLeg1"))

TableLeg2 = scene.world.createEntity(Entity(name="TableLeg2"))
scene.world.addEntityChild(Table,TableLeg2)
trans_TableLeg2 = scene.world.addComponent(TableLeg2, BasicTransform(name="trans_TableLeg2", trs=util.translate(-0.65,-0.5,0.65)))
mesh_TableLeg2 = scene.world.addComponent(TableLeg2, RenderMesh(name="mesh_TableLeg2"))

TableLeg3 = scene.world.createEntity(Entity(name="TableLeg3"))
scene.world.addEntityChild(Table,TableLeg3)
trans_TableLeg3 = scene.world.addComponent(TableLeg3, BasicTransform(name="trans_TableLeg3", trs=util.translate(0.65,-0.5,-0.65)))
mesh_TableLeg3 = scene.world.addComponent(TableLeg3, RenderMesh(name="mesh_TableLeg3"))

TableLeg4 = scene.world.createEntity(Entity(name="TableLeg4"))
scene.world.addEntityChild(Table,TableLeg4)
trans_TableLeg4 = scene.world.addComponent(TableLeg4, BasicTransform(name="trans_TableLeg4", trs=util.translate(-0.65,-0.5,-0.65)))
mesh_TableLeg4 = scene.world.addComponent(TableLeg4, RenderMesh(name="mesh_TableLeg4"))

Head = scene.world.createEntity(Entity(name="Head"))
scene.world.addEntityChild(rootEntity,Head)
trans_head = scene.world.addComponent(Head,BasicTransform(name="trans_head",trs=util.translate(-0.1,-4.0,-4.5)))

Left_Hand = scene.world.createEntity(Entity(name="Left_hand"))
#scene.world.addEntityChild(Head,Left_Hand)
scene.world.addEntityChild(rootEntity,Left_Hand)
trans_left_hand = scene.world.addComponent(Left_Hand,BasicTransform(name="trans_Left_Hand",trs=util.translate(y=-10.0)))
mesh_left_hand = scene.world.addComponent(Left_Hand, RenderMesh(name="mesh_Left_Hand"))

Right_Hand = scene.world.createEntity(Entity(name="Right_hand"))
#scene.world.addEntityChild(Head,Right_Hand)
scene.world.addEntityChild(rootEntity,Right_Hand)
trans_right_hand = scene.world.addComponent(Right_Hand,BasicTransform(name="trans_Right_Hand",trs=util.translate(y=-10.0)))
mesh_right_hand = scene.world.addComponent(Right_Hand, RenderMesh(name="mesh_Right_Hand"))

Left_Ray = scene.world.createEntity(Entity(name="Left_Ray"))
scene.world.addEntityChild(Left_Hand,Left_Ray)
trans_left_ray = scene.world.addComponent(Left_Ray,BasicTransform(name="trans_Left_Ray",trs=util.identity()))
mesh_left_ray = scene.world.addComponent(Left_Ray, RenderMesh(name="mesh_Left_Ray"))

Right_Ray = scene.world.createEntity(Entity(name="Right_Ray"))
scene.world.addEntityChild(Right_Hand,Right_Ray)
trans_Right_ray = scene.world.addComponent(Right_Ray,BasicTransform(name="trans_Right_Ray",trs=util.identity()))
mesh_Right_ray = scene.world.addComponent(Right_Ray, RenderMesh(name="mesh_Right_Ray"))

#Cube
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
indexSkybox = np.array((3,0,1, 2,3,1, 
                  7,3,2, 6,7,2,
                  4,0,3, 7,4,3,
                  1,5,6, 2,1,6,
                  6,5,4, 7,6,4,
                  0,4,5, 1,0,5), np.uint32) 

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

indexCube = np.array((1,0,3, 1,3,2, 
                  2,3,7, 2,7,6,
                  3,0,4, 3,4,7,
                  6,5,1, 6,1,2,
                  4,5,6, 4,6,7,
                  5,4,0, 5,0,1), np.uint32)

colorCube = np.array([
    [1.0, 1.0, 1.0, 1.0],
    [1.0, 1.0, 1.0, 1.0],
    [1.0, 1.0, 1.0, 1.0],
    [1.0, 1.0, 1.0, 1.0],
    [1.0, 1.0, 1.0, 1.0],
    [1.0, 1.0, 1.0, 1.0],
    [1.0, 1.0, 1.0, 1.0],
    [1.0, 1.0, 1.0, 1.0]
], dtype=np.float32)

VertexRay = np.array([[0.0,0.0,0.0,1.0],
                      [0.0,0.0,-50.0,1.0]],dtype=np.float32)

indexRay = np.array((0,1),dtype=np.uint32)

ColorRay = np.array([[1.0,0.0,1.0,1.0],
                     [1.0,0.0,1.0,1.0]],dtype=np.float32)

VertexTerrain = np.array(vertexCube,copy=True) @ util.scale(6.0,0.05,6.0)

VertexTableTop = np.array(vertexCube,copy=True) @ util.scale(1.5,0.2,1.5)

VertexTableLeg = np.array(vertexCube,copy=True) @ util.scale(0.2,1.2,0.2)

verticesTableTop, indicesTableTop, _ = norm.generateUniqueVertices(VertexTableTop,indexCube)
verticesTableLeg, indicesTableLeg, _ = norm.generateUniqueVertices(VertexTableLeg,indexCube)
vertexSkybox, indexSkybox, _ = norm.generateUniqueVertices(vertexSkybox,indexSkybox)
vertexground, indexground, _ = norm.generateUniqueVertices(VertexTerrain,indexCube)
vertexHand, indexHand,ColorHand ,normalsHand = norm.generateFlatNormalsMesh(vertexCube @ util.scale(3.0,3.0,3.0),indexCube,colorCube)

# Systems
transUpdate = scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
renderUpdate = scene.world.createSystem(RenderGLShaderSystem())
initUpdate = scene.world.createSystem(InitGLShaderSystem())

meshSkybox.vertex_attributes.append(vertexSkybox)
meshSkybox.vertex_index.append(indexSkybox)
vArraySkybox = scene.world.addComponent(skybox, VertexArray())
shaderSkybox = scene.world.addComponent(skybox, ShaderGLDecorator(Shader(vertex_source = Shader.STATIC_SKYBOX_VERT, fragment_source=Shader.STATIC_SKYBOX_FRAG)))

# Add ground
ground_mesh.vertex_attributes.append(vertexground) 
ground_mesh.vertex_attributes.append(Texture.CUBE_TEX_COORDINATES)
ground_mesh.vertex_index.append(indexground)
ground_vArray = scene.world.addComponent(ground, VertexArray())
ground_shader = scene.world.addComponent(ground, ShaderGLDecorator(Shader(vertex_source = Shader.SIMPLE_TEXTURE_VERT, fragment_source=Shader.SIMPLE_TEXTURE_FRAG)))

teapot_obj = os.path.join(MODEL_DIR, "teapot.obj")

obj_color = [168/255, 168/255 , 210/255, 1.0]
vert , ind, col = obj_to_mesh(teapot_obj, color=obj_color)
vertices, indices, colors, normals = norm.generateSmoothNormalsMesh(vert , ind, col)

teapot_mesh.vertex_attributes.append(vertices)
teapot_mesh.vertex_attributes.append(colors)
teapot_mesh.vertex_attributes.append(normals)
teapot_mesh.vertex_index.append(indices)
vArray_teapot = scene.world.addComponent(teapot, VertexArray())
ShaderTeapot = scene.world.addComponent(teapot, ShaderGLDecorator(Shader(vertex_source = Shader.VERT_PHONG_MVP, fragment_source=Shader.FRAG_PHONG)))

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

mesh_left_hand.vertex_attributes.append(vertexHand)
mesh_left_hand.vertex_attributes.append(ColorHand)
mesh_left_hand.vertex_attributes.append(normalsHand)
mesh_left_hand.vertex_index.append(indexHand)
VArrayLeftHand = scene.world.addComponent(Left_Hand,VertexArray())
ShaderDec_Left_Hand = scene.world.addComponent(Left_Hand,ShaderGLDecorator(Shader(vertex_source = Shader.VERT_PHONG_MVP, fragment_source=Shader.FRAG_PHONG)))

mesh_right_hand.vertex_attributes.append(vertexHand)
mesh_right_hand.vertex_attributes.append(ColorHand)
mesh_right_hand.vertex_attributes.append(normalsHand)
mesh_right_hand.vertex_index.append(indexHand)
VArrayRightHand = scene.world.addComponent(Right_Hand,VertexArray())
ShaderDec_Right_Hand = scene.world.addComponent(Right_Hand,ShaderGLDecorator(Shader(vertex_source = Shader.VERT_PHONG_MVP, fragment_source=Shader.FRAG_PHONG)))


mesh_left_ray.vertex_attributes.append(VertexRay)
mesh_left_ray.vertex_attributes.append(ColorRay)
mesh_left_ray.vertex_index.append(indexRay)
VArrayLeftRay = scene.world.addComponent(Left_Ray,VertexArray(primitive=GL_LINES))
Shader_Left_Ray = scene.world.addComponent(Left_Ray,ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))

mesh_Right_ray.vertex_attributes.append(VertexRay)
mesh_Right_ray.vertex_attributes.append(ColorRay)
mesh_Right_ray.vertex_index.append(indexRay)
VArrayrightRay = scene.world.addComponent(Right_Ray,VertexArray(primitive=GL_LINES))
Shader_right_Ray = scene.world.addComponent(Right_Ray,ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))

gizmos = Gizmos_XR(rootEntity)
gizmos.add_ignored_item("Head")
gizmos.add_ignored_item("trans_head")

gizmos.add_ignored_item("Left_hand")
gizmos.add_ignored_item("trans_Left_hand")
gizmos.add_ignored_item("mesh_Left_hand")
gizmos.add_ignored_item("Right_hand")
gizmos.add_ignored_item("trans_Right_hand")
gizmos.add_ignored_item("mesh_Right_hand")

gizmos.add_ignored_item("Left_Ray")
gizmos.add_ignored_item("trans_Left_Ray")
gizmos.add_ignored_item("mesh_Left_Ray")
gizmos.add_ignored_item("Right_Ray")
gizmos.add_ignored_item("trans_Right_Ray")
gizmos.add_ignored_item("mesh_Right_Ray")

# MAIN RENDERING LOOP

exit_loop = False

program = ElementsXR_program()
gizmos.program = program
gizmos.exclude_gizmos()

program.set_Head(Head)
program.raycast = True
program.hands = [Left_Hand,Right_Hand]
program.rays = [Left_Ray,Right_Ray]
program.Initialize("Elements: ElementsXR Demo",initUpdate)

skybox_texture_locations = os.path.join(TEXTURE_DIR, "Skyboxes", "Day_Sunless")
front_img = os.path.join(skybox_texture_locations, "front.png")
right_img = os.path.join(skybox_texture_locations,"right.png")
left_img = os.path.join(skybox_texture_locations,"left.png")
back_img = os.path.join(skybox_texture_locations,"back.png")
bottom_img = os.path.join(skybox_texture_locations,"bottom.png")
top_img = os.path.join(skybox_texture_locations,"top.png")

face_data = get_texture_faces(front_img,back_img,top_img,bottom_img,left_img,right_img)
texturePathFloor = os.path.join(TEXTURE_DIR, "black_stones_floor.jpg")
textureFloor = Texture(texturePathFloor)
texturePathWood = os.path.join(TEXTURE_DIR, "Black_Wooden_Floor.png")
textureWood = Texture(texturePathWood)

shaderSkybox.setUniformVariable(key='cubemap', value=face_data, texture3D=True)
ground_shader.setUniformVariable(key='ImageTexture', value=textureFloor, texture=True)
shaderDec_TableTop.setUniformVariable(key='ImageTexture', value=textureWood, texture=True)
shaderDec_TableLeg1.setUniformVariable(key='ImageTexture', value=textureWood, texture=True)
shaderDec_TableLeg2.setUniformVariable(key='ImageTexture', value=textureWood, texture=True)
shaderDec_TableLeg3.setUniformVariable(key='ImageTexture', value=textureWood, texture=True)
shaderDec_TableLeg4.setUniformVariable(key='ImageTexture', value=textureWood, texture=True)

ShaderTeapot.setUniformVariable(key='ambientColor',value=Lambientcolor,float3=True)
ShaderTeapot.setUniformVariable(key='ambientStr',value=Lambientstr,float1=True)
ShaderTeapot.setUniformVariable(key='viewPos',value=LviewPos,float3=True)
ShaderTeapot.setUniformVariable(key='lightPos',value=Lposition,float3=True)
ShaderTeapot.setUniformVariable(key='lightColor',value=Lcolor,float3=True)
ShaderTeapot.setUniformVariable(key='lightIntensity',value=Lintensity,float1=True)
ShaderTeapot.setUniformVariable(key='shininess',value=Mshininess,float1=True)
ShaderTeapot.setUniformVariable(key='matColor',value=Mcolor,float3=True)

ShaderDec_Left_Hand.setUniformVariable(key='ambientColor', value=Lambientcolor, float3=True)
ShaderDec_Left_Hand.setUniformVariable(key='ambientStr',value=Lambientstr,float1=True)
ShaderDec_Left_Hand.setUniformVariable(key='viewPos',value=LviewPos,float3=True)
ShaderDec_Left_Hand.setUniformVariable(key='lightPos',value=Lposition,float3=True)
ShaderDec_Left_Hand.setUniformVariable(key='lightColor',value=Lcolor,float3=True)
ShaderDec_Left_Hand.setUniformVariable(key='lightIntensity',value=Lintensity,float1=True)
ShaderDec_Left_Hand.setUniformVariable(key='shininess',value=Mshininess,float1=True)
ShaderDec_Left_Hand.setUniformVariable(key='matColor',value=Mcolor,float3=True)

ShaderDec_Right_Hand.setUniformVariable(key='ambientColor', value=Lambientcolor, float3=True)
ShaderDec_Right_Hand.setUniformVariable(key='ambientStr',value=Lambientstr,float1=True)
ShaderDec_Right_Hand.setUniformVariable(key='viewPos',value=LviewPos,float3=True)
ShaderDec_Right_Hand.setUniformVariable(key='lightPos',value=Lposition,float3=True)
ShaderDec_Right_Hand.setUniformVariable(key='lightColor',value=Lcolor,float3=True)
ShaderDec_Right_Hand.setUniformVariable(key='lightIntensity',value=Lintensity,float1=True)
ShaderDec_Right_Hand.setUniformVariable(key='shininess',value=Mshininess,float1=True)
ShaderDec_Right_Hand.setUniformVariable(key='matColor',value=Mcolor,float3=True)

while not exit_loop:
    scene.world.traverse_visit(transUpdate,scene.world.root)
    exit_loop = program.poll_events()

    gizmos.update_ray_start()
    gizmos.get_Event()

    if program.session_running:

        # Get new input from controllers
        program.poll_actions()
        program.render_frame(renderUpdate)

    else:
        time.sleep(0.250)