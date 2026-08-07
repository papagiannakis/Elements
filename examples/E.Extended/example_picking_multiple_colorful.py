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
import sdl2

from Elements.extensions.picking_buffer import PickingBuffer as pb
from Elements.definitions import SHADER_DIR


example_description = (
    "Picking demo with 10 cubes using colorful per-vertex shading.\n"
    "Click a cube to print its entity name and picking id.\n"
    "After picking a cube, use W/A/S/D to orbit the camera around it.\n"
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
        ShaderGLDecorator(Shader(vertex_import_file=SHADER_DIR / "Phong.vert", fragment_import_file=SHADER_DIR / "Phong.frag")),
    )
    return terrainTrans, terrainShader


def create_cube(entity_name, vertex_colors, trs):
    cubeNode = scene.world.createEntity(Entity(name=entity_name))
    scene.world.addEntityChild(rootEntity, cubeNode)
    cubeTrans = scene.world.addComponent(cubeNode, BasicTransform(name=f"{entity_name}_TRS", trs=trs))
    cubeMesh = scene.world.addComponent(cubeNode, RenderMesh(name=f"{entity_name}_Mesh"))

    vertexCubeArr, indexCubeArr = create_cube_geometry()
    colorCubeArr = np.array(vertex_colors, dtype=np.float32)
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
        ShaderGLDecorator(Shader(vertex_import_file=SHADER_DIR / "Phong.vert", fragment_import_file=SHADER_DIR / "Phong.frag")),
    )
    return cubeTrans, cubeShader


def make_palette(*rgb_values):
    return [[r, g, b, 1.0] for r, g, b in rgb_values]


def get_orbit_target(cube_trans):
    world = cube_trans.l2world
    target_pos = np.array(world[:3, 3], dtype=np.float32)
    half_height = 0.5 * np.linalg.norm(world[:3, 1])
    target_pos[1] += half_height
    return target_pos


def orbit_state_from_eye(camera_eye, orbit_target):
    offset = np.array(camera_eye, dtype=np.float32) - orbit_target
    radius = max(0.1, np.linalg.norm(offset))
    yaw = np.arctan2(offset[2], offset[0])
    horizontal = np.linalg.norm(offset[[0, 2]])
    pitch = np.arctan2(offset[1], horizontal)
    return radius, yaw, pitch


def orbit_eye_from_state(orbit_target, orbit_radius, orbit_yaw, orbit_pitch):
    cos_pitch = np.cos(orbit_pitch)
    return orbit_target + np.array([
        orbit_radius * cos_pitch * np.cos(orbit_yaw),
        orbit_radius * np.sin(orbit_pitch),
        orbit_radius * cos_pitch * np.sin(orbit_yaw),
    ], dtype=np.float32)


def set_window_camera(window, camera_eye, camera_target, up_vector):
    view_matrix = util.lookat(camera_eye, camera_target, up_vector)
    window._myCamera = view_matrix
    window._cameraEye = np.array(camera_eye, dtype=np.float32)
    window._cameraTarget = np.array(camera_target, dtype=np.float32)
    return view_matrix


def sync_camera(scene_context, window, camera_eye, camera_target, up_vector):
    view_matrix = set_window_camera(window, camera_eye, camera_target, up_vector)
    if scene_context is not window:
        scene_context._eye = tuple(np.array(camera_eye, dtype=np.float32))
        scene_context._target = tuple(np.array(camera_target, dtype=np.float32))
        scene_context._up = tuple(np.array(up_vector, dtype=np.float32))
    return view_matrix


terrainTrans, terrainShader = create_terrain()

