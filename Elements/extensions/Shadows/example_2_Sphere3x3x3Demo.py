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
from Elements.pyGLV.GL.Textures import Texture
from Elements.pyECSS.Event import Event

from Elements.utils.normals import generateFlatNormalsMesh
from Elements.definitions import TEXTURE_DIR

from Elements.utils.Shortcuts import displayGUI_text
import imgui
import time 



from Elements.extensions.Shadows.ShadowShader import ShadowShader, ShadowMappingSystem

LIGHT_TYPE = "directional"  # "point" or "directional"

example_description = f"SHADOW MAPPING DEMO 1 (USING {LIGHT_TYPE.upper()} LIGHTS)\n\n" + \
"This example demonstrates shadow mapping using a " + ("Point Light" if LIGHT_TYPE == "point" else "Directional Light") + ".\n" + \
"A 3x3x3 grid of spheres is illuminated by the light source, casting shadows onto a textured floor.\n\n" + \
"Use the ImGUI panel to adjust shadow settings, visualize the shadow map, and control the light position."

# Globals for ImGUI
enable_shadows = True
enable_soft_shadows = False
pcf_disk_radius = 0.5 
show_shadow_map = False
view_from_light = False 
animate_light = False       
debug_visualization_mode = 0 # 0=Normal, 1=Depth, 2=Comparison

if LIGHT_TYPE == "point":
    shadow_bias = 0.3
else:   
    shadow_bias = 0.005

viz_lit_color = [0.0, 1.0, 0.0]     
viz_shadow_color = [1.0, 0.0, 0.0]

class ObjectCreator():
    def __init__(self, scene, root, name=None, type=None, id=None, vertex_source=None, frag_source=None) -> None:
        self.entity = Entity(name, type, id)
        self.entity.trans  = BasicTransform(name="trans", trs=util.identity())
        self.entity.mesh  = RenderMesh(name="mesh")
        
        if vertex_source is None or frag_source is None:
            # fallback if no shader specified
            vertex_source = ShadowShader.VERT_DIR_PHONG
            frag_source = ShadowShader.FRAG_DIR_PHONG

        self.entity.shadowShader = ShadowShader(name=f"{name}Shader", vertex_source=vertex_source, fragment_source=frag_source)
        self.entity.vArray = VertexArray()
        
        scene.world.createEntity(self.entity)
        scene.world.addEntityChild(root, self.entity)

        scene.world.addComponent(self.entity, self.entity.trans)
        scene.world.addComponent(self.entity, self.entity.mesh)
        scene.world.addComponent(self.entity, self.entity.shadowShader)
        scene.world.addComponent(self.entity, self.entity.vArray)
    
    @property
    def color(self):
        return self.entity._color
    @color.setter
    def color(self, colorArray):
        self.entity._color = colorArray

    def SetVertexAttributes(self, vertex, color, index, texCoords, normals = None):
        self.entity.mesh.vertex_attributes.append(vertex)
        self.entity.mesh.vertex_attributes.append(color)
        if normals is not None:
            self.entity.mesh.vertex_attributes.append(normals)
        self.entity.mesh.vertex_attributes.append(texCoords)
        self.entity.mesh.vertex_index.append(index)

def SphereSpawn(scene, root, color, position, vertex_source, frag_source, spherename = "Sphere"):
    sphere = ObjectCreator(scene, root, spherename, vertex_source=vertex_source, frag_source=frag_source)
    if color is None: color = [1.0,1.0,1.0,1.0]

    vertices = []; colors = []; indices = []; normals = []; texCoords = []
    
    for i in range(0, 21): 
        for j in range(0, 20):
            x = np.cos(2 * np.pi * j / 20) * np.sin(np.pi * i / 20)
            y = np.sin(2 * np.pi * j / 20) * np.sin(np.pi * i / 20)
            z = np.cos(np.pi * i / 20)
            vertices.append([x * 0.8, y * 0.8, z * 0.8, 1.0])
            colors.append(color)
            normals.append([x, y, z])
            texCoords.append([0.0,0.0])
            
    for i in range(0, 20):
        for j in range(0, 20):
            indices.append(i * 20 + j)
            indices.append((i + 1) * 20 + j)
            indices.append((i + 1) * 20 + (j + 1) % 20)
            indices.append(i * 20 + j)
            indices.append((i + 1) * 20 + (j + 1) % 20)
            indices.append(i * 20 + (j + 1) % 20)

    sphere.SetVertexAttributes(vertices, colors, indices, texCoords, normals)
    sphere.entity.trans.trs = util.translate(position[0], position[1], position[2])
    return sphere

