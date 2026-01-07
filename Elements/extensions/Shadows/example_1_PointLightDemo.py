from __future__ import annotations
import numpy as np
import OpenGL.GL as gl
import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, RenderMesh, Camera
from Elements.pyECSS.System import TransformSystem, CameraSystem
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GUI.Viewer import RenderGLStateSystem
from Elements.pyGLV.GUI.ImguiDecorator import ImGUIecssDecorator2
from Elements.pyGLV.GL.VertexArray import VertexArray
from Elements.pyGLV.GL.Shader import InitGLShaderSystem
from Elements.pyECSS.Event import Event
from Elements.utils.normals import generateFlatNormalsMesh
from Elements.utils.Shortcuts import displayGUI_text
import imgui
import time

from Elements.pyGLV.GL.ShadowShader import ShadowShader, ShadowMappingSystem


example_description = f"SHADOW MAPPING DEMO 2 (POINT LIGHTS)\n\n" + \
"This example demonstrates shadow mapping using a  Point Light\n " + \
"A room with walls, floor, and ceiling is illuminated by the light source, casting shadows from two cubes.\n\n" + \
"Use the ImGUI panel to adjust shadow settings, visualize the shadow map, and control the light position."


# Globals for ImGUI
enable_shadows = True
enable_soft_shadows = True
pcf_disk_radius = 0.5 
show_shadow_map = False

view_from_light = False 
animate_light = False       
debug_visualization_mode = 0 # 0=Normal, 1=Depth, 2=Comparison
shadow_bias = 0.3
viz_lit_color = [0.0, 1.0, 0.0]     
viz_shadow_color = [1.0, 0.0, 0.0]  #

