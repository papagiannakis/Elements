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

from Elements.pyECSS.wgpu_components import InfoComponent, TransformComponent, CameraComponent, CameraControllerComponent, MeshComponent
from Elements.pyECSS.wgpu_entity import Entity
from Elements.pyGLV.GL.wpgu_scene import Scene
from Elements.pyGLV.GUI.Input_manager import InputManager 
from Elements.pyGLV.GUI.wgpu_cache_manager import GpuCache

canvas = GLFWWindow(windowHeight=800, windowWidth=1280, wgpu=True, windowTitle="Wgpu Example")
canvas.init()
canvas.init_post()

width = canvas._windowWidth
height = canvas._windowHeight 

# Create a wgpu device
adapter = wgpu.gpu.request_adapter(power_preference="high-performance")
device = adapter.request_device()
GpuCache().set_adapter_device(device=device, adapter=adapter)

# Prepare present context
present_context = canvas.get_context()
render_texture_format = present_context.get_preferred_format(device.adapter)
present_context.configure(device=device, format=render_texture_format) 

InputManager().set_monitor(canvas)

camera = Scene().add_entity() 
Scene().add_component(camera, InfoComponent("main camera"))
Scene().add_component(camera, TransformComponent(glm.vec3(0, 0, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1)))
Scene().add_component(camera, CameraComponent(60, 1.778, 0.01, 500, 1.2, CameraComponent.Type.PERSPECTIVE))
Scene().add_component(camera, CameraControllerComponent())  
Scene().set_primary_cam(camera) 

plane = Scene().add_entity() 
Scene().add_component(plane, InfoComponent("Plane")) 
Scene().add_component(plane, TransformComponent(glm.vec3(0, 0, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1))) 
Scene().add_component(plane, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "cube-sphere" / "cube.obj"))

Scene().add_system(TransformSystem([TransformComponent]))
Scene().add_system(CameraSystem([CameraComponent, TransformComponent]))
Scene().add_system(CameraControllerSystem([CameraControllerComponent, CameraComponent, TransformComponent]))

while canvas._running:
    event = canvas.event_input_process(); 
    Scene().update(event)

    if canvas._need_draw:
        canvas.display()
        canvas.display_post()

canvas.shutdown()