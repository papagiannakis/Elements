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

camera = Scene().add_entity()
Scene().add_component(camera, InfoComponent("main camera"))
Scene().add_component(camera, TransformComponent(glm.vec3(0, 0, 10), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1), static=False))
Scene().add_component(camera, CameraComponent(60, 16/9, 0.01, 500, 10, CameraComponent.Type.PERSPECTIVE))
Scene().add_component(camera, CameraControllerComponent())
Scene().set_primary_cam(camera)

model = Scene().add_entity()
Scene().add_component(model, InfoComponent("model"))
Scene().add_component(model, TransformComponent(glm.vec3(0, 0, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1), static=False))
Scene().add_component(model, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "cube" / "source" / "cube.obj"))
Scene().add_component(model, ForwardShaderComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "base_color_shader.wgsl"))
Scene().add_component(model, MaterialComponent())

model1 = Scene().add_entity()
Scene().add_component(model1, InfoComponent("model"))
Scene().add_component(model1, TransformComponent(glm.vec3(0, 0, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1), static=False))
Scene().add_component(model1, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "cube" / "source" / "cube.obj"))
Scene().add_component(model1, ForwardShaderComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "base_color_shader.wgsl"))
Scene().add_component(model1, MaterialComponent()) 

model2 = Scene().add_entity()
Scene().add_component(model2, InfoComponent("model"))
Scene().add_component(model2, TransformComponent(glm.vec3(0, 0, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1), static=False))
Scene().add_component(model2, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "cube" / "source" / "cube.obj"))
Scene().add_component(model2, ForwardShaderComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "base_color_shader.wgsl"))
Scene().add_component(model2, MaterialComponent())

model3 = Scene().add_entity()
Scene().add_component(model3, InfoComponent("model"))
Scene().add_component(model3, TransformComponent(glm.vec3(0, 0, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1), static=False))
Scene().add_component(model3, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "cube" / "source" / "cube.obj"))
Scene().add_component(model3, ForwardShaderComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "base_color_shader.wgsl"))
Scene().add_component(model3, MaterialComponent())

model4 = Scene().add_entity()
Scene().add_component(model4, InfoComponent("model"))
Scene().add_component(model4, TransformComponent(glm.vec3(0, 0, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1), static=False))
Scene().add_component(model4, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "cube" / "source" / "cube.obj"))
Scene().add_component(model4, ForwardShaderComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "base_color_shader.wgsl"))
Scene().add_component(model4, MaterialComponent())

model5 = Scene().add_entity()
Scene().add_component(model5, InfoComponent("model"))
Scene().add_component(model5, TransformComponent(glm.vec3(0, 0, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1), static=False))
Scene().add_component(model5, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "cube" / "source" / "cube.obj"))
Scene().add_component(model5, ForwardShaderComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "base_color_shader.wgsl"))
Scene().add_component(model5, MaterialComponent())

model6 = Scene().add_entity()
Scene().add_component(model6, InfoComponent("model"))
Scene().add_component(model6, TransformComponent(glm.vec3(0, 0, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1), static=False))
Scene().add_component(model6, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "cube" / "source" / "cube.obj"))
Scene().add_component(model6, ForwardShaderComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "base_color_shader.wgsl"))
Scene().add_component(model6, MaterialComponent())

model7 = Scene().add_entity()
Scene().add_component(model7, InfoComponent("model"))
Scene().add_component(model7, TransformComponent(glm.vec3(0, 0, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1), static=False))
Scene().add_component(model7, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "cube" / "source" / "cube.obj"))
Scene().add_component(model7, ForwardShaderComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "base_color_shader.wgsl"))
Scene().add_component(model7, MaterialComponent())

model8 = Scene().add_entity()
Scene().add_component(model8, InfoComponent("model"))
Scene().add_component(model8, TransformComponent(glm.vec3(0, 0, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1), static=False))
Scene().add_component(model8, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "cube" / "source" / "cube.obj"))
Scene().add_component(model8, ForwardShaderComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "base_color_shader.wgsl"))
Scene().add_component(model8, MaterialComponent())