def main():
    global enable_shadows, enable_soft_shadows, pcf_disk_radius, show_shadow_map, view_from_light, animate_light, debug_visualization_mode, shadow_bias
    global viz_lit_color, viz_shadow_color

    winWidth, winHeight = 1200, 800
    scene = Scene()
    rootEntity = scene.world.createEntity(Entity(name="Root"))

    if LIGHT_TYPE == "point":
        # Point Light Settings
        Lposition = [10.0, 10.0, 10.0] 
        target_shader_vert = ShadowShader.VERT_POINT_PHONG
        target_shader_frag = ShadowShader.FRAG_POINT_PHONG
        orbit_radius = 6.0
    else:
        # Directional Light Settings
        Lposition = [10.0, 10.0, 10.0] 
        target_shader_vert = ShadowShader.VERT_DIR_PHONG
        target_shader_frag = ShadowShader.FRAG_DIR_PHONG
        orbit_radius = 15.0

    Ltarget = [0.0, 0.0, 0.0]
    Lcolor = [2.0, 2.0, 2.0]

    transUpdate = scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
    camUpdate = scene.world.createSystem(CameraSystem("camUpdate", "CameraUpdate", "200"))
    initUpdate = scene.world.createSystem(InitGLShaderSystem())

    # Visual Representation of the Light (Yellow Sphere)
    visualLight = SphereSpawn(scene, rootEntity, [1.0, 1.0, 0.0, 1.0], Lposition, target_shader_vert, target_shader_frag, "VisualLight")
    visualLight.entity.trans.trs = util.translate(Lposition[0], Lposition[1], Lposition[2]) @ util.scale(0.5, 0.5, 0.5)

    # Light Entity (Logic)
    light_Entity = scene.world.createEntity(Entity(name="light_Entity"))
    scene.world.addEntityChild(rootEntity, light_Entity)
    scene.world.addComponent(light_Entity, BasicTransform(name="light_Entity_trans", trs=util.translate(Lposition[0], Lposition[1], Lposition[2])))
    
    light_target_Entity = scene.world.createEntity(Entity(name="light_target_Entity"))
    scene.world.addEntityChild(rootEntity, light_target_Entity)
    scene.world.addComponent(light_target_Entity, BasicTransform(name="light_target_Entity_trans", trs=util.translate(Ltarget[0], Ltarget[1], Ltarget[2])))

    # Shadow Mapping System
    shadowSystem = scene.world.createSystem(ShadowMappingSystem(name="ShadowSystem", lightNode=light_Entity, lightTargetNode=light_target_Entity, shadowMapSize=2048, lightType=LIGHT_TYPE))

    # Camera
    physicalCamera = scene.world.createEntity(Entity(name="entitycam1"))
    scene.world.addEntityChild(rootEntity, physicalCamera)
    scene.world.addComponent(physicalCamera, BasicTransform(name="trans1", trs=util.identity()))

    eye = util.vec(11, 6, 5)
    target = util.vec(0, 0, 0)
    up = util.vec(0, 1, 0)
    projMat = util.perspective(50.0, winWidth/winHeight, 0.1, 100.0)
    viewMat = util.lookat(eye, target, up)
    m = np.linalg.inv(projMat @ viewMat)

    cameraLens = scene.world.createEntity(Entity(name="entitycam2"))
    scene.world.addEntityChild(physicalCamera, cameraLens)
    orthoCamera = scene.world.addComponent(cameraLens, Camera(m, "orthoCam","Camera","500"))

    # Floor
    floorEntity = scene.world.createEntity(Entity(name="Floor"))
    scene.world.addEntityChild(rootEntity, floorEntity)
    scene.world.addComponent(floorEntity, BasicTransform(name="Floor_TRS", trs=util.translate(0, -1.0, 0) @ util.scale(10.0, 0.1, 10.0)))
    floorMesh = scene.world.addComponent(floorEntity, RenderMesh(name="Floor_Mesh"))

    verticesFloor = np.array([[-0.5, -0.5, 0.5, 1.0], 
                              [-0.5, 0.5, 0.5, 1.0], 
                              [0.5, 0.5, 0.5, 1.0],
                              [0.5, -0.5, 0.5, 1.0], 
                              [-0.5, -0.5, -0.5, 1.0], 
                              [-0.5, 0.5, -0.5, 1.0], 
                              [0.5, 0.5, -0.5, 1.0], 
                              [0.5, -0.5, -0.5, 1.0]], dtype=np.float32)
    indicesFloor = np.array((1,0,3, 1,3,2, 2,3,7, 
                             2,7,6, 3,0,4, 3,4,7, 
                             6,5,1, 6,1,2, 4,5,6, 
                             4,6,7, 5,4,0, 5,0,1), np.uint32)

    verticesF, indicesF, colorsF, normalsF = generateFlatNormalsMesh(verticesFloor, indicesFloor)
    floorMesh.vertex_attributes.extend([verticesF, colorsF, normalsF, Texture.CUBE_TEX_COORDINATES])
    floorMesh.vertex_index.append(indicesF)
    scene.world.addComponent(floorEntity, VertexArray())
    
    # Use selected shader
    floorShader = scene.world.addComponent(floorEntity, ShadowShader(name="FloorShader", vertex_source=target_shader_vert, fragment_source=target_shader_frag))

    # 3x3x3 grid of spheres
    spacing = 2.0 
    allSpheres = []
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if (x + y + z) % 2 == 0: current_color = [0.0,0.6,0.35,1.0]
                else: current_color = [0.6,0.05,0.15,1.0]
                pos_x = (x - 1) * spacing 
                pos_y = (y * spacing) + 1 
                pos_z = (z - 1) * spacing
                currentSphere = SphereSpawn(scene, rootEntity, current_color, [pos_x, pos_y, pos_z], target_shader_vert, target_shader_frag, f"Sphere_{x}{y}{z}")
                allSpheres.append(currentSphere)

    # Init
    scene.init(imgui=True, windowWidth=winWidth, windowHeight=winHeight, windowTitle="Elements: Shadow Mapping", customImGUIdecorator=ImGUIecssDecorator2)
    scene.renderWindow.color = [0.5, 0.5, 0.5, 1.0] 
    shadowSystem.init()
    shadowSystem.set_viewport_dimensions(winWidth, winHeight)
    floorShader.init()
    visualLight.entity.shadowShader.init() 
    for sphere in allSpheres:
        sphere.entity.shadowShader.init()
    scene.world.traverse_visit(initUpdate, scene.world.root)

    eManager = scene.world.eventManager; gWindow = scene.renderWindow; gGUI = scene.gContext
    renderGLEventActuator = RenderGLStateSystem()
    updateTRS = Event(name="OnUpdateTRS", id=100, value=None)
    updateBackground = Event(name="OnUpdateBackground", id=200, value=None)
    eManager._events[updateTRS.name] = updateTRS; eManager._events[updateBackground.name] = updateBackground
    eManager._subscribers[updateTRS.name] = gGUI; eManager._subscribers[updateBackground.name] = gGUI
    eManager._subscribers['OnUpdateWireframe'] = gWindow; eManager._actuators['OnUpdateWireframe'] = renderGLEventActuator
    eManager._subscribers['OnUpdateCamera'] = gWindow; eManager._actuators['OnUpdateCamera'] = renderGLEventActuator
    eManager._publishers[updateBackground.name] = gGUI
    gWindow._myCamera = viewMat; gGUI.createViewMatrix(eye, target, up)

    texturePath = TEXTURE_DIR / "dark_wood_texture.jpg"
    texture = Texture(texturePath)
    floorShader.setUniformVariable(key='ImageTexture', value=texture, texture=True)
    floorShader.setUniformVariable(key='useTexture', value=1, boolean=True)
    for sphere in allSpheres:
        sphere.entity.shadowShader.setUniformVariable(key='useTexture', value=0, boolean=True)
    
    # disable texture/shadows on the visual light sphere
   # visualLight.entity.shadowShader.setUniformVariable(key='useTexture', value=0, boolean=True)
   # visualLight.entity.shadowShader.setUniformVariable(key='uHasShadow', value=0, boolean=True)

    running = True
    start_time = time.time()

    while running:
        scene.world.traverse_visit(transUpdate, scene.world.root) 
        scene.world.traverse_visit_pre_camera(camUpdate, orthoCamera)
        scene.world.traverse_visit(camUpdate, scene.world.root)
        
        running = scene.render()
        displayGUI_text(example_description)
        
        # rotating light
        if animate_light:
            curr_time = time.time() - start_time
            speed = 1.0
            
            new_x = np.sin(curr_time * speed) * orbit_radius
            new_z = np.cos(curr_time * speed) * orbit_radius
            new_y = 10.0 + np.sin(curr_time * 1.0) * 5.0
            
            Lposition = [new_x, new_y, new_z]
            
            light_Entity.getChildByType(BasicTransform.getClassName()).trs = util.translate(new_x, new_y, new_z)
            visualLight.entity.trans.trs = util.translate(new_x, new_y, new_z) @ util.scale(0.5, 0.5, 0.5)

        # ImGUI Controls
        imgui.begin("Shadow Mapping Controls", True)
        imgui.text(f"FPS: {imgui.get_io().framerate:.1f}")
        
        if imgui.collapsing_header("Light Controls", True):
            _, animate_light = imgui.checkbox("Auto-Orbit Light", animate_light)
            if not animate_light:
                changed, Lposition = imgui.drag_float3("Light Position", *Lposition, change_speed=0.1)
                if changed:
                    light_Entity.getChildByType(BasicTransform.getClassName()).trs = util.translate(*Lposition)
                    visualLight.entity.trans.trs = util.translate(*Lposition) @ util.scale(0.5, 0.5, 0.5)

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
            _, pcf_disk_radius = imgui.slider_float("PCF Disk Radius", pcf_disk_radius, 0.0, 5.0)
            
            if LIGHT_TYPE == "point":
                _, shadow_bias = imgui.slider_float("Shadow Bias (Acne)", shadow_bias, 0.0, 1.0, "%.4f")
            else:
                _, shadow_bias = imgui.slider_float("Shadow Bias (Acne)", shadow_bias, 0.0, 0.1, "%.4f")
            
            _, show_shadow_map = imgui.checkbox("Show Unfolded Map", show_shadow_map)
            _, view_from_light = imgui.checkbox("View from Light", view_from_light)
        
        imgui.end()

        # View Matrix Selection
        if view_from_light:
            visualLight.entity.trans.trs = util.scale(0.0, 0.0, 0.0) # Hide sphere so it doesn't block view
            viewMat = util.lookat(util.vec(Lposition), util.vec([0,0,0]), util.vec([0,1,0]))
        else:
            visualLight.entity.trans.trs = util.translate(Lposition[0], Lposition[1], Lposition[2]) @ util.scale(0.5, 0.5, 0.5)
            viewMat = gWindow._myCamera

        def set_uniforms(shader):
            shader.setUniformVariable(key='projection', value=projMat, mat4=True)
            shader.setUniformVariable(key='view', value=viewMat, mat4=True) 
            shader.setUniformVariable(key='lightPos', value=Lposition, float3=True)
            shader.setUniformVariable(key='viewPos', value=eye, float3=True)
            shader.setUniformVariable(key='lightColor', value=Lcolor, float3=True)
            shader.setUniformVariable(key='uHasShadow', value=1 if enable_shadows else 0, boolean=True)
            shader.setUniformVariable(key='uSoftShadows', value=1 if enable_soft_shadows else 0, boolean=True)
            shader.setUniformVariable(key='uPcfDisk', value=pcf_disk_radius, float1=True)
            
            # VISUALISATION UNIFORMS
            shader.setUniformVariable(key='uDebugMode', value=debug_visualization_mode, boolean=True)
            shader.setUniformVariable(key='uShadowBias', value=shadow_bias, float1=True)
            shader.setUniformVariable(key='uLitColorViz', value=viz_lit_color, float3=True)
            shader.setUniformVariable(key='uShadowColorViz', value=viz_shadow_color, float3=True)

        set_uniforms(floorShader)
        set_uniforms(visualLight.entity.shadowShader) 
        for sphere in allSpheres:
            set_uniforms(sphere.entity.shadowShader)

        shadowSystem.render(scene.world.root)

        if show_shadow_map:
            shadowSystem.render_debug_view()

        scene.render_post()
        
    scene.shutdown()

if __name__ == "__main__":
    main()