import os
import time
import math
import numpy as np
import imgui

import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, RenderMesh
from Elements.pyECSS.System import TransformSystem

from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GUI.Viewer import RenderGLStateSystem
from Elements.pyGLV.GUI.ImguiDecorator import ImGUIecssDecorator2

from Elements.extensions.BasicShapes.BasicShapes import Light

from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray

from OpenGL.GL import GL_LINES
import OpenGL.GL as gl

import Elements.utils.normals as norm
from Elements.utils.terrain import generateTerrain
from Elements.utils.Shortcuts import displayGUI_text


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SHADERS_DIR = os.path.join(BASE_DIR, "Shaders")

example_description = \
"This example demonstrates Phong lighting with MULTIPLE lights on TWO spheres.\n" \
"Sphere A (left): FLAT shading (flat normals per triangle).\n" \
"Sphere B (right): SMOOTH shading (vertex normals).\n" \
"Lights are managed dynamically through ImGUI (add/remove/animate/reset).\n\n" \
"You may move the camera using the mouse or the GUI.\n" \
"Hit ESC OR Close the window to quit."


# --- Custom Light Classes ---

class PointLight(Light):
    def __init__(self, name="PointLight", position=None, color=None, intensity=1.0):
        super().__init__(name, type="PointLight")
        self.light_type = 0  # 0=Point, 1=Directional, 2=Spot
        self.position = position if position is not None else util.vec(0.0, 2.0, 0.0)
        self.color = color if color is not None else [1.0, 1.0, 1.0]
        self.intensity = intensity
        self.direction = util.vec(0.0, -1.0, 0.0)
        self.cutoff = 0.0
        self.visible = True

        # Animation
        self.animate = False
        self.orbit_radius = 2.0
        self.orbit_speed = 1.0
        self.pulse_speed = 1.0
        self.base_intensity = intensity
        self.base_position = self.position


class DirectionalLight(Light):
    def __init__(self, name="DirectionalLight", direction=None, color=None, intensity=1.0):
        super().__init__(name, type="DirectionalLight")
        self.light_type = 1
        self.direction = direction if direction is not None else util.vec(0.0, -1.0, 0.0)
        self.position = util.vec(0.0, 0.0, 0.0)  # kept for uniform compatibility
        self.color = color if color is not None else [1.0, 1.0, 1.0]
        self.intensity = intensity
        self.cutoff = 0.0
        self.visible = True

        # Animation
        self.animate = False
        self.rotation_speed = 1.0
        self.pulse_speed = 1.0
        self.base_intensity = intensity
        self.base_direction = self.direction


class SpotLight(Light):
    def __init__(self, name="SpotLight", position=None, direction=None, color=None, intensity=1.0, cutoff=12.5):
        super().__init__(name, type="SpotLight")
        self.light_type = 2
        self.position = position if position is not None else util.vec(0.0, 2.0, 0.0)
        self.direction = direction if direction is not None else util.vec(0.0, -1.0, 0.0)
        self.color = color if color is not None else [1.0, 1.0, 1.0]
        self.intensity = intensity
        self.cutoff = cutoff
        self.visible = True

        # Animation
        self.animate = False
        self.orbit_radius = 2.0
        self.orbit_speed = 1.0
        self.pulse_speed = 1.0
        self.base_intensity = intensity
        self.base_position = self.position


def make_default_lights():
    return [
        PointLight("Light_Red",    position=util.vec( 2.0, 2.0, 2.0), color=[1.0, 0.0, 0.0], intensity=1.0),
        PointLight("Light_Green",  position=util.vec(-2.0, 2.0, 2.0), color=[0.0, 1.0, 0.0], intensity=1.0),
        PointLight("Light_Blue",   position=util.vec( 2.0, 2.0,-2.0), color=[0.0, 0.0, 1.0], intensity=1.0),
        PointLight("Light_Yellow", position=util.vec(-2.0, 2.0,-2.0), color=[1.0, 1.0, 0.0], intensity=1.0),
        DirectionalLight("Dir_Light", direction=util.vec(-0.3, -1.0, -0.2), color=[0.7, 0.8, 1.0], intensity=0.8),
        SpotLight("Spot_Light", position=util.vec(-2.5, 2.5, 1.5), direction=util.vec(1.0, -1.0, -0.2), color=[1.0, 1.0, 1.0], intensity=1.0, cutoff=18.0)
    ]


