import os
import numpy as np
import imgui
import time
import math

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
from Elements.pyGLV.GL.Textures import Texture
from Elements.utils.terrain import generateTerrain

# from Elements.definitions import TEXTURE_DIR
from Elements.utils.Shortcuts import displayGUI_text
from Elements.definitions import SHADER_DIR

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SHADERS_DIR = os.path.join(BASE_DIR, "Shaders")
TEXTURES_DIR = os.path.join(BASE_DIR, "Textures")


example_description = \
"This example demonstrates Phong lighting with MULTIPLE lights on THREE cubes.\n\
Cube 1: per-vertex colored (PHONG_MULTI_LIGHTS shaders, is_solid_color=0).\n\
Cube 2: solid material color (PHONG_MULTI_LIGHTS shaders, is_solid_color=1).\n\
Cube 3: textured (TEXTURE_PHONG_MULTI_LIGHTS shaders).\n\
Lights are managed dynamically through ImGUI (add/remove/animate).\n\n\
You may move the camera using the mouse or the GUI.\n\
Hit ESC OR Close the window to quit."


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
        self.position = util.vec(0.0, 0.0, 0.0)  # kept for attenuation path in shader
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
    # Start with all 3 light types (Point/Directional/Spot)
    return [
        PointLight("Light_Red",    position=util.vec( 2.0, 2.0, 2.0), color=[1.0, 0.0, 0.0], intensity=1.0),
        PointLight("Light_Green",  position=util.vec(-2.0, 2.0, 2.0), color=[0.0, 1.0, 0.0], intensity=1.0),
        PointLight("Light_Blue",   position=util.vec( 2.0, 2.0,-2.0), color=[0.0, 0.0, 1.0], intensity=1.0),
        PointLight("Light_Yellow", position=util.vec(-2.0, 2.0,-2.0), color=[1.0, 1.0, 0.0], intensity=1.0),
        DirectionalLight("Dir_Light", direction=util.vec(-0.3, -1.0, -0.2), color=[0.7, 0.8, 1.0], intensity=0.8),
        SpotLight("Spot_Light", position=util.vec(-2.5, 2.5, 1.5), direction=util.vec(1.0, -1.0, -0.2), color=[1.0, 1.0, 1.0], intensity=1.0,cutoff=18.0)
    ]

# --- ImGUI Decorator ---

