# Giorgos Vitsos csd5369

import imgui
import time
import numpy as np
import Elements.pyECSS.math_utilities as util

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
diameter = 5
num_points = 16

# Animation variables
start = False
t = 0.0
speed = 0.1
moving = False

# Camera settings
initial_cam_pos = [5.0, 3.0, 5.0]
cam_pos = initial_cam_pos.copy()
target = np.array([0.0, 0.0, 0.0])
up = np.array([0.0, 1.0, 0.0])

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
    global selected, start, cam_pos, control_points, moving, t, diameter, num_points, speed,initial_cam_pos

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
        cam_pos[:] = initial_cam_pos

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
    _, speed = imgui.slider_float("Animation Speed", speed, 0.1, 2)

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

    _, num_points = imgui.slider_int("Num Points", num_points, 3, 256)
    _, diameter = imgui.input_float("Diameter", diameter)

    if diameter < 3:
        diameter = 3

    imgui.end()

# Camera logic
def N_bezier(points, t):
    pts = [p.copy() for p in points]
    while len(pts) > 1:
        pts = [
            (1 - t) * pts[i] + t * pts[i + 1]
            for i in range(len(pts) - 1)
        ]
    return pts[0]


def orbit_points(diameter, num_points, target):

    radius = diameter / 2
    points = []
    
    tx, ty, tz = target
    
    for i in range(num_points):
        angle = 2 * np.pi * i / num_points
        
        x_offset = radius * np.cos(angle)
        z_offset = radius * np.sin(angle)
        x = tx + x_offset
        z = tz + z_offset
        y = ty + 0.5 
        
        points.append(np.array([x, y, z]))
        
    return points

def start_motion():
    global t, moving, cam_pos

    if len(control_points) < 2:
        return

    t = 0.0
    moving = True
    cam_pos[:] = control_points[0]


def update_camera(sphere_transform, sphere_shader):
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

    elif moving and selected == "Orbit":
        closed_points = orbit_points(diameter, num_points,target)
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

# Main function to run camera logic
def run_camera(sphere_transform, sphere_shader):
    global start, selected

    if start and selected is not None:
        start = False
        start_motion()

    if show_start_gui:
        draw_start_gui()
    else:
        draw_gui()

        if selected == "Bezier":
            bezier()
        elif selected == "Orbit":
            orbit()

        update_camera(sphere_transform, sphere_shader)

# Setters for external control
def set_target(new_target):
    global target
    target = np.array(new_target)

def set_up(new_up):
    global up
    up = np.array(new_up)

def set_cam_pos(new_pos):
    global cam_pos, initial_cam_pos
    initial_cam_pos = list(new_pos)
    cam_pos[:] = new_pos

def set_control_points(points):
    global control_points
    control_points = [np.array(p) for p in points]   