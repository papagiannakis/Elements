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

TextureLib().make_texture(name="3x3", path=definitions.TEXTURE_DIR / "3x3.jpg")
TextureLib().make_texture(name="grass", path=definitions.TEXTURE_DIR / "Texture_Grass.png")
TextureLib().make_texture(name="Cauterizer", path=definitions.MODEL_DIR / "Cauterizer" / "cauterizer_low_01_Cauterizer_Blue_AlbedoTransparency.png")
TextureLib().make_texture(name="building", path=definitions.MODEL_DIR / "stronghold" / "textures" / "texture_building.jpeg")
TextureLib().make_texture(name="plane_texture", path=definitions.TEXTURE_DIR / "dark_wood_texture.jpg")
TextureLib().make_texture(name="white", path=definitions.MODEL_DIR / "sponza" / "white.jpg")
# TextureLib().make_texture(name="earth", path=definitions.TEXTURE_DIR / "earth.jpg")

light = Scene().add_entity()
Scene().add_component(light, InfoComponent("light"))
Scene().add_component(light, TransformComponent(glm.vec3(0, -10, 10), glm.vec3(30, 0, 0), glm.vec3(1, 1, 1), static=False))
Scene().add_component(light, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "cube-sphere" / "cube.obj"))
Scene().add_component(light, ForwardShaderComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "base_color_shader.wgsl"))
Scene().add_component(light, MaterialComponent())
Scene().add_component(light, LightComponent(intensity=1.0)) 
Scene().add_component(light, CameraComponent(60, 16/9, 0.01, 500, 35, CameraComponent.Type.PERSPECTIVE))  

camera = Scene().add_entity()
Scene().add_component(camera, InfoComponent("main camera"))
Scene().add_component(camera, TransformComponent(glm.vec3(0, 0, 10), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1), static=False))
Scene().add_component(camera, CameraComponent(60, 16/9, 0.01, 500, 10, CameraComponent.Type.PERSPECTIVE))
Scene().add_component(camera, CameraControllerComponent())
Scene().set_primary_cam(camera)

deferred_light = Scene().add_entity() 
Scene().add_component(deferred_light, DeferredLightComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "deferred_phong_shader.wgsl")) 
Scene().add_component(deferred_light, MaterialComponent())

building = Scene().add_entity()
Scene().add_component(building, InfoComponent("building"))
Scene().add_component(building, TransformComponent(glm.vec3(0, 2, -5), glm.vec3(0, -90, 180), glm.vec3(0.01, 0.01, 0.01), static=True))
Scene().add_component(building, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "stronghold" / "source" / "building.obj"))
# Scene().add_component(building, ForwardShaderComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "blin_phong_shadow_shader.wgsl"))
Scene().add_component(building, DeferrdGeometryComponent(diffuse_texture="building"))
Scene().add_component(building, MaterialComponent())
Scene().add_component(building, LightAffectionComponent(light_entity=light))

sponza = Scene().add_entity() 
Scene().add_component(sponza, TransformComponent(glm.vec3(-6, 2.5, 5), glm.vec3(0, -120, 180), glm.vec3(0.002, 0.002 ,0.002), static=True)) 
Scene().add_component(sponza, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "sponza" / "sponza.obj"))
# Scene().add_component(sponza, ForwardShaderComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "blin_phong_shader.wgsl")) 
Scene().add_component(sponza, DeferrdGeometryComponent(diffuse_texture="white")) 
Scene().add_component(sponza, MaterialComponent())
Scene().add_component(sponza, LightAffectionComponent(light_entity=light))

plane = Scene().add_entity()
Scene().add_component(plane, InfoComponent("Plane2"))
Scene().add_component(plane, TransformComponent(glm.vec3(0, 3, 0), glm.vec3(0, 0, 0), glm.vec3(100, 0.1, 100), static=True))
Scene().add_component(plane, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "cube-sphere" / "cube.obj"))
Scene().add_component(plane, ForwardShaderComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "blin_phong_shadow_shader.wgsl"))
Scene().add_component(plane, MaterialComponent())
Scene().add_component(plane, ShadowAffectionComponent(light_entity=light)) 

