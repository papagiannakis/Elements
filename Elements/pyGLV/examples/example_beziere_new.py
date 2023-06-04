import numpy as np

import Elements.pyECSS.utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, RenderMesh
from Elements.pyECSS.System import TransformSystem
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GUI.Viewer import RenderGLStateSystem

from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray

from OpenGL.GL import GL_LINES, GL_POINTS

import imgui

from bezier_curve import generate_bezier_data, xyz_to_vertecies

scene = Scene()

# Scenegraph with Entities, Components
rootEntity = scene.world.createEntity(Entity(name="RooT"))
entityCam1 = scene.world.createEntity(Entity(name="entityCam1"))
scene.world.addEntityChild(rootEntity, entityCam1)
trans1 = scene.world.addComponent(entityCam1, BasicTransform(name="trans1", trs=util.identity()))

entityCam2 = scene.world.createEntity(Entity(name="entityCam2"))
scene.world.addEntityChild(entityCam1, entityCam2)
trans2 = scene.world.addComponent(entityCam2, BasicTransform(name="trans2", trs=util.identity()))
# orthoCam = scene.world.addComponent(entityCam2, Camera(util.ortho(-100.0, 100.0, -100.0, 100.0, 1.0, 100.0), "orthoCam","Camera","500"))

node4 = scene.world.createEntity(Entity(name="node4"))
scene.world.addEntityChild(rootEntity, node4)
trans4 = scene.world.addComponent(node4,
                                  BasicTransform(name="trans4", trs=util.translate(0, 0.5, 0)))  # util.identity()
mesh4 = scene.world.addComponent(node4, RenderMesh(name="mesh4"))

axes = scene.world.createEntity(Entity(name="axes"))
scene.world.addEntityChild(rootEntity, axes)
axes_trans = scene.world.addComponent(axes, BasicTransform(name="axes_trans", trs=util.identity()))
axes_mesh = scene.world.addComponent(axes, RenderMesh(name="axes_mesh"))

all_shader = []