model9 = Scene().add_entity()
Scene().add_component(model9, InfoComponent("model"))
Scene().add_component(model9, TransformComponent(glm.vec3(0, 0, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1), static=False))
Scene().add_component(model9, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "cube" / "source" / "cube.obj"))
Scene().add_component(model9, ForwardShaderComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "base_color_shader.wgsl"))
Scene().add_component(model9, MaterialComponent())

model10 = Scene().add_entity()
Scene().add_component(model10, InfoComponent("model"))
Scene().add_component(model10, TransformComponent(glm.vec3(0, 0, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1), static=False))
Scene().add_component(model10, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "cube" / "source" / "cube.obj"))
Scene().add_component(model10, ForwardShaderComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "base_color_shader.wgsl"))
Scene().add_component(model10, MaterialComponent())

model11 = Scene().add_entity()
Scene().add_component(model11, InfoComponent("model"))
Scene().add_component(model11, TransformComponent(glm.vec3(0, 0, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1), static=False))
Scene().add_component(model11, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "cube" / "source" / "cube.obj"))
Scene().add_component(model11, ForwardShaderComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "base_color_shader.wgsl"))
Scene().add_component(model11, MaterialComponent()) 

model12 = Scene().add_entity()
Scene().add_component(model12, InfoComponent("model"))
Scene().add_component(model12, TransformComponent(glm.vec3(0, 0, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1), static=False))
Scene().add_component(model12, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "cube" / "source" / "cube.obj"))
Scene().add_component(model12, ForwardShaderComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "base_color_shader.wgsl"))
Scene().add_component(model12, MaterialComponent())

model13 = Scene().add_entity()
Scene().add_component(model13, InfoComponent("model"))
Scene().add_component(model13, TransformComponent(glm.vec3(0, 0, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1), static=False))
Scene().add_component(model13, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "cube" / "source" / "cube.obj"))
Scene().add_component(model13, ForwardShaderComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "base_color_shader.wgsl"))
Scene().add_component(model13, MaterialComponent())

model14 = Scene().add_entity()
Scene().add_component(model14, InfoComponent("model"))
Scene().add_component(model14, TransformComponent(glm.vec3(0, 0, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1), static=False))
Scene().add_component(model14, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "cube" / "source" / "cube.obj"))
Scene().add_component(model14, ForwardShaderComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "base_color_shader.wgsl"))
Scene().add_component(model14, MaterialComponent())

model15 = Scene().add_entity()
Scene().add_component(model15, InfoComponent("model"))
Scene().add_component(model15, TransformComponent(glm.vec3(0, 0, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1), static=False))
Scene().add_component(model15, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "cube" / "source" / "cube.obj"))
Scene().add_component(model15, ForwardShaderComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "base_color_shader.wgsl"))
Scene().add_component(model15, MaterialComponent())

model16 = Scene().add_entity()
Scene().add_component(model16, InfoComponent("model"))
Scene().add_component(model16, TransformComponent(glm.vec3(0, 0, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1), static=False))
Scene().add_component(model16, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "cube" / "source" / "cube.obj"))
Scene().add_component(model16, ForwardShaderComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "base_color_shader.wgsl"))
Scene().add_component(model16, MaterialComponent())

model17 = Scene().add_entity()
Scene().add_component(model17, InfoComponent("model"))
Scene().add_component(model17, TransformComponent(glm.vec3(0, 0, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1), static=False))
Scene().add_component(model17, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "cube" / "source" / "cube.obj"))
Scene().add_component(model17, ForwardShaderComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "base_color_shader.wgsl"))
Scene().add_component(model17, MaterialComponent())

