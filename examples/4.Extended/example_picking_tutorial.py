"""
Tutorial version of example_picking_multiple_shapes_menu.py, meant to be easy to read and easy to
extend if you're taking this course.

The heavy lifting -- building meshes, wiring up shaders, the click-to-orbit camera math -- lives
in scene_helpers.py, right next to this file. You don't need to read it to use it: everything you
need is a builder.add_something(name, position=..., ...) call. Open scene_helpers.py only if
you're curious how a given add_*() call actually works.

WHAT YOU CAN CLICK: any object you add below. Clicking one prints its name/picking-id to the
console and starts orbiting the camera around it -- then W/A/S/D rotates, +/- zooms.

TO ADD YOUR OWN OBJECT: jump to the "2. ADD OBJECTS TO THE SCENE" section below and copy one of
the builder.add_*() lines. Everything you add is automatically lit and casts/receives real-time
shadows from the scene's lights -- you don't set that up per object.

View > Lights... (shortcut "3") adds/removes/edits point, directional and spotlight lights (see
scene_helpers.LightManager). View > Projection... (shortcut "4") switches the camera between
perspective and orthographic (see scene_helpers.ProjectionSettings).
"""

from pathlib import Path

import imgui
import sdl2
import OpenGL.GL as gl

import Elements.pyECSS.math_utilities as util
import Elements.utils.Shortcuts as Shortcuts
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform
from Elements.pyECSS.System import TransformSystem
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GUI.Viewer import RenderGLStateSystem
from Elements.pyGLV.GUI.MenuBar import MenuBar, Keybinding
from Elements.pyGLV.GL.Shader import InitGLShaderSystem
from Elements.utils.Shortcuts import displayGUI_text
from Elements.definitions import TEXTURE_DIR
from Elements.extensions.Captions_Screenshot.screenshot import save_screenshot
from Elements.extensions.Shadows.ShadowShader import ShadowMappingSystem
from Elements.extensions.picking_buffer import PickingBuffer as pb
from Elements.extensions.showcase.scene_helpers import SceneBuilder, OrbitCamera, LightManager, ProjectionSettings


assignment_goals = (
    "Tutorial picking demo: click any object to print its name/id and orbit around it with\n"
    "W/A/S/D (+/- to zoom). See the menu bar for Screenshot/Wireframe/Shadows/Shortcuts actions,\n"
    "View > Lights... (3) for point/directional/spot lights, and View > Projection... (4) to\n"
    "switch perspective/orthographic. View > Shadow Settings... (2) tweaks the shadows live.\n"
    "Look at scene_helpers.py in this folder to see how add_cube()/add_sphere()/etc. work.\n"
)

width, height = 1280, 720


# ==============================================================================================
# 1. SCENE, CAMERA AND LIGHT
# ==============================================================================================
scene = Scene()
rootEntity = scene.world.createEntity(Entity(name="RooT"))

cameraEntity = scene.world.createEntity(Entity(name="entityCam1"))
scene.world.addEntityChild(rootEntity, cameraEntity)
scene.world.addComponent(cameraEntity, BasicTransform(name="trans1", trs=util.translate(0, 0, -12)))

eye = util.vec(0.0, 5.5, 11.0)
target = util.vec(0.0, 0.8, 0.0)
up = util.vec(0.0, 1.0, 0.0)

# Perspective vs orthographic, and all of the properties either one needs -- see
# View > Projection... (shortcut "4") below.
projSettings = ProjectionSettings(aspect=width / height)

# One point light by default; add more (and switch types) from View > Lights... (shortcut "3").
# Only lights[0] (the "primary" light) can cast real-time shadows, and only while it's a Point
# light -- see LightManager's docstring in scene_helpers.py for why.
lightManager = LightManager(position=(4.0, 8.0, 5.0), color=(1.0, 1.0, 1.0))


# ==============================================================================================
# 2. ADD OBJECTS TO THE SCENE -- this is the part you'll want to edit
# ==============================================================================================
builder = SceneBuilder(scene, rootEntity)

builder.add_terrain()  # the ground plane; everything below sits on top of it (y ~= 0)

# add_cube(name, position, scale=1.0, color=(r, g, b))
# `scale` is the cube's side length; a cube sits on top of y=0, so position's y is usually 0.
builder.add_cube("RedCube", position=(-4.0, 0.0, -1.5), scale=1.0, color=(0.9, 0.25, 0.2))
builder.add_cube("BlueCube", position=(-2.0, 0.0, -1.5), scale=0.7, color=(0.2, 0.5, 0.9))
builder.add_cube("YellowCube", position=(0.0, 0.0, -1.5), scale=0.9, color=(0.95, 0.8, 0.2))