# --- ImGUI Decorator ---

class ImGUISpheresDecorator(ImGUIecssDecorator2):
    """ImGUI panel for dynamic light management + sphere toggles"""
    def __init__(self, wrapee, imguiContext=None):
        super().__init__(wrapee, imguiContext)

        self._lights_list = []
        self._light_counter = 0

        # Material/Ambient
        self.ambient_strength = 0.2
        self.ambient_color = [1.0, 1.0, 1.0]
        self.shininess = 32.0

        # Rotation
        self.rotate_objects = False
        self.rotation_speed = 1.0  # degrees per frame
        self.reset_rotation = False

        # Sphere colors
        self._flat_sphere_color = [0.9, 0.9, 0.9]
        self._smooth_sphere_color = [0.9, 0.6, 0.2]
        
        # Show/Hide spheres
        self._show_flat_sphere = True
        self._show_smooth_sphere = True
        
        # Reset lights
        self.reset_lights = False

    def scenegraphVisualiser(self):
        imgui.begin("Multiple Lights + Spheres Control Panel")
        imgui.columns(1, "Controls")

        imgui.text("Material/Ambient:")
        _, self.ambient_strength = imgui.slider_float("Ambient Strength", self.ambient_strength, 0.0, 1.0, "%.2f")
        _, self.ambient_color = imgui.color_edit3("Ambient Color",
                                                  self.ambient_color[0], self.ambient_color[1], self.ambient_color[2])
        _, self.shininess = imgui.slider_float("Shininess", self.shininess, 1.0, 256.0, "%.1f")
        imgui.separator()

        # Sphere material colors
        imgui.text("Sphere Controls:")
        imgui.text("Sphere Material Colors:")

        changed1, col1 = imgui.color_edit3("Flat Sphere Color",
                                  self._flat_sphere_color[0],
                                  self._flat_sphere_color[1],
                                  self._flat_sphere_color[2])
        if changed1:
            self._flat_sphere_color = [col1[0], col1[1], col1[2]]

        changed2, col2 = imgui.color_edit3("Smooth Sphere Color",
                                  self._smooth_sphere_color[0],
                                  self._smooth_sphere_color[1],
                                  self._smooth_sphere_color[2])
        if changed2:
            self._smooth_sphere_color = [col2[0], col2[1], col2[2]]
            
        
        _, self.rotate_objects = imgui.checkbox("Rotate Spheres", self.rotate_objects)
        _, self.rotation_speed = imgui.slider_float("Rotation Speed", self.rotation_speed, 0.0, 10.0, "%.2f")
        if imgui.button("Reset Rotation"):
            self.reset_rotation = True

        _, self._show_flat_sphere = imgui.checkbox("Show Flat Sphere", self._show_flat_sphere)
        _, self._show_smooth_sphere = imgui.checkbox("Show Smooth Sphere", self._show_smooth_sphere)

        imgui.separator()
        imgui.text("Lights Manager:")

        if imgui.button("Add Point Light"):
            light = PointLight(f"PointLight_{self._light_counter}",
                               position=util.vec(2.0, 2.0, 2.0),
                               color=[1.0, 1.0, 1.0])
            self._lights_list.append(light)
            self._light_counter += 1

        imgui.same_line()
        if imgui.button("Add Directional Light"):
            light = DirectionalLight(f"DirectionalLight_{self._light_counter}",
                                     direction=util.vec(0.0, -1.0, -1.0),
                                     color=[1.0, 1.0, 1.0])
            self._lights_list.append(light)
            self._light_counter += 1

        imgui.same_line()
        if imgui.button("Add Spot Light"):
            light = SpotLight(f"SpotLight_{self._light_counter}",
                              position=util.vec(2.0, 2.0, 2.0),
                              direction=util.vec(0.0, -1.0, 0.0),
                              color=[1.0, 1.0, 1.0])
            self._lights_list.append(light)
            self._light_counter += 1

        imgui.separator()
        imgui.text(f"Total Lights: {len(self._lights_list)}")
        imgui.separator()

        imgui.text("Light Properties:")
        lights_to_remove = []

        for idx, light in enumerate(self._lights_list):
            light_type_str = ["Point", "Directional", "Spot"][light.light_type]
            label = f"{light.name} ({light_type_str})"

            if imgui.tree_node(label):
                _, light.visible = imgui.checkbox(f"Visible##vis_{idx}", light.visible)
                _, light.intensity = imgui.slider_float(f"Intensity##int_{idx}", light.intensity, 0.0, 5.0, "%.2f")
                _, light.color = imgui.color_edit3(f"Color##col_{idx}", light.color[0], light.color[1], light.color[2])

                if light.light_type in [0, 2]:
                    changed_pos, pos_values = imgui.drag_float3(
                        f"Position##pos_{idx}",
                        light.position[0], light.position[1], light.position[2],
                        0.1, -10.0, 10.0, "%.2f"
                    )
                    if changed_pos:
                        light.position = util.vec(pos_values[0], pos_values[1], pos_values[2])

                if light.light_type in [1, 2]:
                    changed_dir, dir_values = imgui.drag_float3(
                        f"Direction##dir_{idx}",
                        light.direction[0], light.direction[1], light.direction[2],
                        0.1, -1.0, 1.0, "%.2f"
                    )
                    if changed_dir:
                        light.direction = util.vec(dir_values[0], dir_values[1], dir_values[2])

                if light.light_type == 2:
                    _, light.cutoff = imgui.slider_float(f"Cutoff##cut_{idx}", light.cutoff, 0.0, 90.0, "%.1f")

                imgui.separator()
                imgui.text("Animation:")
                _, light.animate = imgui.checkbox(f"Enable Animation##anim_{idx}", light.animate)

                if light.animate:
                    if light.light_type in [0, 2]:
                        _, light.orbit_radius = imgui.slider_float(f"Orbit Radius##orb_r_{idx}",
                                                                   light.orbit_radius, 0.1, 5.0, "%.2f")
                        _, light.orbit_speed = imgui.slider_float(f"Orbit Speed##orb_s_{idx}",
                                                                  light.orbit_speed, 0.1, 3.0, "%.2f")
                    _, light.pulse_speed = imgui.slider_float(f"Pulse Speed##pulse_{idx}",
                                                              light.pulse_speed, 0.1, 3.0, "%.2f")

                if imgui.button(f"Delete Light##del_{idx}"):
                    lights_to_remove.append(idx)

                imgui.tree_pop()

        for idx in sorted(lights_to_remove, reverse=True):
            del self._lights_list[idx]

        imgui.separator()
        if imgui.button("Reset Lights to Default##resetlights"):
            self.reset_lights = True

        imgui.separator()
        if imgui.button("Delete All Lights"):
            self._lights_list.clear()
            self._light_counter = 0

        imgui.end()


