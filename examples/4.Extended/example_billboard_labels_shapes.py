# example_billboard_labels_shapes.py: billboard labels on multiple shapes (two cubes, a sphere)

import os, time
import numpy as np
import OpenGL.GL as gl
import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, RenderMesh
from Elements.pyECSS.System import TransformSystem
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray
from Elements.pyGLV.GUI.ImguiDecorator import ImGUIecssDecorator2
from Elements.utils.Shortcuts import displayGUI_text

from Elements.extensions.Captions_Screenshot.billboard_label_component import create_billboard_label, BillboardLabelSystem
example_description = \
"This example shows billboard labels attached to three shapes: a red cube, \n\
a green cube and a blue sphere. Each label is a semi-transparent quad that \n\
always faces the camera (billboarding), rendered just above its parent shape. \n\
The camera automatically orbits around the scene while bobbing up and down. \n\
Hit ESC OR Close the window to quit."
#functions apo preperation gia live askisi
def make_cube(size=1.0):
    s = size * 0.5
    positions = np.array([
        [-s,-s, s],[ s,-s, s],[ s, s, s],[-s, s, s],  # front
        [-s,-s,-s],[ s,-s,-s],[ s, s,-s],[-s, s,-s],  # back
    ], dtype=np.float32)
    indices = np.array([
        0,1,2, 0,2,3,       # front
        1,5,6, 1,6,2,       # right
        5,4,7, 5,7,6,       # back
        4,0,3, 4,3,7,       # left
        3,2,6, 3,6,7,       # top
        4,5,1, 4,1,0        # bottom
    ], dtype=np.uint32)
    return positions, indices


def make_sphere(radius=0.5, segments=16):
    vertices = []
    indices = []
    
    for i in range(segments + 1):
        lat = np.pi * (-0.5 + float(i) / segments)
        y = radius * np.sin(lat)
        r = radius * np.cos(lat)
        
        for j in range(segments + 1):
            lon = 2 * np.pi * float(j) / segments
            x = r * np.cos(lon)
            z = r * np.sin(lon)
            vertices.append([x, y, z])
    
    for i in range(segments):
        for j in range(segments):
            first = i * (segments + 1) + j
            second = first + segments + 1
            
            indices.extend([first, second, first + 1])
            indices.extend([second, second + 1, first + 1])
    
    return np.array(vertices, dtype=np.float32), np.array(indices, dtype=np.uint32)


def solid_color(n, rgba):
    return np.tile(np.array(rgba, dtype=np.float32), (n, 1))

scene = Scene()
root = scene.world.createEntity(Entity(name="Root"))

initSys = scene.world.createSystem(InitGLShaderSystem())
renderSys = scene.world.createSystem(RenderGLShaderSystem())
transSys = scene.world.createSystem(TransformSystem("trans", "TransformSystem", "001"))
labelSys = scene.world.createSystem(BillboardLabelSystem())

# Object 1:Red Cube
cube1 = scene.world.createEntity(Entity(name="Cube1"))
scene.world.addEntityChild(root, cube1)
tCube1 = scene.world.addComponent(cube1, BasicTransform(
    name="Cube1_TRS", 
    trs=util.translate(-2.0, 0.5, 0.0)
))
mCube1 = scene.world.addComponent(cube1, RenderMesh(name="Cube1_Mesh"))
pos1, idx1 = make_cube(1.0)
mCube1.vertex_attributes.append(pos1)
mCube1.vertex_attributes.append(solid_color(8, (0.9, 0.2, 0.2, 1.0)))
mCube1.vertex_index.append(idx1)
scene.world.addComponent(cube1, VertexArray())
shCube1 = scene.world.addComponent(cube1, ShaderGLDecorator(Shader(
    vertex_source=Shader.COLOR_VERT_MVP,
    fragment_source=Shader.COLOR_FRAG
)))

# Object 2:Green Cube
cube2 = scene.world.createEntity(Entity(name="Cube2"))
scene.world.addEntityChild(root, cube2)
tCube2 = scene.world.addComponent(cube2, BasicTransform(
    name="Cube2_TRS", 
    trs=util.translate(0.0, 0.5, 0.0)
))
mCube2 = scene.world.addComponent(cube2, RenderMesh(name="Cube2_Mesh"))
pos2, idx2 = make_cube(1.0)
mCube2.vertex_attributes.append(pos2)
mCube2.vertex_attributes.append(solid_color(8, (0.2, 0.9, 0.2, 1.0)))
mCube2.vertex_index.append(idx2)
scene.world.addComponent(cube2, VertexArray())
shCube2 = scene.world.addComponent(cube2, ShaderGLDecorator(Shader(
    vertex_source=Shader.COLOR_VERT_MVP,
    fragment_source=Shader.COLOR_FRAG
)))

