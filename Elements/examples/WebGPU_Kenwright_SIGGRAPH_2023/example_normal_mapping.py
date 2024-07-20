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
from Elements.pyECSS.systems.wgpu_defered_shader_system import DeferedShaderSystem

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


camera = Scene().add_entity()
Scene().add_component(camera, InfoComponent("main camera"))
Scene().add_component(camera, TransformComponent(glm.vec3(0, 0, 10), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1), static=False))
Scene().add_component(camera, CameraComponent(60, 16/9, 0.01, 500, 10, CameraComponent.Type.PERSPECTIVE))
Scene().add_component(camera, CameraControllerComponent())
Scene().set_primary_cam(camera)

light = Scene().add_entity()
Scene().add_component(light, InfoComponent("light"))
Scene().add_component(light, TransformComponent(glm.vec3(0, -10, 10), glm.vec3(30, 0, 0), glm.vec3(1, 1, 1), static=False))
Scene().add_component(light, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "cube-sphere" / "cube.obj"))
Scene().add_component(light, ForwardShaderComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "base_color_shader.wgsl"))
Scene().add_component(light, MaterialComponent())
Scene().add_component(light, LightComponent(intensity=1.0)) 
Scene().add_component(light, CameraComponent(60, 16/9, 0.01, 500, 35, CameraComponent.Type.PERSPECTIVE)) 

model = Scene().add_entity()
Scene().add_component(model, InfoComponent("model"))
Scene().add_component(model, TransformComponent(glm.vec3(1, 0, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1), static=True))
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
Scene().add_system(DeferedShaderSystem([DeferedShaderComponent]))
Scene().add_system(ForwardShaderSystem([ForwardShaderComponent]))


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



    Renderer().render([width, height])
    canvas.display()

canvas.shutdown()