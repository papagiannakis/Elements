from __future__ import annotations

import imgui
from scipy.spatial.transform import Rotation

from Elements.utils.ChatGPT import GPTBot
from Elements.pyGLV.GL.GameObject import GameObject
from Elements.pyGLV.GUI.Viewer import RenderGLStateSystem, ImGUIecssDecorator
from Elements.utils.SizeCalculation import calc_size
from Elements.definitions import MODEL_DIR


##########################################################
#                   EXAMPLE USAGE                        #
##########################################################
# This example provides functionality to use ChatGPT to  #
# in order to make real-time changes to the objects in   #
# the scene.                                             #
# By typing your prompt in the imgui user interface,     #
# you can configure the scene,                           #
# i.e "Move the cauterizer exactly on top of the table"  #
##########################################################

widgets_basic_str0 = "Hey you, type something here!"
latest = widgets_basic_str0
n = 0
changed = False
bot = GPTBot()


def displayGUI():
    global widgets_basic_str0
    global latest
    global n
    global changed
    imgui.begin("CHATGPT Input")
    changed, widgets_basic_str0 = imgui.input_text(label="input text", value=widgets_basic_str0, buffer_length=400,
                                                   flags=imgui.INPUT_TEXT_ENTER_RETURNS_TRUE)
    imgui.set_item_default_focus()
    imgui.text("How many commands have you typed: " + str(n))
    if changed:
        n += 1
        latest = widgets_basic_str0
        bot.apicall(latest)
        widgets_basic_str0 = ''
    imgui.text("This is what you last typed: " + str(latest.upper()))
    imgui.end()


