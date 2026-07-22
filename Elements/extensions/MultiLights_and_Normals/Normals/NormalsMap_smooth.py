
import numpy as np
import imgui
import time
import math
import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, Camera, RenderMesh, Component
from Elements.pyECSS.System import TransformSystem, CameraSystem
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GUI.Viewer import RenderGLStateSystem
from Elements.pyGLV.GUI.ImguiDecorator import ImGUIecssDecorator2
from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray
from Elements.pyGLV.GL.Textures import Texture
from Elements.extensions.BasicShapes.BasicShapes import Light
import Elements.utils.normals as norm
from PIL import Image
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SHADERS_DIR = os.path.join(BASE_DIR, "Shaders")
TEXTURES_DIR = os.path.join(BASE_DIR, "Textures")


# --- Utility Functions ---

def normalize_safe(v, fallback):
    eps = 1e-8
    # Normalize a 3D vector, or returns fallback if it's too small
    l = np.linalg.norm(v)
    if l < eps:
        return fallback.copy()
    return v / l

def compute_tangent_bitangent(vertices, indices, uvs, normals):
    eps = 1e-8
    
    pos = vertices[:, :3].astype(np.float32)
    uv = uvs.astype(np.float32)
    nrm = normals[:, :3].astype(np.float32)

    N = len(pos)
    tan_acc = np.zeros((N, 3), dtype=np.float32)
    bit_acc = np.zeros((N, 3), dtype=np.float32)

    # Calculates tangents/bitangents per triangle and adds them to the triangle's vertices
    for t in range(0, len(indices), 3):
        i0 = int(indices[t])
        i1 = int(indices[t+1])
        i2 = int(indices[t+2])

        p0, p1, p2 = pos[i0], pos[i1], pos[i2]
        w0, w1, w2 = uv[i0], uv[i1], uv[i2]

        e1 = p1 - p0
        e2 = p2 - p0
        d1 = w1 - w0
        d2 = w2 - w0

        det = d1[0] * d2[1] - d2[0] * d1[1]
        if abs(det) < eps:
            continue

        r = 1.0 / det
        T = (e1 * d2[1] - e2 * d1[1]) * r
        B = (e2 * d1[0] - e1 * d2[0]) * r

        tan_acc[i0] += T
        tan_acc[i1] += T
        tan_acc[i2] += T
        
        bit_acc[i0] += B
        bit_acc[i1] += B
        bit_acc[i2] += B

    # Orthonormalizes per vertex + computes handedness
    tangents = np.zeros((N, 4), dtype=np.float32)
    bitangents = np.zeros((N, 4), dtype=np.float32)

    for i in range(N):
        # Normalizes the normal
        Ni = normalize_safe(nrm[i], np.array([0, 0, 1], dtype=np.float32))

        # Gram-Schmidt, removes the component of T along N
        Ti = tan_acc[i]
        Ti = Ti - Ni * np.dot(Ni, Ti)
        Ti = normalize_safe(Ti, np.array([1, 0, 0], dtype=np.float32))

        # Handedness sign, compares (cross(N,T)) vs accumulated bitangent
        Bi_acc = bit_acc[i]
        c = np.cross(Ni, Ti)
        handedness = 1.0 if np.dot(c, Bi_acc) >= 0.0 else -1.0

        # Reconstructs B so it's perfectly orthogonal
        Bi = c * handedness
        Bi = normalize_safe(Bi, np.array([0, 1, 0], dtype=np.float32))

        tangents[i, :3] = Ti
        tangents[i,  3] = handedness

        bitangents[i, :3] = Bi
        bitangents[i,  3] = 0.0

    return tangents, bitangents


