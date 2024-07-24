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

TextureLib().make_texture(name="grass", path=definitions.TEXTURE_DIR / "Texture_Grass.png")

camera = Scene().add_entity()
Scene().add_component(camera, InfoComponent("main camera"))
Scene().add_component(camera, TransformComponent(glm.vec3(0, 0, 10), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1), static=False))
Scene().add_component(camera, CameraComponent(60, 16/9, 0.01, 500, 10, CameraComponent.Type.PERSPECTIVE))
Scene().add_component(camera, CameraControllerComponent())
Scene().set_primary_cam(camera) 

light = Scene().add_entity()
Scene().add_component(light, InfoComponent("model"))
Scene().add_component(light, TransformComponent(glm.vec3(5, -10, 5), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1), static=True))
Scene().add_component(light, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "cube" / "source" / "cube.obj"))
Scene().add_component(light, ForwardShaderComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "base_color_shader.wgsl")) 
Scene().add_component(light, LightComponent(intensity=1.0, color=glm.vec3(1.0, 1.0, 0.5)))
Scene().add_component(light, MaterialComponent())

model = Scene().add_entity()
Scene().add_component(model, InfoComponent("model"))
Scene().add_component(model, TransformComponent(glm.vec3(0, 0, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1), static=True))
Scene().add_component(model, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "cube" / "source" / "cube.obj"))
Scene().add_component(model, ForwardShaderComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "blin_phong_shader.wgsl")) 
Scene().add_component(model, LightAffectionComponent(light_entity=light))
Scene().add_component(model, MaterialComponent())

Scene().add_system(SkyboxSystem([SkyboxComponent]))
Scene().add_system(TransformSystem([TransformComponent]))
Scene().add_system(CameraSystem([CameraComponent, TransformComponent]))
Scene().add_system(CameraControllerSystem([CameraControllerComponent, CameraComponent, TransformComponent]))
Scene().add_system(MeshSystem([MeshComponent]))
Scene().add_system(DeferedLightShaderSystem([DeferredLightComponent]))
Scene().add_system(ForwardShaderSystem([ForwardShaderComponent])) 

GpuController().set_texture_sampler(
    shader_component=Scene().get_component(model, ForwardShaderComponent), 
    texture_name="diffuse_texture", 
    sampler_name="diffuse_sampler", 
    texture=TextureLib().get_texture(name="grass")
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

def update_model_uniforms(ent: Entity): 
    cam: Entity = Scene().get_primary_cam() 

    transform: TransformComponent = Scene().get_component(ent, TransformComponent)   
    shader: ForwardShaderComponent = Scene().get_component(ent, ForwardShaderComponent)
    cam_comp: CameraComponent = Scene().get_component(cam, CameraComponent) 
    cam_trans: TransformComponent = Scene().get_component(cam, TransformComponent)

    light_link: LightAffectionComponent = Scene().get_component(ent, LightAffectionComponent) 
    light_trans: TransformComponent = Scene().get_component(light_link.light, TransformComponent)
    
    near_far = glm.vec2(cam_comp.near, cam_comp.far) 
    model = transform.world_matrix
    view = cam_comp.view 
    projection = cam_comp.projection
    view_pos = cam_trans.translation
    light_pos = light_trans.translation

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
        member_name="view_pos",
        uniform_value=view_pos,
        float3=True
    )
    GpuController().set_uniform_value(
        shader_component=shader,
        buffer_name="ubuffer",
        member_name="light_pos",
        uniform_value=light_pos,
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
)
while canvas._running:
    ts = TimeStepManager().update()
    event = canvas.event_input_process();
    width = canvas._windowWidth
    height = canvas._windowHeight
    Scene().update(event, ts)

    update_light_uniforms(light)
    update_model_uniforms(model)

    Renderer().render([width, height])
    canvas.display()

canvas.shutdown()