# add_sphere(name, position, scale=1.0, color=(r, g, b)) -- a sphere is centered on `position`,
# so give it y = half its scale to make it sit on the ground instead of half-buried in it.
builder.add_sphere("RedSphere", position=(-3.0, 0.45, 1.5), scale=0.9, color=(0.9, 0.3, 0.25))
builder.add_sphere("GreenSphere", position=(-0.5, 0.35, 1.5), scale=0.7, color=(0.3, 0.75, 0.4))

# add_cylinder(name, position, scale=1.0, color=(r,g,b), radius=0.5, height=1.0)
builder.add_cylinder("PurpleCylinder", position=(2.0, 0.5, 1.5), color=(0.55, 0.35, 0.85), radius=0.4, height=1.0)

# add_cone(name, position, scale=1.0, color=(r,g,b), radius=0.5, height=1.0)
builder.add_cone("YellowCone", position=(4.0, 0.6, 1.5), color=(0.85, 0.8, 0.2), radius=0.55, height=1.2)

# A cube textured with a real image instead of a flat color -- see step 4 below for
# builder.apply_texture(), which needs a GL window to already exist.
builder.add_textured_cube("DiceCube", position=(4.0, 0.5, -1.5))

# <-- add your own object here, e.g.:
# builder.add_sphere("MySphere", position=(0.0, 1.0, 0.0), scale=2.0, color=(0.2, 0.9, 0.6))


# ==============================================================================================
# 3. ECS SYSTEMS (framework plumbing: these walk the scene each frame and do the actual work)
# ==============================================================================================
transUpdate = scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
initUpdate = scene.world.createSystem(InitGLShaderSystem())

light_Entity = scene.world.createEntity(Entity(name="light_Entity"))
scene.world.addEntityChild(rootEntity, light_Entity)
lightTrans = scene.world.addComponent(
    light_Entity, BasicTransform(name="light_Entity_trans", trs=util.translate(*lightManager.primary.position))
)
shadowSystem = scene.world.createSystem(
    ShadowMappingSystem(name="ShadowSystem", lightNode=light_Entity, lightTargetNode=None, shadowMapSize=2048, lightType="point")
)

pickingSystem = pb.PickingSystem(width, height)
scene.world.createSystem(pickingSystem)


# ==============================================================================================
# 4. OPEN THE WINDOW (everything above only describes the scene; nothing is drawn until here)
# ==============================================================================================
scene.init(imgui=True, windowWidth=width, windowHeight=height, windowTitle="Elements: Picking Tutorial", openGLversion=4)

shadowSystem.init()
shadowSystem.set_viewport_dimensions(width, height)
builder.init_shaders()  # compiles every add_*() call's shader -- needs the GL context we just made
scene.world.traverse_visit(initUpdate, scene.world.root)

builder.apply_texture("DiceCube", TEXTURE_DIR / "3x3.jpg")  # also needs the GL context to exist

eManager = scene.world.eventManager
gWindow = scene.renderWindow
gGUI = scene.gContext
renderGLEventActuator = RenderGLStateSystem()
eManager._subscribers["OnUpdateWireframe"] = gWindow
eManager._actuators["OnUpdateWireframe"] = renderGLEventActuator
eManager._subscribers["OnUpdateCamera"] = gWindow
eManager._actuators["OnUpdateCamera"] = renderGLEventActuator

orbitCamera = OrbitCamera(gWindow, scene.gContext, eye, target, up)
pickingSystem.set_camera_matrices(projSettings.matrix(), orbitCamera.view)
pickingSystem.init()


# ==============================================================================================
# 5. MENU BAR: File > Screenshot, View > Wireframe/Shadows/Shadow Settings/Lights/Projection,
#              Help > Shortcuts
# ==============================================================================================
class AppState:
    running = True
    shadows_enabled = True
    show_shadow_settings = False
    soft_shadows = True
    pcf_disk_radius = 0.5
    shadow_bias = 0.15
    show_shadow_map = False
    view_from_light = False
    show_lights = False
    show_projection = False


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


def toggle_lights_panel():
    AppState.show_lights = not AppState.show_lights


def toggle_projection_panel():
    AppState.show_projection = not AppState.show_projection


menu_bar = MenuBar()

file_menu = menu_bar.add_menu("File")
file_menu.add_item("screenshot", "Screenshot", take_screenshot, Keybinding(sdl2.SDL_SCANCODE_P))
file_menu.add_item("quit", "Quit", quit_app, shortcut_label="Esc")  # Esc already quits (RenderDecorator)

view_menu = menu_bar.add_menu("View")
view_menu.add_item("wireframe", "Toggle Wireframe", gGUI.toggle_Wireframe, shortcut_label="F")  # already global
view_menu.add_item("shadows", "Toggle Shadows", toggle_shadows, Keybinding(sdl2.SDL_SCANCODE_1))
view_menu.add_item("shadow_settings", "Shadow Settings...", toggle_shadow_settings_panel, Keybinding(sdl2.SDL_SCANCODE_2))
view_menu.add_item("lights", "Lights...", toggle_lights_panel, Keybinding(sdl2.SDL_SCANCODE_3))
view_menu.add_item("projection", "Projection...", toggle_projection_panel, Keybinding(sdl2.SDL_SCANCODE_4))