cube_specs = [
    (
        "Cube_01",
        (-4.0, 0.0, -1.6),
        0.45,
        make_palette(
            (0.98, 0.25, 0.22), (0.99, 0.60, 0.25), (0.98, 0.84, 0.28), (0.90, 0.20, 0.18),
            (0.75, 0.16, 0.42), (0.47, 0.16, 0.66), (0.22, 0.46, 0.91), (0.14, 0.71, 0.83),
        ),
    ),
    (
        "Cube_02",
        (-2.2, 0.0, -1.4),
        0.95,
        make_palette(
            (0.22, 0.72, 0.90), (0.28, 0.88, 0.63), (0.87, 0.96, 0.33), (0.98, 0.69, 0.19),
            (0.97, 0.40, 0.23), (0.79, 0.25, 0.52), (0.51, 0.28, 0.82), (0.24, 0.40, 0.89),
        ),
    ),
    (
        "Cube_03",
        (-0.4, 0.0, -1.2),
        0.40,
        make_palette(
            (0.96, 0.82, 0.18), (0.99, 0.92, 0.58), (0.84, 0.96, 0.33), (0.55, 0.86, 0.28),
            (0.23, 0.73, 0.34), (0.15, 0.65, 0.67), (0.12, 0.50, 0.86), (0.42, 0.37, 0.85),
        ),
    ),
    (
        "Cube_04",
        (1.4, 0.0, -1.5),
        0.90,
        make_palette(
            (0.29, 0.77, 0.31), (0.67, 0.92, 0.34), (0.98, 0.91, 0.25), (0.98, 0.64, 0.16),
            (0.93, 0.33, 0.21), (0.72, 0.23, 0.47), (0.46, 0.28, 0.82), (0.18, 0.51, 0.93),
        ),
    ),
    (
        "Cube_05",
        (3.2, 0.0, -1.3),
        0.42,
        make_palette(
            (0.14, 0.68, 0.72), (0.22, 0.82, 0.88), (0.53, 0.94, 0.97), (0.91, 0.97, 0.99),
            (0.87, 0.83, 0.99), (0.70, 0.56, 0.94), (0.48, 0.33, 0.85), (0.22, 0.21, 0.56),
        ),
    ),
    (
        "Cube_06",
        (-4.0, 0.0, 1.4),
        0.88,
        make_palette(
            (0.19, 0.49, 0.97), (0.32, 0.66, 0.99), (0.35, 0.85, 0.92), (0.27, 0.83, 0.61),
            (0.66, 0.92, 0.36), (0.97, 0.88, 0.22), (0.98, 0.55, 0.16), (0.95, 0.26, 0.19),
        ),
    ),
    (
        "Cube_07",
        (-2.2, 0.0, 1.2),
        0.38,
        make_palette(
            (0.46, 0.34, 0.83), (0.61, 0.47, 0.90), (0.79, 0.36, 0.84), (0.93, 0.34, 0.69),
            (0.96, 0.47, 0.47), (0.99, 0.67, 0.24), (0.94, 0.86, 0.30), (0.63, 0.88, 0.35),
        ),
    ),
    (
        "Cube_08",
        (-0.4, 0.0, 1.5),
        0.92,
        make_palette(
            (0.78, 0.29, 0.69), (0.91, 0.46, 0.83), (0.99, 0.72, 0.90), (0.98, 0.93, 0.96),
            (0.88, 0.97, 0.82), (0.56, 0.91, 0.63), (0.27, 0.77, 0.73), (0.17, 0.54, 0.86),
        ),
    ),
    (
        "Cube_09",
        (1.4, 0.0, 1.3),
        0.43,
        make_palette(
            (0.85, 0.43, 0.53), (0.96, 0.58, 0.45), (0.99, 0.80, 0.31), (0.94, 0.94, 0.43),
            (0.67, 0.91, 0.38), (0.26, 0.78, 0.47), (0.16, 0.64, 0.75), (0.26, 0.42, 0.82),
        ),
    ),
    (
        "Cube_10",
        (3.2, 0.0, 1.6),
        0.98,
        make_palette(
            (0.25, 0.25, 0.25), (0.45, 0.45, 0.45), (0.66, 0.66, 0.66), (0.87, 0.87, 0.87),
            (0.93, 0.61, 0.24), (0.72, 0.33, 0.18), (0.29, 0.51, 0.86), (0.21, 0.73, 0.54),
        ),
    ),
]

cube_objects = []
for name, position, scale, vertex_colors in cube_specs:
    cubeTrs = util.translate(*position) @ util.scale(scale, scale, scale)
    cubeTrans, cubeShader = create_cube(name, vertex_colors, cubeTrs)
    cube_objects.append((name, cubeTrans, cubeShader))

cube_lookup = {name: cubeTrans for name, cubeTrans, _ in cube_objects}


