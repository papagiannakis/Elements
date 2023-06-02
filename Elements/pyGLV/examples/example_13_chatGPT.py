from __future__ import annotations
import imgui
import numpy as np
from scipy.spatial.transform import Rotation

import Elements.pyECSS.utilities as util
from ChatGPT import GPTBot
from Elements.pyGLV.GL.GameObject import GameObject
from SizeCalculation import calc_size
from Elements.pyECSS.Component import BasicTransform, RenderMesh
from Elements.pyECSS.Entity import Entity
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GL.Shader import Shader, ShaderGLDecorator
from Elements.pyGLV.GL.VertexArray import VertexArray
from Elements.pyGLV.GUI.Viewer import RenderGLStateSystem, ImGUIecssDecorator


class IndexedConverter():

    # Assumes triangulated buffers. Produces indexed results that support
    # normals as well.
    def Convert(self, vertices, colors, indices, produceNormals=True):

        iVertices = []
        iColors = []
        iNormals = []
        iIndices = []
        for i in range(0, len(indices), 3):
            iVertices.append(vertices[indices[i]])
            iVertices.append(vertices[indices[i + 1]])
            iVertices.append(vertices[indices[i + 2]])
            iColors.append(colors[indices[i]])
            iColors.append(colors[indices[i + 1]])
            iColors.append(colors[indices[i + 2]])

            iIndices.append(i)
            iIndices.append(i + 1)
            iIndices.append(i + 2)

        if produceNormals:
            for i in range(0, len(indices), 3):
                iNormals.append(
                    util.calculateNormals(vertices[indices[i]], vertices[indices[i + 1]], vertices[indices[i + 2]]))
                iNormals.append(
                    util.calculateNormals(vertices[indices[i]], vertices[indices[i + 1]], vertices[indices[i + 2]]))
                iNormals.append(
                    util.calculateNormals(vertices[indices[i]], vertices[indices[i + 1]], vertices[indices[i + 2]]))

        iVertices = np.array(iVertices, dtype=np.float32)
        iColors = np.array(iColors, dtype=np.float32)
        iIndices = np.array(iIndices, dtype=np.uint32)

        iNormals = np.array(iNormals, dtype=np.float32)

        return iVertices, iColors, iIndices, iNormals


