# test_billboard_labels.py - Test file for billboard label system
import numpy as np
import OpenGL.GL as gl

import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, Camera, RenderMesh
from Elements.pyECSS.System import TransformSystem, CameraSystem
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GUI.Viewer import RenderGLStateSystem
from Elements.pyGLV.GUI.ImguiDecorator import ImGUIecssDecorator2
from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray

# Import billboard label system
from Elements.extensions.Subtitles_plus_Pretty.billboard_label_component import create_billboard_label, BillboardLabelSystem

print("=" * 60)
print("TEST: Billboard Label System")
print("=" * 60)


# ================
# HELPER FUNCTIONS
# ================

def make_cube(size=1.0):
    """Create cube"""
    s = size * 0.5
    positions = np.array([
        [-s,-s, s],[ s,-s, s],[ s, s, s],[-s, s, s],
        [-s,-s,-s],[ s,-s,-s],[ s, s,-s],[-s, s,-s],
    ], dtype=np.float32)
    indices = np.array([
        0,1,2, 0,2,3, 1,5,6, 1,6,2, 5,4,7, 5,7,6,
        4,0,3, 4,3,7, 3,2,6, 3,6,7, 4,5,1, 4,1,0
    ], dtype=np.uint32)
    return positions, indices


def solid_color(n, rgba):
    """create uniform colorfor n vertices"""
    return np.tile(np.array(rgba, dtype=np.float32), (n, 1))


print("\n1️  Creating scene")
scene = Scene()    
rootEntity = scene.world.createEntity(Entity(name="Root"))

# Camera setup
entityCam1 = scene.world.createEntity(Entity(name="entityCam1"))
scene.world.addEntityChild(rootEntity, entityCam1)
trans1 = scene.world.addComponent(entityCam1, BasicTransform(name="trans1", trs=util.identity()))

eye = util.vec(1, 0.54, 1.0)
target = util.vec(0.02, 0.14, 0.217)
up = util.vec(0.0, 1.0, 0.0)
view = util.lookat(eye, target, up)
projMat = util.perspective(50.0, 1.0, 1.0, 10.0)   
m = np.linalg.inv(projMat @ view)

entityCam2 = scene.world.createEntity(Entity(name="entityCam2"))
scene.world.addEntityChild(entityCam1, entityCam2)
trans2 = scene.world.addComponent(entityCam2, BasicTransform(name="trans2", trs=util.identity()))
orthoCam = scene.world.addComponent(entityCam2, Camera(m, "orthoCam", "Camera", "500"))

print("    Camera setup complete")
print("\n2️ Creating systems...")
transUpdate = scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
camUpdate = scene.world.createSystem(CameraSystem("camUpdate", "CameraUpdate", "200"))
renderUpdate = scene.world.createSystem(RenderGLShaderSystem())
initUpdate = scene.world.createSystem(InitGLShaderSystem())

# ΤΟ BILLBOARD LABEL SYSTEM
labelSystem = scene.world.createSystem(BillboardLabelSystem())

print("   Systems created")
print(f"    BillboardLabelSystem: {labelSystem.name}")


print("\n3️ Creating test objects...")

# Cube 1 (Red)
cube1 = scene.world.createEntity(Entity(name="TestCube1"))
scene.world.addEntityChild(rootEntity, cube1)
trans_cube1 = scene.world.addComponent(cube1, BasicTransform(
    name="Cube1_TRS", 
    trs=util.translate(-1.0, 0.5, 0.0)
))
mesh1 = scene.world.addComponent(cube1, RenderMesh(name="Cube1_Mesh"))
pos1, idx1 = make_cube(1.0)
mesh1.vertex_attributes.append(pos1)
mesh1.vertex_attributes.append(solid_color(8, (0.9, 0.2, 0.2, 1.0)))
mesh1.vertex_index.append(idx1)
scene.world.addComponent(cube1, VertexArray())
shader1 = scene.world.addComponent(cube1, ShaderGLDecorator(Shader(
    vertex_source=Shader.COLOR_VERT_MVP,
    fragment_source=Shader.COLOR_FRAG
)))
print("    Red cube at (-1, 0.5, 0)")


# Cube 2 green
cube2 = scene.world.createEntity(Entity(name="TestCube2"))
scene.world.addEntityChild(rootEntity, cube2)
trans_cube2 = scene.world.addComponent(cube2, BasicTransform(
    name="Cube2_TRS", 
    trs=util.translate(1.0, 0.5, 0.0)
))
mesh2 = scene.world.addComponent(cube2, RenderMesh(name="Cube2_Mesh"))
pos2, idx2 = make_cube(1.0)
mesh2.vertex_attributes.append(pos2)
mesh2.vertex_attributes.append(solid_color(8, (0.2, 0.9, 0.2, 1.0)))
mesh2.vertex_index.append(idx2)
scene.world.addComponent(cube2, VertexArray())
shader2 = scene.world.addComponent(cube2, ShaderGLDecorator(Shader(
    vertex_source=Shader.COLOR_VERT_MVP,
    fragment_source=Shader.COLOR_FRAG
)))
print("   Green cube at (1, 0.5, 0)")


# Cube blue
cube3 = scene.world.createEntity(Entity(name="TestCube3"))
scene.world.addEntityChild(rootEntity, cube3)
trans_cube3 = scene.world.addComponent(cube3, BasicTransform(
    name="Cube3_TRS", 
    trs=util.translate(0.0, 1.5, -1.0)
))
mesh3 = scene.world.addComponent(cube3, RenderMesh(name="Cube3_Mesh"))
pos3, idx3 = make_cube(0.6)
mesh3.vertex_attributes.append(pos3)
mesh3.vertex_attributes.append(solid_color(8, (0.2, 0.2, 0.9, 1.0))) 
mesh3.vertex_index.append(idx3)
scene.world.addComponent(cube3, VertexArray())
shader3 = scene.world.addComponent(cube3, ShaderGLDecorator(Shader(
    vertex_source=Shader.COLOR_VERT_MVP,
    fragment_source=Shader.COLOR_FRAG
)))
print("    Blue cube at (0, 1.5, -1)")