def main():
    global enable_shadows, enable_soft_shadows, pcf_disk_radius, show_shadow_map
    global view_from_light, animate_light, debug_visualization_mode, shadow_bias, viz_lit_color, viz_shadow_color

    winWidth, winHeight = 1200, 800
    scene = Scene()
    rootEntity = scene.world.createEntity(Entity(name="Root"))

    shader_vert = ShadowShader.VERT_POINT_PHONG
    shader_frag = ShadowShader.FRAG_POINT_PHONG
  
    # Initial Light Position
    Lposition = [-3.0, 1.0, -1.2] 
    Ltarget = [0.0, 0.0, 0.0]
    Lcolor = [1.2, 1.2, 1.2]

    # Systems
    transUpdate = scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
    camUpdate = scene.world.createSystem(CameraSystem("camUpdate", "CameraUpdate", "200"))
    initUpdate = scene.world.createSystem(InitGLShaderSystem())

    # --- LIGHT ENTITY ---
    light_Entity = scene.world.createEntity(Entity(name="light_Entity"))
    scene.world.addEntityChild(rootEntity, light_Entity)
    light_trans = scene.world.addComponent(light_Entity, BasicTransform(name="light_Entity_trans", trs=util.translate(*Lposition)))
    
    light_target_Entity = scene.world.createEntity(Entity(name="light_target_Entity"))
    scene.world.addEntityChild(rootEntity, light_target_Entity)
    scene.world.addComponent(light_target_Entity, BasicTransform(name="light_target_Entity_trans", trs=util.translate(*Ltarget)))

    # --- SHADOW SYSTEM ---
    shadowSystem = scene.world.createSystem(ShadowMappingSystem(name="ShadowSystem", lightNode=light_Entity, lightTargetNode=light_target_Entity, shadowMapSize=2048, lightType="point"))

    # --- CAMERA ---
    physicalCamera = scene.world.createEntity(Entity(name="entitycam1"))
    scene.world.addEntityChild(rootEntity, physicalCamera)
    scene.world.addComponent(physicalCamera, BasicTransform(name="trans1", trs=util.identity()))
    
    eye = util.vec(0, 5, 20) 
    target = util.vec(0, 0, 0)
    up = util.vec(0, 1, 0)
    projMat = util.perspective(50.0, winWidth/winHeight, 0.1, 100.0)
    viewMat = util.lookat(eye, target, up)
    m = np.linalg.inv(projMat @ viewMat)

    cameraLens = scene.world.createEntity(Entity(name="entitycam2"))
    scene.world.addEntityChild(physicalCamera, cameraLens)
    orthoCamera = scene.world.addComponent(cameraLens, Camera(m, "orthoCam","Camera","500"))

    vertexCube = np.array([[-0.5, -0.5, 0.5, 1.0], 
                           [-0.5, 0.5, 0.5, 1.0], 
                           [0.5, 0.5, 0.5, 1.0], 
                           [0.5, -0.5, 0.5, 1.0], 
                           [-0.5, -0.5, -0.5, 1.0], 
                           [-0.5, 0.5, -0.5, 1.0], 
                           [0.5, 0.5, -0.5, 1.0], 
                           [0.5, -0.5, -0.5, 1.0]], dtype=np.float32)
    
    indexCube = np.array((1,0,3, 1,3,2, 2,3,7,
                          2,7,6, 3,0,4, 3,4,7,
                          6,5,1, 6,1,2, 4,5,6, 
                          4,6,7, 5,4,0, 5,0,1), np.uint32)

    all_meshes = [] 

    # lets visualize the light source as a small yellow cube
    lightViz = scene.world.createEntity(Entity(name="LightBulb"))
    scene.world.addEntityChild(light_Entity, lightViz) 
    scene.world.addComponent(lightViz, BasicTransform(name="LightBulb_TRS", trs=util.scale(0.3, 0.3, 0.3))) 

    # Create Yellow Mesh
    meshViz = scene.world.addComponent(lightViz, RenderMesh(name="LightBulb_Mesh"))
    colorBulb = np.array([[1.0, 1.0, 0.0, 1.0]] * 8, dtype=np.float32) # Yellow
    v, i, c, n = generateFlatNormalsMesh(vertexCube, indexCube, colorBulb)
    meshViz.vertex_attributes.extend([v, c, n, np.zeros_like(v)[:,:2]]) 
    meshViz.vertex_index.append(i)
    scene.world.addComponent(lightViz, VertexArray())
    
    # Add Shader to list so it gets updated
    shaderViz = scene.world.addComponent(lightViz, ShadowShader(name="LightBulb_Shader", vertex_source=shader_vert, fragment_source=shader_frag))
    all_meshes.append(shaderViz)

    # ==========================================================


    def create_object(name, pos, scale, color):
        """Helper to spawn walls and cubes"""
        entity = scene.world.createEntity(Entity(name=name))
        scene.world.addEntityChild(rootEntity, entity)
        scene.world.addComponent(entity, BasicTransform(name=f"{name}_TRS", trs=util.translate(*pos) @ util.scale(*scale)))
        
        mesh = scene.world.addComponent(entity, RenderMesh(name=f"{name}_Mesh"))
        colorArray = np.array([color] * 8, dtype=np.float32)
        v, i, c, n = generateFlatNormalsMesh(vertexCube, indexCube, colorArray)
        mesh.vertex_attributes.extend([v, c, n, np.zeros_like(v)[:,:2]]) 
        mesh.vertex_index.append(i)
        scene.world.addComponent(entity, VertexArray())
        
        shader = scene.world.addComponent(entity, ShadowShader(name=f"{name}_Shader", vertex_source=shader_vert, fragment_source=shader_frag))
        all_meshes.append(shader)
        return entity

    # Colors
    grey = [0.7, 0.7, 0.7, 1.0]
    red = [1.0, 0.2, 0.2, 1.0]
    blue = [0.2, 0.2, 1.0, 1.0]

    # --- ROOM ---
    create_object("Floor", [0, -5, 0], [20, 1, 20], grey)
    create_object("Ceiling", [0, 5, 0], [20, 1, 20], grey)
    create_object("BackWall", [0, 0, -10], [20, 10, 1], grey)
    create_object("LeftWall", [-10, 0, 0], [1, 10, 20], grey)
    create_object("RightWall", [10, 0, 0], [1, 10, 20], grey)

    # --- OBJECTS ---
    create_object("CubeLeft", [-4, -3, 0], [3, 3, 3], red)
    create_object("CubeRight", [4, -2, 0], [3, 3, 3], blue)
    cube3 = create_object("CubeFloat", [0, 3, 0], [1, 1, 1], [0.2, 1.0, 0.2, 1.0])

    # --- INIT ---
    scene.init(imgui=True, windowWidth=winWidth, windowHeight=winHeight, windowTitle="Elements: Shadow Mapping", customImGUIdecorator=ImGUIecssDecorator2)
    scene.renderWindow.color = [0.0, 0.0, 0.0, 1.0] 
    shadowSystem.init()
    shadowSystem.set_viewport_dimensions(winWidth, winHeight)
    
    for shader in all_meshes:
        shader.init()
        
    scene.world.traverse_visit(initUpdate, scene.world.root)

    # Event Manager
    eManager = scene.world.eventManager
    gWindow = scene.renderWindow
    gGUI = scene.gContext
    renderGLEventActuator = RenderGLStateSystem()
    updateTRS = Event(name="OnUpdateTRS", id=100, value=None)
    updateBackground = Event(name="OnUpdateBackground", id=200, value=None)
    eManager._events[updateTRS.name] = updateTRS
    eManager._events[updateBackground.name] = updateBackground
    eManager._subscribers[updateTRS.name] = gGUI
    eManager._subscribers[updateBackground.name] = gGUI
    eManager._subscribers['OnUpdateWireframe'] = gWindow
    eManager._actuators['OnUpdateWireframe'] = renderGLEventActuator
    eManager._subscribers['OnUpdateCamera'] = gWindow
    eManager._actuators['OnUpdateCamera'] = renderGLEventActuator
    eManager._publishers[updateBackground.name] = gGUI
    gWindow._myCamera = viewMat
    gGUI.createViewMatrix(eye, target, up)
    
    # disable texture/shadows on the visual light sphere so it glows
    shaderViz.setUniformVariable(key='uHasShadow', value=0, boolean=True)
    shaderViz.setUniformVariable(key='useTexture', value=0, boolean=True)

    running = True
    rotation_angle = 0.0
    start_time = time.time()

    while running:
        scene.world.traverse_visit(transUpdate, scene.world.root) 
        scene.world.traverse_visit_pre_camera(camUpdate, orthoCamera)
        scene.world.traverse_visit(camUpdate, scene.world.root)
        
        running = scene.render()
        displayGUI_text(example_description)
        
        # moving light
        if animate_light:
            curr_time = time.time() - start_time
            radius = 9.0 
            speed = 1.0
            
            new_x = np.sin(curr_time * speed) * radius
            new_z = np.cos(curr_time * speed) * radius
            new_y = np.sin(curr_time * speed * 0.5) * 3.0
            
            Lposition = [new_x, new_y, new_z]
            
            light_trans.trs = util.translate(*Lposition)

        # CONTROLS 
        imgui.begin("Shadow & Light Control")
        imgui.text(f"FPS: {imgui.get_io().framerate:.1f}")
        
        if imgui.collapsing_header("Light Controls", True):
            _, animate_light = imgui.checkbox("Auto-Orbit Light", animate_light)
            if not animate_light:
                changed, Lposition = imgui.drag_float3("Light Position", *Lposition, change_speed=0.1)
                if changed:
                    light_trans.trs = util.translate(*Lposition)
        
        if imgui.collapsing_header("Visualization", True):
            if imgui.radio_button("Normal Render", debug_visualization_mode == 0): debug_visualization_mode = 0
            if imgui.radio_button("Light Depth", debug_visualization_mode == 1): debug_visualization_mode = 1
            if imgui.radio_button("Shadow Check", debug_visualization_mode == 2): debug_visualization_mode = 2
            
            if debug_visualization_mode == 2:
                _, viz_lit_color = imgui.color_edit3("Lit Color", *viz_lit_color)
                _, viz_shadow_color = imgui.color_edit3("Shadow Color", *viz_shadow_color)

        if imgui.collapsing_header("Shadow Settings", True):
            _, enable_shadows = imgui.checkbox("Enable Shadows", enable_shadows)
            _, enable_soft_shadows = imgui.checkbox("Soft Shadows (PCF)", enable_soft_shadows)
            _, pcf_disk_radius = imgui.slider_float("PCF Softness", pcf_disk_radius, 0.0, 5.0)
            
            _, shadow_bias = imgui.slider_float("Shadow Bias (Acne)", shadow_bias, 0.0, 1.0, "%.4f")
            
            _, show_shadow_map = imgui.checkbox("Show Unfolded Map", show_shadow_map)
            _, view_from_light = imgui.checkbox("View from Light", view_from_light)
            
        imgui.end()

        cube3.getChildByType(BasicTransform.getClassName()).trs = util.translate(0, 3, 0) @ util.rotate((0, 1, 0), rotation_angle) @ util.rotate((1, 0, 0), rotation_angle)
        rotation_angle += 1.0

        light_viz_trans = lightViz.getChildByType(BasicTransform.getClassName())
        if view_from_light:
            light_viz_trans.trs = util.scale(0.0, 0.0, 0.0)
            cam_eye = util.vec(Lposition[0], Lposition[1], Lposition[2])
            viewMat = util.lookat(cam_eye, util.vec([0,0,0]), util.vec([0,1,0]))
        else:
            light_viz_trans.trs = util.scale(0.3, 0.3, 0.3)
            viewMat = gWindow._myCamera

        # Update Uniforms
        for shader in all_meshes:
            shader.setUniformVariable(key='projection', value=projMat, mat4=True)
            shader.setUniformVariable(key='view', value=viewMat, mat4=True) 
            shader.setUniformVariable(key='lightPos', value=Lposition, float3=True)
            shader.setUniformVariable(key='viewPos', value=eye, float3=True)
            shader.setUniformVariable(key='lightColor', value=Lcolor, float3=True)
            shader.setUniformVariable(key='uHasShadow', value=1 if enable_shadows else 0, boolean=True)
            shader.setUniformVariable(key='uSoftShadows', value=1 if enable_soft_shadows else 0, boolean=True)
            shader.setUniformVariable(key='uPcfDisk', value=pcf_disk_radius, float1=True)
            
            shader.setUniformVariable(key='uDebugMode', value=debug_visualization_mode, boolean=True)
            shader.setUniformVariable(key='uShadowBias', value=shadow_bias, float1=True)
            shader.setUniformVariable(key='uLitColorViz', value=viz_lit_color, float3=True)
            shader.setUniformVariable(key='uShadowColorViz', value=viz_shadow_color, float3=True)


        shadowSystem.render(scene.world.root)
        
        if show_shadow_map:
            shadowSystem.render_debug_view()
            
        scene.render_post()
        
    scene.shutdown()

if __name__ == "__main__":
    main()