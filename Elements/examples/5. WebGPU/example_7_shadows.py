from random import random, randint
import wgpu
import glm
import numpy as np
import Elements.definitions as definitions

from Elements.pyGLV.GUI.Viewer import GLFWWindow
from Elements.pyGLV.GUI.Viewer import button_map

from Elements.pyECSS.systems.wgpu_transform_system import TransformSystem
from Elements.pyECSS.systems.wgpu_camera_controller_system import CameraControllerSystem
from Elements.pyECSS.systems.wgpu_camera_system import CameraSystem
from Elements.pyECSS.systems.wgpu_mesh_system import MeshSystem
from Elements.pyECSS.systems.wpgu_forward_shader_system import ForwardShaderSystem
from Elements.pyECSS.systems.wgpu_skybox_system import SkyboxSystem
from Elements.pyECSS.systems.wgpu_defered_shader_system import DeferedLightShaderSystem

from Elements.pyECSS.wgpu_components import *
from Elements.pyECSS.wgpu_entity import Entity
from Elements.pyECSS.wgpu_time_manager import TimeStepManager
from Elements.pyGLV.GL.wpgu_scene import Scene

from Elements.pyGLV.GUI.wgpu_renderer import Renderer
from Elements.pyGLV.GUI.Input_manager import InputManager
from Elements.pyGLV.GUI.wgpu_gpu_controller import GpuController

from Elements.pyGLV.GL.wgpu_texture import TextureLib

canvas = GLFWWindow(windowHeight=800, windowWidth=1280, wgpu=True, windowTitle="Wgpu Example", vsync=None)
canvas.init()

# Create a wgpu device
adapter = wgpu.gpu.request_adapter(power_preference="high-performance")
device = adapter.request_device()
GpuController().set_adapter_device(device=device, adapter=adapter)

# Prepare present context
present_context = canvas.get_context()
render_texture_format = present_context.get_preferred_format(device.adapter)
present_context.configure(device=device, format=render_texture_format)
InputManager().set_monitor(canvas) 

TextureLib().make_texture(name="plane_texture", path=definitions.TEXTURE_DIR / "dark_wood_texture.jpg")
TextureLib().make_texture(name="building", path=definitions.MODEL_DIR / "stronghold" / "textures" / "texture_building.jpeg")

camera = Scene().add_entity()
Scene().add_component(camera, InfoComponent("main camera"))
Scene().add_component(camera, TransformComponent(glm.vec3(0, 0, 10), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1), static=False))
Scene().add_component(camera, CameraComponent(60, 16/9, 0.01, 500, 10, CameraComponent.Type.PERSPECTIVE))
Scene().add_component(camera, CameraControllerComponent())
Scene().set_primary_cam(camera) 

light = Scene().add_entity()
Scene().add_component(light, InfoComponent("light"))
Scene().add_component(light, TransformComponent(glm.vec3(0, -10, 10), glm.vec3(30, 0, 0), glm.vec3(1, 1, 1), static=False))
Scene().add_component(light, LightComponent(intensity=1.0)) 
Scene().add_component(light, CameraComponent(60, 16/9, 0.01, 500, 35, CameraComponent.Type.PERSPECTIVE))  

building = Scene().add_entity()
Scene().add_component(building, InfoComponent("building"))
Scene().add_component(building, TransformComponent(glm.vec3(0, 2, -5), glm.vec3(0, -90, 180), glm.vec3(0.01, 0.01, 0.01), static=True))
Scene().add_component(building, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "stronghold" / "source" / "building.obj"))
Scene().add_component(building, ForwardShaderComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "blin_phong_shadow_shader.wgsl"))
Scene().add_component(building, MaterialComponent())
Scene().add_component(building, ShadowAffectionComponent(light_entity=light)) 

plane = Scene().add_entity()
Scene().add_component(plane, InfoComponent("Plane2"))
Scene().add_component(plane, TransformComponent(glm.vec3(0, 3, 0), glm.vec3(0, 0, 0), glm.vec3(100, 0.1, 100), static=True))
Scene().add_component(plane, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "cube-sphere" / "cube.obj"))
Scene().add_component(plane, ForwardShaderComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "blin_phong_shadow_shader.wgsl"))
Scene().add_component(plane, MaterialComponent())
Scene().add_component(plane, ShadowAffectionComponent(light_entity=light))