class ImGUILeptoDecorator(ImGUIecssDecorator2):
    """ImGUI panel for dynamic light management + cube toggles"""

    def __init__(self, wrapee, imguiContext=None):
        super().__init__(wrapee, imguiContext)
        self._lights_list = []
        self._light_counter = 0

        # Material/Ambient
        self.ambient_strength = 0.2
        self.ambient_color = [1.0, 1.0, 1.0]
        self.shininess = 32.0
        
        # Rotation GUI
        self.rotate_cubes = False
        self.rotation_speed = 1.0  # degrees per frame
        self.reset_rotation = False
        self._show_vertex_cube = True
        self._show_solid_cube = True
        self._show_textured_cube = True


        # Solid material color (for the solid cube)
        self._solid_material_color = [0.9, 0.9, 0.9]
        
        # Reset Lights
        self.reset_lights = False

    def scenegraphVisualiser(self):
        imgui.begin("Multiple Lights Control Panel")
        imgui.columns(1, "LightControls")

        # Shader Params (material/ambient)
        imgui.text("Material/Ambient:")
        _, self.ambient_strength = imgui.slider_float("Ambient Strength", self.ambient_strength, 0.0, 1.0, "%.2f")
        _, self.ambient_color = imgui.color_edit3("Ambient Color", self.ambient_color[0], self.ambient_color[1], self.ambient_color[2],)
        _, self.shininess = imgui.slider_float("Shininess", self.shininess, 1.0, 256.0, "%.1f")
        imgui.separator()
        
        # Solid material color picker
        _, self._solid_material_color = imgui.color_edit3(
            "Solid Material Color",
            self._solid_material_color[0],
            self._solid_material_color[1],
            self._solid_material_color[2],
        )

        # Cube Rotation Controls
        imgui.text("Cube Controls:")
        _, self.rotate_cubes = imgui.checkbox("Rotate Cubes", self.rotate_cubes)
        _, self.rotation_speed = imgui.slider_float("Rotation Speed", self.rotation_speed, 0.0, 10.0, "%.2f")
        if imgui.button("Reset Rotation##resetrot"):
            self.reset_rotation = True
            
        # Show/Hide cubes
        _, self._show_vertex_cube = imgui.checkbox("Show Vertex-Color Cube", self._show_vertex_cube)
        _, self._show_solid_cube = imgui.checkbox("Show Solid-Material Cube", self._show_solid_cube)
        _, self._show_textured_cube = imgui.checkbox("Show Textured Cube", self._show_textured_cube)

    
       
        imgui.separator()
        # Add Light Buttons
        imgui.text("Lights Manager:")
        imgui.text("Create New Light:")
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
                            color=[1.0, 1.0, 1.0])
            self._lights_list.append(light)
            self._light_counter += 1
        
        imgui.separator() 
        imgui.text(f"Total Lights: {len(self._lights_list)}")
        imgui.separator()
        
        # Light List and Properties
        imgui.text("Light Properties:")
        lights_to_remove = []
        
        for idx, light in enumerate(self._lights_list):
            light_type_str = ["Point", "Directional", "Spot"][light.light_type]
            label = f"{light.name} ({light_type_str})"
            
            if imgui.tree_node(label):
                changed_vis, light.visible = imgui.checkbox(f"Visible##vis_{idx}", light.visible)
                
                changed_int, light.intensity = imgui.slider_float(f"Intensity##int_{idx}", 
                                                                   light.intensity, 0.0, 5.0, "%.2f")
                
                changed_col, light.color = imgui.color_edit3(f"Color##col_{idx}", 
                                                             light.color[0], light.color[1], light.color[2])
                
                if light.light_type in [0, 1, 2]:
                    changed_pos, pos_values = imgui.drag_float3(f"Position##pos_{idx}",
                                                                light.position[0],
                                                                light.position[1],
                                                                light.position[2],
                                                                0.1, -10.0, 10.0, "%.2f")
                    light.position = util.vec(pos_values[0], pos_values[1], pos_values[2])
                
                if light.light_type in [1, 2]:
                    changed_dir, dir_values = imgui.drag_float3(f"Direction##dir_{idx}",
                                                                light.direction[0],
                                                                light.direction[1],
                                                                light.direction[2],
                                                                0.1, -1.0, 1.0, "%.2f")
                    light.direction = util.vec(dir_values[0], dir_values[1], dir_values[2])
                
                if light.light_type == 2:
                    changed_cut, light.cutoff = imgui.slider_float(f"Cutoff##cut_{idx}",
                                                                   light.cutoff, 0.0, 90.0, "%.1f")
                
                imgui.separator()
                imgui.text("Animation:")
                changed_anim, light.animate = imgui.checkbox(f"Enable Animation##anim_{idx}", light.animate)
                
                if light.animate:
                    if light.light_type in [0, 2]:
                        changed_orb_r, light.orbit_radius = imgui.slider_float(f"Orbit Radius##orb_r_{idx}",
                                                                               light.orbit_radius, 0.1, 5.0, "%.2f")
                        changed_orb_s, light.orbit_speed = imgui.slider_float(f"Orbit Speed##orb_s_{idx}",
                                                                              light.orbit_speed, 0.1, 3.0, "%.2f")
                    
                    changed_pulse, light.pulse_speed = imgui.slider_float(f"Pulse Speed##pulse_{idx}",
                                                                          light.pulse_speed, 0.1, 3.0, "%.2f")
                
                if imgui.button(f"Delete Light##del_{idx}"):
                    lights_to_remove.append(idx)
                
                imgui.tree_pop()
        
        for idx in sorted(lights_to_remove, reverse=True):
            del self._lights_list[idx]
        
        # Delete/Restore Lights
        imgui.separator()
        if imgui.button("Reset Lights to Default##resetlights"):
            self.reset_lights = True
    
        imgui.separator()
        if imgui.button("Delete All Lights"):
            self._lights_list.clear()
            self._light_counter = 0
        
        imgui.end()


# --- Scene Setup ---

# Material / ambient / attenuation
AmbientColor = util.vec(1.0, 1.0, 1.0)
AmbientStrength = 0.2
Matshininess = 64.0

k = 0.08
d = 0.030

# Default lights
initial_lights = make_default_lights()

winWidth = 1200
winHeight = 800

scene = Scene()
rootEntity = scene.world.createEntity(Entity(name="RooT"))

# Shared cube geometry
vertexCube = np.array([
    [-0.5, -0.5, 0.5, 1.0],
    [-0.5, 0.5, 0.5, 1.0],
    [0.5, 0.5, 0.5, 1.0],
    [0.5, -0.5, 0.5, 1.0], 
    [-0.5, -0.5, -0.5, 1.0], 
    [-0.5, 0.5, -0.5, 1.0], 
    [0.5, 0.5, -0.5, 1.0], 
    [0.5, -0.5, -0.5, 1.0]
],dtype=np.float32)

