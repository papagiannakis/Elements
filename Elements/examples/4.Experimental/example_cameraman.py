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

show_start_gui = True # flag for start GUI
selected = None # selected path type

last_time = time.time() # Initialize last_time for delta time calculation

#Bezier curve control points
start_point = np.array([5,3,5])    
end_point = np.array([0, 0, 0])
control_point= np.array([0.0, 0, 0.0])

#Animation variables
t=0.0
speed=0.1
moving=False

scene = Scene()

#Scenegraph
root=scene.world.createEntity(Entity(name="Root"))

cube=scene.world.createEntity(Entity(name="Cube"))
scene.world.addEntityChild(root, cube)
cube_transform=scene.world.addComponent(cube, BasicTransform(name="Cube_Transform", trs=util.translate(0,0,0)))
cube_mesh=scene.world.addComponent(cube, RenderMesh(name="cube_mesh"))

#Cube
vertexCube = np.array([
    [-1,-1,1,1],[1,-1,1,1],[1,1,1,1],[-1,1,1,1],#front
    [-1,-1,-1,1],[-1,1,-1,1],[1,1,-1,1],[1,-1,-1,1],#back
    [-1,-1,-1,1],[-1,-1,1,1],[-1,1,1,1],[-1,1,-1,1],#left
    [1,-1,1,1],[1,-1,-1,1],[1,1,-1,1],[1,1,1,1],#right
    [-1,1,1,1],[1,1,1,1],[1,1,-1,1],[-1,1,-1,1],#top
    [-1,-1,-1,1],[1,-1,-1,1],[1,-1,1,1],[-1,-1,1,1]#bottom
], dtype=np.float32)

faceColors = [
    [1.0, 0.0, 0.0, 1.0],#front-red
    [0.0, 1.0, 0.0, 1.0],#back-green
    [0.0, 0.0, 1.0, 1.0],#left-blue
    [1.0, 1.0, 0.0, 1.0],#right-yellow
    [1.0, 0.0, 1.0, 1.0],#top-magenta
    [0.0, 1.0, 1.0, 1.0] #bottom-cyan
]

colorCube=[]

for color in faceColors:
    for _ in range(4):
        colorCube.append(color)

indexCube=[]
for i in range(6):
    offset=i*4
    indexCube.extend([0+offset,1+offset,2+offset, 0+offset,2+offset,3+offset])

cube_mesh.vertex_attributes.append(vertexCube)
cube_mesh.vertex_attributes.append(colorCube)
cube_mesh.vertex_index.append(indexCube)

cube_vao=scene.world.addComponent(cube,VertexArray())
cube_shader=scene.world.addComponent(cube,ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))

#Camera setup
cam_pos = [5.0, 3.0, 5.0]
target = np.array([0.0, 0.0, 0.0])
up = np.array([0.0, 1.0, 0.0])

#System
renderUpdate = scene.world.createSystem(RenderGLShaderSystem())
initUpdate = scene.world.createSystem(InitGLShaderSystem())

#Initialize
scene.init(
    imgui=True,
    windowWidth=1000,
    windowHeight=800,
    windowTitle="CameraMan Project",
    openGLversion=4
)

#GUIS
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
    global selected,start, cam_pos

    imgui.begin("Options")

    imgui.text("Cam Position (for debugging):")
    _, cam_pos[0] = imgui.slider_float("Cam X", cam_pos[0], -20.0, 20.0)
    _, cam_pos[1] = imgui.slider_float("Cam Y", cam_pos[1], -20.0, 20.0)
    _, cam_pos[2] = imgui.slider_float("Cam Z", cam_pos[2], -20.0, 20.0)

    imgui.separator()

    if imgui.button("Reset"):
        selected = None
        start = False
        cam_pos = [5.0, 3.0, 5.0]

    imgui.same_line()

    if imgui.button("Start"):
        start_motion()

    imgui.same_line()

    if imgui.button("Bezier"):
        selected = "Bezier"

    imgui.same_line()

    if imgui.button("Curve"):
        selected = "Curve"

    imgui.same_line()

    imgui.text(f"Selected: {selected}")

    imgui.end()

def update_camera():
    global cam_pos, t, moving,last_time

    #calculate delta time
    current_time = time.time()
    delta_time = current_time - last_time
    last_time = current_time

    if moving:
        if selected == "Bezier":

            cam_pos[:] = quadratic_bezier(start_point, control_point, end_point, t)
            t += speed *delta_time

            if t >= 1.0:#animation ends

                t = 1.0
                moving = False

        elif selected == "Curve":#under construction
            pass

    view = util.lookat(np.array(cam_pos), target, up)
    projMat = util.perspective(60.0, 1000/800, 0.1, 100.0)
    mvpMat = projMat @ view @ cube_transform.trs
    cube_shader.setUniformVariable(key='modelViewProj', value=mvpMat, mat4=True)

def quadratic_bezier(p0, p1, p2, t):
    return (1-t)**2 * p0 + 2*(1-t)*t * p1 + t**2 * p2   

def bezier():
    global cam_pos,start_point,end_point,control_point

    imgui.begin("Bezier Path")

    imgui.text("Choose 2 points to define the path:")
    imgui.text("Start Point:")
    _, start_point[0] = imgui.input_float("start_x", start_point[0])
    _, start_point[1] = imgui.input_float("start_y", start_point[1])
    _, start_point[2] = imgui.input_float("start_z", start_point[2])
    imgui.text("Control Point:")
    _, control_point[0] = imgui.input_float("ctrl_x", control_point[0])
    _, control_point[1] = imgui.input_float("ctrl_y", control_point[1])
    _, control_point[2] = imgui.input_float("ctrl_z", control_point[2])
    imgui.text("End Point:")
    _, end_point[0] = imgui.input_float("end_x", end_point[0])
    _, end_point[1] = imgui.input_float("end_y", end_point[1])
    _, end_point[2] = imgui.input_float("end_z", end_point[2])
    imgui.separator()

    imgui.end()
   

def start_motion():
    global t, moving, cam_pos

    t = 0.0
    moving = True
    cam_pos[:] = start_point


def closed_curve():#under construction
    return

running = True
scene.world.traverse_visit(initUpdate, scene.world.root)
while running:

    running = scene.render()

    if show_start_gui:
        draw_start_gui()
    else:
        draw_gui()
        if selected is not None:
            if selected == "Bezier":
                bezier()
            elif selected == "Curve":
                closed_curve()
        update_camera()
    scene.world.traverse_visit(renderUpdate, scene.world.root)
    scene.render_post()
scene.shutdown()