model18 = Scene().add_entity()
Scene().add_component(model18, InfoComponent("model"))
Scene().add_component(model18, TransformComponent(glm.vec3(0, 0, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1), static=False))
Scene().add_component(model18, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "cube" / "source" / "cube.obj"))
Scene().add_component(model18, ForwardShaderComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "base_color_shader.wgsl"))
Scene().add_component(model18, MaterialComponent())

model19 = Scene().add_entity()
Scene().add_component(model19, InfoComponent("model"))
Scene().add_component(model19, TransformComponent(glm.vec3(0, 0, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1), static=False))
Scene().add_component(model19, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "cube" / "source" / "cube.obj"))
Scene().add_component(model19, ForwardShaderComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "base_color_shader.wgsl"))
Scene().add_component(model19, MaterialComponent())

model20 = Scene().add_entity()
Scene().add_component(model20, InfoComponent("model"))
Scene().add_component(model20, TransformComponent(glm.vec3(0, 0, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1), static=False))
Scene().add_component(model20, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "cube" / "source" / "cube.obj"))
Scene().add_component(model20, ForwardShaderComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "base_color_shader.wgsl"))
Scene().add_component(model20, MaterialComponent())

model21 = Scene().add_entity()
Scene().add_component(model21, InfoComponent("model"))
Scene().add_component(model21, TransformComponent(glm.vec3(0, 0, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1), static=False))
Scene().add_component(model21, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "cube" / "source" / "cube.obj"))
Scene().add_component(model21, ForwardShaderComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "base_color_shader.wgsl"))
Scene().add_component(model21, MaterialComponent()) 

model22 = Scene().add_entity()
Scene().add_component(model22, InfoComponent("model"))
Scene().add_component(model22, TransformComponent(glm.vec3(0, 0, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1), static=False))
Scene().add_component(model22, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "cube" / "source" / "cube.obj"))
Scene().add_component(model22, ForwardShaderComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "base_color_shader.wgsl"))
Scene().add_component(model22, MaterialComponent())

model23 = Scene().add_entity()
Scene().add_component(model23, InfoComponent("model"))
Scene().add_component(model23, TransformComponent(glm.vec3(0, 0, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1), static=False))
Scene().add_component(model23, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "cube" / "source" / "cube.obj"))
Scene().add_component(model23, ForwardShaderComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "base_color_shader.wgsl"))
Scene().add_component(model23, MaterialComponent())

model24 = Scene().add_entity()
Scene().add_component(model24, InfoComponent("model"))
Scene().add_component(model24, TransformComponent(glm.vec3(0, 0, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1), static=False))
Scene().add_component(model24, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "cube" / "source" / "cube.obj"))
Scene().add_component(model24, ForwardShaderComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "base_color_shader.wgsl"))
Scene().add_component(model24, MaterialComponent())

model25 = Scene().add_entity()
Scene().add_component(model25, InfoComponent("model"))
Scene().add_component(model25, TransformComponent(glm.vec3(0, 0, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1), static=False))
Scene().add_component(model25, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "cube" / "source" / "cube.obj"))
Scene().add_component(model25, ForwardShaderComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "base_color_shader.wgsl"))
Scene().add_component(model25, MaterialComponent())

model26 = Scene().add_entity()
Scene().add_component(model26, InfoComponent("model"))
Scene().add_component(model26, TransformComponent(glm.vec3(0, 0, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1), static=False))
Scene().add_component(model26, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "cube" / "source" / "cube.obj"))
Scene().add_component(model26, ForwardShaderComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "base_color_shader.wgsl"))
Scene().add_component(model26, MaterialComponent())

model27 = Scene().add_entity()
Scene().add_component(model27, InfoComponent("model"))
Scene().add_component(model27, TransformComponent(glm.vec3(0, 0, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1), static=False))
Scene().add_component(model27, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "cube" / "source" / "cube.obj"))
Scene().add_component(model27, ForwardShaderComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "base_color_shader.wgsl"))
Scene().add_component(model27, MaterialComponent())