indexCube = np.array((
    1,0,3, 1,3,2,
    2,3,7, 2,7,6,
    3,0,4, 3,4,7,
    6,5,1, 6,1,2,
    4,5,6, 4,6,7,
    5,4,0, 5,0,1
), np.uint32)

colorCube = np.array([
    [1,0,0,1],  # red
    [0,1,0,1],  # green
    [0,0,1,1],  # blue
    [1,1,0,1],  # yellow
    [1,0,1,1],  # magenta
    [0,1,1,1],  # cyan
    [1,1,1,1],  # white
    [0,0,0,1],  # black
], dtype=np.float32)

# vertices, indices, _, normals = norm.generateFlatNormalsMesh(vertexCube, indexCube)
# vertices, indices, colors, normals = norm.generateSmoothNormalsMesh(vertexCube , indexCube, colorCube)
vertices, indices, colors, normals = norm.generateFlatNormalsMesh(vertexCube , indexCube, colorCube)

# --- CUBES ---
# Cube 1: per-vertex colors (PHONG_MULTI_LIGHTS)
node_vtx = scene.world.createEntity(Entity(name="Cube_VertexColor"))
scene.world.addEntityChild(rootEntity, node_vtx)
trans_vtx = scene.world.addComponent(node_vtx, BasicTransform(name="Cube_VertexColor_TRS", trs=util.translate(-2.0, 0.5, 0.0)))

mesh_vtx = scene.world.addComponent(node_vtx, RenderMesh(name="Cube_VertexColor_mesh"))
mesh_vtx.vertex_attributes.append(vertices)
mesh_vtx.vertex_attributes.append(colors)
mesh_vtx.vertex_attributes.append(normals)
mesh_vtx.vertex_index.append(indices)
scene.world.addComponent(node_vtx, VertexArray())

# Cube 2: solid material color (PHONG_MULTI_LIGHTS)
node_solid = scene.world.createEntity(Entity(name="Cube_Solid"))
scene.world.addEntityChild(rootEntity, node_solid)
trans_solid = scene.world.addComponent(node_solid, BasicTransform(name="Cube_Solid_TRS", trs=util.translate(0.0, 0.5, 0.0)))

solid_color = np.ones((vertices.shape[0], 4), dtype=np.float32)

mesh_solid = scene.world.addComponent(node_solid, RenderMesh(name="Cube_Solid_mesh"))
mesh_solid.vertex_attributes.append(vertices)
mesh_solid.vertex_attributes.append(solid_color)
mesh_solid.vertex_attributes.append(normals)
mesh_solid.vertex_index.append(indices)
scene.world.addComponent(node_solid, VertexArray())

# Cube 3: textured (TEXTURE_PHONG_MULTI_LIGHTS)
node_tex = scene.world.createEntity(Entity(name="Cube_Textured"))
scene.world.addEntityChild(rootEntity, node_tex)
trans_tex = scene.world.addComponent(node_tex, BasicTransform(name="Cube_Textured_TRS", trs=util.translate(2.0, 0.5, 0.0)))

mesh_tex = scene.world.addComponent(node_tex, RenderMesh(name="Cube_Textured_mesh"))
mesh_tex.vertex_attributes.append(vertices)
mesh_tex.vertex_attributes.append(normals)
mesh_tex.vertex_attributes.append(Texture.CUBE_TEX_COORDINATES)
mesh_tex.vertex_index.append(indices)
scene.world.addComponent(node_tex, VertexArray())

# --- Shaders ---
# Shaders   
with open(os.path.join(SHADERS_DIR, "TEXTURE_PHONG_MULTI_LIGHTS.vert"), "r") as f:
    tex_phong_vert_src = f.read()
with open(os.path.join(SHADERS_DIR, "TEXTURE_PHONG_MULTI_LIGHTS.frag"), "r") as f:
    tex_phong_frag_src = f.read()

with open(os.path.join(SHADERS_DIR, "PHONG_MULTI_LIGHTS.vert"), "r") as f:
    phong_vert_src = f.read()
with open(os.path.join(SHADERS_DIR, "PHONG_MULTI_LIGHTS.frag"), "r") as f:
    phong_frag_src = f.read()

shader_tex = scene.world.addComponent(
    node_tex, ShaderGLDecorator(Shader(vertex_source = tex_phong_vert_src, fragment_source = tex_phong_frag_src))
)
shader_vtx = scene.world.addComponent(
    node_vtx, ShaderGLDecorator(Shader(vertex_source = phong_vert_src, fragment_source = phong_frag_src))
)
shader_solid = scene.world.addComponent(
    node_solid, ShaderGLDecorator(Shader(vertex_source = phong_vert_src, fragment_source = phong_frag_src))
)

