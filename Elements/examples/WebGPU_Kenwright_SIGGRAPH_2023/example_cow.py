import time 

import glm  
from random import random, randint

import wgpu    
import numpy as np   
import glfw
import Elements.definitions as definitions

from Elements.pyGLV.GUI.Viewer import GLFWWindow, RenderDecorator
from Elements.pyGLV.GL.Shader import ShaderLoader  
from Elements.pyECSS.Event import EventManager
from Elements.pyGLV.GUI.windowEvents import EventTypes 
from Elements.pyGLV.GUI.Viewer import button_map
from Elements.pyGLV.GUI.fps_cammera import cammera
from Elements.pyGLV.GL.wgpu_meshes import  obj_loader
import Elements.pyECSS.math_utilities as util 
from Elements.definitions import TEXTURE_DIR, MODEL_DIR
from Elements.pyGLV.GL.wgpu_material import wgpu_material 
import Elements.utils.normals as norm
from Elements.utils.obj_to_mesh import obj_to_mesh 

from Elements.pyGLV.GL.wpgu_scene import Scene, Object
from Elements.pyGLV.GUI.wgpu_renderer import SimpleRenderer


canvas = GLFWWindow(windowHeight=1050, windowWidth=1600, wgpu=True, windowTitle="Wgpu Example")
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

class newObj(Object): 
    def __init__(self, instasnce_count):
        super().__init__(instasnce_count) 
        self.load_mesh_from_obj(definitions.MODEL_DIR / "ToolsTable" / "ToolsTable.obj")
        self.load_materila(definitions.MODEL_DIR / "ToolsTable" / "Cloth-TOOLtable_LOW_Material__126_Albedo.png")

    def onInit(self): 
        for i in range(1, self.instance_count):
            self.transforms.append(glm.transpose(glm.translate(glm.mat4x4(1), glm.vec3(randint(0, 20), randint(0, 20), randint(0, 20)))))

    def onUpdate(self): 
        return;


class oldObj(Object): 
    def __init__(self, instasnce_count):
        super().__init__(instasnce_count) 
        self.load_mesh_from_obj(definitions.MODEL_DIR / "Tray" / "Tray.obj")
        self.load_materila(definitions.MODEL_DIR / "Tray" / "TrayTexture.png")
    
    def onInit(self): 
        for i in range(1, self.instance_count):
            self.transforms.append(glm.transpose(glm.translate(glm.mat4x4(1), glm.vec3(randint(0, 20), randint(0, 20), randint(0, 20)))))

    def onUpdate(self): 
        return;

scene = Scene()
obj1 = newObj(500); 
obj2 = oldObj(500);
scene.append_object(obj1)   
scene.append_object(obj2)

cam = cammera([-5, 0, 2.5], 0, 0)
scene.set_cammera(cam=cam)

renderer = SimpleRenderer(
    scene=scene,
    device=device,
    canvas=canvas,
    present_context=present_context,
    render_texture_format=render_texture_format
)

renderer.init()

def draw_frame(): 
    renderer.render()
    pass; 

canvas.request_draw(draw_frame)

while canvas._running:
    event = canvas.event_input_process();   
    scene.update(canvas, event)
    if canvas._need_draw:
        canvas.display()
        canvas.display_post() 
        
canvas.shutdown()