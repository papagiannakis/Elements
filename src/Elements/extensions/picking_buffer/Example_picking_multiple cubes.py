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


assignment_goals = (
    "Picking demo with 10 cubes of alternating sizes and unique colors.\n"
    "Click a cube to print its entity name and picking id.\n"
)

width = 1280
height = 720

scene = Scene()
rootEntity = scene.world.createEntity(Entity(name="RooT"))


entityCam1 = scene.world.createEntity(Entity(name="entityCam1"))
scene.world.addEntityChild(rootEntity, entityCam1)
scene.world.addComponent(entityCam1, BasicTransform(name="trans1", trs=util.translate(0, 0, -12)))

eye = util.vec(0.0, 5.5, 11.0)
target = util.vec(0.0, 0.8, 0.0)
up = util.vec(0.0, 1.0, 0.0)
view = util.lookat(eye, target, up)

projMat = util.perspective(50.0, width / height, 0.01, 100.0)

Lposition = util.vec(4.0, 8.0, 5.0)
Lambientcolor = util.vec(1.0, 1.0, 1.0)
Lambientstr = 0.3
LviewPos = eye
Lcolor = util.vec(1.0, 1.0, 1.0)
Lintensity = 0.9
Mshininess = 1.0
Mcolor = util.vec(1.0, 1.0, 1.0)

transUpdate = scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
renderUpdate = scene.world.createSystem(RenderGLShaderSystem())
initUpdate = scene.world.createSystem(InitGLShaderSystem())

pickingSystem = pb.PickingSystem(width, height)
scene.world.createSystem(pickingSystem)


def create_cube_geometry():
    vertexCubeArr = np.array([
        [-0.5, 0.0, 0.5, 1.0],
        [-0.5, 1.0, 0.5, 1.0],
        [0.5, 1.0, 0.5, 1.0],
        [0.5, 0.0, 0.5, 1.0],
        [-0.5, 0.0, -0.5, 1.0],
        [-0.5, 1.0, -0.5, 1.0],
        [0.5, 1.0, -0.5, 1.0],
        [0.5, 0.0, -0.5, 1.0],
    ])
    indexCubeArr = np.array((
        1, 0, 3, 1, 3, 2,
        2, 3, 7, 2, 7, 6,
        3, 0, 4, 3, 4, 7,
        6, 5, 1, 6, 1, 2,
        4, 5, 6, 4, 6, 7,
        5, 4, 0, 5, 0, 1,
    ), np.uint32)
    return vertexCubeArr, indexCubeArr


def create_terrain():
    vertTerrainArr = np.array([
        [6.0, 0.0, 4.5, 1.0],
        [-6.0, 0.0, 4.5, 1.0],
        [-6.0, 0.0, -4.5, 1.0],
        [6.0, 0.0, -4.5, 1.0],
    ])
    colorTerrainArr = np.array([
        [0.55, 0.55, 0.58, 1.0],
        [0.55, 0.55, 0.58, 1.0],
        [0.55, 0.55, 0.58, 1.0],
        [0.55, 0.55, 0.58, 1.0],
    ], dtype=np.float32)
    indexTerrainArr = np.array((0, 1, 3, 2, 1, 3))

    terrainEntity = scene.world.createEntity(Entity(name="Terrain"))
    scene.world.addEntityChild(rootEntity, terrainEntity)
    terrainTrans = scene.world.addComponent(terrainEntity, BasicTransform(name="Terrain_TRS", trs=util.identity()))
    terrainMesh = scene.world.addComponent(terrainEntity, RenderMesh(name="Terrain_Mesh"))

    vertTerrain, indexTerrain, colorTerrain, normalsTerrain = norm.generateSmoothNormalsMesh(
        vertTerrainArr, indexTerrainArr, colorTerrainArr
    )
    normalsTerrain[:] = [0, 1, 0]

    terrainMesh.vertex_attributes.append(vertTerrain)
    terrainMesh.vertex_attributes.append(colorTerrain)
    terrainMesh.vertex_attributes.append(normalsTerrain)
    terrainMesh.vertex_index.append(indexTerrain)

    scene.world.addComponent(terrainEntity, VertexArray())
    terrainShader = scene.world.addComponent(
        terrainEntity,
        ShaderGLDecorator(Shader(vertex_source=Shader.VERT_PHONG_MVP, fragment_source=Shader.FRAG_PHONG)),
    )
    return terrainTrans, terrainShader


def create_cube(entity_name, color, trs):
    cubeNode = scene.world.createEntity(Entity(name=entity_name))
    scene.world.addEntityChild(rootEntity, cubeNode)
    cubeTrans = scene.world.addComponent(cubeNode, BasicTransform(name=f"{entity_name}_TRS", trs=trs))
    cubeMesh = scene.world.addComponent(cubeNode, RenderMesh(name=f"{entity_name}_Mesh"))

    vertexCubeArr, indexCubeArr = create_cube_geometry()
    colorCubeArr = np.tile(np.array([*color, 1.0], dtype=np.float32), (8, 1))
    cubeVertices, cubeIndices, cubeColors, cubeNormals = norm.generateSmoothNormalsMesh(
        vertexCubeArr, indexCubeArr, colorCubeArr
    )
    cubeNormals[:] = [0, 1, 0]

    cubeMesh.vertex_attributes.append(cubeVertices)
    cubeMesh.vertex_attributes.append(cubeColors)
    cubeMesh.vertex_attributes.append(cubeNormals)
    cubeMesh.vertex_index.append(cubeIndices)

    scene.world.addComponent(cubeNode, VertexArray())
    cubeShader = scene.world.addComponent(
        cubeNode,
        ShaderGLDecorator(Shader(vertex_source=Shader.VERT_PHONG_MVP, fragment_source=Shader.FRAG_PHONG)),
    )
    return cubeTrans, cubeShader


