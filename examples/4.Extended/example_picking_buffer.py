import numpy as np

import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, RenderMesh
from Elements.pyECSS.System import TransformSystem
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GUI.Viewer import RenderGLStateSystem
from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray
import Elements.utils.normals as norm
from Elements.utils.Shortcuts import displayGUI_text

from Elements.extensions.picking_buffer import PickingBuffer as pb

example_description = \
"Simple scene containing cube and terrain to test PickingSystem \n" \
"Clicked entity information is printed in console \n" \

# Initializing scene
scene = Scene()

# Initializing Root entity
rootEntity = scene.world.createEntity(Entity(name="RooT"))

########## - CAMERA - ##########

# Initializing camera
entityCam1 = scene.world.createEntity(Entity(name="entityCam1"))
scene.world.addEntityChild(rootEntity, entityCam1)
trans1 = scene.world.addComponent(entityCam1, BasicTransform(name="trans1", trs=util.translate(0,0,-8)))

# Initializing Camera parameters
eye = util.vec(2.5, 2.5, 2.5)
target = util.vec(0.0, 0.0, 0.0)
up = util.vec(0.0, 1.0, 0.0)
view = util.lookat(eye, target, up)

# Added these:
width = 1024
height = 768
fov = 50.0
aspect_ratio = width/height
near = 0.01
far = 60.0
projMat = util.perspective(fov, aspect_ratio, near, far)

########## - LIGHTING - ##########

Lposition = util.vec(2.0, 5.5, 2.0)
Lambientcolor = util.vec(1.0, 1.0, 1.0)
Lambientstr = 0.3
LviewPos = util.vec(2.5, 2.8, 5.0)
Lcolor = util.vec(1.0, 1.0, 1.0)
Lintensity = 0.8
Mshininess = 1.0
Mcolor = util.vec(0.8, 0.8, 0.8)

########## - SYSTEMS - ##########

# Initialize Systems
transUpdate = scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
renderUpdate = scene.world.createSystem(RenderGLShaderSystem())
initUpdate = scene.world.createSystem(InitGLShaderSystem())

# PICKING SYSTEM: CREATE AND ADD TO WORLD
pickingSystem = pb.PickingSystem(width, height)
scene.world.createSystem(pickingSystem)

########## - CREATE OBJECTS - ##########

# Create CUBE Entity (Entity, Add to root, Trnassform and Mesh)
cubeNode = scene.world.createEntity(Entity(name="Cube"))
scene.world.addEntityChild(rootEntity, cubeNode)
cubeTrans = scene.world.addComponent(cubeNode, BasicTransform(name="Cube_TRS", trs=util.scale(0.1, 0.1, 0.1)))
cubeMesh = scene.world.addComponent(cubeNode, RenderMesh(name="Cube_Mesh"))

# White cube position and color data
vertexCubeArr = np.array([
    [-0.5, 0.0,  0.5, 1.0],
    [-0.5, 1.0,  0.5, 1.0],
    [ 0.5, 1.0,  0.5, 1.0],
    [ 0.5, 0.0,  0.5, 1.0], 
    [-0.5, 0.0, -0.5, 1.0], 
    [-0.5, 1.0, -0.5, 1.0], 
    [ 0.5, 1.0, -0.5, 1.0], 
    [ 0.5, 0.0, -0.5, 1.0]
])
colorCubeArr = np.array([
    [1.0, 1.0, 1.0, 1.0],
    [1.0, 1.0, 1.0, 1.0],
    [1.0, 1.0, 1.0, 1.0],
    [1.0, 1.0, 1.0, 1.0],
    [1.0, 1.0, 1.0, 1.0],
    [1.0, 1.0, 1.0, 1.0],
    [1.0, 1.0, 1.0, 1.0],
    [1.0, 1.0, 1.0, 1.0]
], dtype=np.float32)
indexCubeArr = np.array((1,0,3, 1,3,2, 
                  2,3,7, 2,7,6,
                  3,0,4, 3,4,7,
                  6,5,1, 6,1,2,
                  4,5,6, 4,6,7,
                  5,4,0, 5,0,1), np.uint32) #rhombus out of two triangles

# Normalize cube mesh
cubeVertices, cubeIndices, cubeColors, cubeNormals = norm.generateSmoothNormalsMesh(vertexCubeArr, indexCubeArr, colorCubeArr)

cubeNormals[:] = [0,1,0]

cubeMesh.vertex_attributes.append(cubeVertices)
cubeMesh.vertex_attributes.append(cubeColors)
cubeMesh.vertex_attributes.append(cubeNormals)
cubeMesh.vertex_index.append(cubeIndices)

vArrayCube = scene.world.addComponent(cubeNode, VertexArray())
cubeShader = scene.world.addComponent(cubeNode, ShaderGLDecorator(Shader(vertex_source=Shader.VERT_PHONG_MVP, fragment_source=Shader.FRAG_PHONG)))

# Create TERRAIN entity
#vertTerrain, indexTerrain, colorTerrain = generateTerrain(size=3, mode="triangles")

vertTerArr = np.array([
    [3.0, 0.0, 3.0, 1.0],
    [-3.0, 0.0, 3.0, 1.0],
    [-3.0, 0.0, -3.0, 1.0],
    [3.0, 0.0, -3.0, 1.0]
])
colorTerrArr= np.array([
    [0.7, 0.7, 0.7, 1.0],
    [0.7, 0.7, 0.7, 1.0],
    [0.7, 0.7, 0.7, 1.0],
    [0.7, 0.7, 0.7, 1.0]
])
indexTerrArr = np.array(
    (0,1,3 , 2,1,3)
)

