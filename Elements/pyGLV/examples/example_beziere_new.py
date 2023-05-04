import numpy as np

import Elements.pyECSS.utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, RenderMesh
from Elements.pyECSS.System import TransformSystem
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GUI.Viewer import RenderGLStateSystem

from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray

from OpenGL.GL import GL_LINES

import bezier

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
# terrain_shader.setUniformVariable(key='modelViewProj', value=mvpMat, mat4=True)

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


#### BEZIER 2D ####


bezier_control_nodes = [[0, 0], [1, 2], [0, 3]]

# def separate_coordinates(coordinates):
#     x_coordinates = [coord[0] for coord in coordinates]
#     y_coordinates = [coord[1] for coord in coordinates]
#     return [x_coordinates, y_coordinates]
#
# def combine_coordinates(coordinates):
#     return [[coord[0], coord[1]] for coord in zip(coordinates[0], coordinates[1])]
#
# def xy_to_vertecies(coords):
#     return [coord + [0.0, 1.0] for coord in coords]

def vertecies_to_line_vertecies(coordinates):
    vertecies = []
    vertecies.append(coordinates[0])
    for coord in coordinates[1:-1]:
        vertecies.extend([coord, coord])
    vertecies.append(coordinates[-1])
    return vertecies

def generate_bezier_data(bezier_nodes, numberPoints, start_x, end_x):
    bezier_curve = bezier.Curve.from_nodes(separate_coordinates(bezier_nodes))
    print("created bezier curve:", bezier_curve)

    x_values = np.linspace(start_x, end_x, numberPoints)
    xy_values = combine_coordinates(bezier_curve.evaluate_multi(x_values))
    print("xy_values:", xy_values)

    vertexBezier = np.array(vertecies_to_line_vertecies(xy_to_vertecies(xy_values)), dtype=np.float32)
    print("vertexBezier", vertexBezier)

    colorBezier = np.array([[1.0, 0.0, 1.0, 1.0]] * len(vertexBezier), dtype=np.float32)
    print("colorBezier", colorBezier)

    indexBezier = np.array(range(len(vertexBezier)), np.uint32)

    return vertexBezier, colorBezier, indexBezier



#### BEZIER 3D ####


bezier_control_nodes_3D = [[0, 0, 0], [1, 2, 1], [0, 3, 2]]

def separate_coordinates_3D(coordinates):
    x_coordinates = [coord[0] for coord in coordinates]
    y_coordinates = [coord[1] for coord in coordinates]
    z_coordinates = [coord[2] for coord in coordinates]
    return [x_coordinates, y_coordinates, z_coordinates]

def combine_coordinates_3D(coordinates):
    return [[coord[0], coord[1], coord[2]] for coord in zip(coordinates[0], coordinates[1], coordinates[2])]

def xyz_to_vertecies(coords):
    return [coord + [1.0] for coord in coords]

def generate_points(num_points, start_x, end_x, start_z, end_z):
    x_values = np.linspace(start_x, end_x, num_points)
    z_values = np.linspace(start_z, end_z, num_points)
    points = []
    for x in x_values:
        for z in z_values:
            points.append([x, z])
    return points

def generate_bezier_data_3D(bezier_nodes, num_points, start_x, end_x):
    bezier_curve = bezier.Curve.from_nodes(separate_coordinates_3D(bezier_nodes))
    print("created bezier curve:", bezier_curve)

    x_values = np.linspace(start_x, end_x, num_points)
    bezier_points = bezier_curve.evaluate_multi(x_values)
    print("bezier_points", bezier_points)

    xyz_values = combine_coordinates_3D(bezier_points)
    print("xyz_values:", xyz_values)

    vertexBezier = np.array(vertecies_to_line_vertecies(xyz_to_vertecies(xyz_values)), dtype=np.float32)
    print("vertexBezier", vertexBezier)

    colorBezier = np.array([[0.5, 0.0, 1.0, 1.0]] * len(vertexBezier), dtype=np.float32)
    print("colorBezier", colorBezier)

    indexBezier = np.array(range(len(vertexBezier)), np.uint32)

    return vertexBezier, colorBezier, indexBezier


#vertexBezier, colorBezier, indexBezier = generate_bezier_data(bezier_control_nodes, 100, -1, 1)
vertexBezier, colorBezier, indexBezier = generate_bezier_data_3D(bezier_control_nodes_3D, 100, -1, 1)

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


# MAIN RENDERING LOOP

running = True
scene.init(imgui=True, windowWidth=1024, windowHeight=768, windowTitle="Elements: A Working Event Manager",
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
    mvp_cube = projMat @ view @ model_cube
    mvp_terrain_axes = projMat @ view @ model_terrain_axes
    axes_shader.setUniformVariable(key='modelViewProj', value=mvp_terrain_axes, mat4=True)
    bezier_shader.setUniformVariable(key='modelViewProj', value=mvp_terrain_axes, mat4=True)
    terrain_shader.setUniformVariable(key='modelViewProj', value=mvp_terrain_axes, mat4=True)
    scene.render_post()

scene.shutdown()