def generate_cube_with_uvs():
    """Generate cube with UV coordinates"""
    # Create 24 vertices (4/face)
    positions = [
        # Front face
        [-0.5, -0.5,  0.5, 1.0], [ 0.5, -0.5,  0.5, 1.0], [ 0.5,  0.5,  0.5, 1.0], [-0.5,  0.5,  0.5, 1.0],
        # Right face
        [ 0.5, -0.5,  0.5, 1.0], [ 0.5, -0.5, -0.5, 1.0], [ 0.5,  0.5, -0.5, 1.0], [ 0.5,  0.5,  0.5, 1.0],
        # Back face
        [ 0.5, -0.5, -0.5, 1.0], [-0.5, -0.5, -0.5, 1.0], [-0.5,  0.5, -0.5, 1.0], [ 0.5,  0.5, -0.5, 1.0],
        # Left face
        [-0.5, -0.5, -0.5, 1.0], [-0.5, -0.5,  0.5, 1.0], [-0.5,  0.5,  0.5, 1.0], [-0.5,  0.5, -0.5, 1.0],
        # Top face
        [-0.5,  0.5,  0.5, 1.0], [ 0.5,  0.5,  0.5, 1.0], [ 0.5,  0.5, -0.5, 1.0], [-0.5,  0.5, -0.5, 1.0],
        # Bottom face
        [-0.5, -0.5, -0.5, 1.0], [ 0.5, -0.5, -0.5, 1.0], [ 0.5, -0.5,  0.5, 1.0], [-0.5, -0.5,  0.5, 1.0],
    ]

    vertices = np.array(positions, dtype=np.float32)
    colors = np.array([[1.0, 1.0, 1.0, 1.0]] * len(vertices), dtype=np.float32)

    # Indices (24= 6*2*3)
    indices = np.array([
        0, 1, 2, 0, 2, 3,       # Front
        4, 5, 6, 4, 6, 7,       # Right
        8, 9,10, 8,10,11,       # Back
       12,13,14,12,14,15,       # Left
       16,17,18,16,18,19,       # Top
       20,21,22,20,22,23,       # Bottom
    ], dtype=np.uint32)

    # UVs per face (each face has full texture)
    uvs = np.array([
        [0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0],
    ] * 6, dtype=np.float32)

    return vertices, colors, indices, uvs

# --- Custom Light Classes ---

class PointLight(Light):
    """Point light entity with transform and shader components"""
    def __init__(self, name="PointLight", position=None, color=None, intensity=1.0):
        super().__init__(name, type="PointLight")
        self.light_type = 0
        self.position = position if position is not None else util.vec(0.0, 2.0, 0.0)
        self.color = color if color is not None else [1.0, 1.0, 1.0]
        self.intensity = intensity
        self.direction = util.vec(0.0, -1.0, 0.0)
        self.cutoff = 0.0
        self.visible = True
        self.animate = False
        self.orbit_radius = 2.0
        self.orbit_speed = 1.0
        self.pulse_speed = 1.0
        self.base_intensity = intensity
        self.base_position = position if position is not None else util.vec(0.0, 2.0, 0.0)

class DirectionalLight(Light):
    """Directional light entity"""
    def __init__(self, name="DirectionalLight", direction=None, color=None, intensity=1.0):
        super().__init__(name, type="DirectionalLight")
        self.light_type = 1
        self.direction = direction if direction is not None else util.vec(0.0, -1.0, 0.0)
        self.position = util.vec(0.0, 0.0, 0.0)
        self.color = color if color is not None else [1.0, 1.0, 1.0]
        self.intensity = intensity
        self.cutoff = 0.0
        self.visible = True
        self.animate = False
        self.rotation_speed = 1.0
        self.pulse_speed = 1.0
        self.base_intensity = intensity
        self.base_direction = direction if direction is not None else util.vec(0.0, -1.0, 0.0)

