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

TextureLib().make_texture(name="building", path=definitions.MODEL_DIR / "stronghold" / "textures" / "texture_building.jpeg")

camera = Scene().add_entity()
Scene().add_component(camera, InfoComponent("main camera"))
Scene().add_component(camera, TransformComponent(glm.vec3(0, 0, 10), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1), static=False))
Scene().add_component(camera, CameraComponent(60, 16/9, 0.01, 500, 10, CameraComponent.Type.PERSPECTIVE))
Scene().add_component(camera, CameraControllerComponent())
Scene().set_primary_cam(camera)

light = Scene().add_entity()
Scene().add_component(light, InfoComponent("model"))
Scene().add_component(light, TransformComponent(glm.vec3(5, -10, 5), glm.vec3(0, 0, 0), glm.vec3(0.3, 0.3, 0.3), static=True))
Scene().add_component(light, LightComponent(intensity=1.0, color=glm.vec3(1.0, 1.0, 0.5))) 

deferred_light = Scene().add_entity() 
Scene().add_component(deferred_light, DeferredLightComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "deferred_simple_shader.wgsl")) 
Scene().add_component(deferred_light, MaterialComponent())
Scene().add_component(deferred_light, LightAffectionComponent(light_entity=light))

building = Scene().add_entity()
Scene().add_component(building, InfoComponent("building"))
Scene().add_component(building, TransformComponent(glm.vec3(0, 2, -5), glm.vec3(0, -90, 180), glm.vec3(0.01, 0.01, 0.01), static=True))
Scene().add_component(building, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "stronghold" / "source" / "building.obj"))
Scene().add_component(building, DeferrdGeometryComponent(diffuse_texture="building"))
Scene().add_component(building, MaterialComponent())

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

    update_uniforms(deferred_light)

    Renderer().render([width, height])
    canvas.display()

canvas.shutdown()