# --- Sphere generator ---
def generate_sphere(radius=1.0, num_latitude=26, num_longitude=26):
    vertices = []
    indices = []
    normals = []
    colors = []

    for i in range(num_latitude + 1):
        for j in range(num_longitude + 1):
            theta = (j / num_longitude) * (2.0 * np.pi)
            phi = (i / num_latitude) * np.pi

            x = radius * np.cos(theta) * np.sin(phi)
            y = radius * np.sin(theta) * np.sin(phi)
            z = radius * np.cos(phi)

            vertices.append([x, y, z, 1.0])

            n = np.array([x, y, z], dtype=np.float32)
            nlen = np.linalg.norm(n)
            if nlen > 1e-8:
                n = n / nlen
            normals.append([n[0], n[1], n[2], 0.0])

            # solid color
            colors.append([1.0, 1.0, 1.0, 1.0])

    for i in range(num_latitude):
        for j in range(num_longitude):
            first = i * (num_longitude + 1) + j
            second = first + num_longitude + 1

            indices.extend([first, second, first + 1])
            indices.extend([second, second + 1, first + 1])

    return (np.array(vertices, dtype=np.float32),
            np.array(indices, dtype=np.uint32),
            np.array(colors, dtype=np.float32),
            np.array(normals, dtype=np.float32))


# --- Scene Setup ---
k = 0.08
d = 0.030

winWidth = 1200
winHeight = 800

scene = Scene()
rootEntity = scene.world.createEntity(Entity(name="RooT"))