scene.init(
    imgui=True,
    windowWidth=width,
    windowHeight=height,
    windowTitle="Picking Buffer Multiple Colorful Cubes",
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

view = sync_camera(scene.gContext, gWindow, eye, target, up)

pickingSystem.set_camera_matrices(projMat, view)
pickingSystem.init()

camera_eye = np.array(gWindow._cameraEye, dtype=np.float32)
selected_cube_name = None
selected_cube_trans = None
orbit_target = np.array(gWindow._cameraTarget, dtype=np.float32)
desired_orbit_target = np.array(orbit_target, dtype=np.float32)
orbit_radius, orbit_yaw, orbit_pitch = orbit_state_from_eye(camera_eye, orbit_target)
orbit_speed = 0.025
orbit_pitch_limit = 1.25
orbit_zoom_speed = 0.35
orbit_target_lerp = 0.12

scene.world.print()

running = True
while running:
    running = scene.render()
    scene.world.traverse_visit(transUpdate, scene.world.root)
    scene.world.traverse_visit(renderUpdate, scene.world.root)
    displayGUI_text(example_description)

    key_states = sdl2.SDL_GetKeyboardState(None)
    if selected_cube_trans is not None:
        camera_eye = np.array(gWindow._cameraEye, dtype=np.float32)
        desired_orbit_target = get_orbit_target(selected_cube_trans)
        target_delta = desired_orbit_target - orbit_target
        if np.linalg.norm(target_delta) > 1e-4:
            orbit_target = orbit_target + orbit_target_lerp * target_delta
            view = sync_camera(scene.gContext, gWindow, camera_eye, orbit_target, up)
        orbit_radius, orbit_yaw, orbit_pitch = orbit_state_from_eye(camera_eye, orbit_target)
        orbit_changed = False
        if key_states[sdl2.SDL_SCANCODE_A]:
            orbit_yaw -= orbit_speed
            orbit_changed = True
        if key_states[sdl2.SDL_SCANCODE_D]:
            orbit_yaw += orbit_speed
            orbit_changed = True
        if key_states[sdl2.SDL_SCANCODE_W]:
            orbit_pitch += orbit_speed
            orbit_changed = True
        if key_states[sdl2.SDL_SCANCODE_S]:
            orbit_pitch -= orbit_speed
            orbit_changed = True
        if key_states[sdl2.SDL_SCANCODE_EQUALS] or key_states[sdl2.SDL_SCANCODE_KP_PLUS]:
            orbit_radius = max(0.5, orbit_radius - orbit_zoom_speed)
            orbit_changed = True
        if key_states[sdl2.SDL_SCANCODE_MINUS] or key_states[sdl2.SDL_SCANCODE_KP_MINUS]:
            orbit_radius += orbit_zoom_speed
            orbit_changed = True

        if orbit_changed:
            orbit_pitch = np.clip(orbit_pitch, -orbit_pitch_limit, orbit_pitch_limit)
            camera_eye = orbit_eye_from_state(orbit_target, orbit_radius, orbit_yaw, orbit_pitch)
            view = sync_camera(scene.gContext, gWindow, camera_eye, orbit_target, up)

    view = gWindow._myCamera
    camera_eye = np.array(gWindow._cameraEye, dtype=np.float32)
    LviewPos = camera_eye
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
            if entity.name in cube_lookup:
                selected_cube_name = entity.name
                selected_cube_trans = cube_lookup[selected_cube_name]
                camera_eye = np.array(gWindow._cameraEye, dtype=np.float32)
                desired_orbit_target = get_orbit_target(selected_cube_trans)
                orbit_radius, orbit_yaw, orbit_pitch = orbit_state_from_eye(camera_eye, orbit_target)
                print(f"Orbit target: {selected_cube_name}")

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
    terrainShader.setUniformVariable(key="modelViewProj", value=projMat @ view @ terrainTrans.l2world, mat4=True)
    terrainShader.setUniformVariable(key="model", value=terrainTrans.l2world, mat4=True)
    terrainShader.setUniformVariable(key="ambientColor", value=Lambientcolor, float3=True)
    terrainShader.setUniformVariable(key="ambientStr", value=Lambientstr, float1=True)
    terrainShader.setUniformVariable(key="viewPos", value=LviewPos, float3=True)
    terrainShader.setUniformVariable(key="lightPos", value=Lposition, float3=True)
    terrainShader.setUniformVariable(key="lightColor", value=Lcolor, float3=True)
    terrainShader.setUniformVariable(key="lightIntensity", value=Lintensity, float1=True)
    terrainShader.setUniformVariable(key="shininess", value=Mshininess, float1=True)
    scene.world.traverse_visit(renderUpdate, scene.world.root)
    scene.render_post()

scene.shutdown()
