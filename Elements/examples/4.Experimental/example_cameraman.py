import numpy as np
import imgui
import time
import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, RenderMesh
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray


example_description = \
"In this example, the camera moves smoothly along a predefined path,\
such as a Bezier curve or a closed curve.\nWhile moving, the camera " \
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

cube = scene.world.createEntity(Entity(name="Cube"))
scene.world.addEntityChild(root, cube)
cube_transform = scene.world.addComponent(
    cube, BasicTransform(name="Cube_Transform", trs=util.translate(0, 0, 0))
)
cube_mesh = scene.world.addComponent(cube, RenderMesh(name="cube_mesh"))

# Cube
vertexCube = np.array([
    [-1,-1,1,1],[1,-1,1,1],[1,1,1,1],[-1,1,1,1],
    [-1,-1,-1,1],[-1,1,-1,1],[1,1,-1,1],[1,-1,-1,1],
    [-1,-1,-1,1],[-1,-1,1,1],[-1,1,1,1],[-1,1,-1,1],
    [1,-1,1,1],[1,-1,-1,1],[1,1,-1,1],[1,1,1,1],
    [-1,1,1,1],[1,1,1,1],[1,1,-1,1],[-1,1,-1,1],
    [-1,-1,-1,1],[1,-1,-1,1],[1,-1,1,1],[-1,-1,1,1]
], dtype=np.float32)

faceColors = [
    [1.0, 0.0, 0.0, 1.0],
    [0.0, 1.0, 0.0, 1.0],
    [0.0, 0.0, 1.0, 1.0],
    [1.0, 1.0, 0.0, 1.0],
    [1.0, 0.0, 1.0, 1.0],
    [0.0, 1.0, 1.0, 1.0]
]

colorCube = []
for color in faceColors:
    for _ in range(4):
        colorCube.append(color)

indexCube = []
for i in range(6):
    offset = i * 4
    indexCube.extend([0+offset,1+offset,2+offset, 0+offset,2+offset,3+offset])

cube_mesh.vertex_attributes.append(vertexCube)
cube_mesh.vertex_attributes.append(colorCube)
cube_mesh.vertex_index.append(indexCube)

cube_vao = scene.world.addComponent(cube, VertexArray())
cube_shader = scene.world.addComponent(
    cube,
    ShaderGLDecorator(
        Shader(
            vertex_source=Shader.COLOR_VERT_MVP,
            fragment_source=Shader.COLOR_FRAG
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
    global selected, start, cam_pos, control_points,moving,t,diameter,num_points

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

    imgui.end()


def N_bezier(points, t):
    pts = [p.copy() for p in points]
    while len(pts) > 1:
        pts = [
            (1 - t) * pts[i] + t * pts[i + 1]
            for i in range(len(pts) - 1)
        ]
    return pts[0]


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

    view = util.lookat(np.array(cam_pos), target, up)
    projMat = util.perspective(60.0, 1000/800, 0.1, 100.0)
    mvpMat = projMat @ view @ cube_transform.trs
    cube_shader.setUniformVariable(key='modelViewProj', value=mvpMat, mat4=True)

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

def orbit():
    global diameter, num_points

    imgui.begin("Orbit")

    # Slider for number of points
    imgui.text("Number of points:")
    changed, num_points = imgui.slider_int("##num_points", num_points, 3, 256)

    imgui.separator()

    # Slider for diameter
    imgui.text("Diameter:")
    _, diameter = imgui.input_float("##diameter", diameter)
    if diameter<1:
        diameter=1

    imgui.end()
    


# MAIN LOOP
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