with open(os.path.join(SHADERS_DIR, "PHONG_MULTI_LIGHTS.vert"), "r") as f:
    phong_vert_src = f.read()
with open(os.path.join(SHADERS_DIR, "PHONG_MULTI_LIGHTS.frag"), "r") as f:
    phong_frag_src = f.read()

# Sphere geometry
sphere_vertices, sphere_indices, sphere_colors, sphere_normals_smooth = generate_sphere(radius=1.0, num_latitude=12, num_longitude=12)

# Smooth sphere uses normals directly
vertices_smooth = sphere_vertices
indices_smooth = sphere_indices
colors_smooth = sphere_colors
normals_smooth = sphere_normals_smooth

# Flat sphere, rebuilds flat normals per triangle
vertices_flat, indices_flat, colors_flat, normals_flat = norm.generateFlatNormalsMesh(
    sphere_vertices, sphere_indices, sphere_colors
)

# Left sphere, FLAT
node_flat = scene.world.createEntity(Entity(name="Sphere_Flat"))
scene.world.addEntityChild(rootEntity, node_flat)
scene.world.addComponent(node_flat, BasicTransform(name="Sphere_Flat_TRS", trs=util.translate(-1.6, 0.8, 0.0)))
mesh_flat = scene.world.addComponent(node_flat, RenderMesh(name="Sphere_Flat_mesh"))
mesh_flat.vertex_attributes.append(vertices_flat)
mesh_flat.vertex_attributes.append(colors_flat)
mesh_flat.vertex_attributes.append(normals_flat)
mesh_flat.vertex_index.append(indices_flat)
scene.world.addComponent(node_flat, VertexArray())
shader_flat = scene.world.addComponent(
    node_flat, ShaderGLDecorator(Shader(vertex_source=phong_vert_src, fragment_source=phong_frag_src))
)

# Right sphere, SMOOTH
node_smooth = scene.world.createEntity(Entity(name="Sphere_Smooth"))
scene.world.addEntityChild(rootEntity, node_smooth)
scene.world.addComponent(node_smooth, BasicTransform(name="Sphere_Smooth_TRS", trs=util.translate(1.6, 0.8, 0.0)))
mesh_smooth = scene.world.addComponent(node_smooth, RenderMesh(name="Sphere_Smooth_mesh"))
mesh_smooth.vertex_attributes.append(vertices_smooth)
mesh_smooth.vertex_attributes.append(colors_smooth)
mesh_smooth.vertex_attributes.append(normals_smooth)
mesh_smooth.vertex_index.append(indices_smooth)
scene.world.addComponent(node_smooth, VertexArray())
shader_smooth = scene.world.addComponent(
    node_smooth, ShaderGLDecorator(Shader(vertex_source=phong_vert_src, fragment_source=phong_frag_src))
)

# Terrain, axes
vertexTerrain, indexTerrain, colorTerrain = generateTerrain(size=4, N=20)
terrain = scene.world.createEntity(Entity(name="terrain"))
scene.world.addEntityChild(rootEntity, terrain)
terrain_trans = scene.world.addComponent(terrain, BasicTransform(name="terrain_trans", trs=util.identity()))
terrain_mesh = scene.world.addComponent(terrain, RenderMesh(name="terrain_mesh"))
terrain_mesh.vertex_attributes.append(vertexTerrain)
terrain_mesh.vertex_attributes.append(colorTerrain)
terrain_mesh.vertex_index.append(indexTerrain)
scene.world.addComponent(terrain, VertexArray(primitive=GL_LINES))
terrain_shader = scene.world.addComponent(
    terrain, ShaderGLDecorator(Shader(vertex_source=Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG))
)

vertexAxes = np.array(
    [
        [0.0, 0.0, 0.0, 1.0],
        [1.5, 0.0, 0.0, 1.0],
        [0.0, 0.0, 0.0, 1.0],
        [0.0, 1.5, 0.0, 1.0],
        [0.0, 0.0, 0.0, 1.0],
        [0.0, 0.0, 1.5, 1.0],
    ],
    dtype=np.float32,
)
colorAxes = np.array(
    [
        [1.0, 0.0, 0.0, 1.0],
        [1.0, 0.0, 0.0, 1.0],
        [0.0, 1.0, 0.0, 1.0],
        [0.0, 1.0, 0.0, 1.0],
        [0.0, 0.0, 1.0, 1.0],
        [0.0, 0.0, 1.0, 1.0],
    ],
    dtype=np.float32,
)
indexAxes = np.array((0, 1, 2, 3, 4, 5), np.uint32)