terrainTrans, terrainShader = create_terrain()

cube_specs = [
    ("Cube_01", (-4.0, 0.0, -1.6), 0.45, (0.92, 0.25, 0.21)),
    ("Cube_02", (-2.2, 0.0, -1.4), 0.95, (0.96, 0.55, 0.16)),
    ("Cube_03", (-0.4, 0.0, -1.2), 0.40, (0.97, 0.84, 0.18)),
    ("Cube_04", (1.4, 0.0, -1.5), 0.90, (0.36, 0.77, 0.29)),
    ("Cube_05", (3.2, 0.0, -1.3), 0.42, (0.13, 0.69, 0.71)),
    ("Cube_06", (-4.0, 0.0, 1.4), 0.88, (0.18, 0.49, 0.96)),
    ("Cube_07", (-2.2, 0.0, 1.2), 0.38, (0.45, 0.33, 0.83)),
    ("Cube_08", (-0.4, 0.0, 1.5), 0.92, (0.78, 0.29, 0.69)),
    ("Cube_09", (1.4, 0.0, 1.3), 0.43, (0.85, 0.43, 0.53)),
    ("Cube_10", (3.2, 0.0, 1.6), 0.98, (0.35, 0.35, 0.35)),
]

cube_objects = []
for name, position, scale, color in cube_specs:
    cubeTrs = util.translate(*position) @ util.scale(scale, scale, scale)
    cubeTrans, cubeShader = create_cube(name, color, cubeTrs)
    cube_objects.append((name, cubeTrans, cubeShader))


scene.init(
    imgui=True,
    windowWidth=width,
    windowHeight=height,
    windowTitle="Picking Buffer Multiple Cubes",
    openGLversion=4,
)

scene.world.traverse_visit(initUpdate, scene.world.root)

eManager = scene.world.eventManager
gWindow = scene.renderWindow
renderGLEventActuator = RenderGLStateSystem()

eManager._subscribers["OnUpdateWireframe"] = gWindow
eManager._actuators["OnUpdateWireframe"] = renderGLEventActuator
eManager._subscribers["OnUpdateCamera"] = gWindow
eManager._actuators["OnUpdateCamera"] = renderGLEventActuator

gWindow._myCamera = view

pickingSystem.set_camera_matrices(projMat, view)
pickingSystem.init()

scene.world.print()

running = True
while running:
    running = scene.render()
    scene.world.traverse_visit(transUpdate, scene.world.root)
    scene.world.traverse_visit(renderUpdate, scene.world.root)
    displayGUI_text(assignment_goals)

    view = gWindow._myCamera
    window_height = scene.renderWindow._windowHeight

    click_coords = pickingSystem.check_for_click()
    if click_coords:
        mouse_x, mouse_y = click_coords
        pickingSystem.set_camera_matrices(projMat, view)
        pickingSystem.begin_picking_pass()
        scene.world.traverse_visit(pickingSystem, scene.world.root)
        pickingSystem.end_picking_pass()

        entity, picked_id = pickingSystem.pick(mouse_x, mouse_y, window_height)
        if entity is None:
            print(f"Picked id: {picked_id} -> no entity")
        else:
            print(f"Picked id: {picked_id} -> {entity.name}")

    for _, cubeTrans, cubeShader in cube_objects:
        cubeShader.setUniformVariable(key="modelViewProj", value=projMat @ view @ cubeTrans.l2world, mat4=True)
        cubeShader.setUniformVariable(key="model", value=cubeTrans.l2world, mat4=True)
        cubeShader.setUniformVariable(key="ambientColor", value=Lambientcolor, float3=True)
        cubeShader.setUniformVariable(key="ambientStr", value=Lambientstr, float1=True)
        cubeShader.setUniformVariable(key="viewPos", value=LviewPos, float3=True)
        cubeShader.setUniformVariable(key="lightPos", value=Lposition, float3=True)
        cubeShader.setUniformVariable(key="lightColor", value=Lcolor, float3=True)
        cubeShader.setUniformVariable(key="lightIntensity", value=Lintensity, float1=True)
        cubeShader.setUniformVariable(key="shininess", value=Mshininess, float1=True)
        cubeShader.setUniformVariable(key="matColor", value=Mcolor, float3=True)

    terrainShader.setUniformVariable(key="modelViewProj", value=projMat @ view @ terrainTrans.l2world, mat4=True)
    terrainShader.setUniformVariable(key="model", value=terrainTrans.l2world, mat4=True)
    terrainShader.setUniformVariable(key="ambientColor", value=Lambientcolor, float3=True)
    terrainShader.setUniformVariable(key="ambientStr", value=Lambientstr, float1=True)
    terrainShader.setUniformVariable(key="viewPos", value=LviewPos, float3=True)
    terrainShader.setUniformVariable(key="lightPos", value=Lposition, float3=True)
    terrainShader.setUniformVariable(key="lightColor", value=Lcolor, float3=True)
    terrainShader.setUniformVariable(key="lightIntensity", value=Lintensity, float1=True)
    terrainShader.setUniformVariable(key="shininess", value=Mshininess, float1=True)
    terrainShader.setUniformVariable(key="matColor", value=Mcolor, float3=True)

    scene.world.traverse_visit(renderUpdate, scene.world.root)
    scene.render_post()

scene.shutdown()
