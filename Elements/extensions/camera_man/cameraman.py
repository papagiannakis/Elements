# Giorgos Vitsos csd5369

import imgui
import time
import numpy as np
import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, RenderMesh
from Elements.pyECSS.System import TransformSystem
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GUI.Viewer import RenderGLStateSystem
from Elements.pyGLV.GUI.ImguiDecorator import ImGUIecssDecorator2
from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray
from Elements.pyGLV.GL.Textures import Texture
from Elements.definitions import TEXTURE_DIR


example_description = \
"In this example, the camera moves smoothly along a predefined path,\
such as a Bezier curve or a closed curve (Orbit).\nWhile moving, the camera " \
"continuously points toward a target. Use the interface to start, " \
"reset, or choose any other option."

show_start_gui = True
selected = None

last_time = time.time()

# Bezier curve control points
control_points = [
    np.array([0.0, 0.0, 0.0]),
    np.array([1.0, 1.0, 0.0]),
]

# Orbit settings
diameter=5
num_points=16

start = False

# Animation variables
t = 0.0
speed = 0.1
moving = False

scene = Scene()

# Scenegraph
root = scene.world.createEntity(Entity(name="Root"))

sphere = scene.world.createEntity(Entity(name="sphere"))
scene.world.addEntityChild(root, sphere)
sphere_transform = scene.world.addComponent(
    sphere, BasicTransform(name="sphere_Transform", trs=util.translate(0, 0, 0))
)
sphere_mesh = scene.world.addComponent(sphere, RenderMesh(name="sphere_mesh"))

# Sphere
segments = 64
rings = 32
radius = 1

vertices_sphere = []
uvs_sphere = []
colors_sphere = []
indices_sphere = []

for i in range(rings + 1):
    phi = np.pi * i / rings
    v = 1 - i / rings
    for j in range(segments + 1):
        theta = 2 * np.pi * j / segments
        u = 1 - (j / segments)
        x = radius * np.sin(phi) * np.cos(theta)
        y = radius * np.cos(phi)
        z = radius * np.sin(phi) * np.sin(theta)
        vertices_sphere.append([x, y, z, 1.0])
        uvs_sphere.append([u, v])
        colors_sphere.append([1.0, 1.0, 1.0, 1.0])

for i in range(rings):
    for j in range(segments):
        first = i * (segments + 1) + j
        second = first + segments + 1
        indices_sphere.extend([first, second, first + 1])
        indices_sphere.extend([second, second + 1, first + 1])

vertices_sphere = np.array(vertices_sphere, dtype=np.float32)
uvs_sphere = np.array(uvs_sphere, dtype=np.float32)
colors_sphere = np.array(colors_sphere, dtype=np.float32)
indices_sphere = np.array(indices_sphere, dtype=np.uint32)

sphere_mesh.vertex_attributes.append(vertices_sphere)
sphere_mesh.vertex_attributes.append(uvs_sphere)
sphere_mesh.vertex_attributes.append(colors_sphere)
sphere_mesh.vertex_index.append(indices_sphere)

sphere_vao = scene.world.addComponent(sphere, VertexArray())
sphere_shader = scene.world.addComponent(
    sphere,
    ShaderGLDecorator(
        Shader(
            vertex_source=Shader.SIMPLE_TEXTURE_VERT,
            fragment_source=Shader.SIMPLE_TEXTURE_FRAG
        )
    )
)

# Camera setup
cam_pos = [5.0, 3.0, 5.0]
target = np.array([0.0, 0.0, 0.0])
up = np.array([0.0, 1.0, 0.0])

# Systems
renderUpdate = scene.world.createSystem(RenderGLShaderSystem())
initUpdate = scene.world.createSystem(InitGLShaderSystem())

# Initialize
scene.init(
    imgui=True,
    windowWidth=1000,
    windowHeight=800,
    windowTitle="CameraMan Project",
    openGLversion=4
)

# Texture
texturePath = TEXTURE_DIR / "earth.jpg"
texture = Texture(texturePath)
sphere_shader.setUniformVariable("ImageTexture", texture, texture=True)

# GUIs
def draw_start_gui():
    global show_start_gui
    imgui.begin("Welcome")
    imgui.text_wrapped("Camera-Man Project")
    imgui.separator()
    imgui.text(example_description)
    if imgui.button("Start"):
        show_start_gui = False
    imgui.end()