model28 = Scene().add_entity()
Scene().add_component(model28, InfoComponent("model"))
Scene().add_component(model28, TransformComponent(glm.vec3(0, 0, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1), static=False))
Scene().add_component(model28, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "cube" / "source" / "cube.obj"))
Scene().add_component(model28, ForwardShaderComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "base_color_shader.wgsl"))
Scene().add_component(model28, MaterialComponent())

model29 = Scene().add_entity()
Scene().add_component(model29, InfoComponent("model"))
Scene().add_component(model29, TransformComponent(glm.vec3(0, 0, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1), static=False))
Scene().add_component(model29, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "cube" / "source" / "cube.obj"))
Scene().add_component(model29, ForwardShaderComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "base_color_shader.wgsl"))
Scene().add_component(model29, MaterialComponent())

model30 = Scene().add_entity()
Scene().add_component(model30, InfoComponent("model"))
Scene().add_component(model30, TransformComponent(glm.vec3(0, 0, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1), static=False))
Scene().add_component(model30, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "cube" / "source" / "cube.obj"))
Scene().add_component(model30, ForwardShaderComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "base_color_shader.wgsl"))
Scene().add_component(model30, MaterialComponent())

model31 = Scene().add_entity()
Scene().add_component(model31, InfoComponent("model"))
Scene().add_component(model31, TransformComponent(glm.vec3(0, 0, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1), static=False))
Scene().add_component(model31, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "cube" / "source" / "cube.obj"))
Scene().add_component(model31, ForwardShaderComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "base_color_shader.wgsl"))
Scene().add_component(model31, MaterialComponent()) 

model32 = Scene().add_entity()
Scene().add_component(model32, InfoComponent("model"))
Scene().add_component(model32, TransformComponent(glm.vec3(0, 0, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1), static=False))
Scene().add_component(model32, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "cube" / "source" / "cube.obj"))
Scene().add_component(model32, ForwardShaderComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "base_color_shader.wgsl"))
Scene().add_component(model32, MaterialComponent())

model33 = Scene().add_entity()
Scene().add_component(model33, InfoComponent("model"))
Scene().add_component(model33, TransformComponent(glm.vec3(0, 0, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1), static=False))
Scene().add_component(model33, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "cube" / "source" / "cube.obj"))
Scene().add_component(model33, ForwardShaderComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "base_color_shader.wgsl"))
Scene().add_component(model33, MaterialComponent())

model34 = Scene().add_entity()
Scene().add_component(model34, InfoComponent("model"))
Scene().add_component(model34, TransformComponent(glm.vec3(0, 0, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1), static=False))
Scene().add_component(model34, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "cube" / "source" / "cube.obj"))
Scene().add_component(model34, ForwardShaderComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "base_color_shader.wgsl"))
Scene().add_component(model34, MaterialComponent())

model35 = Scene().add_entity()
Scene().add_component(model35, InfoComponent("model"))
Scene().add_component(model35, TransformComponent(glm.vec3(0, 0, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1), static=False))
Scene().add_component(model35, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "cube" / "source" / "cube.obj"))
Scene().add_component(model35, ForwardShaderComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "base_color_shader.wgsl"))
Scene().add_component(model35, MaterialComponent())

model36 = Scene().add_entity()
Scene().add_component(model36, InfoComponent("model"))
Scene().add_component(model36, TransformComponent(glm.vec3(0, 0, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1), static=False))
Scene().add_component(model36, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "cube" / "source" / "cube.obj"))
Scene().add_component(model36, ForwardShaderComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "base_color_shader.wgsl"))
Scene().add_component(model36, MaterialComponent())

model37 = Scene().add_entity()
Scene().add_component(model37, InfoComponent("model"))
Scene().add_component(model37, TransformComponent(glm.vec3(0, 0, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1), static=False))
Scene().add_component(model37, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "cube" / "source" / "cube.obj"))
Scene().add_component(model37, ForwardShaderComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "base_color_shader.wgsl"))
Scene().add_component(model37, MaterialComponent())