class SpotLight(Light):
    """Spot light entity"""
    def __init__(self, name="SpotLight", position=None, direction=None, color=None, intensity=1.0, cutoff=12.5):
        super().__init__(name, type="SpotLight")
        self.light_type = 2
        self.position = position if position is not None else util.vec(0.0, 2.0, 0.0)
        self.direction = direction if direction is not None else util.vec(0.0, -1.0, 0.0)
        self.color = color if color is not None else [1.0, 1.0, 1.0]
        self.intensity = intensity
        self.cutoff = cutoff
        self.visible = True
        self.animate = False
        self.orbit_radius = 2.0
        self.orbit_speed = 1.0
        self.pulse_speed = 1.0
        self.base_intensity = intensity
        self.base_position = position if position is not None else util.vec(0.0, 2.0, 0.0)

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
# --- Custom ImGUI Decorator ---

class ImGUILeptoDecorator(ImGUIecssDecorator2):
    """Custom ImGUI decorator for Multi Lights and Normal Mapping support"""
    def __init__(self, wrapee, imguiContext=None):
        super().__init__(wrapee, imguiContext)
        self._lights_list = []
        self._light_counter = 0
        
        # normal mapping controls
        self.use_normal_map = True
        self.use_albedo_map = False
        self.debug_normals = False
        self.normal_strength = 1.0
        
        # Material/Ambient
        self.ambient_strength = 0.2
        self.shininess = 32.0

        # Rotation GUI
        self.rotate_cubes = False
        self.rotation_speed = 1.0  # degrees per frame
        self.reset_rotation = False
        
        # Reset Lights
        self.reset_lights = False
        
    def scenegraphVisualiser(self):
        """Display the ECSS and light controls in ImGUI"""
        imgui.begin("Normal Map Control Panel")
        imgui.columns(1, "LightControls")
        
        # Normal Mapping Controls 
        imgui.text("Normal Mapping:")
        changed_nm, self.use_normal_map = imgui.checkbox("Enable Normal Map", self.use_normal_map)
        if self.use_normal_map:
            changed_ns, self.normal_strength = imgui.slider_float("Normal Strength", self.normal_strength, 0.0, 2.0, "%.2f")

        # Albedo (diffuse) texture toggle
        changed_ab, self.use_albedo_map = imgui.checkbox("Use Albedo Map", self.use_albedo_map)
        if self.use_albedo_map:
            imgui.text("Place an albedo PNG named 'albedo.png' in the script folder.")

        # Debug normals visualization
        changed_dbg, self.debug_normals = imgui.checkbox("Debug: Show Normals", self.debug_normals)
        
        imgui.separator()
        
        # Shader Params (material/ambient)
        imgui.text("Material/Ambient:")
        _, self.ambient_strength = imgui.slider_float("Ambient Strength", self.ambient_strength, 0.0, 1.0, "%.2f")
        _, self.shininess = imgui.slider_float("Shininess", self.shininess, 1.0, 256.0, "%.1f")
        imgui.separator()

        # Cube Rotation Controls
        imgui.text("Cube Rotation:")
        _, self.rotate_cubes = imgui.checkbox("Rotate Cubes##rot", self.rotate_cubes)
        _, self.rotation_speed = imgui.slider_float("Rotation Speed (deg/frame)##rotspeed", self.rotation_speed, 0.0, 10.0, "%.2f")
        if imgui.button("Reset Rotation##resetrot"):
            self.reset_rotation = True

        imgui.separator()
        
        # Add Light Buttons
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

scene = Scene()    
rootEntity = scene.world.createEntity(Entity(name="RooT"))

# Default lights
initial_lights = make_default_lights()

# Camera Setup
entityCam1 = scene.world.createEntity(Entity(name="Entity1"))
scene.world.addEntityChild(rootEntity, entityCam1)
trans1 = scene.world.addComponent(entityCam1, BasicTransform(name="Entity1_TRS", trs=util.translate(0,0,-8)))

eye = util.vec(0.0, 2.5, 6.0)
target = util.vec(0.0, 0.5, 0.0)
up = util.vec(0.0, 1.0, 0.0)
view = util.lookat(eye, target, up)
projMat = util.perspective(50.0, 1200/800, 0.01, 100.0)   