help_menu = menu_bar.add_menu("Help")
help_menu.add_item(
    "shortcuts", "Keyboard Shortcuts", toggle_shortcuts_window, Keybinding(sdl2.SDL_SCANCODE_SLASH, sdl2.KMOD_GUI)
)

# Written next to this script on first run; hand-edit it (e.g. "mods": "Alt") to change a
# shortcut without touching this file. See MenuBar.py for the "mods" format.
keybindings_path = Path(__file__).with_name("example_picking_tutorial_keybindings.json")
if not keybindings_path.exists():
    menu_bar.save_keybindings_json(keybindings_path)
menu_bar.load_keybindings_json(keybindings_path)


# ==============================================================================================
# 6. MAIN RENDER LOOP
# ==============================================================================================
running = True
while running and AppState.running:
    running = scene.render()  # clears the frame, processes SDL input
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

    if AppState.show_lights:
        AppState.show_lights = lightManager.draw_panel()

    if AppState.show_projection:
        AppState.show_projection = projSettings.draw_panel()

    # keep the projection's aspect in sync with the *actual* window size -- otherwise, after a
    # resize, it's stale (whatever it was at startup or last set from the panel below), and the
    # scene looks stretched/squashed relative to the new window shape.
    projSettings.aspect = scene.renderWindow._windowWidth / scene.renderWindow._windowHeight

    # the projection can change every frame from the panel above; recompute it each frame
    projMat = projSettings.matrix()

    # -- camera: free-flies until you click something below, then W/A/S/D orbits it --
    orbitCamera.handle_keys(sdl2.SDL_GetKeyboardState(None))
    view = orbitCamera.view

    # PickingSystem's own FBO (and the viewport it renders into) is a fixed size set at
    # construction; it has a resize() that reallocates it, but nothing was ever calling it, so
    # after a window resize the picking pass kept rendering into (and reading pixels from) the
    # *old* window size -- clicks were being tested against where objects used to be. Only
    # actually resize (a real GL texture/renderbuffer reallocation) when the size changed.
    if (pickingSystem.width, pickingSystem.height) != (scene.renderWindow._windowWidth, scene.renderWindow._windowHeight):
        pickingSystem.resize(scene.renderWindow._windowWidth, scene.renderWindow._windowHeight)

    # -- picking: did the user click the window this frame? --
    click_coords = pickingSystem.check_for_click()
    if click_coords:
        mouse_x, mouse_y = click_coords
        pickingSystem.set_camera_matrices(projMat, view)
        pickingSystem.begin_picking_pass()
        scene.world.traverse_visit(pickingSystem, scene.world.root)
        pickingSystem.end_picking_pass()

        entity, picked_id = pickingSystem.pick(mouse_x, mouse_y, scene.renderWindow._windowHeight)
        if entity is None:
            print(f"Picked id: {picked_id} -> no entity")
        else:
            print(f"Picked id: {picked_id} -> {entity.name}")
            if entity.name in builder.objects:
                orbitCamera.focus_on(builder.objects[entity.name])

    # ShadowMappingSystem reads the shadow-casting light's position from this transform every
    # frame, so keep it in sync with whatever the Lights panel set lights[0].position to.
    lightTrans.trs = util.translate(*lightManager.primary.position)

    # -- "View from Light" (Shadow Settings panel) only swaps what the *shaders* see as the
    # camera, as a debug aid -- it never touches orbitCamera/picking, which keep using `view`.
    if AppState.view_from_light:
        shader_view = util.lookat(lightManager.primary.position, util.vec(0.0, 0.0, 0.0), util.vec(0.0, 1.0, 0.0))
    else:
        shader_view = view

    builder.update_lighting(
        projMat, shader_view, lightManager, orbitCamera.eye,
        shadows_enabled=AppState.shadows_enabled, soft_shadows=AppState.soft_shadows,
        pcf_radius=AppState.pcf_disk_radius, shadow_bias=AppState.shadow_bias,
    )

    # ShadowMappingSystem.render() sets its own glViewport back to whatever it was last told
    # via set_viewport_dimensions() (once, at startup) -- keep it in sync with the *actual*
    # window size, or after a resize it clamps rendering back to the old size for the rest of
    # this frame.
    shadowSystem.set_viewport_dimensions(scene.renderWindow._windowWidth, scene.renderWindow._windowHeight)

    # Two-pass render: shadow-map depth pass from the light, then the lit pass with shadows.
    # Backface culling is scoped to just this render: without it, the paper-thin gap between the
    # terrain's front and back face would let its own back face show through from below.
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