cube = Scene().add_entity()
Scene().add_component(cube, InfoComponent("Plane"))
Scene().add_component(cube, TransformComponent(glm.vec3(0, 0, 0), glm.vec3(0, 0, 0), glm.vec3(0.1, 0.1, 0.1), static=True))
Scene().add_component(cube, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "cube-sphere" / "cube.obj"))
Scene().add_component(cube, ForwardShaderComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "blin_phong_shadow_shader.wgsl"))
Scene().add_component(cube, MaterialComponent())
Scene().add_component(cube, ShadowAffectionComponent(light_entity=light))

cube2 = Scene().add_entity()
Scene().add_component(cube2, InfoComponent("Plane2"))
Scene().add_component(cube2, TransformComponent(glm.vec3(2, 0, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1), static=True))
Scene().add_component(cube2, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "cube-sphere" / "cube.obj"))
Scene().add_component(cube2, ForwardShaderComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "blin_phong_shadow_shader.wgsl"))
Scene().add_component(cube2, MaterialComponent())
Scene().add_component(cube2, ShadowAffectionComponent(light_entity=light))

model = Scene().add_entity()
Scene().add_component(model, InfoComponent("model"))
Scene().add_component(model, TransformComponent(glm.vec3(-1, 0, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1), static=True))
Scene().add_component(model, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "Cauterizer" / "Cauterizer.obj"))
Scene().add_component(model, ForwardShaderComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "blin_phong_shadow_shader.wgsl"))
Scene().add_component(model, MaterialComponent())
Scene().add_component(model, ShadowAffectionComponent(light_entity=light))

skyPaths = [
    definitions.TEXTURE_DIR / "Skyboxes" / "Sea" / "back.jpg",
    definitions.TEXTURE_DIR / "Skyboxes" / "Sea" / "front.jpg",
    definitions.TEXTURE_DIR / "Skyboxes" / "Sea" / "bottom.jpg",
    definitions.TEXTURE_DIR / "Skyboxes" / "Sea" / "top.jpg",
    definitions.TEXTURE_DIR / "Skyboxes" / "Sea" / "right.jpg",
    definitions.TEXTURE_DIR / "Skyboxes" / "Sea" / "left.jpg",
]

sky = Scene().add_entity()
Scene().add_component(sky, InfoComponent("Giati mporw"))
Scene().add_component(sky, SkyboxComponent("sky", skyPaths))

Scene().add_system(SkyboxSystem([SkyboxComponent]))
Scene().add_system(TransformSystem([TransformComponent]))
Scene().add_system(CameraSystem([CameraComponent, TransformComponent]))
Scene().add_system(CameraControllerSystem([CameraControllerComponent, CameraComponent, TransformComponent]))
Scene().add_system(MeshSystem([MeshComponent]))
Scene().add_system(DeferedLightShaderSystem([DeferredLightComponent]))
Scene().add_system(ForwardShaderSystem([ForwardShaderComponent]))

GpuController().set_texture_sampler(
    shader_component=Scene().get_component(cube, ForwardShaderComponent), texture_name="albedo_texture", sampler_name="albedo_sampler", texture=TextureLib().get_texture(name="3x3")
)
GpuController().set_texture_sampler(
    shader_component=Scene().get_component(cube2, ForwardShaderComponent), texture_name="albedo_texture", sampler_name="albedo_sampler", texture=TextureLib().get_texture(name="grass")
)
GpuController().set_texture_sampler(
    shader_component=Scene().get_component(model, ForwardShaderComponent), texture_name="albedo_texture", sampler_name="albedo_sampler", texture=TextureLib().get_texture(name="Cauterizer")
)
# GpuController().set_texture_sampler(
#     shader_component=Scene().get_component(building, ForwardShaderComponent), texture_name="albedo_texture", sampler_name="albedo_sampler", texture=TextureLib().get_texture(name="building")
# )
GpuController().set_texture_sampler(
    shader_component=Scene().get_component(plane, ForwardShaderComponent), texture_name="albedo_texture", sampler_name="albedo_sampler", texture=TextureLib().get_texture(name="plane_texture")
)
# GpuController().set_texture_sampler(
#     shader_component=Scene().get_component(sponza, ForwardShaderComponent), texture_name="albedo_texture", sampler_name="albedo_sampler", texture=TextureLib().get_texture(name="white")
# )