axes = scene.world.createEntity(Entity(name="axes"))
scene.world.addEntityChild(rootEntity, axes)
axes_trans = scene.world.addComponent(axes, BasicTransform(name="axes_trans", trs=util.translate(0.0, 0.001, 0.0)))
axes_mesh = scene.world.addComponent(axes, RenderMesh(name="axes_mesh"))
axes_mesh.vertex_attributes.append(vertexAxes)
axes_mesh.vertex_attributes.append(colorAxes)
axes_mesh.vertex_index.append(indexAxes)
scene.world.addComponent(axes, VertexArray(primitive=gl.GL_LINES))
axes_shader = scene.world.addComponent(
    axes, ShaderGLDecorator(Shader(vertex_source=Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG))
)

# Systems
transUpdate = scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
renderUpdate = scene.world.createSystem(RenderGLShaderSystem())
initUpdate = scene.world.createSystem(InitGLShaderSystem())

scene.init(
    imgui=True,
    windowWidth=winWidth,
    windowHeight=winHeight,
    windowTitle="Two Spheres (Flat vs Smooth) + Multi-Lights",
    openGLversion=4,
    customImGUIdecorator=ImGUISpheresDecorator,
)
scene.world.traverse_visit(initUpdate, scene.world.root)

eManager = scene.world.eventManager
gWindow = scene.renderWindow
renderGLEventActuator = RenderGLStateSystem()
eManager._subscribers["OnUpdateWireframe"] = gWindow
eManager._actuators["OnUpdateWireframe"] = renderGLEventActuator
eManager._subscribers["OnUpdateCamera"] = gWindow
eManager._actuators["OnUpdateCamera"] = renderGLEventActuator

# Camera
eye0 = util.vec(2.8, 2.2, 3.5)
target0 = util.vec(0.0, 0.7, 0.0)
up0 = util.vec(0.0, 1.0, 0.0)
view0 = util.lookat(eye0, target0, up0)
projMat = util.perspective(50.0, winWidth / winHeight, 0.01, 100.0)
gWindow._myCamera = view0

# Init ImGUI lights
imgui_decorator = scene.gContext
for L in make_default_lights():
    imgui_decorator._lights_list.append(L)
    imgui_decorator._light_counter += 1

running = True
rot_angle = 0.0
start_time = time.time()

base_flat = util.translate(-1.6, 0.8, 0.0) @ util.scale(0.8)
base_smooth = util.translate(1.6, 0.8, 0.0) @ util.scale(0.8)