entityCam2 = scene.world.createEntity(Entity(name="Entity_Camera"))
scene.world.addEntityChild(entityCam1, entityCam2)
trans2 = scene.world.addComponent(entityCam2, BasicTransform(name="Camera_TRS", trs=util.identity()))
mainCam = scene.world.addComponent(entityCam2, Camera(util.inverse(view), "mainCam","Camera","500"))

# --- Cube Creation with Normal Mapping Support ---

nodeCube = scene.world.createEntity(Entity(name="Cube"))
scene.world.addEntityChild(rootEntity, nodeCube)
transCube = scene.world.addComponent(nodeCube, BasicTransform(name="Cube_TRS", trs=util.translate(0,0.5,0)))
meshCube = scene.world.addComponent(nodeCube, RenderMesh(name="Cube_Mesh"))

# Generate cube with UV coordinates
vertexCube, colorCube, indexCube, uvsCube = generate_cube_with_uvs()

# Compute normals from vertices per-face
vertices = vertexCube
indices = indexCube
colors = colorCube

# Compute flat face normals first
normals = np.zeros_like(vertices, dtype=np.float32)
for i in range(0, len(indices), 3):
    ia, ib, ic = int(indices[i]), int(indices[i+1]), int(indices[i+2])
    v0 = vertices[ia][:3]
    v1 = vertices[ib][:3]
    v2 = vertices[ic][:3]
    face_normal = np.cross(v1 - v0, v2 - v0)
    fn = face_normal / (np.linalg.norm(face_normal) + 1e-9)
    normals[ia][:3] = fn
    normals[ib][:3] = fn
    normals[ic][:3] = fn

# Group verices by position and average normals
# for smooth shading
pos_groups = {}
for idx, v in enumerate(vertices):
    key = (float(v[0]), float(v[1]), float(v[2]))
    pos_groups.setdefault(key, []).append(idx)

for key, idxs in pos_groups.items():
    avg = np.zeros(3, dtype=np.float32)
    for i in idxs:
        avg += normals[i][:3]
    avg_len = np.linalg.norm(avg) + 1e-9
    avg_normal = (avg / avg_len)
    for i in idxs:
        normals[i][0:3] = avg_normal

normals[:, 3] = 0.0

# Compute tangent and bitangent vectors
tangents, bitangents = compute_tangent_bitangent(vertices, indices, uvsCube, normals)

# Add vertex attributes
meshCube.vertex_attributes.append(vertices)      # Position
meshCube.vertex_attributes.append(colors)        # Color
meshCube.vertex_attributes.append(normals)       # Normal
meshCube.vertex_attributes.append(uvsCube)       # UV coordinates
meshCube.vertex_attributes.append(tangents)      # Tangent
meshCube.vertex_attributes.append(bitangents)    # Bitangent
meshCube.vertex_index.append(indices)

vArrayCube = scene.world.addComponent(nodeCube, VertexArray())

# Shaders
with open(os.path.join(SHADERS_DIR, "PHONG_NORMALS_v2.vert"), "r", encoding="utf-8") as f:
    vertex_shader_source = f.read()

with open(os.path.join(SHADERS_DIR, "PHONG_NORMALS_v2.frag"), "r", encoding="utf-8") as f:
    fragment_shader_source = f.read()
    
shaderDecCube = scene.world.addComponent(nodeCube, ShaderGLDecorator(Shader(vertex_source = vertex_shader_source, fragment_source = fragment_shader_source)))


# Textures/Normals
normal_map_path = os.path.join(TEXTURES_DIR, "tiles.png")
normal_map_texture = None
albedo_map_path = os.path.join(TEXTURES_DIR, "albedo.png")
albedo_texture = None

# --- Create a Simple Normal Map ---
# This creates a simple embossed-style normal map
if not os.path.exists(normal_map_path):
    os.makedirs(TEXTURES_DIR, exist_ok=True)
    # Create a simple normal map (blue-dominant for relatively flat surfaces with slight detail)
    normal_map = Image.new('RGB', (256, 256), color=(128, 128, 255))
    # Add some texture detail
    pixels = normal_map.load()
    for i in range(0, 256, 32):
        for j in range(0, 256, 32):
            for di in range(16):
                for dj in range(16):
                    if 0 <= i+di < 256 and 0 <= j+dj < 256:
                        pixels[i+di, j+dj] = (150, 150, 200)
    normal_map.save(normal_map_path)
    

