from __future__ import annotations
import sys
sys.path.append("../../../")
import numpy as np
import Elements.pyECSS.utilities as util
from Elements.pyGLV.GL.GameObject import GameObject
from Elements.pyECSS.Component import BasicTransform, RenderMesh
from Elements.pyECSS.Entity import Entity
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GL.Shader import Shader, ShaderGLDecorator
from Elements.pyGLV.GL.VertexArray import VertexArray

import numpy as np

import Elements.pyECSS.utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, RenderMesh, Camera
from Elements.pyECSS.System import TransformSystem, CameraSystem
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GUI.Viewer import RenderGLStateSystem

from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray

from OpenGL.GL import GL_LINES


def CreateRoomScene(visualize=False):
    scene = Scene()

    # Scenegraph with Entities, Components
    rootEntity = scene.world.createEntity(Entity(name="RooT"))
    entityCam1 = scene.world.createEntity(Entity(name="entityCam1"))
    scene.world.addEntityChild(rootEntity, entityCam1)
    trans1 = scene.world.addComponent(entityCam1, BasicTransform(name="trans1", trs=util.identity()))

    entityCam2 = scene.world.createEntity(Entity(name="entityCam2"))
    scene.world.addEntityChild(entityCam1, entityCam2)
    trans2 = scene.world.addComponent(entityCam2, BasicTransform(name="trans2", trs=util.identity()))
    orthoCam = scene.world.addComponent(entityCam2,
                                        Camera(util.ortho(-100.0, 100.0, -100.0, 100.0, 1.0, 100.0), "orthoCam",
                                               "Camera",
                                               "500"))



    # Systems
    transUpdate = scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
    camUpdate = scene.world.createSystem(CameraSystem("camUpdate", "CameraUpdate", "200"))
    renderUpdate = scene.world.createSystem(RenderGLShaderSystem())
    initUpdate = scene.world.createSystem(InitGLShaderSystem())
    shaders = []
    obj_to_import = "models/LivingRoom/Chair/Chair.obj"
    shaderchair = GameObject.Spawn(scene, obj_to_import, "Chair", rootEntity, util.translate(-0.2, 0, 0) @ util.scale(0.1) @ util.rotate((0, 1, 0), 0),
                                      )
    shaders.append(shaderchair)

    obj_to_import = "models/LivingRoom/Lamp/Lamp.obj"
    shaderlamp = GameObject.Spawn(scene, obj_to_import, "Lamp", rootEntity,  util.translate(-0.4, 0, 0.5) @ util.scale(0.1),
                                      )
    shaders.append(shaderlamp)
    
    obj_to_import = "models/LivingRoom/Sofa/Sofa.obj"
    shadersofa = GameObject.Spawn(scene, obj_to_import, "Sofa", rootEntity, util.translate(0.2, 0, 0) @ util.scale(0.1) @ util.rotate((0, 1, 0), -90),
                                      )
    shaders.append(shadersofa)

    obj_to_import = "models/LivingRoom/Sofa2/Sofa2.obj"
    shadersofa2 = GameObject.Spawn(scene, obj_to_import, "Sofa2", rootEntity,  util.translate(0, 0, 0.5) @ util.scale(0.1) @ util.rotate((0, 1, 0), 0),
                                      )
    shaders.append(shadersofa2)

   
    obj_to_import = "models/LivingRoom/Table/Table.obj"
    shadertable = GameObject.Spawn(scene, obj_to_import, "Table", rootEntity,  util.translate(0, 0, 0) @ util.scale(0.1),
                                      )
    shaders.append(shadertable)
    
    obj_to_import = "models/LivingRoom/TV/TV.obj"
    shaderTV = GameObject.Spawn(scene, obj_to_import, "TV", rootEntity, util.translate(-0.1, 0, -0.3) @ util.scale(0.1) @ util.rotate((0, 1, 0), 90),
                                      )
    shaders.append(shaderTV)
   

    # Generate terrain
    from Elements.pyGLV.utils.terrain import generateTerrain

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
    terrain_shader = scene.world.addComponent(terrain, ShaderGLDecorator(
        Shader(vertex_source=Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))
    # terrain_shader.setUniformVariable(key='modelViewProj', value=mvpMat, mat4=True)

    # MAIN RENDERING LOOP

    running = True
    scene.init(imgui=True, windowWidth=1024, windowHeight=768, windowTitle="Elements: Textures example",
               openGLversion=4)

    # pre-pass scenegraph to initialise all GL context dependent geometry, shader classes
    # needs an active GL context
    scene.world.traverse_visit(initUpdate, scene.world.root)

    ################### EVENT MANAGER ###################

    eManager = scene.world.eventManager
    gWindow = scene.renderWindow
    gGUI = scene.gContext

    renderGLEventActuator = RenderGLStateSystem()
    transUpdate = scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
    camUpdate = scene.world.createSystem(CameraSystem("camUpdate", "CameraUpdate", "200"))
    renderUpdate = scene.world.createSystem(RenderGLShaderSystem())
    initUpdate = scene.world.createSystem(InitGLShaderSystem())
    eManager._subscribers['OnUpdateWireframe'] = gWindow
    eManager._actuators['OnUpdateWireframe'] = renderGLEventActuator
    eManager._subscribers['OnUpdateCamera'] = gWindow
    eManager._actuators['OnUpdateCamera'] = renderGLEventActuator

    eManager._subscribers['OnUpdateWireframe'] = gWindow
    eManager._actuators['OnUpdateWireframe'] = renderGLEventActuator

    # START
    eManager._subscribers['OnUpdateCamera'] = gWindow
    eManager._actuators['OnUpdateCamera'] = renderGLEventActuator
    # END



    eye = util.vec(1.5, 1.5, 1.5)
    target = util.vec(0.0, 0.0, 0.0)
    up = util.vec(0.0, 1.0, 0.0)
    view = util.lookat(eye, target, up)
    # projMat = util.ortho(-10.0, 10.0, -10.0, 10.0, -1.0, 10.0)
    # projMat = util.perspective(90.0, 1.33, 0.1, 100)
    projMat = util.perspective(50.0, 1.0, 0.01, 10.0)

    

    gWindow._myCamera = view  # otherwise, an imgui slider must be moved to properly update

    

    model_terrain_axes = terrain.getChild(0).trs  # notice that terrain.getChild(0) == terrain_trans

    Lposition = util.vec(-1, 1.5, 1.2)  # uniform lightpos
    Lambientcolor = util.vec(1.0, 1.0, 1.0)  # uniform ambient color
    Lcolor = util.vec(1.0, 1.0, 1.0)
    Lintensity = 40.0
    for shader in shaders:
        shader.initialize_gl(Lposition, Lcolor, Lintensity)
   
    if visualize:
        while running:
            running = scene.render()
            scene.world.traverse_visit(renderUpdate, scene.world.root)
            scene.world.traverse_visit_pre_camera(camUpdate, orthoCam)
            scene.world.traverse_visit(camUpdate, scene.world.root)
            view = gWindow._myCamera  # updates view via the imgui
            mvp_terrain_axes = projMat @ view @ model_terrain_axes
            terrain_shader.setUniformVariable(key='modelViewProj', value=mvp_terrain_axes, mat4=True)
            for shader in shaders:
                model_cube = shader.transform_component.trs
                for i in range(len(shader.mesh_entities)):
                    shader.mesh_entities[i].shader_decorator_component.setUniformVariable(key='model', value=model_cube, mat4=True)
                    shader.mesh_entities[i].shader_decorator_component.setUniformVariable(key='view', value=view, mat4=True)
                    shader.mesh_entities[i].shader_decorator_component.setUniformVariable(key='projection', value=projMat, mat4=True)
                    normalMatrix = np.transpose(util.inverse(model_cube))
                    shader.mesh_entities[i].shader_decorator_component.setUniformVariable(key='normalMatrix', value=normalMatrix, mat4=True)
                    shader.mesh_entities[i].shader_decorator_component.setUniformVariable(key='camPos', value=eye, float3=True)
            scene.render_post()

    scene.shutdown()
    return scene



def CreateORScene(visualize=False):
    scene = Scene()

    # Scenegraph with Entities, Components
    rootEntity = scene.world.createEntity(Entity(name="RooT"))
    entityCam1 = scene.world.createEntity(Entity(name="entityCam1"))
    scene.world.addEntityChild(rootEntity, entityCam1)
    trans1 = scene.world.addComponent(entityCam1, BasicTransform(name="trans1", trs=util.identity()))

    entityCam2 = scene.world.createEntity(Entity(name="entityCam2"))
    scene.world.addEntityChild(entityCam1, entityCam2)
    trans2 = scene.world.addComponent(entityCam2, BasicTransform(name="trans2", trs=util.identity()))
    orthoCam = scene.world.addComponent(entityCam2,
                                        Camera(util.ortho(-100.0, 100.0, -100.0, 100.0, 1.0, 100.0), "orthoCam",
                                               "Camera",
                                               "500"))


    # Systems
    transUpdate = scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
    camUpdate = scene.world.createSystem(CameraSystem("camUpdate", "CameraUpdate", "200"))
    renderUpdate = scene.world.createSystem(RenderGLShaderSystem())
    initUpdate = scene.world.createSystem(InitGLShaderSystem())
    shaders = []
    obj_to_import = "models/ToolsTable/ToolsTable.obj"
    shaderToolsTable = GameObject.Spawn(scene, obj_to_import, "ToolsTable", rootEntity, util.translate(0, 0, 0),
                                      )
    shaders.append(shaderToolsTable)

    obj_to_import = "models/Scalpel/Scalpel.obj"
    shaderscalpel = GameObject.Spawn(scene, obj_to_import, "Scalpel", rootEntity, util.translate(0, 0.5, 0),
                                      )
    shaders.append(shaderscalpel)
    
    obj_to_import = "models/Cauterizer/Cauterizer.obj"
    shadercauterizer = GameObject.Spawn(scene, obj_to_import, "Cauterizer", rootEntity, util.translate(0.3, 0.5, 0),
                                      )
    shaders.append(shadercauterizer)

    obj_to_import = "models/ImplantsTable/ImplantsTable.obj"
    shaderimplants = GameObject.Spawn(scene, obj_to_import, "ImplantsTable", rootEntity,  util.translate(1, 0, 0),
                                      )
    shaders.append(shaderimplants)

   
    obj_to_import = "models/Anesthesia/Anesthesia.obj"
    shaderanesthesia = GameObject.Spawn(scene, obj_to_import, "Anesthesia", rootEntity,  util.translate(-1, 0, 0) @ util.rotate((0, 1, 0), 0),
                                      )
    shaders.append(shaderanesthesia)
    


    # Generate terrain
    from Elements.pyGLV.utils.terrain import generateTerrain

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
    terrain_shader = scene.world.addComponent(terrain, ShaderGLDecorator(
        Shader(vertex_source=Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))
    # terrain_shader.setUniformVariable(key='modelViewProj', value=mvpMat, mat4=True)


    # MAIN RENDERING LOOP

    running = True
    scene.init(imgui=True, windowWidth=1024, windowHeight=768, windowTitle="Elements: Textures example",
               openGLversion=4)

    # pre-pass scenegraph to initialise all GL context dependent geometry, shader classes
    # needs an active GL context
    scene.world.traverse_visit(initUpdate, scene.world.root)

    ################### EVENT MANAGER ###################

    eManager = scene.world.eventManager
    gWindow = scene.renderWindow
    gGUI = scene.gContext

    renderGLEventActuator = RenderGLStateSystem()
    transUpdate = scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
    camUpdate = scene.world.createSystem(CameraSystem("camUpdate", "CameraUpdate", "200"))
    renderUpdate = scene.world.createSystem(RenderGLShaderSystem())
    initUpdate = scene.world.createSystem(InitGLShaderSystem())
    eManager._subscribers['OnUpdateWireframe'] = gWindow
    eManager._actuators['OnUpdateWireframe'] = renderGLEventActuator
    eManager._subscribers['OnUpdateCamera'] = gWindow
    eManager._actuators['OnUpdateCamera'] = renderGLEventActuator

    eManager._subscribers['OnUpdateWireframe'] = gWindow
    eManager._actuators['OnUpdateWireframe'] = renderGLEventActuator

    # START
    eManager._subscribers['OnUpdateCamera'] = gWindow
    eManager._actuators['OnUpdateCamera'] = renderGLEventActuator
    # END

    # Add RenderWindow to the EventManager publishers

    eye = util.vec(2.5, 2.5, 2.5)
    target = util.vec(0.0, 0.0, 0.0)
    up = util.vec(0.0, 1.0, 0.0)
    view = util.lookat(eye, target, up)

    projMat = util.perspective(50.0, 1.0, 0.01, 10.0)

    gWindow._myCamera = view  # otherwise, an imgui slider must be moved to properly update


    model_terrain_axes = terrain.getChild(0).trs  # notice that terrain.getChild(0) == terrain_trans
    Lposition = util.vec(-1, 1.5, 1.2)  # uniform lightpos
    Lambientcolor = util.vec(1.0, 1.0, 1.0)  # uniform ambient color
    Lcolor = util.vec(1.0, 1.0, 1.0)
    Lintensity = 40.0
    for shader in shaders:
        shader.initialize_gl(Lposition, Lcolor, Lintensity)
    if visualize:
        while running:
            running = scene.render()
            scene.world.traverse_visit(renderUpdate, scene.world.root)
            scene.world.traverse_visit_pre_camera(camUpdate, orthoCam)
            scene.world.traverse_visit(camUpdate, scene.world.root)
            view = gWindow._myCamera  # updates view via the imgui
            mvp_terrain_axes = projMat @ view @ model_terrain_axes
            terrain_shader.setUniformVariable(key='modelViewProj', value=mvp_terrain_axes, mat4=True)
            for shader in shaders:
                model_cube = shader.transform_component.trs
                for i in range(len(shader.mesh_entities)):
                    shader.mesh_entities[i].shader_decorator_component.setUniformVariable(key='model', value=model_cube, mat4=True)
                    shader.mesh_entities[i].shader_decorator_component.setUniformVariable(key='view', value=view, mat4=True)
                    shader.mesh_entities[i].shader_decorator_component.setUniformVariable(key='projection', value=projMat, mat4=True)
                    normalMatrix = np.transpose(util.inverse(model_cube))
                    shader.mesh_entities[i].shader_decorator_component.setUniformVariable(key='normalMatrix', value=normalMatrix, mat4=True)
                    shader.mesh_entities[i].shader_decorator_component.setUniformVariable(key='camPos', value=eye, float3=True)
            scene.render_post()

    scene.shutdown()
    return scene



insertPerf = True
removePerf = False
allShaders = []
USD_input_filepath = "PathToScene.usd"
def CreatePaperScene(visualize=False):
    import imgui
    from Elements.pyGLV.GUI.Viewer import ImGUIecssDecorator
    from Elements.pyGLV.GL.UsdImporter import LoadScene, SaveScene
    from Elements.pyGLV.utils.terrain import generateTerrain
    from Elements.pyGLV.GL.ActionSystems import InsertAction, InsertCollider, RemoveAction, RemoveComponent
    import OpenGL.GL as gl


    def SceneGUI(scene, initUpdate, textures):
        global USD_input_filepath
        global allShaders
        imgui.begin("Scene")

        changed, USD_input_filepath = imgui.input_text(label="filepath", buffer_length=400,
                                                   flags=imgui.INPUT_TEXT_ENTER_RETURNS_TRUE, value=USD_input_filepath)
        if imgui.button('Save Current Scene'):
            SaveScene(scene, USD_input_filepath)
            print('Scene was saved successfully.')

        if imgui.button('Load USD Scene'):
            allShaders = LoadScene(scene, USD_input_filepath)
            scene.world.traverse_visit(initUpdate, scene.world.root)
        imgui.end()
        return scene


    

    def CheckBoxGUI():
        global insertPerf
        global removePerf
        imgui.begin("Actions")
        # print(imgui.checkbox("Insert Action", insertPerf))
        if imgui.checkbox("Insert Action", insertPerf)[0]:
            insertPerf = not insertPerf
        if imgui.checkbox("Remove Action", removePerf)[0]:
            removePerf = not removePerf
        imgui.end()




    scene = Scene()

    # Scenegraph with Entities, Components
    rootEntity = scene.world.createEntity(Entity(name="RooT"))
    entityCam1 = scene.world.createEntity(Entity(name="Entity1"))
    scene.world.addEntityChild(rootEntity, entityCam1)

    eye = util.vec(1, 0.54, 1.0)
    target = util.vec(0.02, 0.14, 0.217)
    up = util.vec(0.0, 1.0, 0.0)
    view = util.lookat(eye, target, up)
    # projMat = util.ortho(-10.0, 10.0, -10.0, 10.0, -1.0, 10.0)
    # projMat = util.perspective(90.0, 1.33, 0.1, 100)
    projMat = util.perspective(50.0, 1.0, 1.0, 10.0)

    m = np.linalg.inv(projMat @ view)

    entityCam2 = scene.world.createEntity(Entity(name="Entity_Camera"))
    scene.world.addEntityChild(entityCam1, entityCam2)
    # orthoCam = scene.world.addComponent(entityCam2, Camera(util.ortho(-100.0, 100.0, -100.0, 100.0, 1.0, 100.0), "orthoCam","Camera","500"))
    orthoCam = scene.world.addComponent(entityCam2, Camera(m, "orthoCam", "Camera", "500"))

    # Systems
    transUpdate = scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
    camUpdate = scene.world.createSystem(CameraSystem("camUpdate", "CameraUpdate", "200"))
    renderUpdate = scene.world.createSystem(RenderGLShaderSystem())
    initUpdate = scene.world.createSystem(InitGLShaderSystem())
    # updateUniVals = scene.world.createSystem(UpdateUniformValuesSystem())
    
    vertexTerrain, indexTerrain, colorTerrain = generateTerrain(size=4, N=20)
    # Add terrain
    terrain = scene.world.createEntity(Entity(name="terrain"))
    scene.world.addEntityChild(rootEntity, terrain)
    terrain_trans = scene.world.addComponent(terrain, BasicTransform(name="terrain_trans",
                                                                    trs=util.identity() @ util.translate(0.0, -0.8, 0.0)))
    terrain_mesh = scene.world.addComponent(terrain, RenderMesh(name="terrain_mesh"))
    terrain_mesh.vertex_attributes.append(vertexTerrain)
    terrain_mesh.vertex_attributes.append(colorTerrain)
    terrain_mesh.vertex_index.append(indexTerrain)
    terrain_vArray = scene.world.addComponent(terrain, VertexArray(primitive=GL_LINES))
    terrain_shader = scene.world.addComponent(terrain, ShaderGLDecorator(
        Shader(vertex_source=Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))
    # terrain_shader.setUniformVariable(key='modelViewProj', value=mvpMat, mat4=True)

    running = True
    scene.init(imgui=True, windowWidth=1200, windowHeight=800, windowTitle="Elements: Tea anyone?", openGLversion=4,
            customImGUIdecorator=ImGUIecssDecorator)

    # pre-pass scenegraph to initialise all GL context dependent geometry, shader classes
    # needs an active GL context
    scene.world.traverse_visit(initUpdate, scene.world.root)

    ################### EVENT MANAGER ###################

    eManager = scene.world.eventManager
    gWindow = scene.renderWindow

    renderGLEventActuator = RenderGLStateSystem()

    eManager._subscribers['OnUpdateWireframe'] = gWindow
    eManager._actuators['OnUpdateWireframe'] = renderGLEventActuator
    eManager._subscribers['OnUpdateCamera'] = gWindow
    eManager._actuators['OnUpdateCamera'] = renderGLEventActuator

    eye = util.vec(2.5, 2.5, 2.5)
    target = util.vec(0.0, 0.0, 0.0)
    up = util.vec(0.0, 1.0, 0.0)
    view = util.lookat(eye, target, up)

    projMat = util.perspective(50.0, 1200 / 800, 0.01, 100.0)

    gWindow._myCamera = view  # otherwise, an imgui slider must be moved to properly update

    # ----Behavior setup-----
    # ------INSERT ACTION------
    insertColliderComponent = InsertCollider("insertCollider", "InsertCollider", 45, GameObject.Find("Hand"))
    scene.world.addComponent(GameObject.Find("BagMask"), insertColliderComponent)
    insertAction = InsertAction("insertAction", "InsertAction", "003")

    # ------Remove ACTION------
    removeComponent = RemoveComponent("removeComponent", "RemoveComponent", 0.2)
    scene.world.addComponent(GameObject.Find("Swab"), removeComponent)
    removeAction = RemoveAction("removeAction", "RemoveAction", "004")
    # ----------------------
    textures = []
    texture = "../models/ToolsTable/Cloth-TOOLtable_LOW_Material__126_AlbedoTransparency.png"
    textures.append(texture)
    texture = "../models/Scalpel/scalpel NEW 01B_LOW_Material _128_AlbedoTransparency.png"
    textures.append(texture)
    texture = "../models/Cauterizer/cauterizer_low_01_Cauterizer_Blue_AlbedoTransparency.png"
    textures.append(texture)
    texture = "../models/Anesthesia/Anaisthesia UVS 02_Material _26_AlbedoTransparency.png"
    textures.append(texture)
    texture = "../models/ImplantsTable/table_with_implants_01_Material _3_AlbedoTransparency.png"
    textures.append(texture)
    texture = "../models/Tray/TrayTexture.png"
    textures.append(texture)
    texture = "../models/Swab/Pliers.png"
    textures.append(texture)
    texture = "../models/BagMask/BagMaskTexture.png"
    textures.append(texture)
    texture = "../models/Hand/HandTexture.png"
    textures.append(texture)
    texture = "../models/ToolsTable/Cloth-TOOLtable_LOW_Material__126_AlbedoTransparency.png"
    textures.append(texture)
    Lposition = util.vec(-1, 1.5, 1.2)  # uniform lightpos
    Lambientcolor = util.vec(1.0, 1.0, 1.0)  # uniform ambient color
    Lcolor = util.vec(1.0, 1.0, 1.0)
    Lintensity = 40.0
    if visualize:
        while running:
            running = scene.render(running)
            scene.world.traverse_visit(renderUpdate, scene.world.root)
            scene.world.traverse_visit_pre_camera(camUpdate, orthoCam)
            scene.world.traverse_visit(camUpdate, scene.world.root)
            CheckBoxGUI()
            SceneGUI(scene, initUpdate, textures=textures)
            view = gWindow._myCamera  # updates view via the imgui
            mvp_terrain = projMat @ view @ terrain_trans.trs
            terrain_shader.setUniformVariable(key='modelViewProj', value=mvp_terrain, mat4=True)


            # Set Object Real Time Shader Data
            for shader in allShaders:
                model_cube = shader.parent.getChildByType(BasicTransform.getClassName()).trs
                # --- Set vertex shader data ---
                shader.setUniformVariable(key='projection', value=projMat, mat4=True)
                shader.setUniformVariable(key='view', value=view, mat4=True)
                shader.setUniformVariable(key='model', value=model_cube, mat4=True)

                # --- Set fragment shader data ---
                normalMatrix = np.transpose(util.inverse(model_cube))
                shader.setUniformVariable(key='normalMatrix', value=normalMatrix, mat4=True)

                shader.setUniformVariable(key='lightPos', value=Lposition, float3=True)
                shader.setUniformVariable(key='lightColor', value=Lcolor, float3=True)
                shader.setUniformVariable(key='lightIntensity', value=Lintensity, float1=True)
                # Camera position
                shader.setUniformVariable(key='camPos', value=eye, float3=True)
            scene.render_post()
    scene.shutdown()
