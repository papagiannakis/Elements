import numpy as np
import OpenGL.GL as gl  # Χρειάζεται για το blending των labels
import time  # Χρειάζεται για τους υπότιτλους

import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, Camera, RenderMesh
from Elements.pyECSS.System import TransformSystem, CameraSystem
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GUI.Viewer import RenderGLStateSystem
from Elements.pyGLV.GUI.ImguiDecorator import ImGUIecssDecorator2
from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray

from Elements.utils.Shortcuts import displayGUI_text
import imgui

# Εισαγωγή του billboard label system
from billboard_label_component import create_billboard_label, BillboardLabelSystem

# Εισαγωγή του subtitle system για υπότιτλους
from subtitle_system import SubtitleManager, SubtitleRenderer

example_description = \
"Απλή σκηνή με έναν κύβο και billboard label! \n\
Το label πάντα κοιτάζει την κάμερα.\n\n\
" 

winWidth = 1024
winHeight = 768

scene = Scene()    

rootEntity = scene.world.createEntity(Entity(name="RooT"))
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

#my cube
node4 = scene.world.createEntity(Entity(name="node4"))
scene.world.addEntityChild(rootEntity, node4)
trans4 = scene.world.addComponent(node4, BasicTransform(name="trans4", trs=util.translate(0, 0.5, 0)))
mesh4 = scene.world.addComponent(node4, RenderMesh(name="mesh4"))

# Vertices
vertexCube = np.array([
    [-0.5, -0.5, 0.5, 1.0],
    [-0.5, 0.5, 0.5, 1.0],
    [0.5, 0.5, 0.5, 1.0],
    [0.5, -0.5, 0.5, 1.0], 
    [-0.5, -0.5, -0.5, 1.0], 
    [-0.5, 0.5, -0.5, 1.0], 
    [0.5, 0.5, -0.5, 1.0], 
    [0.5, -0.5, -0.5, 1.0]
], dtype=np.float32) 

#colors of vertices
colorCube = np.array([
    [0.0, 0.0, 0.0, 1.0],
    [1.0, 0.0, 0.0, 1.0],
    [1.0, 1.0, 0.0, 1.0],
    [0.0, 1.0, 0.0, 1.0],
    [0.0, 0.0, 1.0, 1.0],
    [1.0, 0.0, 1.0, 1.0],
    [1.0, 1.0, 1.0, 1.0],
    [0.0, 1.0, 1.0, 1.0]
], dtype=np.float32)

# Indices
indexCube = np.array((1, 0, 3, 1, 3, 2, 
                      2, 3, 7, 2, 7, 6,
                      3, 0, 4, 3, 4, 7,
                      6, 5, 1, 6, 1, 2,
                      4, 5, 6, 4, 6, 7,
                      5, 4, 0, 5, 0, 1), np.uint32)


transUpdate = scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
camUpdate = scene.world.createSystem(CameraSystem("camUpdate", "CameraUpdate", "200"))
renderUpdate = scene.world.createSystem(RenderGLShaderSystem())
initUpdate = scene.world.createSystem(InitGLShaderSystem())

# create the Billboard Label System to update labels
labelSystem = scene.world.createSystem(BillboardLabelSystem())


mesh4.vertex_attributes.append(vertexCube)
mesh4.vertex_attributes.append(colorCube)
mesh4.vertex_index.append(indexCube)
vArray4 = scene.world.addComponent(node4, VertexArray())
shaderDec4 = scene.world.addComponent(node4, ShaderGLDecorator(Shader(
    vertex_source=Shader.COLOR_VERT_MVP, 
    fragment_source=Shader.COLOR_FRAG
)))

running = True
scene.init(imgui=True, windowWidth=winWidth, windowHeight=winHeight, 
          windowTitle="Ο Κύβος μου με Billboard Label", 
          customImGUIdecorator=ImGUIecssDecorator2, openGLversion=4)

gl.glEnable(gl.GL_BLEND)
gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)