# --- Systems Setup ---
transUpdate = scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
camUpdate = scene.world.createSystem(CameraSystem("camUpdate", "CameraUpdate", "200"))
renderUpdate = scene.world.createSystem(RenderGLShaderSystem())
initUpdate = scene.world.createSystem(InitGLShaderSystem())

# --- Main Loop ---
scene.init(imgui=True, windowWidth=1200, windowHeight=800, windowTitle="Normal Mapping with Multiple Lights", 
           openGLversion=4, customImGUIdecorator=ImGUILeptoDecorator)
scene.world.traverse_visit(initUpdate, scene.world.root)

eManager = scene.world.eventManager
gWindow = scene.renderWindow
renderGLEventActuator = RenderGLStateSystem()
eManager._subscribers['OnUpdateWireframe'] = gWindow
eManager._actuators['OnUpdateWireframe'] = renderGLEventActuator
eManager._subscribers['OnUpdateCamera'] = gWindow 
eManager._actuators['OnUpdateCamera'] = renderGLEventActuator
gWindow._myCamera = view

imgui_decorator = scene.gContext

# Load normal map texture
normal_map_texture = Texture(filepath=normal_map_path, texture_channel=0)
# Load albedo map if present
if os.path.exists(albedo_map_path):
    albedo_texture = Texture(filepath=albedo_map_path, texture_channel=1)
else:
    albedo_texture = None

# Copies the initial_lights list to the gui_decorator
imgui_decorator._lights_list = list(initial_lights)
imgui_decorator._light_counter = len(imgui_decorator._lights_list)


running = True
rot_angle = 0.0
start_time = time.time()

