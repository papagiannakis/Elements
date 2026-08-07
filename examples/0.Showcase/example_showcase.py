"""
Improved/extended duplicate of example_picking_tutorial.py: same scene-building, picking,
click-to-orbit camera, lights, projection and shadows, plus four more rendering techniques, each
built with a helper class from showcase_helpers.py (in this same folder) so this script stays
readable -- open that file only if you're curious how a given feature works under the hood.

  View > Objects...    (5) -- an OBJ model (Teapot/Cow/Teddy) you can swap and toggle
                              smooth/flat shading on, as in
                              Normals_USDimporter_BSP/example_cow.py.
  View > Skybox...     (6) -- a cube-mapped sky around the scene, on by default, with a
                              swappable texture set, as in
                              examples/2.Intermediate/example_10_cube_mapping.py.
  View > Refraction... (7) -- a "glass" object (Bunny by default) that refracts the skybox
                              behind it, with a live refractive-index slider, as in
                              Refraction/refraction_example_bunny.py.
  View > Reflection... (8) -- a "mirror" object (Pig by default) that reflects the skybox,
                              tintable (Gold/Chrome/Blue presets or any custom color/strength),
                              as in environment_mapping/example_environment_mapping_pigs.py.

WHAT YOU CAN CLICK: any SceneBuilder object (cubes/spheres/etc., see section 2 below), the
ObjGallery model, or the currently-visible Refraction/Reflection model -- clicking one prints its
name/picking-id and starts orbiting the camera around it (W/A/S/D rotate, +/- zoom). Clicking the
skybox or empty space orbits around the world origin (0,0,0) instead.
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
from Elements.pyGLV.GL.Shader import InitGLShaderSystem, RenderGLShaderSystem
from Elements.utils.Shortcuts import displayGUI_text
from Elements.definitions import TEXTURE_DIR
from Elements.extensions.Captions_Screenshot.screenshot import save_screenshot
from Elements.extensions.Shadows.ShadowShader import ShadowMappingSystem
from Elements.extensions.picking_buffer import PickingBuffer as pb
from Elements.extensions.showcase.scene_helpers import SceneBuilder, OrbitCamera, LightManager, ProjectionSettings
from Elements.extensions.showcase.showcase_helpers import ObjGallery, Skybox, RefractionShowcase, ReflectionShowcase


assignment_goals = (
    "Picking showcase: click any cube/sphere/etc. to print its name/id and orbit around it with\n"
    "W/A/S/D (+/- to zoom). View > Lights.../Projection.../Shadow Settings... (3/4/2) tweak the\n"
    "point/directional/spot lights, perspective vs orthographic, and shadow quality live.\n"
    "View > Objects.../Skybox.../Refraction.../Reflection... (5/6/7/8) add an OBJ model viewer, a\n"
    "toggleable cube-mapped sky, a glass (refractive) object and a mirror (reflective) object.\n"
    "Look at scene_helpers.py / showcase_helpers.py in this folder to see how each works.\n"
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

builder.add_terrain(size=(14.0, 7.0))  # the ground plane; everything below sits on top of it (y ~= 0)

# add_cube(name, position, scale=1.0, color=(r, g, b))
# `scale` is the cube's side length; a cube sits on top of y=0, so position's y is usually 0.
builder.add_cube("BlueCube", position=(-2.0, 0.0, 1.5), scale=0.7, color=(0.2, 0.5, 0.9))

# add_torus(name, position, scale=1.0, color=(r,g,b), radius=0.5, tube_radius=None) -- radius is
# the ring's own size, tube_radius is the tube's thickness (defaults to 35% of radius); position's
# y should be tube_radius * scale so it rests on the ground instead of poking through it.
builder.add_torus("RedTorus", position=(-4.0, 0.3, 1.5), scale=1.7, color=(0.9, 0.25, 0.2), radius=0.4, tube_radius=0.15)

# add_sphere(name, position, scale=1.0, color=(r, g, b)) -- a sphere is centered on `position`,
# so give it y = half its scale to make it sit on the ground instead of half-buried in it.
builder.add_sphere("GreenSphere", position=(4.0, 0.35, 1.5), scale=0.7, color=(0.3, 0.75, 0.4))

# add_cylinder(name, position, scale=1.0, color=(r,g,b), radius=0.5, height=1.0)
builder.add_cylinder("PurpleCylinder", position=(2.0, 0.5, 1.5), color=(0.55, 0.35, 0.85), radius=0.4, height=1.0)

# add_cone(name, position, scale=1.0, color=(r,g,b), radius=0.5, height=1.0)
builder.add_cone("YellowCone", position=(0.0, 0.6, 1.5), color=(0.85, 0.8, 0.2), radius=0.55, height=1.2)

# A cube textured with a real image instead of a flat color -- see step 4 below for
# builder.apply_texture(), which needs a GL window to already exist.
builder.add_textured_cube("DiceCube", position=(1.5, 0.5, -1.5))

# <-- add your own object here, e.g.:
# builder.add_sphere("MySphere", position=(0.0, 1.0, 0.0), scale=2.0, color=(0.2, 0.9, 0.6))

# The four showcase features: each just needs an entity built now and (since Texture/Texture3D
# need a live GL context) its actual image/cubemap bound after scene.init() -- see section 4
# below. ObjGallery sits where YellowCube used to (removed above) so the scene doesn't get more
# crowded; scale_multiplier=3.0 on ObjGallery grows whichever model is picked to 3x its original
# (pre-showcase) size. Its y is a small lift, not a big one: teapot.obj's own base already sits at
# its local y=0 regardless of scale (no offset needed), so this is just enough clearance to avoid
# z-fighting with the terrain for the default model -- Cow/Teddy sit into the ground more when
# picked from the dropdown instead, since all three share this one position/transform.
# RefractionShowcase/ReflectionShowcase's y works the same way: it's the clearance above the
# terrain, not a per-model height -- each model variant is auto-lifted by its own bounding box so
# it never sinks into (or floats above) the ground, however it's scaled, no matter which one is
# picked from their dropdowns.
objGallery = ObjGallery(scene, rootEntity, position=(-1.5, 0.03, -1.5), scale_multiplier=3.0)
skybox = Skybox(scene, rootEntity, enabled=True)
refractionShowcase = RefractionShowcase(scene, rootEntity, position=(4.5, 0.03, -1.5))
reflectionShowcase = ReflectionShowcase(scene, rootEntity, position=(-4.5, 0.03, -1.5))


# ==============================================================================================
# 3. ECS SYSTEMS (framework plumbing: these walk the scene each frame and do the actual work)
# ==============================================================================================
transUpdate = scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
initUpdate = scene.world.createSystem(InitGLShaderSystem())
# Draws the showcase objects above: they use the plain Shader/ShaderGLDecorator pipeline (like
# most Elements examples), not ShadowShader/ShadowMappingSystem like SceneBuilder's objects, so
# they need their own render system/traversal (see the main loop below).
renderUpdate = scene.world.createSystem(RenderGLShaderSystem())

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
scene.init(imgui=True, windowWidth=width, windowHeight=height, windowTitle="Elements: Picking Showcase", openGLversion=4)

shadowSystem.init()
shadowSystem.set_viewport_dimensions(width, height)
builder.init_shaders()  # compiles every add_*() call's shader -- needs the GL context we just made

# Bind real images/cubemaps now that a GL context exists (Texture/Texture3D issue GL calls in
# their own constructors, so they can't be created any earlier).
skybox.load_textures()
refractionShowcase.load_textures(skybox.cubemap)
reflectionShowcase.build_shaders(skybox.cubemap)  # also creates Reflection's shaders (see its docstring)
builder.apply_texture("DiceCube", TEXTURE_DIR / "3x3.jpg")

# One traversal compiles every plain Shader/ShaderGLDecorator created above (ObjGallery, Skybox,
# RefractionShowcase, ReflectionShowcase) and uploads every entity's GPU vertex buffers.
scene.world.traverse_visit(initUpdate, scene.world.root)

eManager = scene.world.eventManager
gWindow = scene.renderWindow
gGUI = scene.gContext
renderGLEventActuator = RenderGLStateSystem()
eManager._subscribers["OnUpdateWireframe"] = gWindow
eManager._actuators["OnUpdateWireframe"] = renderGLEventActuator
eManager._subscribers["OnUpdateCamera"] = gWindow
eManager._actuators["OnUpdateCamera"] = renderGLEventActuator

# zoom_speed is half OrbitCamera's default (0.35) -- the default felt too fast when zooming
# with +/-.
orbitCamera = OrbitCamera(gWindow, scene.gContext, eye, target, up, zoom_speed=0.175)
pickingSystem.set_camera_matrices(projSettings.matrix(), orbitCamera.view)
pickingSystem.init()


# ==============================================================================================
# 5. MENU BAR
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
    show_objects = False
    show_skybox = False
    show_refraction = False
    show_reflection = False


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


def toggle_objects_panel():
    AppState.show_objects = not AppState.show_objects


def toggle_skybox_panel():
    AppState.show_skybox = not AppState.show_skybox


def toggle_refraction_panel():
    AppState.show_refraction = not AppState.show_refraction


def toggle_reflection_panel():
    AppState.show_reflection = not AppState.show_reflection


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
view_menu.add_item("objects", "Objects...", toggle_objects_panel, Keybinding(sdl2.SDL_SCANCODE_5))
view_menu.add_item("skybox", "Skybox...", toggle_skybox_panel, Keybinding(sdl2.SDL_SCANCODE_6))
view_menu.add_item("refraction", "Refraction...", toggle_refraction_panel, Keybinding(sdl2.SDL_SCANCODE_7))
view_menu.add_item("reflection", "Reflection...", toggle_reflection_panel, Keybinding(sdl2.SDL_SCANCODE_8))

help_menu = menu_bar.add_menu("Help")
help_menu.add_item(
    "shortcuts", "Keyboard Shortcuts", toggle_shortcuts_window, Keybinding(sdl2.SDL_SCANCODE_SLASH, sdl2.KMOD_GUI)
)

# Written next to this script on first run; hand-edit it (e.g. "mods": "Alt") to change a
# shortcut without touching this file. See MenuBar.py for the "mods" format.
keybindings_path = Path(__file__).with_name("showcase_keybindings.json")
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

    if AppState.show_objects:
        AppState.show_objects, objects_changed = objGallery.draw_panel()
        if objects_changed:
            # swapping model/shading needs the new mesh re-uploaded to the GPU, same as
            # Normals_USDimporter_BSP/example_cow.py does in its own main loop
            scene.world.traverse_visit(initUpdate, scene.world.root)

    if AppState.show_skybox:
        AppState.show_skybox, skybox_texture_changed = skybox.draw_panel()
        if skybox_texture_changed:
            refractionShowcase.load_textures(skybox.cubemap)
            reflectionShowcase.rebind_cubemap(skybox.cubemap)

    if AppState.show_refraction:
        AppState.show_refraction = refractionShowcase.draw_panel()

    if AppState.show_reflection:
        AppState.show_reflection = reflectionShowcase.draw_panel()

    # keep the projection's aspect in sync with the *actual* window size -- otherwise, after a
    # resize, it's stale (whatever it was at startup or last set from the panel below), and
    # anything meant to fill the whole screen edge-to-edge (the skybox) visibly falls short of
    # the new window's edges instead of stretching to match, as in example_cow.py's main loop.
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
            # Nothing there to orbit -- fall back to the world origin instead of leaving
            # W/A/S/D/+/- doing nothing.
            orbitCamera.focus_on_point((0.0, 0.0, 0.0))
        else:
            print(f"Picked id: {picked_id} -> {entity.name}")
            # builder.objects covers the cubes/spheres/etc. from section 2; the showcase
            # features have their own pickable_objects since they're not SceneBuilder entities.
            pickable_objects = {
                **builder.objects,
                **objGallery.pickable_objects,
                **refractionShowcase.pickable_objects,
                **reflectionShowcase.pickable_objects,
            }
            if entity.name in pickable_objects:
                orbitCamera.focus_on(pickable_objects[entity.name])
            elif entity.name == skybox.entity.name:
                # The skybox has no fixed position to orbit around (it always surrounds the
                # camera) -- treat clicking it the same as clicking empty space.
                orbitCamera.focus_on_point((0.0, 0.0, 0.0))

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
    objGallery.update_lighting(lightManager, orbitCamera.eye)
    objGallery.update_transform(projMat, view)
    skybox.update(projMat, view)
    refractionShowcase.update(projMat, view, orbitCamera.eye)
    reflectionShowcase.update(projMat, view, orbitCamera.eye)

    # ShadowMappingSystem.render() sets its own glViewport back to whatever it was last told
    # via set_viewport_dimensions() (once, at startup) -- keep it in sync with the *actual*
    # window size, or after a resize it clamps rendering back to the old size for the rest of
    # this frame (everything drawn after it, including the skybox, would then get cut off at
    # the old width/height instead of covering the new, actual window).
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

    # Second render pass, for the showcase objects above (they're plain Shader/ShaderGLDecorator
    # entities, not ShadowShader ones, so shadowSystem.render() doesn't draw them -- see
    # RenderGLShaderSystem in section 3). Runs *after* shadowSystem.render() on purpose: that
    # call clears the whole screen before its own pass, which would erase these otherwise.
    scene.world.traverse_visit(renderUpdate, scene.world.root)

    # poll shortcuts (incl. Screenshot) only after this frame's geometry has actually been drawn,
    # so a screenshot captures real pixels instead of the just-cleared background color
    menu_bar.poll_shortcuts()
    scene.render_post()

scene.shutdown()