# Object 3:Blue Sphere
sphere = scene.world.createEntity(Entity(name="Sphere"))
scene.world.addEntityChild(root, sphere)
tSphere = scene.world.addComponent(sphere, BasicTransform(
    name="Sphere_TRS", 
    trs=util.translate(2.0, 0.5, 0.0)
))
mSphere = scene.world.addComponent(sphere, RenderMesh(name="Sphere_Mesh"))
pos3, idx3 = make_sphere(0.5, 20)
mSphere.vertex_attributes.append(pos3)
mSphere.vertex_attributes.append(solid_color(len(pos3), (0.2, 0.2, 0.9, 1.0)))  # Blue
mSphere.vertex_index.append(idx3)
scene.world.addComponent(sphere, VertexArray())
shSphere = scene.world.addComponent(sphere, ShaderGLDecorator(Shader(
    vertex_source=Shader.COLOR_VERT_MVP,
    fragment_source=Shader.COLOR_FRAG
)))

scene.init(
    imgui=False, 
    windowWidth=1200, 
    windowHeight=800,
    windowTitle="Billboard Labels - Complete Example",
    openGLversion=4, 
    customImGUIdecorator=ImGUIecssDecorator2
)

# 2. Enable blending for transparent labels
gl.glEnable(gl.GL_BLEND)
gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
#3. create labels
#Label for Cube 1
label1_entity, label1_comp = create_billboard_label(
    scene=scene,
    parent_entity=cube1,
    text="RED CUBE",
    bg_rgba=(0.8, 0.1, 0.1, 0.9),
    fg_rgba=(1.0, 1.0, 1.0, 1.0),
    world_height=0.4,
    offset_local=(0.0, 0.8, 0.0),
    padding_px=12,
    font_size=36
)

#Label for Cube 2
label2_entity, label2_comp = create_billboard_label(
    scene=scene,
    parent_entity=cube2,
    text="GREEN CUBE",
    bg_rgba=(0.1, 0.8, 0.1, 0.9),
    fg_rgba=(1.0, 1.0, 1.0, 1.0),
    world_height=0.4,
    offset_local=(0.0, 0.8, 0.0),
    padding_px=12,
    font_size=36
)

#Label for Sphere
label3_entity, label3_comp = create_billboard_label(
    scene=scene,
    parent_entity=sphere,
    text="BLUE SPHERE",
    bg_rgba=(0.1, 0.1, 0.8, 0.9),
    fg_rgba=(1.0, 1.0, 1.0, 1.0),
    world_height=0.4,
    offset_local=(0.0, 0.8, 0.0),
    padding_px=12,
    font_size=36
)

scene.world.traverse_visit(initSys, scene.world.root)

eye = util.vec(0.0, 3.0, 10.0)
target = util.vec(0.0, 0.5, 0.0)
up = util.vec(0.0, 1.0, 0.0)

t0 = time.monotonic()
frame_count = 0
running = True
camera_angle = 0.0

while running:
    running = scene.render()
    displayGUI_text(example_description)
    frame_count += 1
    t = time.monotonic() - t0
    camera_angle = t * 0.3
    radius = 10.0
    eye = util.vec(
        radius * np.cos(camera_angle),
        3.0 + np.sin(t * 0.5) * 1.0, 
        radius * np.sin(camera_angle)
    )
    
    View = util.lookat(eye, target, up)
    Proj = util.perspective(60.0, 1200/800, 0.1, 100.0)
    
    # Update transforms
    scene.world.traverse_visit(transSys, scene.world.root)
    
    # Update object shaders
    shCube1.setUniformVariable(key='modelViewProj', value=Proj @ View @ tCube1.l2world, mat4=True)
    shCube2.setUniformVariable(key='modelViewProj', value=Proj @ View @ tCube2.l2world, mat4=True)
    shSphere.setUniformVariable(key='modelViewProj', value=Proj @ View @ tSphere.l2world, mat4=True)
    
    # 4. UPDATE ALL BILLBOARD LABELS
    view_inv = np.linalg.inv(View)
    cam_right = view_inv[:3, 0]
    cam_up = view_inv[:3, 1]
    
    # Helper function to update a billboard
    def update_billboard(billboard_comp, parent_transform):
        if billboard_comp.shader:
            offset_world = parent_transform.l2world @ util.vec(*billboard_comp.offset_local, 1.0)
            center = offset_world[:3]
            
            billboard_comp.shader.setUniformVariable(key='View', value=View, mat4=True)
            billboard_comp.shader.setUniformVariable(key='Proj', value=Proj, mat4=True)
            billboard_comp.shader.setUniformVariable(key='center', value=center, float3=True)
            billboard_comp.shader.setUniformVariable(key='camRight', value=cam_right, float3=True)
            billboard_comp.shader.setUniformVariable(key='camUp', value=cam_up, float3=True)
            billboard_comp.shader.setUniformVariable(
                key='size',
                value=util.vec(billboard_comp.world_width, billboard_comp.world_height, 0.0),
                float3=True
            )
    
    update_billboard(label1_comp, tCube1)
    update_billboard(label2_comp, tCube2)
    update_billboard(label3_comp, tSphere)
    
    scene.world.traverse_visit(renderSys, scene.world.root)
    scene.render_post()


scene.shutdown()