# Colored Axes
vertexAxes = np.array([
    [0.0, 0.0, 0.0, 1.0],
    [1.0, 0.0, 0.0, 1.0],
    [0.0, 0.0, 0.0, 1.0],
    [0.0, 1.0, 0.0, 1.0],
    [0.0, 0.0, 0.0, 1.0],
    [0.0, 0.0, 1.0, 1.0]
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


# Systems
transUpdate = scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
# camUpdate = scene.world.createSystem(CameraSystem("camUpdate", "CameraUpdate", "200"))
renderUpdate = scene.world.createSystem(RenderGLShaderSystem())
initUpdate = scene.world.createSystem(InitGLShaderSystem())

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
all_shader.append(terrain_shader)

## ADD AXES ##
axes = scene.world.createEntity(Entity(name="axes"))
scene.world.addEntityChild(rootEntity, axes)
axes_trans = scene.world.addComponent(axes, BasicTransform(name="axes_trans", trs=util.identity()))
axes_mesh = scene.world.addComponent(axes, RenderMesh(name="axes_mesh"))
axes_mesh.vertex_attributes.append(vertexAxes)
axes_mesh.vertex_attributes.append(colorAxes)
axes_mesh.vertex_index.append(indexAxes)
axes_vArray = scene.world.addComponent(axes, VertexArray(primitive=GL_LINES))  # note the primitive change

axes_shader = scene.world.addComponent(axes, ShaderGLDecorator(
    Shader(vertex_source=Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))
all_shader.append(axes_shader)


input_bezier_control_nodes = [[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]]
FuncValues = [0,1,2,3]
def Bezier_GUI():
    global FuncValues
    # global f_x_y
    # global f_x
    #
    # global superfuncchild2D
    # global superfuncchild3D
    funcDetail = 100
    # global platforms

    global input_bezier_control_nodes
    imgui.begin("Print Bezier Curve")

    imgui.text("Control nodes X, Y, Z")
    for i, control_node in enumerate(input_bezier_control_nodes):
        changed, input_bezier_control_nodes[i] = imgui.input_float3(f"Control Node {i+1}", *control_node)

    button_remove_node_pressed = imgui.button("Remove Node")
    imgui.same_line()
    button_add_node_pressed = imgui.button("Add Node")
    if (button_remove_node_pressed):
        input_bezier_control_nodes.pop()
    if (button_add_node_pressed):
        input_bezier_control_nodes.append([0.0, 0.0, 0.0])

    button_bezier_pressed = imgui.button("Print Bezier")



    imgui.text("Give a to b values for X and c to d for Y")
    changed, FuncValues = imgui.input_float4('', *FuncValues)
    # imgui.same_line()
    imgui.text("a: %.1f, b: %.1f, c: %.1f, d: %.1f" % (FuncValues[0], FuncValues[1], FuncValues[2], FuncValues[3]))
    changed, funcDetail = imgui.input_int('Detailed', funcDetail)
    if imgui.is_item_hovered():
        imgui.set_tooltip("Make sure the detail is between 4 to 100")



    if (button_bezier_pressed):
        input_bezier_control_nodes = np.array(input_bezier_control_nodes)
        vertexBezier, colorBezier, indexBezier = generate_bezier_data(input_bezier_control_nodes, 100, 0, 1)

        ## ADD BEZIER ##
        bezier = scene.world.createEntity(Entity(name="bezier"))
        scene.world.addEntityChild(rootEntity, bezier)
        bezier_trans = scene.world.addComponent(bezier, BasicTransform(name="bezier_trans", trs=util.identity()))
        bezier_mesh = scene.world.addComponent(bezier, RenderMesh(name="bezier_mesh"))
        bezier_mesh.vertex_attributes.append(vertexBezier)
        bezier_mesh.vertex_attributes.append(colorBezier)
        bezier_mesh.vertex_index.append(indexBezier)
        bezier_vArray = scene.world.addComponent(bezier, VertexArray(primitive=GL_LINES))  # note the primitive change

        bezier_shader = scene.world.addComponent(bezier, ShaderGLDecorator(
            Shader(vertex_source=Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))
        all_shader.append(bezier_shader)

        ## VISUALIZE BEZIER CONTROL NODES ##

        vertexControlNodes = xyz_to_vertecies(input_bezier_control_nodes)
        colorControlNodes = np.array([[0.5, 0.5, 1.0, 1.0]] * len(vertexControlNodes), dtype=np.float32)
        indexControlNodes = np.array(range(len(vertexControlNodes)), np.uint32)

        control_nodes = scene.world.createEntity(Entity(name="control_nodes"))
        scene.world.addEntityChild(rootEntity, control_nodes)
        control_nodes_trans = scene.world.addComponent(control_nodes,
                                                       BasicTransform(name="control_nodes_trans", trs=util.identity()))
        control_nodes_mesh = scene.world.addComponent(control_nodes, RenderMesh(name="control_nodes_mesh"))
        control_nodes_mesh.vertex_attributes.append(vertexControlNodes)
        control_nodes_mesh.vertex_attributes.append(colorControlNodes)
        control_nodes_mesh.vertex_index.append(indexControlNodes)
        control_nodes_vArray = scene.world.addComponent(control_nodes, VertexArray(primitive=GL_POINTS))

        # TODO
        # GL POINT SIZE ASK DOMINIK!

        control_nodes_shader = scene.world.addComponent(control_nodes, ShaderGLDecorator(
            Shader(vertex_source=Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))
        all_shader.append(control_nodes_shader)

        scene.world.traverse_visit(initUpdate, scene.world.root)

    imgui.end()


# MAIN RENDERING LOOP

running = True
scene.init(imgui=True, windowWidth=1024, windowHeight=768, windowTitle="Elements: Bezier Curve Rendering",
           openGLversion=4)

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

projMat = util.perspective(50.0, 1.0, 0.01, 10.0)
## OR
# projMat = util.perspective(90.0, 1.33, 0.1, 100)
## OR
# projMat = util.ortho(-10.0, 10.0, -10.0, 10.0, -1.0, 10.0)

gWindow._myCamera = view  # otherwise, an imgui slider must be moved to properly update

model_cube = trans4.trs
## OR
# model_cube = util.scale(0.3) @ util.translate(0.0,0.5,0.0) ## COMPLETELY OVERRIDE OBJECT's TRS
## OR
# model_cube =  trans4.trs @ util.scale(0.3) @ util.translate(0.0,0.5,0.0) ## TAMPER WITH OBJECT's TRS

model_terrain_axes = terrain.getChild(0).trs  # notice that terrain.getChild(0) == terrain_trans
# OR
# model_terrain_axes = util.translate(0.0,0.0,0.0) ## COMPLETELY OVERRIDE OBJECT's TRS

while running:
    running = scene.render(running)
    scene.world.traverse_visit(renderUpdate, scene.world.root)
    view = gWindow._myCamera  # updates view via the imgui

    mvp_terrain_axes = projMat @ view @ model_terrain_axes

    Bezier_GUI()

    for shader in all_shader:
        shader.setUniformVariable(key='modelViewProj', value=mvp_terrain_axes, mat4=True)

    scene.render_post()

scene.shutdown()