while running:
    running = scene.render()
    scene.world.traverse_visit_pre_camera(camUpdate, mainCam)
    scene.world.traverse_visit(transUpdate, scene.world.root)
    scene.world.traverse_visit(camUpdate, scene.world.root)
    view = gWindow._myCamera
    
    elapsed_time = time.time() - start_time
    
    # Cube Rotation
    if imgui_decorator.reset_rotation:
        rot_angle = 0.0
        imgui_decorator.reset_rotation = False

    if imgui_decorator.rotate_cubes:
        rot_angle += float(imgui_decorator.rotation_speed)

    model_cube = util.translate(0, 0.5, 0) @ util.rotate((0, 1, 0), rot_angle)
    
    # Reset lights to default (simple factory restore)
    if imgui_decorator.reset_lights:
        imgui_decorator._lights_list = make_default_lights()
        imgui_decorator._light_counter = len(imgui_decorator._lights_list)
        imgui_decorator.reset_lights = False
        
    # Update animated lights
    for light in imgui_decorator._lights_list:
        if light.animate:
            if light.light_type == 0:  # PointLight
                light.position = util.vec(
                    light.orbit_radius * math.cos(elapsed_time * light.orbit_speed),
                    light.base_position[1],
                    light.orbit_radius * math.sin(elapsed_time * light.orbit_speed)
                )
                light.intensity = light.base_intensity * (0.5 + 0.5 * math.sin(elapsed_time * light.pulse_speed))
            
            elif light.light_type == 1:  # DirectionalLight
                angle = elapsed_time * light.rotation_speed
                light.direction = util.vec(
                    math.sin(angle),
                    light.base_direction[1],
                    math.cos(angle)
                )
                light.intensity = light.base_intensity * (0.5 + 0.5 * math.sin(elapsed_time * light.pulse_speed))
            
            elif light.light_type == 2:  # SpotLight
                light.position = util.vec(
                    light.orbit_radius * math.cos(elapsed_time * light.orbit_speed),
                    light.base_position[1],
                    light.orbit_radius * math.sin(elapsed_time * light.orbit_speed)
                )
                light.intensity = light.base_intensity * (0.5 + 0.5 * math.sin(elapsed_time * light.pulse_speed))

    mvp = projMat @ view @ model_cube
    
    # --- Shader Uniforms Setup ---
    
    shaderDecCube.setUniformVariable(key='model', value=model_cube, mat4=True)
    shaderDecCube.setUniformVariable(key='View', value=view, mat4=True)
    shaderDecCube.setUniformVariable(key='Proj', value=projMat, mat4=True)   

    # Camera
    # shaderDecCube.setUniformVariable(key='viewPos', value=eye, float3=True)
    # correct position in world-space
    inv_view = util.inverse(view)
    cam_pos4 = inv_view @ np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32)
    w = float(cam_pos4[3])
    cam_pos = util.vec(float(cam_pos4[0]) / w, float(cam_pos4[1]) / w, float(cam_pos4[2]) / w)
    shaderDecCube.setUniformVariable(key='viewPos', value=cam_pos, float3=True)
    
    # Ambient
    shaderDecCube.setUniformVariable(key="ambientColor", value=AmbientColor, float3=True)
    # shaderDecCube.setUniformVariable(key="ambientStrength", value=AmbientStrength, float1=True)
    shaderDecCube.setUniformVariable(key="ambientStrength", value=imgui_decorator.ambient_strength, float1=True)
    
    # Attenuation constants
    shaderDecCube.setUniformVariable(key="k", value=k, float1=True)
    shaderDecCube.setUniformVariable(key="d", value=d, float1=True)

    # Material
    # shaderDecCube.setUniformVariable(key="shininess", value=Matshininess, float1=True)
    shaderDecCube.setUniformVariable(key="shininess", value=imgui_decorator.shininess, float1=True)
    shaderDecCube.setUniformVariable(key='materialColor', value=util.vec(1.0, 1.0, 1.0), float3=True)
    
    # Normal mapping uniforms
    shaderDecCube.setUniformVariable(key='useNormalMap', value=1.0 if imgui_decorator.use_normal_map else 0.0, float1=True)
    shaderDecCube.setUniformVariable(key='normalStrength', value=imgui_decorator.normal_strength, float1=True)
    shaderDecCube.setUniformVariable(key='normalMap', value=normal_map_texture, texture=True)
    # Albedo (diffuse) map and debug normal uniforms
    shaderDecCube.setUniformVariable(key='useAlbedoMap', value=1.0 if imgui_decorator.use_albedo_map else 0.0, float1=True)
    if albedo_texture is not None:
        shaderDecCube.setUniformVariable(key='albedoMap', value=albedo_texture, texture=True)
    shaderDecCube.setUniformVariable(key='debugNormal', value=1.0 if imgui_decorator.debug_normals else 0.0, float1=True)
    
    active_lights = [light for light in imgui_decorator._lights_list if light.visible]
    
    shaderDecCube.setUniformVariable(key='numLights', value=len(active_lights), float1=True)
    
    for i, light in enumerate(active_lights):
        if i >= 50: 
            break
        
        shaderDecCube.setUniformVariable(key=f'lights[{i}].type', value=light.light_type, float1=True)
        shaderDecCube.setUniformVariable(key=f'lights[{i}].position', value=light.position, float3=True)
        shaderDecCube.setUniformVariable(key=f'lights[{i}].direction', value=light.direction, float3=True)
        shaderDecCube.setUniformVariable(key=f'lights[{i}].color', value=util.vec(light.color[0], light.color[1], light.color[2]), float3=True)
        shaderDecCube.setUniformVariable(key=f'lights[{i}].intensity', value=light.intensity, float1=True)
        shaderDecCube.setUniformVariable(key=f'lights[{i}].cutoff', value=light.cutoff, float1=True)

    scene.world.traverse_visit(renderUpdate, scene.world.root)
    scene.render_post()
    
scene.shutdown()