# --- Terrain ---
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
    terrain, ShaderGLDecorator(Shader(vertex_import_file=SHADER_DIR / "ColorMVP.vert", fragment_import_file=SHADER_DIR / "Color.frag"))
)

# --- Axes ---
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
axes_shader = scene.world.addComponent(axes, ShaderGLDecorator(Shader(vertex_import_file=SHADER_DIR / "ColorMVP.vert", fragment_import_file=SHADER_DIR / "Color.frag")))

# --- Systems ---
transUpdate = scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
renderUpdate = scene.world.createSystem(RenderGLShaderSystem())
initUpdate = scene.world.createSystem(InitGLShaderSystem())

# Init window + GL
scene.init(
    imgui=True,
    windowWidth=winWidth,
    windowHeight=winHeight,
    windowTitle="Three Cubes + Multi-Lights",
    openGLversion=4,
    customImGUIdecorator=ImGUILeptoDecorator,
)

scene.world.traverse_visit(initUpdate, scene.world.root)

# Event manager wiring
eManager = scene.world.eventManager
gWindow = scene.renderWindow
renderGLEventActuator = RenderGLStateSystem()
eManager._subscribers["OnUpdateWireframe"] = gWindow
eManager._actuators["OnUpdateWireframe"] = renderGLEventActuator
eManager._subscribers["OnUpdateCamera"] = gWindow
eManager._actuators["OnUpdateCamera"] = renderGLEventActuator

# Camera
eye0 = util.vec(2.5, 2.5, 2.5)
target0 = util.vec(0.0, 0.0, 0.0)
up0 = util.vec(0.0, 1.0, 0.0)
view0 = util.lookat(eye0, target0, up0)
projMat = util.perspective(50.0, winWidth / winHeight, 0.01, 100.0)
gWindow._myCamera = view0

# Texture
texturePath = os.path.join(TEXTURES_DIR, "uoc_logo.png")
texture = Texture(texturePath)
shader_tex.setUniformVariable(key="ImageTexture", value=texture, texture=True)

# Init ImGUI lights
imgui_decorator = scene.gContext
for L in make_default_lights():
    imgui_decorator._lights_list.append(L)
    imgui_decorator._light_counter += 1

# Main loop
running = True
rot_angle = 0.0
start_time = time.time()

# Cubes' base transforms
base_vtx = util.translate(-2.0, 0.5, 0.0)
base_solid = util.translate(0.0, 0.5, 0.0)
base_tex = util.translate(2.0, 0.5, 0.0)

