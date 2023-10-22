import os
import imgui
import numpy as np
import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, Camera, RenderMesh
from Elements.pyECSS.System import TransformSystem, CameraSystem
from Elements.pyGLV.GL.ActionSystems import InsertAction, InsertCollider, RemoveAction, RemoveComponent
from Elements.pyGLV.GL.GameObject import GameObject
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GUI.Viewer import RenderGLStateSystem, ImGUIecssDecorator
from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray
from OpenGL.GL import GL_LINES
import OpenGL.GL as gl
from Elements.utils.objimporter.entities import ModelEntity
from Elements.utils.terrain import generateTerrain
from Elements.definitions import MODEL_DIR

from Elements.utils.Shortcuts import displayGUI_text
example_description = \
"This example demonstrates how we can detect behavior patterns, i.e., \n\
introduce some game logic in our scene. \n\n\
If you move (via the ECSS GUI) the left cube (RemoveCube) above the \n\
terrain, the Remove Action will be ticked. If you move the right cube \n\
(InsertCube) towards the ground it will mark the Instert Action as complete.\n\n\
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
modelsList = [] 


# Scenegraph with Entities, Components
rootEntity = scene.world.createEntity(Entity(name="RooT"))
entityCam1 = scene.world.createEntity(Entity(name="Entity1"))
scene.world.addEntityChild(rootEntity, entityCam1)
trans1 = scene.world.addComponent(entityCam1, BasicTransform(name="Entity1_TRS", trs=util.translate(0,0,-8)))

eye = util.vec(2.5, 2.5, -2.5)
target = util.vec(0.0, 0.0, 0.0)
up = util.vec(0.0, 1.0, 0.0)
view = util.lookat(eye, target, up)
projMat = util.perspective(50.0, 1.0, 1.0, 10.0)

m = np.linalg.inv(projMat @ view)

entityCam2 = scene.world.createEntity(Entity(name="Entity_Camera"))
scene.world.addEntityChild(entityCam1, entityCam2)
trans2 = scene.world.addComponent(entityCam2, BasicTransform(name="Camera_TRS", trs=util.identity()))
orthoCam = scene.world.addComponent(entityCam2, Camera(m, "orthoCam","Camera","500"))


light_node = scene.world.createEntity(Entity(name="LightPos"))
scene.world.addEntityChild(rootEntity, light_node)
light_transform = scene.world.addComponent(light_node, BasicTransform(name="Light_TRS", trs=util.scale(1.0, 1.0, 1.0) ))

# Systems
transUpdate = scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
camUpdate = scene.world.createSystem(CameraSystem("camUpdate", "CameraUpdate", "200"))
renderUpdate = scene.world.createSystem(RenderGLShaderSystem())
initUpdate = scene.world.createSystem(InitGLShaderSystem())


# Load Object

obj_to_import = MODEL_DIR / "cube" / "cube.obj"
model_entity = GameObject.Spawn(scene, obj_to_import, "RemoveCube", rootEntity, util.scale(0.2))
modelsList.append(model_entity)

insertCube_entity = GameObject.Spawn(scene, obj_to_import, "InsertCube", rootEntity, util.scale(0.2)@util.translate(5,5,-5))
modelsList.append(insertCube_entity)

insertCollider_entity = GameObject.Spawn(scene, obj_to_import, "InsertCollider", rootEntity, util.scale(0.2,0.05,0.2)@util.translate(5,0,-5))
modelsList.append(insertCollider_entity)

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

#index arrays for above vertex Arrays
index = np.array((0,1,2), np.uint32) #simple triangle


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

insertPerf = False
removePerf = False

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
insertCube_entity.initialize_gl(Lposition, Lcolor, Lintensity)
insertCollider_entity.initialize_gl(Lposition, Lcolor, Lintensity)

def CheckBoxGUI():
    global insertPerf
    global removePerf
    imgui.begin("Actions")

    if imgui.checkbox("Insert Action", insertPerf)[0]:
        insertPerf = not insertPerf

    if imgui.checkbox("Remove Action", removePerf)[0]:
        removePerf = not removePerf

    imgui.end()

def RemoveActionPerformGUI():
    global removePerf
    removePerf = True

def InsertActionPerformGUI():
    global insertPerf
    insertPerf = True

# ----Behavior setup-----
# ------INSERT ACTION------
insertColliderComponent = InsertCollider("InsertCollider", "insertCollider", 45, GameObject.Find("InsertCollider"))
scene.world.addComponent(GameObject.Find("InsertCube"), insertColliderComponent)
insertAction = InsertAction("insertAction", "InsertAction", "003", InsertActionPerformGUI)

# ------Remove ACTION------
removeComponent = RemoveComponent("RemoveComponent", "removeComponent", 0.2)
scene.world.addComponent(GameObject.Find("RemoveCube"), removeComponent)
removeAction = RemoveAction("removeAction", "RemoveAction", "004", RemoveActionPerformGUI)
# ----------------------


while running:
    running = scene.render()
    displayGUI_text(example_description)
    scene.world.traverse_visit(renderUpdate, scene.world.root)
    scene.world.traverse_visit_pre_camera(camUpdate, orthoCam)
    scene.world.traverse_visit(camUpdate, scene.world.root)
    scene.world.traverse_visit(transUpdate, scene.world.root)

    # Behavior systems
    scene.world.traverse_visit(insertAction, scene.world.root)
    scene.world.traverse_visit(removeAction, scene.world.root)

    view =  gWindow._myCamera # updates view via the imgui
    light_shader_decorator.setUniformVariable(key="modelViewProj", value= projMat @ view @ (util.translate(Lposition[0], Lposition[1], Lposition[2]) @ util.scale(0.05, 0.05, 0.05)), mat4=True)
    mvp_terrain = projMat @ view @ terrain_trans.trs
    terrain_shader.setUniformVariable(key='modelViewProj', value=mvp_terrain, mat4=True)
    CheckBoxGUI()

    for model in modelsList:
        # Set Object Real Time Shader Data
        for mesh_entity in model.mesh_entities:
            # --- Set vertex shader data ---
            mesh_entity.shader_decorator_component.setUniformVariable(key='projection', value=projMat, mat4=True)
            mesh_entity.shader_decorator_component.setUniformVariable(key='view', value=view, mat4=True)
            mesh_entity.shader_decorator_component.setUniformVariable(key='model', value=mesh_entity.transform_component.l2world, mat4=True)
            # Calculate normal matrix
            normalMatrix = np.transpose(util.inverse(mesh_entity.transform_component.l2world))
            mesh_entity.shader_decorator_component.setUniformVariable(key='normalMatrix', value=normalMatrix, mat4=True)

            # --- Set fragment shader data ---
            # Camera position
            mesh_entity.shader_decorator_component.setUniformVariable(key='camPos', value=eye, float3=True)

    scene.render_post()
    
scene.shutdown()