terrainEntity = scene.world.createEntity(Entity(name="Terrain"))
scene.world.addEntityChild(rootEntity, terrainEntity)
terrainTrans = scene.world.addComponent(terrainEntity, BasicTransform(name="Terrain_TRS", trs=util.identity()))
terrainMesh = scene.world.addComponent(terrainEntity, RenderMesh(name="Terrain_Mesh"))

vertTerrain, indexTerrain, colorTerrain, normalsTerrain = norm.generateSmoothNormalsMesh(vertTerArr,indexTerrArr,colorTerrArr)

normalsTerrain[:] = [0,1,0]

terrainMesh.vertex_attributes.append(vertTerrain)
terrainMesh.vertex_attributes.append(colorTerrain)
terrainMesh.vertex_attributes.append(normalsTerrain)
terrainMesh.vertex_index.append(indexTerrain)

vArrayTerrain = scene.world.addComponent(terrainEntity, VertexArray())
terrainShader = scene.world.addComponent(terrainEntity, ShaderGLDecorator(Shader(vertex_source=Shader.VERT_PHONG_MVP, fragment_source=Shader.FRAG_PHONG)))

########## - MAIN RENDERING LOOP INIT - ##########

# Flag for loop
running = True
scene.init(imgui=True,
           windowWidth= width,
           windowHeight= height,
           windowTitle="Assignment_1_4470",
           openGLversion= 4)
# Removed customImGUIdecorator= ImGUIecssDecorator2

# Initialization first run
scene.world.traverse_visit(initUpdate, scene.world.root)

########## - EVENT MANAGER - ##########

eManager = scene.world.eventManager
gWindow = scene.renderWindow
gGUI = scene.gContext

renderGLEventActuator = RenderGLStateSystem()

eManager._subscribers['OnUpdateWireframe'] = gWindow
eManager._actuators['OnUpdateWireframe'] = renderGLEventActuator
eManager._subscribers['OnUpdateCamera'] = gWindow
eManager._actuators['OnUpdateCamera'] = renderGLEventActuator

gWindow._myCamera = view

projMat = util.perspective(50.0, width/height, 0.01, 100.0)

# PICKING SYSTEM: SET CAMERA MATRICES AND INITIALIZE
pickingSystem.set_camera_matrices(projMat, view)
pickingSystem.init()

print("cube verts:", cubeVertices.shape)
print("cube colors:", cubeColors.shape)
print("cube normals:", cubeNormals.shape)
print("cube indices:", cubeIndices.shape)

print("terrain verts:", vertTerrain.shape)
print("terrain colors:", colorTerrain.shape)
print("terrain indices:", indexTerrain.shape)

scene.world.print()

########### - RUN - ############

while running:

    running = scene.render()
    scene.world.traverse_visit(transUpdate,  scene.world.root)
    scene.world.traverse_visit(renderUpdate, scene.world.root)
    displayGUI_text(example_description)
    view = gWindow._myCamera
    height = scene.renderWindow._windowHeight
    width = scene.renderWindow._windowWidth

    # PICKING SYSTEM: PER FRAME
    click_coords = pickingSystem.check_for_click()
    if click_coords:
        mouse_x = click_coords[0]
        mouse_y = click_coords[1]

        pickingSystem.set_camera_matrices(projMat, view)
        pickingSystem.begin_picking_pass()   
        scene.world.traverse_visit(pickingSystem, scene.world.root)  
        pickingSystem.end_picking_pass()

        entity, picked_id = pickingSystem.pick(mouse_x, mouse_y, height)

        print("\nPicked id: ", picked_id, entity,"\n")

    cubeShader.setUniformVariable(key='modelViewProj', value=projMat @ view @ cubeTrans.l2world, mat4=True)
    cubeShader.setUniformVariable(key='model',value=cubeTrans.l2world,mat4=True)
    cubeShader.setUniformVariable(key='ambientColor',value=Lambientcolor,float3=True)
    cubeShader.setUniformVariable(key='ambientStr',value=Lambientstr,float1=True)
    cubeShader.setUniformVariable(key='viewPos',value=LviewPos,float3=True)
    cubeShader.setUniformVariable(key='lightPos',value=Lposition,float3=True)
    cubeShader.setUniformVariable(key='lightColor',value=Lcolor,float3=True)
    cubeShader.setUniformVariable(key='lightIntensity',value=Lintensity,float1=True)
    cubeShader.setUniformVariable(key='shininess',value=Mshininess,float1=True)
    cubeShader.setUniformVariable(key='matColor',value=Mcolor,float3=True)

    terrainShader.setUniformVariable(key='modelViewProj', value=projMat @ view @ terrainTrans.l2world, mat4=True)
    terrainShader.setUniformVariable(key='model',value=terrainTrans.l2world,mat4=True)
    terrainShader.setUniformVariable(key='ambientColor',value=Lambientcolor,float3=True)
    terrainShader.setUniformVariable(key='ambientStr',value=Lambientstr,float1=True)
    terrainShader.setUniformVariable(key='viewPos',value=LviewPos,float3=True)
    terrainShader.setUniformVariable(key='lightPos',value=Lposition,float3=True)
    terrainShader.setUniformVariable(key='lightColor',value=Lcolor,float3=True)
    terrainShader.setUniformVariable(key='lightIntensity',value=Lintensity,float1=True)
    terrainShader.setUniformVariable(key='shininess',value=Mshininess,float1=True)
    terrainShader.setUniformVariable(key='matColor',value=Mcolor,float3=True)

    scene.world.traverse_visit(renderUpdate, scene.world.root)
    scene.render_post()

scene.shutdown()    
