from random import random, randint 
import os
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

# os.environ["WGPU_BACKEND_TYPE"] = "D3D12"
# os.environ["RUST_BACKTRACE"] = "1"

canvas = GLFWWindow(windowHeight=800, windowWidth=1280, wgpu=True, windowTitle="Wgpu Example", vsync=None)
canvas.init()

# Create a wgpu device 
adapter: wgpu.GPUAdapter = wgpu.gpu.request_adapter(power_preference="high-performance") 
print(adapter.request_adapter_info()) 
device = adapter.request_device()
GpuController().set_adapter_device(device=device, adapter=adapter)

# Prepare present context
present_context:wgpu.GPUCanvasContext = canvas.get_context() 
render_texture_format = present_context.get_preferred_format(adapter)  
present_context.configure(device=device, format=render_texture_format)
InputManager().set_monitor(canvas) 

TextureLib().make_texture(name="white", path=definitions.MODEL_DIR / "sponza" / "white.jpg")

camera = Scene().add_entity()
Scene().add_component(camera, InfoComponent("main camera"))
Scene().add_component(camera, TransformComponent(glm.vec3(0, 0, 10), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1), static=False))
Scene().add_component(camera, CameraComponent(60, 16/9, 0.01, 500, 10, CameraComponent.Type.PERSPECTIVE))
Scene().add_component(camera, CameraControllerComponent(movement_speed=10))
Scene().set_primary_cam(camera)

light = Scene().add_entity()
Scene().add_component(light, InfoComponent("model"))
Scene().add_component(light, TransformComponent(glm.vec3(50, -70, 5), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1), static=True))
Scene().add_component(light, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "cube" / "source" / "cube.obj"))
Scene().add_component(light, ForwardShaderComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "base_color_shader.wgsl")) 
Scene().add_component(light, LightComponent(intensity=1.0, color=glm.vec3(1.0, 1.0, 0.5)))
Scene().add_component(light, MaterialComponent())

deferred_light = Scene().add_entity() 
Scene().add_component(deferred_light, DeferredLightComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "deferred_phong_shader.wgsl")) 
Scene().add_component(deferred_light, MaterialComponent())
Scene().add_component(deferred_light, LightAffectionComponent(light_entity=light))

sponza = Scene().add_entity() 
Scene().add_component(sponza, TransformComponent(glm.vec3(0, 0, 0), glm.vec3(0, -120, 180), glm.vec3(0.1, 0.1, 0.1), static=True)) 
Scene().add_component(sponza, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "sponza" / "sponza.obj"))
Scene().add_component(sponza, DeferrdGeometryComponent(diffuse_texture="white")) 
Scene().add_component(sponza, MaterialComponent())

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

def update_uniforms(ent: Entity): 
    cam: Entity = Scene().get_primary_cam()   

    light_link: LightAffectionComponent = Scene().get_component(ent, LightAffectionComponent) 
    light_trans: TransformComponent = Scene().get_component(light_link.light, TransformComponent)
    shader: DeferredLightComponent = Scene().get_component(ent, DeferredLightComponent)
    cam_comp: CameraComponent = Scene().get_component(cam, CameraComponent) 
    cam_trans: TransformComponent = Scene().get_component(cam, TransformComponent)
    
    near_far = glm.vec2(cam_comp.near, cam_comp.far)  
    screen_size = glm.vec2(GpuController().render_target_size)
    view_pos = cam_trans.translation
    ligh_pos = light_trans.translation

    GpuController().set_uniform_value(
        shader_component=shader,
        buffer_name="ubuffer",
        member_name="view_pos",
        uniform_value=view_pos,
        float3=True
    )
    GpuController().set_uniform_value(
        shader_component=shader,
        buffer_name="ubuffer",
        member_name="light_pos",
        uniform_value=ligh_pos,
        float3=True
    )
    GpuController().set_uniform_value(
        shader_component=shader,
        buffer_name="ubuffer",
        member_name="screen_size",
        uniform_value=screen_size,
        float2=True
    )
    GpuController().set_uniform_value(
        shader_component=shader,
        buffer_name="ubuffer",
        member_name="near_far",
        uniform_value=near_far,
        float2=True
    )

def update_light_uniforms(ent: Entity): 
    cam: Entity = Scene().get_primary_cam() 

    transform: TransformComponent = Scene().get_component(ent, TransformComponent)   
    shader: ForwardShaderComponent = Scene().get_component(ent, ForwardShaderComponent)
    cam: CameraComponent = Scene().get_component(cam, CameraComponent) 
    light_comp: LightComponent = Scene().get_component(ent, LightComponent)
    
    near_far = glm.vec2(cam.near, cam.far) 
    color = light_comp.color
    model = transform.world_matrix
    view = cam.view 
    projection = cam.projection

    GpuController().set_uniform_value(
        shader_component=shader,
        buffer_name="ubuffer",
        member_name="projection",
        uniform_value=projection,
        mat4x4f=True
    )
    GpuController().set_uniform_value(
        shader_component=shader,
        buffer_name="ubuffer",
        member_name="view",
        uniform_value=view,
        mat4x4f=True
    )
    GpuController().set_uniform_value(
        shader_component=shader,
        buffer_name="ubuffer",
        member_name="model",
        uniform_value=model,
        mat4x4f=True
    )
    GpuController().set_uniform_value(
        shader_component=shader,
        buffer_name="ubuffer",
        member_name="color",
        uniform_value=color,
        float3=True
    )
    GpuController().set_uniform_value(
        shader_component=shader,
        buffer_name="ubuffer",
        member_name="near_far",
        uniform_value=near_far,
        float2=True
    )


Renderer().init(
    present_context=present_context,
    render_texture_format=render_texture_format,
    SSAO=True
)
while canvas._running:
    ts = TimeStepManager().update()
    event = canvas.event_input_process();
    width = canvas._windowWidth
    height = canvas._windowHeight
    Scene().update(event, ts)

    update_uniforms(deferred_light)
    update_light_uniforms(light)

    Renderer().render([1920, 1080])
    canvas.display()

canvas.shutdown()