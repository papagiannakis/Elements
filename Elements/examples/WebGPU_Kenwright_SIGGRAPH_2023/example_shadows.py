from random import random, randint
import wgpu
import glm
import numpy as np
import Elements.definitions as definitions

from Elements.pyGLV.GUI.Viewer import GLFWWindow
from Elements.pyGLV.GUI.Viewer import button_map
from Elements.pyGLV.GUI.fps_cammera import cammera
import Elements.pyECSS.math_utilities as util
from Elements.definitions import TEXTURE_DIR, MODEL_DIR
from Elements.pyGLV.GL.wgpu_texture import ImprotTexture, CubeMapTexture
import Elements.utils.normals as norm

from Elements.pyGLV.GL.wpgu_scene import Scene
from Elements.pyGLV.GL.wgpu_material import Material
from Elements.pyGLV.GL.wgpu_object import Object, import_mesh
from Elements.pyGLV.GUI.wgpu_renderer import Renderer, RENDER_PASSES, PASS
from Elements.pyGLV.GL.Shader.wgpu_SimpleShader import SimpleShader
from Elements.pyGLV.GL.Shader.wgpu_ShadowShader import ShadowShader
from Elements.pyGLV.GL.Shader.wgpu_CubeMapShader import CubeMapShader 


canvas = GLFWWindow(windowHeight=800, windowWidth=1280, wgpu=True, windowTitle="Wgpu Example")
canvas.init()
canvas.init_post()

width = canvas._windowWidth
height = canvas._windowHeight

# Create a wgpu device
adapter = wgpu.gpu.request_adapter(power_preference="high-performance")
device = adapter.request_device()

# Prepare present context
present_context = canvas.get_context()
render_texture_format = present_context.get_preferred_format(device.adapter)
present_context.configure(device=device, format=render_texture_format) 

class simple(Object):
    def __init__(self, *args, instance_count, **kwards):
        super(*args).__init__(*args, **kwards)
        self.instance_count = instance_count  

    def onInit(self): 
        self.attachedMaterial = Material(tag="name", shader=SimpleShader(device=device)) 

        model = glm.mat4x4(1)
        model = glm.transpose(glm.translate(model, glm.vec3(10, 10, 10))) 
        model = np.array(model, dtype=np.float32)
        self.attachedMaterial.shader.Models.append(model) 

        self.load_mesh_from_obj(path=definitions.MODEL_DIR / "cube-sphere" / "cube.obj")
        texture = ImprotTexture("cubeTexture", path=definitions.MODEL_DIR / "cube-sphere" / "CubeTexture.png")
        texture.make(device=device)
        self.attachedMaterial.shader.setTexture(value=texture)

    def onUpdate(self):
        return


class cubemap(Object): 
    def __init__(self, *args, instance_count, **kwards):
        super(*args).__init__(*args, **kwards)
        self.instance_count = instance_count  

    def onInit(self): 
        self.attachedMaterial = Material(tag="cubemap", shader=CubeMapShader(device=device)) 
        paths = [] 
        paths.append(TEXTURE_DIR / "Skyboxes" / "Cloudy" / "back.jpg")
        paths.append(TEXTURE_DIR / "Skyboxes" / "Cloudy" / "front.jpg")
        paths.append(TEXTURE_DIR / "Skyboxes" / "Cloudy" / "left.jpg")
        paths.append(TEXTURE_DIR / "Skyboxes" / "Cloudy" / "right.jpg") 
        paths.append(TEXTURE_DIR / "Skyboxes" / "Cloudy" / "top.jpg") 
        paths.append(TEXTURE_DIR / "Skyboxes" / "Cloudy" / "bottom.jpg")  

        texture = CubeMapTexture("cubemap", paths)  
        texture.make(device=device) 
        self.attachedMaterial.shader.setTexture(value=texture) 

        self.vertices = np.array([
            [ 1.0,  1.0],
            [ 1.0, -1.0],
            [-1.0, -1.0],
            [ 1.0,  1.0],
            [-1.0, -1.0],
            [-1.0,  1.0]
        ], dtype=np.float32) 

        self.normals = np.array([
            [0.0, 0.0, 1.0, 1.0],  # Front face
            [0.0, 0.0, -1.0, 1.0],  # Back face
            [1.0, 0.0, 0.0, 1.0],  # Right face
            [-1.0, 0.0, 0.0, 1.0],  # Left face
            [0.0, 1.0, 0.0, 1.0],  # Top face
            [0.0, -1.0, 0.0, 1.0]  # Bottom face
        ], dtype=np.float32)  

        self.indices = np.array([
            0, 1, 2, 3, 4, 5
        ], dtype=np.uint32)

        model = glm.mat4x4(1)
        model = glm.transpose(glm.translate(model, glm.vec3(0, 0, 0))) 
        model = np.array(model, dtype=np.float32)
        self.attachedMaterial.shader.Models.append(model)

    def onUpdate(self): 
        return;