skyPaths = [
    definitions.TEXTURE_DIR / "Skyboxes" / "Sea" / "back.jpg",
    definitions.TEXTURE_DIR / "Skyboxes" / "Sea" / "front.jpg",
    definitions.TEXTURE_DIR / "Skyboxes" / "Sea" / "bottom.jpg",
    definitions.TEXTURE_DIR / "Skyboxes" / "Sea" / "top.jpg",
    definitions.TEXTURE_DIR / "Skyboxes" / "Sea" / "right.jpg",
    definitions.TEXTURE_DIR / "Skyboxes" / "Sea" / "left.jpg",
]

sky = Scene().add_entity()
Scene().add_component(sky, InfoComponent("cubemap"))
Scene().add_component(sky, SkyboxComponent("sky", skyPaths))

Scene().add_system(SkyboxSystem([SkyboxComponent]))
Scene().add_system(TransformSystem([TransformComponent]))
Scene().add_system(CameraSystem([CameraComponent, TransformComponent]))
Scene().add_system(CameraControllerSystem([CameraControllerComponent, CameraComponent, TransformComponent]))
Scene().add_system(MeshSystem([MeshComponent]))
Scene().add_system(DeferedLightShaderSystem([DeferredLightComponent]))
Scene().add_system(ForwardShaderSystem([ForwardShaderComponent])) 

GpuController().set_texture_sampler(
    shader_component=Scene().get_component(plane, ForwardShaderComponent), texture_name="albedo_texture", sampler_name="albedo_sampler", texture=TextureLib().get_texture(name="plane_texture")
)
GpuController().set_texture_sampler(
    shader_component=Scene().get_component(building, ForwardShaderComponent), texture_name="albedo_texture", sampler_name="albedo_sampler", texture=TextureLib().get_texture(name="building")
)

def update_uniforms(ent: Entity): 
    camera_ent:Entity = Scene().get_primary_cam()

    camera_comp: CameraComponent = Scene().get_component(camera_ent, CameraComponent) 
    camera_trans: TransformComponent = Scene().get_component(camera_ent, TransformComponent) 
    shader_comp: ForwardShaderComponent = Scene().get_component(ent, ForwardShaderComponent)
    plane_trans: TransformComponent = Scene().get_component(ent, TransformComponent)  
    light_link: ShadowAffectionComponent = Scene().get_component(ent, ShadowAffectionComponent) 

    light:Entity = light_link.light 
    light_camera:CameraComponent = Scene().get_component(light, CameraComponent)
    light_trans:TransformComponent = Scene().get_component(light, TransformComponent)

    view = camera_comp.view
    projection = camera_comp.projection
    model = plane_trans.world_matrix  
    light_view = light_camera.view 
    light_proj = light_camera.projection 
    light_pos = light_trans.translation 
    view_pos = camera_trans.translation
    near = camera_comp.near
    far = camera_comp.far
    near_far = glm.vec2(near, far)

    GpuController().set_uniform_value(
        shader_component=shader_comp, buffer_name="ubuffer", member_name="view", uniform_value=view, mat4x4f=True
    )
    GpuController().set_uniform_value(
        shader_component=shader_comp, buffer_name="ubuffer", member_name="projection", uniform_value=projection, mat4x4f=True
    )
    GpuController().set_uniform_value(
        shader_component=shader_comp, buffer_name="ubuffer", member_name="model", uniform_value=model, mat4x4f=True
    )
    GpuController().set_uniform_value(
        shader_component=shader_comp, buffer_name="ubuffer", member_name="light_view", uniform_value=light_view, mat4x4f=True
    )
    GpuController().set_uniform_value(
        shader_component=shader_comp, buffer_name="ubuffer", member_name="light_proj", uniform_value=light_proj, mat4x4f=True
    )
    GpuController().set_uniform_value(
        shader_component=shader_comp, buffer_name="ubuffer", member_name="light_pos", uniform_value=light_pos, float3=True
    )
    GpuController().set_uniform_value(
        shader_component=shader_comp, buffer_name="ubuffer", member_name="view_pos", uniform_value=view_pos, float3=True
    ) 
    GpuController().set_uniform_value(
        shader_component=shader_comp, buffer_name="ubuffer", member_name="near_far", uniform_value=near_far, float2=True
    ) 


Renderer().init(
    present_context=present_context,
    render_texture_format=render_texture_format,
)
while canvas._running:
    ts = TimeStepManager().update()
    event = canvas.event_input_process();
    width = canvas._windowWidth
    height = canvas._windowHeight
    Scene().update(event, ts)

    update_uniforms(building)
    update_uniforms(plane)

    Renderer().render([width, height])
    canvas.display()

canvas.shutdown()