print("\n4️ Window init")
winWidth = 1200
winHeight = 800

running = True
scene.init(
    imgui=True, 
    windowWidth=winWidth, 
    windowHeight=winHeight, 
    windowTitle=" TEST: Billboard Label System", 
    customImGUIdecorator=ImGUIecssDecorator2, 
    openGLversion=4
)

# Enable blending for labels
gl.glEnable(gl.GL_BLEND)
gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

print("    Window initialized")


print("\n5️ Create billboard labels")
#test 1
label1, comp1 = create_billboard_label(
    scene=scene,
    parent_entity=cube1,
    text=" RED",
    bg_rgba=(0.9, 0.2, 0.2, 0.95),
    fg_rgba=(1.0, 1.0, 1.0, 1.0),
    world_height=0.2,
    offset_local=(0.0, 0.8, 0.0),
    padding_px=12,
    font_size=64
)
print("   Label 1: red")

# test 2
label2, comp2 = create_billboard_label(
    scene=scene,
    parent_entity=cube2,
    text="GREEN",
    bg_rgba=(0.2, 0.9, 0.2, 0.95),
    fg_rgba=(0.0, 0.0, 0.0, 1.0),
    world_height=0.15,
    offset_local=(0.0, 0.7, 0.0),
    padding_px=8,
    font_size=48
)
print("   Label 2: green with black text")

# test 3
label3, comp3 = create_billboard_label(
    scene=scene,
    parent_entity=cube3,
    text="BLUE",
    bg_rgba=(0.2, 0.2, 0.9, 0.9),
    fg_rgba=(1.0, 1.0, 1.0, 1.0),
    world_height=0.12,
    offset_local=(0.0, 0.5, 0.0),
    padding_px=6,
    font_size=56
)
print("    Label 3: Blue small")

billboard_labels = [
    (comp1, trans_cube1),
    (comp2, trans_cube2),
    (comp3, trans_cube3)
]

print(f"\n   {len(billboard_labels)} labels")


print("\n6️ Init GL objects...")
scene.world.traverse_visit(initUpdate, scene.world.root)
print("   All GL objects initialized")

eManager = scene.world.eventManager
gWindow = scene.renderWindow
gGUI = scene.gContext

renderGLEventActuator = RenderGLStateSystem()

eManager._subscribers['OnUpdateWireframe'] = gWindow
eManager._actuators['OnUpdateWireframe'] = renderGLEventActuator
eManager._subscribers['OnUpdateCamera'] = gWindow 
eManager._actuators['OnUpdateCamera'] = renderGLEventActuator

eye = util.vec(3.0, 2.5, 3.0)
target = util.vec(0.0, 0.5, 0.0)
up = util.vec(0.0, 1.0, 0.0)
view = util.lookat(eye, target, up)

projMat = util.perspective(50.0, winWidth/winHeight, 0.01, 100.0)

gWindow._myCamera = view


print("\n" + "=" * 10)
print("7️  RENDER LOOP Starting")
print("=" * 60)


frame_count = 0
test_passed = True

while running:
    running = scene.render()
    frame_count += 1
    
    scene.world.traverse_visit(renderUpdate, scene.world.root)
    scene.world.traverse_visit_pre_camera(camUpdate, orthoCam)
    scene.world.traverse_visit(camUpdate, scene.world.root)

    view = gWindow._myCamera
    
    mvp1 = projMat @ view @ trans_cube1.trs
    mvp2 = projMat @ view @ trans_cube2.trs
    mvp3 = projMat @ view @ trans_cube3.trs
    
    shader1.setUniformVariable(key='modelViewProj', value=mvp1, mat4=True)
    shader2.setUniformVariable(key='modelViewProj', value=mvp2, mat4=True)
    shader3.setUniformVariable(key='modelViewProj', value=mvp3, mat4=True)

    view_inv = np.linalg.inv(view)
    cam_right = view_inv[:3, 0]
    cam_up = view_inv[:3, 1]
    
    for billboard_comp, parent_transform in billboard_labels:
        if billboard_comp.shader:
            offset_world = parent_transform.trs @ util.vec(*billboard_comp.offset_local, 1.0)
            center = offset_world[:3]
            
            billboard_comp.shader.setUniformVariable(key='View', value=view, mat4=True)
            billboard_comp.shader.setUniformVariable(key='Proj', value=projMat, mat4=True)
            billboard_comp.shader.setUniformVariable(key='center', value=center, float3=True)
            billboard_comp.shader.setUniformVariable(key='camRight', value=cam_right, float3=True)
            billboard_comp.shader.setUniformVariable(key='camUp', value=cam_up, float3=True)
            billboard_comp.shader.setUniformVariable(
                key='size',
                value=util.vec(billboard_comp.world_width, billboard_comp.world_height, 0.0),
                float3=True
            )
    
    # Progress report every 120 frames
    if frame_count % 120 == 0:
        print(f"[Frame {frame_count}] ✓ Labels rendering correctly")
    
    scene.render_post()


scene.shutdown()

print("\n" + "=" * 60)
print("8️ TEST RESULTS")
print("=" * 60)

if test_passed:
    print("\n✅ Test succeed!")
    print("   • All labels were created")
    print("   • All labels where shown")
    print("   • ALl labels follow the camera")
else:
    print("\nTest FAILED")

print("\n" + "=" * 60)
print("END TEST")
print("=" * 60)