while running:
    running = scene.render()
    displayGUI_text(example_description)

    scene.world.traverse_visit(transUpdate, scene.world.root)
    view = gWindow._myCamera
    elapsed_time = time.time() - start_time

    if imgui_decorator.reset_rotation:
        rot_angle = 0.0
        imgui_decorator.reset_rotation = False

    if imgui_decorator.rotate_objects:
        rot_angle += float(imgui_decorator.rotation_speed)

    rot = util.rotate((0.0, 1.0, 0.0), rot_angle)
    model_flat = base_flat @ rot
    model_smooth = base_smooth @ rot

    # Reset lights to default rig if requested from GUI
    if imgui_decorator.reset_lights:
        imgui_decorator._lights_list = make_default_lights()
        imgui_decorator._light_counter = len(imgui_decorator._lights_list)
        imgui_decorator.reset_lights = False

    # Animate lights
    for light in imgui_decorator._lights_list:
        if not light.animate:
            continue

        if light.light_type == 0:
            light.position = util.vec(
                light.orbit_radius * math.cos(elapsed_time * light.orbit_speed),
                light.base_position[1],
                light.orbit_radius * math.sin(elapsed_time * light.orbit_speed),
            )
            light.intensity = light.base_intensity * (0.5 + 0.5 * math.sin(elapsed_time * light.pulse_speed))

        elif light.light_type == 1:
            angle = elapsed_time * light.rotation_speed
            light.direction = util.vec(math.sin(angle), light.base_direction[1], math.cos(angle))
            light.intensity = light.base_intensity * (0.5 + 0.5 * math.sin(elapsed_time * light.pulse_speed))

        elif light.light_type == 2:
            light.position = util.vec(
                light.orbit_radius * math.cos(elapsed_time * light.orbit_speed),
                light.base_position[1],
                light.orbit_radius * math.sin(elapsed_time * light.orbit_speed),
            )
            light.intensity = light.base_intensity * (0.5 + 0.5 * math.sin(elapsed_time * light.pulse_speed))

    # Terrain/Axes
    terrain_shader.setUniformVariable(key="modelViewProj", value=projMat @ view @ terrain_trans.l2world, mat4=True)
    axes_shader.setUniformVariable(key="modelViewProj", value=projMat @ view @ axes_trans.l2world, mat4=True)

    # Camera position in world
    inv_view = util.inverse(view)
    cam_pos4 = inv_view @ np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32)
    w = float(cam_pos4[3])
    cam_pos = util.vec(float(cam_pos4[0]) / w, float(cam_pos4[1]) / w, float(cam_pos4[2]) / w)

    active_lights = [L for L in imgui_decorator._lights_list if L.visible]
    if len(active_lights) > 50:
        active_lights = active_lights[:50]

    if not imgui_decorator._show_flat_sphere:
        model_flat = util.translate(1000.0, 1000.0, 1000.0)
    if not imgui_decorator._show_smooth_sphere:
        model_smooth = util.translate(1000.0, 1000.0, 1000.0)

    for shaderDec, modelMat in [(shader_flat, model_flat), (shader_smooth, model_smooth)]:
        shaderDec.setUniformVariable(key="model", value=modelMat, mat4=True)
        shaderDec.setUniformVariable(key="View", value=view, mat4=True)
        shaderDec.setUniformVariable(key="Proj", value=projMat, mat4=True)

        shaderDec.setUniformVariable(key="viewPos", value=cam_pos, float3=True)

        shaderDec.setUniformVariable(key="ambientStrength", value=float(imgui_decorator.ambient_strength), float1=True)
        shaderDec.setUniformVariable(key="ambientColor", 
                                     value=util.vec(imgui_decorator.ambient_color[0], imgui_decorator.ambient_color[1], imgui_decorator.ambient_color[2]),
                                     float3=True)
        
        shaderDec.setUniformVariable(key="shininess", value=float(imgui_decorator.shininess), float1=True)

        shaderDec.setUniformVariable(key="k", value=k, float1=True)
        shaderDec.setUniformVariable(key="d", value=d, float1=True)

        shaderDec.setUniformVariable(key="numLights", value=float(len(active_lights)), float1=True)

        for i, light in enumerate(active_lights):
            shaderDec.setUniformVariable(key=f"lights[{i}].type", value=float(light.light_type), float1=True)
            shaderDec.setUniformVariable(key=f"lights[{i}].position", value=light.position, float3=True)
            shaderDec.setUniformVariable(key=f"lights[{i}].direction", value=light.direction, float3=True)
            shaderDec.setUniformVariable(key=f"lights[{i}].color",
                                         value=util.vec(light.color[0], light.color[1], light.color[2]),
                                         float3=True,)
            shaderDec.setUniformVariable(key=f"lights[{i}].intensity", value=float(light.intensity), float1=True)
            shaderDec.setUniformVariable(key=f"lights[{i}].cutoff", value=float(light.cutoff), float1=True)

    # flat sphere color
    colF = imgui_decorator._flat_sphere_color
    shader_flat.setUniformVariable(key="materialColor", value=util.vec(colF[0], colF[1], colF[2]), float3=True)
    shader_flat.setUniformVariable(key="is_solid_color", value=1.0, float1=True)

    # smooth sphere color
    colS = imgui_decorator._smooth_sphere_color
    shader_smooth.setUniformVariable(key="materialColor", value=util.vec(colS[0], colS[1], colS[2]), float3=True)
    shader_smooth.setUniformVariable(key="is_solid_color", value=1.0, float1=True)

    scene.world.traverse_visit(renderUpdate, scene.world.root)
    scene.render_post()

scene.shutdown()