while running:
    running = scene.render()
    displayGUI_text(example_description)

    scene.world.traverse_visit(transUpdate, scene.world.root)
    view = gWindow._myCamera

    elapsed_time = time.time() - start_time
    
    # Cube Rotation
    if imgui_decorator.reset_rotation:
        rot_angle = 0.0
        imgui_decorator.reset_rotation = False

    if imgui_decorator.rotate_cubes:
        rot_angle += float(imgui_decorator.rotation_speed)

    rot = util.rotate((0.0, 1.0, 0.0), rot_angle)
    model_vtx = base_vtx @ rot
    model_solid = base_solid @ rot
    model_tex = base_tex @ rot
    
    # Reset lights to default rig if requested from GUI
    if imgui_decorator.reset_lights:
        imgui_decorator._lights_list = make_default_lights()
        imgui_decorator._light_counter = len(imgui_decorator._lights_list)
        imgui_decorator.reset_lights = False

    # Animate lights
    for light in imgui_decorator._lights_list:
        if not light.animate:
            continue

        if light.light_type == 0:  # Point
            light.position = util.vec(
                light.orbit_radius * math.cos(elapsed_time * light.orbit_speed),
                light.base_position[1],
                light.orbit_radius * math.sin(elapsed_time * light.orbit_speed),
            )
            light.intensity = light.base_intensity * (0.5 + 0.5 * math.sin(elapsed_time * light.pulse_speed))

        elif light.light_type == 1:  # Directional
            angle = elapsed_time * light.rotation_speed
            light.direction = util.vec(math.sin(angle), light.base_direction[1], math.cos(angle))
            light.intensity = light.base_intensity * (0.5 + 0.5 * math.sin(elapsed_time * light.pulse_speed))

        elif light.light_type == 2:  # Spot
            light.position = util.vec(
                light.orbit_radius * math.cos(elapsed_time * light.orbit_speed),
                light.base_position[1],
                light.orbit_radius * math.sin(elapsed_time * light.orbit_speed),
            )
            light.intensity = light.base_intensity * (0.5 + 0.5 * math.sin(elapsed_time * light.pulse_speed))

    # Terrain/Axes MVPs
    mvp_terrain = projMat @ view @ terrain_trans.l2world
    mvp_axes = projMat @ view @ axes_trans.l2world
    terrain_shader.setUniformVariable(key="modelViewProj", value=mvp_terrain, mat4=True)
    axes_shader.setUniformVariable(key="modelViewProj", value=mvp_axes, mat4=True)

    # Camera
    # shaderDecCube.setUniformVariable(key='viewPos', value=eye, float3=True)
    # correct position in world-space
    inv_view = util.inverse(view)
    cam_pos4 = inv_view @ np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32)
    w = float(cam_pos4[3])
    cam_pos = util.vec(float(cam_pos4[0]) / w, float(cam_pos4[1]) / w, float(cam_pos4[2]) / w)
    

    # Active lights
    active_lights = [L for L in imgui_decorator._lights_list if L.visible]
    if len(active_lights) > 50:
        active_lights = active_lights[:50]

    # Show/Hide via far-translation
    if not imgui_decorator._show_vertex_cube:
        model_vtx = util.translate(1000.0, 1000.0, 1000.0)
    if not imgui_decorator._show_solid_cube:
        model_solid = util.translate(1000.0, 1000.0, 1000.0)
    if not imgui_decorator._show_textured_cube:
        model_tex = util.translate(1000.0, 1000.0, 1000.0)
    
         
    # --- Common uniforms for ALL cube shaders ---
    for shaderDec, modelMat in [(shader_vtx, model_vtx), (shader_solid, model_solid), (shader_tex, model_tex)]:
        shaderDec.setUniformVariable(key="model", value=modelMat, mat4=True)
        shaderDec.setUniformVariable(key="View", value=view, mat4=True)
        shaderDec.setUniformVariable(key="Proj", value=projMat, mat4=True)

        # Camera
        shaderDec.setUniformVariable(key="viewPos", value=cam_pos, float3=True)
        
        # Ambient
        shaderDec.setUniformVariable(key="ambientStrength", value=float(imgui_decorator.ambient_strength), float1=True)
        shaderDec.setUniformVariable(key="ambientColor", 
                                     value=util.vec(imgui_decorator.ambient_color[0], imgui_decorator.ambient_color[1], imgui_decorator.ambient_color[2]),
                                     float3=True)

        # Material
        shaderDec.setUniformVariable(key="shininess", value=float(imgui_decorator.shininess), float1=True)
        
        # Attenuation constants
        shaderDec.setUniformVariable(key="k", value=k, float1=True)
        shaderDec.setUniformVariable(key="d", value=d, float1=True)

        # Lights
        shaderDec.setUniformVariable(key="numLights", value=float(len(active_lights)), float1=True)


        for i, light in enumerate(active_lights):
            shaderDec.setUniformVariable(key=f"lights[{i}].type", value=float(light.light_type), float1=True)
            shaderDec.setUniformVariable(key=f"lights[{i}].position", value=light.position, float3=True)
            shaderDec.setUniformVariable(key=f"lights[{i}].direction", value=light.direction, float3=True)
            shaderDec.setUniformVariable(key=f"lights[{i}].color", value=util.vec(light.color[0], light.color[1], light.color[2]), float3=True,)
            shaderDec.setUniformVariable(key=f"lights[{i}].intensity", value=float(light.intensity), float1=True)
            shaderDec.setUniformVariable(key=f"lights[{i}].cutoff", value=float(light.cutoff), float1=True)

    # Material/color for the non-textured cubes 
    # Cube 1: per-vertex colors (materialColor=(1,1,1), is_solid_color=0)
    shader_vtx.setUniformVariable(key="materialColor", value=util.vec(1.0, 1.0, 1.0), float3=True)
    shader_vtx.setUniformVariable(key="is_solid_color", value=0.0, float1=True)

    # Cube 2: solid material only (ignore vertex colors)
    solid_col = imgui_decorator._solid_material_color
    shader_solid.setUniformVariable(key="materialColor", value=util.vec(solid_col[0], solid_col[1], solid_col[2]), float3=True)
    shader_solid.setUniformVariable(key="is_solid_color", value=1.0, float1=True)

    scene.world.traverse_visit(renderUpdate, scene.world.root)
    scene.render_post()

scene.shutdown()

