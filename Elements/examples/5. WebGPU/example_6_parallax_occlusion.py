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

TextureLib().make_texture(name="brick", path=definitions.MODEL_DIR / "cube" / "textures" / "bricks2.jpg")
TextureLib().make_texture(name="brick_normal", path=definitions.MODEL_DIR / "cube" / "textures" / "bricks2_normal.jpg")
TextureLib().make_texture(name="birck_disp", path=definitions.MODEL_DIR / "cube" / "textures" / "bricks2_disp.jpg")

camera = Scene().add_entity()
Scene().add_component(camera, InfoComponent("main camera"))
Scene().add_component(camera, TransformComponent(glm.vec3(0, 0, 10), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1), static=False))
Scene().add_component(camera, CameraComponent(60, 16/9, 0.01, 500, 10, CameraComponent.Type.PERSPECTIVE))
Scene().add_component(camera, CameraControllerComponent())
Scene().set_primary_cam(camera)

light = Scene().add_entity()
Scene().add_component(light, InfoComponent("model"))
Scene().add_component(light, TransformComponent(glm.vec3(0, 0, 5), glm.vec3(0, 0, 0), glm.vec3(0.3, 0.3, 0.3), static=True))
Scene().add_component(light, LightComponent(intensity=1.0, color=glm.vec3(1.0, 1.0, 0.5)))

model = Scene().add_entity()
Scene().add_component(model, InfoComponent("model"))
Scene().add_component(model, TransformComponent(glm.vec3(0, 0, 0), glm.vec3(-90, 0, 0), glm.vec3(1, 1, 1), static=True))
Scene().add_component(model, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "cube-sphere" / "plane.obj"))
Scene().add_component(model, ForwardShaderComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "paralax_oclusion_shader.wgsl"))
Scene().add_component(model, MaterialComponent())
Scene().add_component(model, LightAffectionComponent(light_entity=light))

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
    shader_component=Scene().get_component(model, ForwardShaderComponent), 
    texture_name="u_AlbedoTexture", 
    sampler_name="u_AlbedoSampler", 
    texture=TextureLib().get_texture(name="brick")
)
GpuController().set_texture_sampler(
    shader_component=Scene().get_component(model, ForwardShaderComponent), 
    texture_name="u_NormalMap", 
    sampler_name="u_NormalSampler", 
    texture=TextureLib().get_texture(name="brick_normal")
)
GpuController().set_texture_sampler(
    shader_component=Scene().get_component(model, ForwardShaderComponent), 
    texture_name="u_DisplacementMap", 
    sampler_name="u_DisplacementSampler", 
    texture=TextureLib().get_texture(name="birck_disp")
)

def update_uniforms(ent: Entity): 
    cam: Entity = Scene().get_primary_cam()
    light_link: LightAffectionComponent = Scene().get_component(ent, LightAffectionComponent)  
    light_comp: LightComponent = Scene().get_component(light_link.light, LightComponent)
    light_trans: TransformComponent = Scene().get_component(light_link.light, TransformComponent)

    transform: TransformComponent = Scene().get_component(ent, TransformComponent)   
    shader: ForwardShaderComponent = Scene().get_component(ent, ForwardShaderComponent)
    cam_trans: TransformComponent = Scene().get_component(cam, TransformComponent)
    cam: CameraComponent = Scene().get_component(cam, CameraComponent)
    
    model = glm.transpose(transform.world_matrix)
    view = glm.transpose(cam.view)
    projection = glm.transpose(cam.projection)
    objectColor = glm.vec4(1.0, 1.0, 1.0, 1.0)
    view_pos = glm.vec4(cam_trans.translation, 1.0) 
    light_pos = glm.vec4(light_trans.translation, 1.0) 
    light_color = glm.vec4(light_comp.color, 1.0)

    GpuController().set_uniform_value(
        shader_component=shader,
        buffer_name="u_UniformData",
        member_name="projectionMatrix",
        uniform_value=projection,
        mat4x4f=True
    )
    GpuController().set_uniform_value(
        shader_component=shader,
        buffer_name="u_UniformData",
        member_name="viewMatrix",
        uniform_value=view,
        mat4x4f=True
    )
    GpuController().set_uniform_value(
        shader_component=shader,
        buffer_name="u_UniformData",
        member_name="modelMatrix",
        uniform_value=model,
        mat4x4f=True
    )
    GpuController().set_uniform_value(
        shader_component=shader,
        buffer_name="u_UniformData",
        member_name="objectColor",
        uniform_value=objectColor,
        float4=True
    ) 
    GpuController().set_uniform_value(
        shader_component=shader,
        buffer_name="u_UniformData",
        member_name="viewPosition",
        uniform_value=view_pos,
        float4=True
    )
    GpuController().set_uniform_value(
        shader_component=shader,
        buffer_name="u_UniformData",
        member_name="lightPositions",
        uniform_value=light_pos,
        float4=True
    )
    GpuController().set_uniform_value(
        shader_component=shader,
        buffer_name="u_UniformData",
        member_name="lightColors",
        uniform_value=light_color,
        float4=True
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

    update_uniforms(model)

    Renderer().render([width, height])
    canvas.display()

canvas.shutdown()