model38 = Scene().add_entity()
Scene().add_component(model38, InfoComponent("model"))
Scene().add_component(model38, TransformComponent(glm.vec3(0, 0, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1), static=False))
Scene().add_component(model38, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "cube" / "source" / "cube.obj"))
Scene().add_component(model38, ForwardShaderComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "base_color_shader.wgsl"))
Scene().add_component(model38, MaterialComponent())

model39 = Scene().add_entity()
Scene().add_component(model39, InfoComponent("model"))
Scene().add_component(model39, TransformComponent(glm.vec3(0, 0, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1), static=False))
Scene().add_component(model39, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "cube" / "source" / "cube.obj"))
Scene().add_component(model39, ForwardShaderComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "base_color_shader.wgsl"))
Scene().add_component(model39, MaterialComponent())

model40 = Scene().add_entity()
Scene().add_component(model40, InfoComponent("model"))
Scene().add_component(model40, TransformComponent(glm.vec3(0, 0, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1), static=False))
Scene().add_component(model40, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "cube" / "source" / "cube.obj"))
Scene().add_component(model40, ForwardShaderComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "base_color_shader.wgsl"))
Scene().add_component(model40, MaterialComponent())

model41 = Scene().add_entity()
Scene().add_component(model41, InfoComponent("model"))
Scene().add_component(model41, TransformComponent(glm.vec3(0, 0, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1), static=False))
Scene().add_component(model41, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "cube" / "source" / "cube.obj"))
Scene().add_component(model41, ForwardShaderComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "base_color_shader.wgsl"))
Scene().add_component(model41, MaterialComponent()) 

model42 = Scene().add_entity()
Scene().add_component(model42, InfoComponent("model"))
Scene().add_component(model42, TransformComponent(glm.vec3(0, 0, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1), static=False))
Scene().add_component(model42, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "cube" / "source" / "cube.obj"))
Scene().add_component(model42, ForwardShaderComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "base_color_shader.wgsl"))
Scene().add_component(model42, MaterialComponent())

model43 = Scene().add_entity()
Scene().add_component(model43, InfoComponent("model"))
Scene().add_component(model43, TransformComponent(glm.vec3(0, 0, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1), static=False))
Scene().add_component(model43, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "cube" / "source" / "cube.obj"))
Scene().add_component(model43, ForwardShaderComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "base_color_shader.wgsl"))
Scene().add_component(model43, MaterialComponent())

model44 = Scene().add_entity()
Scene().add_component(model44, InfoComponent("model"))
Scene().add_component(model44, TransformComponent(glm.vec3(0, 0, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1), static=False))
Scene().add_component(model44, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "cube" / "source" / "cube.obj"))
Scene().add_component(model44, ForwardShaderComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "base_color_shader.wgsl"))
Scene().add_component(model44, MaterialComponent())

model45 = Scene().add_entity()
Scene().add_component(model45, InfoComponent("model"))
Scene().add_component(model45, TransformComponent(glm.vec3(0, 0, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1), static=False))
Scene().add_component(model45, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "cube" / "source" / "cube.obj"))
Scene().add_component(model45, ForwardShaderComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "base_color_shader.wgsl"))
Scene().add_component(model45, MaterialComponent())

model46 = Scene().add_entity()
Scene().add_component(model46, InfoComponent("model"))
Scene().add_component(model46, TransformComponent(glm.vec3(0, 0, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1), static=False))
Scene().add_component(model46, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "cube" / "source" / "cube.obj"))
Scene().add_component(model46, ForwardShaderComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "base_color_shader.wgsl"))
Scene().add_component(model46, MaterialComponent())