def set_base_shader_uniforms(ent:Entity):
    camera_ent:Entity = Scene().get_primary_cam()

    camera_comp: CameraComponent = Scene().get_component(camera_ent, CameraComponent)
    shader_comp: ForwardShaderComponent = Scene().get_component(ent, ForwardShaderComponent)
    plane_trans: TransformComponent = Scene().get_component(ent, TransformComponent)

    view = camera_comp.view
    projection = camera_comp.projection
    model = plane_trans.world_matrix
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
        shader_component=shader_comp, buffer_name="ubuffer", member_name="near_far", uniform_value=near_far, float2=True
    )

def set_base_color_shader_uniforms(ent:Entity):
    camera_ent:Entity = Scene().get_primary_cam()

    camera_comp: CameraComponent = Scene().get_component(camera_ent, CameraComponent)
    shader_comp: ForwardShaderComponent = Scene().get_component(ent, ForwardShaderComponent)
    plane_trans: TransformComponent = Scene().get_component(ent, TransformComponent)

    view = camera_comp.view
    projection = camera_comp.projection
    model = plane_trans.world_matrix
    color = glm.vec3(1.0, 1.0, 0.8)
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
        shader_component=shader_comp, buffer_name="ubuffer", member_name="color", uniform_value=color, float3=True
    )
    GpuController().set_uniform_value(
        shader_component=shader_comp, buffer_name="ubuffer", member_name="near_far", uniform_value=near_far, float2=True
    )

def set_shadow_shader_uniforms(ent:Entity):
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

def set_blin_phong_shader_uniforms(ent:Entity):
    camera_ent:Entity = Scene().get_primary_cam()

    camera_comp: CameraComponent = Scene().get_component(camera_ent, CameraComponent) 
    camera_trans: TransformComponent = Scene().get_component(camera_ent, TransformComponent) 
    shader_comp: ForwardShaderComponent = Scene().get_component(ent, ForwardShaderComponent)
    plane_trans: TransformComponent = Scene().get_component(ent, TransformComponent)  
    light_link: LightAffectionComponent = Scene().get_component(ent, LightAffectionComponent) 

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

def deferred_phong_uniforms(ent: Entity, light: Entity): 
    cam: Entity = Scene().get_primary_cam()  

    shader: DeferredLightComponent = Scene().get_component(ent, DeferredLightComponent)
    cam_comp: CameraComponent = Scene().get_component(cam, CameraComponent) 
    cam_pos: TransformComponent = Scene().get_component(cam, TransformComponent) 
    light_pos: TransformComponent = Scene().get_component(light, TransformComponent)

    screen_size = glm.vec2(GpuController().render_target_size) 
    near_far = glm.vec2(cam_comp.near, cam_comp.far) 

    GpuController().set_uniform_value(
        shader_component=shader, buffer_name="ubuffer", member_name="view_pos", uniform_value=cam_pos.translation, float3=True 
    )
    GpuController().set_uniform_value(
        shader_component=shader, buffer_name="ubuffer", member_name="light_pos", uniform_value=light_pos.translation, float3=True 
    )
    GpuController().set_uniform_value(
        shader_component=shader, buffer_name="ubuffer", member_name="screen_size", uniform_value=screen_size, float2=True 
    )
    GpuController().set_uniform_value(
        shader_component=shader, buffer_name="ubuffer", member_name="near_far", uniform_value=near_far, float2=True 
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

    set_shadow_shader_uniforms(cube)
    set_shadow_shader_uniforms(cube2)
    set_shadow_shader_uniforms(model)
    set_shadow_shader_uniforms(plane)
    set_base_color_shader_uniforms(light)
    deferred_phong_uniforms(deferred_light, light)

    Renderer().render([width, height])
    canvas.display()

canvas.shutdown()