# cREATE label that follows the camera
label_cube, comp_cube = create_billboard_label(
    scene=scene,                  
    parent_entity=node4,
    text="CUBE",
    bg_rgba=(0.9, 0.6, 0.2, 0.95),
    fg_rgba=(1.0, 1.0, 1.0, 1.0),
    world_height=0.15,
    offset_local=(0.0, 0.7, 0.0),
    padding_px=8,
    font_size=64
)

# save label component
billboard_labels = [
    (comp_cube, trans4)  # (billboard_component, parent_transform)
]

scene.world.traverse_visit(initUpdate, scene.world.root)

eManager = scene.world.eventManager
gWindow = scene.renderWindow
gGUI = scene.gContext

renderGLEventActuator = RenderGLStateSystem()

eManager._subscribers['OnUpdateWireframe'] = gWindow
eManager._actuators['OnUpdateWireframe'] = renderGLEventActuator
eManager._subscribers['OnUpdateCamera'] = gWindow 
eManager._actuators['OnUpdateCamera'] = renderGLEventActuator

eye = util.vec(2.5, 2.5, 2.5)
target = util.vec(0.0, 0.0, 0.0)
up = util.vec(0.0, 1.0, 0.0)
view = util.lookat(eye, target, up)

projMat = util.perspective(50.0, 1.0, 0.01, 10.0)

gWindow._myCamera = view

model_cube = trans4.trs

# create subtitle manager
subtitle_manager = SubtitleManager()
subtitle_renderer = SubtitleRenderer(
    font_size=56,
    bg_color=(0, 0, 0, 200),
    text_color=(255, 255, 255, 255),    # text
    padding=24                           # Padding 
)

# Add subtitles
subtitle_manager.add_subtitle("Welcome to my scene", duration=2.0)
subtitle_manager.add_subtitle("this is my cube", duration=2.0)
subtitle_manager.add_subtitle("You can move the camera", duration=2.0)
subtitle_manager.add_subtitle("an the labels always looks forward", duration=2.5)


# track time with delta time
last_time = time.time()



while running:
    running = scene.render()
    
    # calculate delta time
    current_time = time.time()
    delta_time = current_time - last_time
    last_time = current_time
    
    #update subtitles
    current_subtitle = subtitle_manager.update(delta_time)
    
    displayGUI_text(example_description)
    
    scene.world.traverse_visit(renderUpdate, scene.world.root)
    scene.world.traverse_visit_pre_camera(camUpdate, orthoCam)
    scene.world.traverse_visit(camUpdate, scene.world.root)
    view = gWindow._myCamera
    
    mvp_cube = projMat @ view @ model_cube
    
    shaderDec4.setUniformVariable(key='modelViewProj', value=mvp_cube, mat4=True)


    view_inv = np.linalg.inv(view)
    cam_right = view_inv[:3, 0]
    cam_up = view_inv[:3, 1] 
    
    for billboard_comp, parent_transform in billboard_labels:
        if billboard_comp.shader:
    
            offset_world = parent_transform.trs @ util.vec(*billboard_comp.offset_local, 1.0)
            center = offset_world[:3]
            
            # Pass uniforms to shader of billboard
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
    

    if current_subtitle:
        imgui.set_next_window_position(winWidth // 2 - 300, winHeight - 120)
        imgui.set_next_window_size(600, 100)
        
        imgui.begin("##subtitle", flags=imgui.WINDOW_NO_TITLE_BAR | 
                                        imgui.WINDOW_NO_RESIZE | 
                                        imgui.WINDOW_NO_MOVE |
                                        imgui.WINDOW_NO_SCROLLBAR)
        
        imgui.push_style_color(imgui.COLOR_TEXT, 1.0, 1.0, 1.0, 1.0)
        
        # Calculate padding to center
        text_width = imgui.calc_text_size(current_subtitle).x
        window_width = imgui.get_window_width()
        imgui.set_cursor_pos_x((window_width - text_width) * 0.5)
        imgui.set_cursor_pos_y(40)
        
        imgui.text(current_subtitle)
        imgui.pop_style_color()
        imgui.end()

    scene.render_post()
    
scene.shutdown()