model47 = Scene().add_entity()
Scene().add_component(model47, InfoComponent("model"))
Scene().add_component(model47, TransformComponent(glm.vec3(0, 0, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1), static=False))
Scene().add_component(model47, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "cube" / "source" / "cube.obj"))
Scene().add_component(model47, ForwardShaderComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "base_color_shader.wgsl"))
Scene().add_component(model47, MaterialComponent())

model48 = Scene().add_entity()
Scene().add_component(model48, InfoComponent("model"))
Scene().add_component(model48, TransformComponent(glm.vec3(0, 0, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1), static=False))
Scene().add_component(model48, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "cube" / "source" / "cube.obj"))
Scene().add_component(model48, ForwardShaderComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "base_color_shader.wgsl"))
Scene().add_component(model48, MaterialComponent())

model49 = Scene().add_entity()
Scene().add_component(model49, InfoComponent("model"))
Scene().add_component(model49, TransformComponent(glm.vec3(0, 0, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1), static=False))
Scene().add_component(model49, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "cube" / "source" / "cube.obj"))
Scene().add_component(model49, ForwardShaderComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "base_color_shader.wgsl"))
Scene().add_component(model49, MaterialComponent())

model50 = Scene().add_entity()
Scene().add_component(model50, InfoComponent("model"))
Scene().add_component(model50, TransformComponent(glm.vec3(0, 0, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1), static=False))
Scene().add_component(model50, MeshComponent(mesh_type=MeshComponent.Type.IMPORT, import_path=definitions.MODEL_DIR / "cube" / "source" / "cube.obj"))
Scene().add_component(model50, ForwardShaderComponent(shader_path=definitions.SHADER_DIR / "WGPU" / "base_color_shader.wgsl"))
Scene().add_component(model50, MaterialComponent())

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

    transform: TransformComponent = Scene().get_component(ent, TransformComponent)   
    shader: ForwardShaderComponent = Scene().get_component(ent, ForwardShaderComponent)
    cam: CameraComponent = Scene().get_component(cam, CameraComponent)
    
    transform.translation = glm.vec3(randint(10, 200), randint(10, 200), randint(10, 200))

    near_far = glm.vec2(cam.near, cam.far) 
    color = glm.vec3(0.0, 1.0, 0.0)
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
)
while canvas._running:
    ts = TimeStepManager().update()
    event = canvas.event_input_process();
    width = canvas._windowWidth
    height = canvas._windowHeight
    Scene().update(event, ts)

    update_uniforms(model)
    update_uniforms(model1)
    update_uniforms(model2)
    update_uniforms(model3)
    update_uniforms(model4)
    update_uniforms(model5)
    update_uniforms(model6)
    update_uniforms(model7)
    update_uniforms(model8)
    update_uniforms(model9)
    update_uniforms(model10)
    update_uniforms(model11)
    update_uniforms(model12)
    update_uniforms(model13)
    update_uniforms(model14)
    update_uniforms(model15)
    update_uniforms(model16)
    update_uniforms(model17)
    update_uniforms(model18)
    update_uniforms(model19)
    update_uniforms(model20)
    update_uniforms(model21)
    update_uniforms(model22)
    update_uniforms(model23)
    update_uniforms(model24)
    update_uniforms(model25)
    update_uniforms(model26)
    update_uniforms(model27)
    update_uniforms(model28)
    update_uniforms(model29)
    update_uniforms(model30)
    update_uniforms(model31)
    update_uniforms(model32)
    update_uniforms(model33)
    update_uniforms(model34)
    update_uniforms(model35)
    update_uniforms(model36)
    update_uniforms(model37)
    update_uniforms(model38)
    update_uniforms(model39)
    update_uniforms(model40)
    update_uniforms(model41)
    update_uniforms(model42)
    update_uniforms(model43)
    update_uniforms(model44)
    update_uniforms(model45)
    update_uniforms(model46)
    update_uniforms(model47)
    update_uniforms(model48)
    update_uniforms(model49)
    update_uniforms(model50)

    Renderer().render([1920, 1080])
    canvas.display()

canvas.shutdown()