def draw_gui():
    global selected, start, cam_pos, control_points,moving,t,diameter,num_points,speed

    imgui.begin("Options")

    imgui.text("Cam Position (for debugging):")
    _, cam_pos[0] = imgui.slider_float("Cam X", cam_pos[0], -20.0, 20.0)
    _, cam_pos[1] = imgui.slider_float("Cam Y", cam_pos[1], -20.0, 20.0)
    _, cam_pos[2] = imgui.slider_float("Cam Z", cam_pos[2], -20.0, 20.0)

    imgui.separator()

    if imgui.button("Reset"):
        selected = None
        start = False
        moving = False
        t = 0.0
        cam_pos[:] = [5.0, 3.0, 5.0]
        control_points[:] = control_points[:2]
        diameter=5
        num_points=16
        speed=0.1

    imgui.same_line()

    if imgui.button("Start"):
        if selected is not None:
            start = True

    imgui.same_line()

    if imgui.button("Bezier"):
        selected = "Bezier"

    imgui.same_line()

    if imgui.button("Orbit"):
        selected = "Orbit"

    imgui.same_line()

    imgui.text(f"Selected: {selected}")

    imgui.separator()
    imgui.push_item_width(120)
    _, speed = imgui.slider_float("Animation Speed", speed, 0.1, 2)
    imgui.pop_item_width()


    imgui.end()

def bezier():
    global control_points

    imgui.begin("Bezier Path")

    if imgui.button("Add Point"):
        control_points.append(control_points[-1].copy())

    imgui.same_line()

    if imgui.button("Remove Point") and len(control_points) > 2:
        control_points.pop()

    imgui.separator()

    for i, p in enumerate(control_points):
        _, p[:] = imgui.drag_float3(f"Point {i}", *p, 0.01)

    imgui.end()

def orbit():
    global diameter, num_points

    imgui.begin("Orbit")

    imgui.text("Number of points:")
    changed, num_points = imgui.slider_int("##num_points", num_points, 3, 256)

    imgui.separator()

    imgui.text("Diameter:")
    _, diameter = imgui.input_float("##diameter", diameter)
    if diameter<3:
        diameter=3

    imgui.end()

def N_bezier(points, t):
    pts = [p.copy() for p in points]
    while len(pts) > 1:
        pts = [
            (1 - t) * pts[i] + t * pts[i + 1]
            for i in range(len(pts) - 1)
        ]
    return pts[0]

def start_motion():
    global t, moving, cam_pos

    if len(control_points) < 2:
        return

    t = 0.0
    moving = True
    cam_pos[:] = control_points[0]


def update_camera():
    global cam_pos, t, moving, last_time

    current_time = time.time()
    delta_time = current_time - last_time
    last_time = current_time

    if moving and selected == "Bezier":
        cam_pos[:] = N_bezier(control_points, t)
        t += speed * delta_time
        if t >= 1.0:
            t = 1.0
            moving = False
    elif moving and selected =="Orbit":
        closed_points = orbit_points(diameter,num_points)
        cam_pos[:] = N_bezier(closed_points, t)
        t += speed * delta_time
        if t >= 1.0:
            t = 0.0

    model = sphere_transform.l2world
    view = util.lookat(np.array(cam_pos), target, up)
    proj = util.perspective(60.0, 1000/800, 0.1, 100.0)

    sphere_shader.setUniformVariable("model", model, mat4=True)
    sphere_shader.setUniformVariable("View", view, mat4=True)
    sphere_shader.setUniformVariable("Proj", proj, mat4=True)


def orbit_points(diameter,num_points):
    radius=diameter/2
    points=[]
    for i in range(num_points):
        angle=2*np.pi*i/num_points
        x=radius*np.cos(angle)
        z=radius*np.sin(angle)
        y=0.5
        points.append(np.array([x,y,z]))
    return points

# Main loop
scene.world.traverse_visit(initUpdate, scene.world.root)
running = True

while running:
    running = scene.render()

    if start and selected is not None: 
        start = False
        start_motion()

    if show_start_gui:
        draw_start_gui()
    else:
        draw_gui()
        if selected == "Bezier":
            bezier()
        elif selected =="Orbit":
            orbit()
        update_camera()

    scene.world.traverse_visit(renderUpdate, scene.world.root)
    scene.render_post()

scene.shutdown()
