"""
Duplicate/extended version of example_picking_multiple_colorful_menu.py: same GPU picking-buffer
selection, W/A/S/D orbit, modular ImGui menu bar (Elements.pyGLV.GUI.MenuBar) and single point
light + real-time shadows (Elements.extensions.Shadows.ShadowShader, as in
Elements.extensions.Shadows.example_1_PointLightDemo), plus:

  1. Spheres, cylinders and a cone, built from
     Elements.extensions.Shapes.geometry_factory (create_solid_shape() below wraps its
     raw params-dict interface into a typical scale=/color=/**kwargs call).
  2. A textured cube (create_textured_cube_shape()), UV-mapped per face as in
     examples/2.Intermediate/example_8b_more_textures.py.
  3. A "Shadow Settings" ImGui window -- Enable Shadows / Soft Shadows (PCF) / PCF Softness /
     Shadow Bias / Show Unfolded Map / View from Light -- ported from the "Shadow Settings"
     header of Elements.extensions.Shadows.example_1_PointLightDemo's control panel. It is
     hidden by default; View > Shadow Settings... (shortcut "2") shows/hides it.
  4. The default shadow bias was raised (0.3 -> 0.6) to stop the flat terrain from
     self-shadowing ("shadow acne": with too small a bias, a point-light cube-map depth
     comparison can decide a flat receiver is behind itself, painting shadow speckle across the
     terrain even where nothing occludes it). It's still live-tunable from the panel above if a
     given light position/GPU needs a different value.

File > Screenshot still defaults to "P", View > Toggle Wireframe to "F" (app-wide, from
RenderDecorator), View > Toggle Shadows to "1"; all shortcuts are hardcoded below (the
Keybinding(...) argument in each menu_bar add_item() call) -- edit those directly, or call
menu_bar.rebind(...) at runtime, to change one.
"""

import numpy as np
import imgui
import OpenGL.GL as gl

import Elements.pyECSS.math_utilities as util
import Elements.utils.Shortcuts as Shortcuts
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, RenderMesh
from Elements.pyECSS.System import TransformSystem
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GUI.Viewer import RenderGLStateSystem
from Elements.pyGLV.GUI.MenuBar import MenuBar, Keybinding
from Elements.pyGLV.GL.Shader import InitGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray
from Elements.pyGLV.GL.Textures import Texture
from Elements.definitions import TEXTURE_DIR, SHADER_DIR
import Elements.utils.normals as norm
from Elements.utils.Shortcuts import displayGUI_text
from Elements.extensions.Captions_Screenshot.screenshot import save_screenshot
from Elements.extensions.Shadows.ShadowShader import ShadowShader, ShadowMappingSystem
from Elements.extensions.Shapes import geometry_factory
import sdl2

from Elements.extensions.picking_buffer import PickingBuffer as pb