def main(imguiFlag=False):
    import os
    import numpy as np

    import Elements.pyECSS.math_utilities as util
    from Elements.pyECSS.Entity import Entity
    from Elements.pyECSS.Component import BasicTransform, Camera, RenderMesh
    from Elements.pyECSS.System import TransformSystem, CameraSystem
    from Elements.pyGLV.GL.Scene import Scene

    from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
    from Elements.pyGLV.GL.VertexArray import VertexArray

    from OpenGL.GL import GL_LINES
    import OpenGL.GL as gl

    from Elements.utils.terrain import generateTerrain



    scene = Scene()

    # Scenegraph with Entities, Components
    rootEntity = scene.world.createEntity(Entity(name="RooT"))
    entityCam1 = scene.world.createEntity(Entity(name="Entity1"))
    scene.world.addEntityChild(rootEntity, entityCam1)

    eye = util.vec(1, 0.54, 1.0)
    target = util.vec(0.02, 0.14, 0.217)
    up = util.vec(0.0, 1.0, 0.0)
    view = util.lookat(eye, target, up)
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
    shaders = []
    # --------ToolsTable--------
    obj_to_import = MODEL_DIR / "ToolsTable" / "ToolsTable.obj"
    shadertoolstable = GameObject.Spawn(scene, obj_to_import, "ToolsTable", rootEntity,
                                        util.rotate((0.0, 1.0, 0.0), 0),
                                        )
    width, height, depth = calc_size(obj_to_import)
    bot.scenegraph["tools_table"] = {'width': width, 'height': height, 'depth': depth, "position": [0, 0, 0],
                                     "rotation": [0, 0, 0]}
    shaders.append(shadertoolstable)
    # -------Cauterizer-------------
    obj_to_import = MODEL_DIR / "Scalpel" / "Scalpel.obj"
    shaderscalp = GameObject.Spawn(scene, obj_to_import, "Scalpel", rootEntity, util.translate(0, 0, 0.0))
    width, height, depth = calc_size(obj_to_import)
    bot.scenegraph["scalpel"] = {'width': width, 'height': height, 'depth': depth, "position": [0, 0, 0],
                                    "rotation": [0, 0, 0]}
    shaders.append(shaderscalp)

    vertexTerrain, indexTerrain, colorTerrain = generateTerrain(size=4, N=20)
    # Add terrain
    terrain = scene.world.createEntity(Entity(name="terrain"))
    scene.world.addEntityChild(rootEntity, terrain)
    terrain_trans = scene.world.addComponent(terrain, BasicTransform(name="terrain_trans",
                                                                     trs=util.identity() @ util.translate(0.0, -0.8,
                                                                                                          0.0)))
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

    projMat = util.perspective(50.0, 1200 / 800, 0.01, 100.0)

    gWindow._myCamera = view  # otherwise, an imgui slider must be moved to properly update

    Lposition = util.vec(-1, 1.5, 1.2)  # uniform lightpos
    Lambientcolor = util.vec(1.0, 1.0, 1.0)  # uniform ambient color
    Lcolor = util.vec(1.0, 1.0, 1.0)
    Lintensity = 40.0
    for shader in shaders:
        shader.initialize_gl(Lposition, Lcolor, Lintensity)
    while running:
        running = scene.render()
        displayGUI()
        scene.world.traverse_visit(renderUpdate, scene.world.root)
        scene.world.traverse_visit_pre_camera(camUpdate, orthoCam)
        scene.world.traverse_visit(camUpdate, scene.world.root)
        view = gWindow._myCamera  # updates view via the imgui
        # mvp_table = projMat @ view @ medicaltabletrs  # @ util.scale(0.1, 0.1, 0.1)
        # mvp_cauterizer = projMat @ view @ cauterizertrs
        scene.world._viewProj = projMat @ view

        view = gWindow._myCamera  # updates view via the imgui
        mvp_terrain = projMat @ view @ terrain_trans.trs
        terrain_shader.setUniformVariable(key='modelViewProj', value=mvp_terrain, mat4=True)
        for shader in shaders:
            model_cube = shader.transform_component.trs
            # model_cube = util.translate(0, 0, 0)
            shader.mesh_entities[0].shader_decorator_component.setUniformVariable(key='model', value=model_cube, mat4=True)
            shader.mesh_entities[0].shader_decorator_component.setUniformVariable(key='view', value=view, mat4=True)
            shader.mesh_entities[0].shader_decorator_component.setUniformVariable(key='projection', value=projMat, mat4=True)
            normalMatrix = np.transpose(util.inverse(model_cube))
            shader.mesh_entities[0].shader_decorator_component.setUniformVariable(key='normalMatrix', value=normalMatrix, mat4=True)
            shader.mesh_entities[0].shader_decorator_component.setUniformVariable(key='camPos', value=eye, float3=True)
        scene.render_post()
        if changed:

            if "tools_table" in bot.scenegraph:
                r = Rotation.from_euler("xyz", bot.scenegraph['tools_table']['rotation'], degrees=True)
                newr = np.zeros((4, 4))
                newr[:3, :3] = r.as_matrix()
                newr[3, 3] = 1
                medicaltabletrs = util.translate(bot.scenegraph['tools_table']['position'][0],
                                                 bot.scenegraph['tools_table']['position'][1],
                                                 bot.scenegraph['tools_table']['position'][2]) @ newr
                GameObject.Find("ToolsTable").getChildByType(BasicTransform.getClassName()).trs = medicaltabletrs
            if "cauterizer" in bot.scenegraph:
                r = Rotation.from_euler("xyz", bot.scenegraph['cauterizer']['rotation'], degrees=True)
                newr = np.zeros((4, 4))
                newr[:3, :3] = r.as_matrix()
                newr[3, 3] = 1
                cauterizertrs = util.translate(bot.scenegraph['cauterizer']['position'][0],
                                               bot.scenegraph['cauterizer']['position'][1],
                                               bot.scenegraph['cauterizer']['position'][2]) @ newr
                GameObject.Find("Cauterizer").getChildByType(BasicTransform.getClassName()).trs = cauterizertrs

    scene.shutdown()


if __name__ == "__main__":
    main(imguiFlag=True)