class GameObjectEntity(Entity):
    def __init__(self, name=None, type=None, id=None) -> None:
        super().__init__(name, type, id)

        # Gameobject basic properties
        self._color = [1, 0.5, 0.2, 1.0]  # this will be used as a uniform var
        # Create basic components of a primitive object
        self.trans = BasicTransform(name="trans", trs=util.identity())
        self.mesh = RenderMesh(name="mesh")
        # self.shaderDec      = ShaderGLDecorator(Shader(vertex_source=Shader.VERT_PHONG_MVP, fragment_source=Shader.FRAG_PHONG));
        self.shaderDec = ShaderGLDecorator(
            Shader(vertex_source=Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG))
        self.vArray = VertexArray()
        # Add components to entity
        scene = Scene()
        scene.world.createEntity(self)
        scene.world.addComponent(self, self.trans)
        scene.world.addComponent(self, self.mesh)
        scene.world.addComponent(self, self.shaderDec)
        scene.world.addComponent(self, self.vArray)

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, colorArray):
        self._color = colorArray

    def drawSelfGui(self, imgui):
        changed, value = imgui.color_edit3("Color", self.color[0], self.color[1], self.color[2])
        self.color = [value[0], value[1], value[2], 1.0]

    def SetVertexAttributes(self, vertex, color, index, normals=None):
        self.mesh.vertex_attributes.append(vertex)
        self.mesh.vertex_attributes.append(color)
        if normals is not None:
            self.mesh.vertex_attributes.append(normals)
        self.mesh.vertex_index.append(index)


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

    import Elements.pyECSS.utilities as util
    from Elements.pyECSS.Entity import Entity
    from Elements.pyECSS.Component import BasicTransform, Camera, RenderMesh
    from Elements.pyECSS.System import TransformSystem, CameraSystem
    from Elements.pyGLV.GL.Scene import Scene

    from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
    from Elements.pyGLV.GL.VertexArray import VertexArray

    from OpenGL.GL import GL_LINES
    import OpenGL.GL as gl

    from Elements.pyGLV.utils.terrain import generateTerrain

    ## object load
    dirname = os.path.dirname(__file__)

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
    shaders = []
    # --------ToolsTable--------
    obj_to_import = os.path.join(dirname, "models/ToolsTable", "ToolsTable.obj")
    tex_to_import = os.path.join(dirname, "models/ToolsTable", "Cloth-TOOLtable_LOW_Material__126_AlbedoTransparency"
                                                               ".png")
    shadertoolstable = GameObject.Spawn(scene, obj_to_import, "ToolsTable", rootEntity,
                                        util.rotate((0.0, 1.0, 0.0), 0),
                                        tex_to_import)
    width, height, depth = calc_size(obj_to_import)
    bot.scenegraph["tools_table"] = {'width': width, 'height': height, 'depth': depth, "position": [0, 0, 0],
                                     "rotation": [0, 0, 0]}
    shaders.append(shadertoolstable)
    # -------Cauterizer-------------
    obj_to_import = os.path.join(dirname, "models/Scalpel", "Scalpel.obj")
    tex_to_import = os.path.join(dirname, "models/Scalpel", "scalpel NEW 01B_LOW_Material _128_AlbedoTransparency.png")
    shaderscalp = GameObject.Spawn(scene, obj_to_import, "Scalpel", rootEntity, util.translate(0, 0, 0.0), tex_to_import)
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

    ## ADD AXES ##
    axes = scene.world.createEntity(Entity(name="axes"))
    scene.world.addEntityChild(rootEntity, axes)
    axes_trans = scene.world.addComponent(axes, BasicTransform(name="axes_trans",
                                                               trs=util.translate(0.0, 0.001, 0.0)))  # util.identity()
    # Colored Axes
    vertexAxes = np.array([
        [0.0, 0.0, 0.0, 1.0],
        [1.5, 0.0, 0.0, 1.0],
        [0.0, 0.0, 0.0, 1.0],
        [0.0, 1.5, 0.0, 1.0],
        [0.0, 0.0, 0.0, 1.0],
        [0.0, 0.0, 1.5, 1.0]
    ], dtype=np.float32)
    colorAxes = np.array([
        [1.0, 0.0, 0.0, 1.0],
        [1.0, 0.0, 0.0, 1.0],
        [0.0, 1.0, 0.0, 1.0],
        [0.0, 1.0, 0.0, 1.0],
        [0.0, 0.0, 1.0, 1.0],
        [0.0, 0.0, 1.0, 1.0]
    ], dtype=np.float32)

    # index arrays for above vertex Arrays
    indexAxes = np.array((0, 1, 2, 3, 4, 5), np.uint32)  # 3 simple colored Axes as R,G,B lines
    axes_mesh = scene.world.addComponent(axes, RenderMesh(name="axes_mesh"))
    axes_mesh.vertex_attributes.append(vertexAxes)
    axes_mesh.vertex_attributes.append(colorAxes)
    axes_mesh.vertex_index.append(indexAxes)
    scene.world.addComponent(axes, VertexArray(primitive=gl.GL_LINES))  # note the primitive change

    # shaderDec_axes = scene.world.addComponent(axes, Shader())
    # OR
    axes_shader = scene.world.addComponent(axes, ShaderGLDecorator(
        Shader(vertex_source=Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))

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
        mvp_axes = projMat @ view @ axes_trans.trs

        axes_shader.setUniformVariable(key='modelViewProj', value=mvp_axes, mat4=True)
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