class plane(Object):
    def __init__(self, *args, instance_count, **kwards):
        super(*args).__init__(*args, **kwards)
        self.instance_count = instance_count

    def onInit(self):
        self.attachedMaterial = Material(tag="simple^2", shader=ShadowShader(device=device))
        model = glm.mat4x4(1)

        model = glm.transpose(glm.translate(model, glm.vec3(0, 0, 0)))
        model = glm.scale(model, glm.vec3(50, 50, 0.1))
        model = glm.rotate(model, np.deg2rad(-90), glm.vec3(1, 0, 0))

        model_ti = glm.transpose(glm.inverse(model))

        model = np.array(model, dtype=np.float32)
        model_ti = np.array(model_ti, dtype=np.float32)

        self.attachedMaterial.shader.Models.append(model)
        self.attachedMaterial.shader.Models_ti.append(model_ti)
        self.load_mesh_from_obj(path=definitions.MODEL_DIR / "cube-sphere" / "cube.obj")
        texture = ImprotTexture("cubeTexture", path=definitions.MODEL_DIR / "cube-sphere" / "CubeTexture.png")
        texture.make(device=device)
        self.attachedMaterial.shader.setTexture(value=texture)  

    def onUpdate(self):
        return;


class talble(Object):
    def __init__(self, *args, instance_count, **kwards):
        super(*args).__init__(*args, **kwards)
        self.instance_count = instance_count

    def onInit(self):
        self.attachedMaterial = Material(tag="simple", shader=ShadowShader(device=device))

        model = glm.mat4x4(1)
        model = glm.transpose(glm.translate(model, glm.vec3(0.0, 0.5, 0.0)))
        model = glm.scale(model, glm.vec3(10, 10, 10))

        model_ti = glm.transpose(glm.inverse(model))

        model = np.array(model, dtype=np.float32)
        model_ti = np.array(model_ti, dtype=np.float32)

        self.attachedMaterial.shader.Models.append(model)
        self.attachedMaterial.shader.Models_ti.append(model_ti)

        self.load_mesh_from_obj(path=definitions.MODEL_DIR / "ImplantsTable" / "ImplantsTable.obj")
        texture = ImprotTexture("toolsTable", path=definitions.MODEL_DIR / "ImplantsTable" / "table_with_implants_01_Material__3_Albedo.png")
        texture.make(device=device)
        self.attachedMaterial.shader.setTexture(value=texture)  

    def onUpdate(self):
        return;


class stronghold(Object):
    def __init__(self, *args, instance_count, **kwards):
        super(*args).__init__(*args, **kwards)
        self.instance_count = instance_count

    def onInit(self):
        self.attachedMaterial = Material(tag="simple", shader=ShadowShader(device=device))

        model = glm.mat4x4(1)
        model = glm.transpose(glm.translate(model, glm.vec3(0.0, 0.0, 0.0)))
        model = glm.scale(model, glm.vec3(0.1, 0.1, 0.1))

        model_ti = glm.transpose(glm.inverse(model))

        model = np.array(model, dtype=np.float32)
        model_ti = np.array(model_ti, dtype=np.float32)

        self.attachedMaterial.shader.Models.append(model)
        self.attachedMaterial.shader.Models_ti.append(model_ti)

        self.load_mesh_from_obj(path=definitions.MODEL_DIR / "stronghold" / "source" / "StrongHold.obj")
        texture = ImprotTexture("toolsTable", path=definitions.MODEL_DIR / "stronghold" / "textures" / "texture_building_bumpmap.jpg")
        texture.make(device=device)
        self.attachedMaterial.shader.setTexture(value=texture)  

    def onUpdate(self):
        return;


scene = Scene() 
cube = cubemap(instance_count=1)
obj = plane(instance_count=1)
obj1 = talble(instance_count=1); 
s = simple(instance_count=1)
# obj2 = mediumRare(instance_count=256) 
scene.append_object(cube)
scene.append_object(s)
scene.append_object(obj)
scene.append_object(obj1)   
# obj = stronghold(instance_count=1) 
# scene.append_object(obj)
# scene.append_object(obj2) 

scene.set_light(glm.vec4(-10, 15, -10, 1.0))

cam = cammera([25, 25, 20], -90, 0)
scene.set_cammera(cam=cam)

renderer = Renderer()

renderer.init(
    scene=scene,
    device=device,
    present_context=present_context
)

RENDER_PASSES.append(PASS.SHADOW)
RENDER_PASSES.append(PASS.MODEL)

def draw_frame():
    renderer.render()
    canvas.request_draw()

canvas.request_draw(draw_frame)

while canvas._running:
    event = canvas.event_input_process();
    scene.update(canvas, event)

    canvas.display()
    canvas.display_post()

canvas.shutdown()