assignment_goals = (
    "Picking demo with cubes, spheres, cylinders, a cone and a textured cube, lit by one point\n"
    "light with real-time shadows.\n"
    "Click any object to print its entity name and picking id, then orbit it with W/A/S/D.\n"
    "See the menu bar at the top of the window for Screenshot/Wireframe/Shadows/Shortcuts actions,\n"
    "and View > Shadow Settings... (shortcut 2) for shadow tuning controls.\n"
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

# Single point light (as in examples/2.Intermediate/example_9_textures_with_lights.py), now also
# driving real-time shadows via ShadowShader/ShadowMappingSystem.
Lposition = util.vec(4.0, 8.0, 5.0)
Lcolor = util.vec(1.0, 1.0, 1.0)
LviewPos = eye

# --- LIGHT ENTITY (its BasicTransform is what ShadowMappingSystem reads the light position from) ---
light_Entity = scene.world.createEntity(Entity(name="light_Entity"))
scene.world.addEntityChild(rootEntity, light_Entity)
light_trans = scene.world.addComponent(light_Entity, BasicTransform(name="light_Entity_trans", trs=util.translate(*Lposition)))

transUpdate = scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
initUpdate = scene.world.createSystem(InitGLShaderSystem())
shadowSystem = scene.world.createSystem(
    ShadowMappingSystem(name="ShadowSystem", lightNode=light_Entity, lightTargetNode=None, shadowMapSize=2048, lightType="point")
)

pickingSystem = pb.PickingSystem(width, height)
scene.world.createSystem(pickingSystem)

# Every ShadowShader component we create (terrain + every shape), so we can .init() and update
# their uniforms each frame in one place; ShadowMappingSystem.render() draws them (both the
# shadow-map depth pass and the final lit pass), so there is no separate RenderGLShaderSystem here.
shadow_shaders = []


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
    """
    A real box, not a zero-thickness plane. A flat quad's "underside" is just its own back face,
    so the shadow test (which only depends on world position, not viewing side) gives the exact
    same result from below as from above, and culling alone just makes that face invisible --
    letting you see straight through to whatever's on the other side (e.g. the objects sitting on
    top of it). With real thickness the underside is a genuinely separate, physically-lower
    surface: it faces away from the light entirely (ambient-only, uniformly dark) and its own top
    face blocks the view, so from below you see a solid dark slab, not shadow patterns or objects
    showing through.
    """
    terrainEntity = scene.world.createEntity(Entity(name="Terrain"))
    scene.world.addEntityChild(rootEntity, terrainEntity)
    terrain_thickness = 0.05
    terrainTrans = scene.world.addComponent(
        terrainEntity,
        BasicTransform(name="Terrain_TRS", trs=util.translate(0, -0.5 * terrain_thickness - 0.001, 0)),
    )
    terrainMesh = scene.world.addComponent(terrainEntity, RenderMesh(name="Terrain_Mesh"))

    # Same 12x9 footprint as the old flat quad (X in [-6, 6], Z in [-4.5, 4.5]), its top face at
    # local y = +0.5 * terrain_thickness, i.e. world y ~= 0 once translated above.
    vertTerrain, indexTerrain, colorTerrain, normalsTerrain = geometry_factory.build_render_mesh(
        "rectangular_prism", {"scale": [12.0, terrain_thickness, 9.0], "color": [0.55, 0.55, 0.58]}
    )

    terrainMesh.vertex_attributes.append(vertTerrain)
    terrainMesh.vertex_attributes.append(colorTerrain)
    terrainMesh.vertex_attributes.append(normalsTerrain)
    terrainMesh.vertex_attributes.append(np.zeros((vertTerrain.shape[0], 2), dtype=np.float32))  # unused UV
    terrainMesh.vertex_index.append(indexTerrain)

    scene.world.addComponent(terrainEntity, VertexArray())
    terrainShader = scene.world.addComponent(
        terrainEntity,
        ShadowShader(name="Terrain_Shader", vertex_import_file=SHADER_DIR / "PointPhong.vert", fragment_import_file=SHADER_DIR / "PointPhong.frag"),
    )
    terrainShader.setUniformVariable(key="useTexture", value=0, boolean=True)
    shadow_shaders.append(terrainShader)
    return terrainTrans, terrainShader


def create_solid_cube(entity_name, position, scale, color):
    """Spawn a single flat-colored, point-lit-and-shadowed cube at position, uniformly scaled."""
    cubeNode = scene.world.createEntity(Entity(name=entity_name))
    scene.world.addEntityChild(rootEntity, cubeNode)
    cubeTrans = scene.world.addComponent(
        cubeNode,
        BasicTransform(name=f"{entity_name}_TRS", trs=util.translate(*position) @ util.scale(scale, scale, scale)),
    )
    cubeMesh = scene.world.addComponent(cubeNode, RenderMesh(name=f"{entity_name}_Mesh"))

    vertexCubeArr, indexCubeArr = create_cube_geometry()
    colorCubeArr = np.array([color] * len(vertexCubeArr), dtype=np.float32)
    cubeVertices, cubeIndices, cubeColors, cubeNormals = norm.generateFlatNormalsMesh(
        vertexCubeArr, indexCubeArr, colorCubeArr
    )

    cubeMesh.vertex_attributes.append(cubeVertices)
    cubeMesh.vertex_attributes.append(cubeColors)
    cubeMesh.vertex_attributes.append(cubeNormals)
    cubeMesh.vertex_attributes.append(np.zeros((cubeVertices.shape[0], 2), dtype=np.float32))  # unused UV
    cubeMesh.vertex_index.append(cubeIndices)

    scene.world.addComponent(cubeNode, VertexArray())
    cubeShader = scene.world.addComponent(
        cubeNode,
        ShadowShader(name=f"{entity_name}_Shader", vertex_import_file=SHADER_DIR / "PointPhong.vert", fragment_import_file=SHADER_DIR / "PointPhong.frag"),
    )
    cubeShader.setUniformVariable(key="useTexture", value=0, boolean=True)
    shadow_shaders.append(cubeShader)
    return cubeTrans, cubeShader


def create_solid_shape(entity_name, shape_type, position, scale=1.0, color=(0.8, 0.8, 0.8), **shape_params):
    """
    Spawn a single flat/smooth-shaded, point-lit-and-shadowed shape built by
    Elements.extensions.Shapes.geometry_factory (shape_type e.g. "sphere", "cylinder",
    "cone", "pyramid", ...), with a typical scale=/color=/**shape_params keyword interface instead
    of geometry_factory's own raw params dict.
    """
    scale_vec = [scale, scale, scale] if isinstance(scale, (int, float)) else list(scale)
    params = {"scale": scale_vec, "color": list(color[:3]), **shape_params}

    entity = scene.world.createEntity(Entity(name=entity_name))
    scene.world.addEntityChild(rootEntity, entity)
    trans = scene.world.addComponent(entity, BasicTransform(name=f"{entity_name}_TRS", trs=util.translate(*position)))
    mesh = scene.world.addComponent(entity, RenderMesh(name=f"{entity_name}_Mesh"))

    vertices, indices, colors, normals = geometry_factory.build_render_mesh(shape_type, params)

    mesh.vertex_attributes.append(vertices)
    mesh.vertex_attributes.append(colors)
    mesh.vertex_attributes.append(normals)
    mesh.vertex_attributes.append(np.zeros((vertices.shape[0], 2), dtype=np.float32))  # unused UV
    mesh.vertex_index.append(indices)

    scene.world.addComponent(entity, VertexArray())
    shader = scene.world.addComponent(
        entity,
        ShadowShader(name=f"{entity_name}_Shader", vertex_import_file=SHADER_DIR / "PointPhong.vert", fragment_import_file=SHADER_DIR / "PointPhong.frag"),
    )
    shader.setUniformVariable(key="useTexture", value=0, boolean=True)
    shadow_shaders.append(shader)
    return trans, shader


def create_solid_sphere(entity_name, position, scale=1.0, color=(0.8, 0.8, 0.8), lat=24, lon=24):
    return create_solid_shape(entity_name, "sphere", position, scale=scale, color=color, lat=lat, lon=lon)


def create_solid_cylinder(entity_name, position, scale=1.0, color=(0.8, 0.8, 0.8), radius=0.5, height=1.0, segments=24):
    return create_solid_shape(
        entity_name, "cylinder", position, scale=scale, color=color, radius=radius, height=height, segments=segments
    )


def create_solid_cone(entity_name, position, scale=1.0, color=(0.8, 0.8, 0.8), radius=0.5, height=1.0, segments=24):
    return create_solid_shape(
        entity_name, "cone", position, scale=scale, color=color, radius=radius, height=height, segments=segments
    )


def create_textured_cube_shape(entity_name, position, scale):
    """
    Spawn a single ShadowShader-lit cube with real per-face UV coordinates, as in
    examples/2.Intermediate/example_8b_more_textures.py. This does NOT bind an actual image yet:
    Texture() itself issues GL calls (glGenTextures/glTexImage2D) immediately in its constructor,
    so it needs a live GL context -- unlike Shader/VertexArray's lazy .init(), which we can defer
    until after scene.init(). Call set_cube_texture() below once a context exists.
    """
    entity = scene.world.createEntity(Entity(name=entity_name))
    scene.world.addEntityChild(rootEntity, entity)
    trans = scene.world.addComponent(entity, BasicTransform(name=f"{entity_name}_TRS", trs=util.translate(*position)))
    mesh = scene.world.addComponent(entity, RenderMesh(name=f"{entity_name}_Mesh"))

    rawVertices, rawIndices, uv = geometry_factory.create_textured_mesh("cube", {"scale": [scale, scale, scale]})
    # ShadowShader always reads a vColor attribute even with useTexture=1; a neutral white keeps
    # the lighting math correct without tinting the texture.
    placeholderColors = np.ones((rawVertices.shape[0], 4), dtype=np.float32)
    vertices, indices, colors, normals = norm.generateFlatNormalsMesh(rawVertices, rawIndices, placeholderColors)

    mesh.vertex_attributes.append(vertices)
    mesh.vertex_attributes.append(colors)
    mesh.vertex_attributes.append(normals)
    mesh.vertex_attributes.append(np.asarray(uv, dtype=np.float32))
    mesh.vertex_index.append(indices)

    scene.world.addComponent(entity, VertexArray())
    shader = scene.world.addComponent(
        entity,
        ShadowShader(name=f"{entity_name}_Shader", vertex_import_file=SHADER_DIR / "PointPhong.vert", fragment_import_file=SHADER_DIR / "PointPhong.frag"),
    )
    shader.setUniformVariable(key="useTexture", value=1, boolean=True)
    shadow_shaders.append(shader)
    return trans, shader


def set_cube_texture(shader, texture_path):
    """Bind an actual image to a create_textured_cube_shape() shader. Call only after
    scene.init() -- see create_textured_cube_shape()'s docstring for why."""
    texture = Texture(texture_path)
    shader.setUniformVariable(key="ImageTexture", value=texture, texture=True)
    return texture


def get_orbit_target(obj_trans):
    world = obj_trans.l2world
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

# Same 10 cubes/layout as example_picking_multiple_colorful_menu.py (Z in [-1.6, 1.6]).
cube_specs = [
    ("Cube_01", (-4.0, 0.0, -1.6), 0.45, [0.98, 0.25, 0.22, 1.0]),
    ("Cube_02", (-2.2, 0.0, -1.4), 0.95, [0.22, 0.72, 0.90, 1.0]),
    ("Cube_03", (-0.4, 0.0, -1.2), 0.40, [0.96, 0.82, 0.18, 1.0]),
    ("Cube_04", (1.4, 0.0, -1.5), 0.90, [0.29, 0.77, 0.31, 1.0]),
    ("Cube_05", (3.2, 0.0, -1.3), 0.42, [0.14, 0.68, 0.72, 1.0]),
    ("Cube_06", (-4.0, 0.0, 1.4), 0.88, [0.19, 0.49, 0.97, 1.0]),
    ("Cube_07", (-2.2, 0.0, 1.2), 0.38, [0.46, 0.34, 0.83, 1.0]),
    ("Cube_08", (-0.4, 0.0, 1.5), 0.92, [0.78, 0.29, 0.69, 1.0]),
    ("Cube_09", (1.4, 0.0, 1.3), 0.43, [0.85, 0.43, 0.53, 1.0]),
    ("Cube_10", (3.2, 0.0, 1.6), 0.98, [0.25, 0.25, 0.25, 1.0]),
]

pickable_objects = []
for name, position, scale, color in cube_specs:
    objTrans, objShader = create_solid_cube(name, position, scale, color)
    pickable_objects.append((name, objTrans))

# New row of spheres (Z = -3.2, in front of the cube rows), sitting on the terrain (y = radius).
sphere_specs = [
    ("Sphere_01", -4.0, 0.9, (0.90, 0.35, 0.25)),
    ("Sphere_02", -1.2, 0.7, (0.30, 0.75, 0.40)),
    ("Sphere_03", 1.6, 0.8, (0.25, 0.45, 0.90)),
]
for name, x, scale, color in sphere_specs:
    objTrans, objShader = create_solid_sphere(name, (x, 0.5 * scale, -3.2), scale=scale, color=color)
    pickable_objects.append((name, objTrans))

# New row of cylinders + a cone + the textured cube (Z = 3.2, behind the cube rows).
cylinder_specs = [
    ("Cylinder_01", -3.4, 0.4, 1.0, (0.55, 0.35, 0.85)),
    ("Cylinder_02", -1.0, 0.35, 1.4, (0.95, 0.55, 0.15)),
]
for name, x, radius, cyl_height, color in cylinder_specs:
    objTrans, objShader = create_solid_cylinder(
        name, (x, 0.5 * cyl_height, 3.2), scale=1.0, color=color, radius=radius, height=cyl_height
    )
    pickable_objects.append((name, objTrans))

cone_height = 1.2
objTrans, objShader = create_solid_cone(
    "Cone_01", (1.2, 0.5 * cone_height, 3.2), scale=1.0, color=(0.85, 0.80, 0.20), radius=0.55, height=cone_height
)
pickable_objects.append(("Cone_01", objTrans))

textured_cube_scale = 1.0
objTrans, texturedCubeShader = create_textured_cube_shape(
    "TexturedCube_01", (3.4, 0.5 * textured_cube_scale, 3.2), textured_cube_scale
)
pickable_objects.append(("TexturedCube_01", objTrans))

object_lookup = {name: trans for name, trans in pickable_objects}


scene.init(
    imgui=True,
    windowWidth=width,
    windowHeight=height,
    windowTitle="Picking Buffer: Shapes, Textures and Shadows with a Menu Bar",
    openGLversion=4,
)

shadowSystem.init()
shadowSystem.set_viewport_dimensions(width, height)
for shader in shadow_shaders:
    shader.init()

scene.world.traverse_visit(initUpdate, scene.world.root)

# Texture() issues GL calls in its own constructor, so it can only be created now that scene.init()
# has actually made a GL context current -- see create_textured_cube_shape()'s docstring.
set_cube_texture(texturedCubeShader, TEXTURE_DIR / "3x3.jpg")

eManager = scene.world.eventManager
gWindow = scene.renderWindow
gGUI = scene.gContext
renderGLEventActuator = RenderGLStateSystem()

eManager._subscribers["OnUpdateWireframe"] = gWindow
eManager._actuators["OnUpdateWireframe"] = renderGLEventActuator
eManager._subscribers["OnUpdateCamera"] = gWindow
eManager._actuators["OnUpdateCamera"] = renderGLEventActuator

view = sync_camera(scene.gContext, gWindow, eye, target, up)

pickingSystem.set_camera_matrices(projMat, view)
pickingSystem.init()

################### MENU BAR ###################
# A tiny holder so a menu callback (a plain zero-arg function) can stop the main loop / toggle
# state below -- including the "Shadow Settings" panel controls (ported from the "Shadow
# Settings" header of Shadows/example_1_PointLightDemo.py's control panel).
class AppState:
    running = True
    shadows_enabled = True
    show_shadow_settings = False
    soft_shadows = True
    pcf_disk_radius = 0.5
    # Raised from the demo's original 0.3: at 0.3 the flat terrain self-shadowed ("shadow
    # acne") over its whole surface. Still live-tunable below if your scene/GPU needs more.
    shadow_bias = 0.15
    show_shadow_map = False
    view_from_light = False


def take_screenshot():
    save_screenshot(width=scene.renderWindow._windowWidth, height=scene.renderWindow._windowHeight)


def quit_app():
    AppState.running = False


def toggle_shortcuts_window():
    Shortcuts.show_shortcuts_window = not Shortcuts.show_shortcuts_window


def toggle_shadows():
    AppState.shadows_enabled = not AppState.shadows_enabled


def toggle_shadow_settings_panel():
    AppState.show_shadow_settings = not AppState.show_shadow_settings


menu_bar = MenuBar()

file_menu = menu_bar.add_menu("File")
file_menu.add_item("screenshot", "Screenshot", take_screenshot, Keybinding(sdl2.SDL_SCANCODE_P))
# Esc already quits via RenderDecorator's own handling; shown here for discoverability only,
# so this entry does not also poll for Esc itself.
file_menu.add_item("quit", "Quit", quit_app, shortcut_label="Esc")

view_menu = menu_bar.add_menu("View")
# Plain F already toggles wireframe app-wide (RenderDecorator.toggle_Wireframe); reuse it here too,
# again with shortcut_label only, so the key isn't polled twice.
view_menu.add_item("wireframe", "Toggle Wireframe", gGUI.toggle_Wireframe, shortcut_label="F")
view_menu.add_item("shadows", "Toggle Shadows", toggle_shadows, Keybinding(sdl2.SDL_SCANCODE_1))
view_menu.add_item("shadow_settings", "Shadow Settings...", toggle_shadow_settings_panel, Keybinding(sdl2.SDL_SCANCODE_2))

help_menu = menu_bar.add_menu("Help")
help_menu.add_item(
    "shortcuts", "Keyboard Shortcuts", toggle_shortcuts_window, Keybinding(sdl2.SDL_SCANCODE_SLASH, sdl2.KMOD_GUI)
)

camera_eye = np.array(gWindow._cameraEye, dtype=np.float32)
selected_object_name = None
selected_object_trans = None
orbit_target = np.array(gWindow._cameraTarget, dtype=np.float32)
desired_orbit_target = np.array(orbit_target, dtype=np.float32)
orbit_radius, orbit_yaw, orbit_pitch = orbit_state_from_eye(camera_eye, orbit_target)
orbit_speed = 0.025
orbit_pitch_limit = 1.25
orbit_zoom_speed = 0.35
orbit_target_lerp = 0.12

scene.world.print()

running = True
while running and AppState.running:
    running = scene.render()
    menu_bar.draw()
    scene.world.traverse_visit(transUpdate, scene.world.root)
    displayGUI_text(assignment_goals)

    if AppState.show_shadow_settings:
        _, AppState.show_shadow_settings = imgui.begin("Shadow Settings", True)
        imgui.text(f"FPS: {imgui.get_io().framerate:.1f}")
        _, AppState.shadows_enabled = imgui.checkbox("Enable Shadows", AppState.shadows_enabled)
        _, AppState.soft_shadows = imgui.checkbox("Soft Shadows (PCF)", AppState.soft_shadows)
        _, AppState.pcf_disk_radius = imgui.slider_float("PCF Softness", AppState.pcf_disk_radius, 0.0, 5.0)
        _, AppState.shadow_bias = imgui.slider_float("Shadow Bias (Acne)", AppState.shadow_bias, 0.0, 1.0, "%.4f")
        _, AppState.show_shadow_map = imgui.checkbox("Show Unfolded Map", AppState.show_shadow_map)
        _, AppState.view_from_light = imgui.checkbox("View from Light", AppState.view_from_light)
        imgui.end()

    key_states = sdl2.SDL_GetKeyboardState(None)
    if selected_object_trans is not None:
        camera_eye = np.array(gWindow._cameraEye, dtype=np.float32)
        desired_orbit_target = get_orbit_target(selected_object_trans)
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
            if entity.name in object_lookup:
                selected_object_name = entity.name
                selected_object_trans = object_lookup[selected_object_name]
                camera_eye = np.array(gWindow._cameraEye, dtype=np.float32)
                desired_orbit_target = get_orbit_target(selected_object_trans)
                orbit_radius, orbit_yaw, orbit_pitch = orbit_state_from_eye(camera_eye, orbit_target)
                print(f"Orbit target: {selected_object_name}")

    # "View from Light" only swaps the *rendered* view matrix (a debug aid); it never touches the
    # orbit camera / picking's own view, both of which keep using `view` above.
    if AppState.view_from_light:
        shader_view = util.lookat(Lposition, util.vec(0.0, 0.0, 0.0), util.vec(0.0, 1.0, 0.0))
    else:
        shader_view = view

    # Update every ShadowShader's uniforms (model/lightPos/shadowMap are set internally, per
    # object, by ShadowMappingSystem itself during its traversal below).
    for shader in shadow_shaders:
        shader.setUniformVariable(key="projection", value=projMat, mat4=True)
        shader.setUniformVariable(key="view", value=shader_view, mat4=True)
        shader.setUniformVariable(key="lightPos", value=Lposition, float3=True)
        shader.setUniformVariable(key="viewPos", value=LviewPos, float3=True)
        shader.setUniformVariable(key="lightColor", value=Lcolor, float3=True)
        shader.setUniformVariable(key="uHasShadow", value=1 if AppState.shadows_enabled else 0, boolean=True)
        shader.setUniformVariable(key="uSoftShadows", value=1 if AppState.soft_shadows else 0, boolean=True)
        shader.setUniformVariable(key="uPcfDisk", value=AppState.pcf_disk_radius, float1=True)
        shader.setUniformVariable(key="uDebugMode", value=0, boolean=True)
        shader.setUniformVariable(key="uShadowBias", value=AppState.shadow_bias, float1=True)
        shader.setUniformVariable(key="uLitColorViz", value=[0.0, 1.0, 0.0], float3=True)
        shader.setUniformVariable(key="uShadowColorViz", value=[1.0, 0.0, 0.0], float3=True)

    # Two-pass render: shadow-map depth pass from the light, then the lit pass with shadows.
    # Cull back faces for this render only: the app disables culling globally (some examples rely
    # on double-sided geometry), but our terrain is a single zero-thickness plane, and without
    # culling its back face renders too -- with the exact same shadow test result as the front
    # face, since that test only depends on world position, not which side you're viewing from.
    # Seen from below, that showed the cubes'/spheres'/etc. shadow silhouettes burned through the
    # terrain. Culling back faces means the underside simply isn't drawn.
    gl.glEnable(gl.GL_CULL_FACE)
    gl.glCullFace(gl.GL_BACK)
    shadowSystem.render(scene.world.root)
    gl.glDisable(gl.GL_CULL_FACE)
    if AppState.show_shadow_map:
        shadowSystem.render_debug_view()

    # poll shortcuts (incl. Screenshot) only after this frame's geometry has actually been drawn,
    # so a screenshot captures real pixels instead of the just-cleared background color
    menu_bar.poll_shortcuts()
    scene.render_post()

scene.shutdown()
