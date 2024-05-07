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
from Elements.pyGLV.GL.wgpu_texture import ImprotTexture 
import Elements.utils.normals as norm

from Elements.pyGLV.GL.wpgu_scene import Scene 
from Elements.pyGLV.GL.wgpu_material import Material
from Elements.pyGLV.GL.wgpu_object import Object, import_mesh
from Elements.pyGLV.GUI.wgpu_renderer import Renderer, RENDER_PASSES, PASS
from Elements.pyGLV.GL.Shader.wgpu_SimpleShader import SimpleShader 
from Elements.pyGLV.GL.Shader.wgpu_BlinPhongShader import BlinPhongShader


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


class talble(Object): 
    def __init__(self, *args, instance_count, **kwards):
        super(*args).__init__(*args, **kwards) 
        self.instance_count = instance_count

    def onInit(self):  
        self.attachedMaterial = Material(tag="simple", shader=BlinPhongShader(device=device))
        texture = ImprotTexture("toolsTable", path=definitions.MODEL_DIR / "cube-sphere" / "CubeTexture.png")
        texture.make(device=device)
        self.attachedMaterial.shader.setTexture(value=texture)  

        for i in range(0, self.instance_count - 1): 
            self.attachedMaterial.shader.Models.append(
                np.array(
                    glm.transpose(
                        glm.translate(
                            glm.mat4x4(1), glm.vec3(randint(-10, 10), randint(-10, 10), randint(-10, 10))
                            # glm.mat4x4(1), glm.vec3(0.0, 0.0, 5.0)
                        )
                    ),
                    dtype=np.float32
                )
            )

        self.load_mesh_from_obj(path=definitions.MODEL_DIR / "cube-sphere" / "sphere.obj") 

    def onUpdate(self): 
        return; 

class ble(Object): 
    def __init__(self, *args, instance_count, **kwards):
        super(*args).__init__(*args, **kwards) 
        self.instance_count = instance_count

    def onInit(self):  
        self.attachedMaterial = Material(tag="simple", shader=SimpleShader(device=device))
        texture = ImprotTexture("toolsTable", path=definitions.MODEL_DIR / "cube-sphere" / "CubeTexture.png")
        texture.make(device=device)
        self.attachedMaterial.shader.setTexture(value=texture)  

        for i in range(0, self.instance_count - 1): 
            self.attachedMaterial.shader.Models.append(
                np.array(
                    glm.transpose(
                        glm.translate(
                            glm.mat4x4(1), glm.vec3(randint(-20, 20), randint(-20, 20), randint(-20, 20))
                            # glm.mat4x4(1), glm.vec3(0.0, 0.0, 5.0)
                        )
                    ),
                    dtype=np.float32
                )
            )

        self.load_mesh_from_obj(path=definitions.MODEL_DIR / "cube-sphere" / "sphere.obj") 

    def onUpdate(self): 
        return; 


scene = Scene()
obj1 = talble(instance_count=256); 
obj2 = ble(instance_count=128)
scene.append_object(obj1) 
scene.append_object(obj2) 

cam = cammera([0, 0, 0], -90, 0)
scene.set_cammera(cam=cam)

renderer = Renderer()
renderer.init(
    scene=scene,
    device=device,
    present_context=present_context,
)  

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