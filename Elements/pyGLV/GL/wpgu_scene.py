import wgpu
import glm
import numpy as np  
from Elements.pyGLV.GL.wgpu_object import Object
from Elements.pyGLV.GL.wgpu_material import Material
from Elements.pyGLV.GUI import fps_cammera, static_cammera

class Scene():
    """
    Singleton Scene that assembles ECSSManager and Viewer classes together for Scene authoring
    in pyglGA. It also brings together the new extensions to pyglGA: Shader, VertexArray and 
    RenderMeshDecorators
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            print('Creating Scene Singleton Object')
            cls._instance = super(Scene, cls).__new__(cls)

            cls._cammera = None
            cls._objects = []
        return cls._instance
    
    
    def __init__(self):
        None;

    def set_cammera(self, cam: fps_cammera.cammera):
        self._cammera = cam

    def append_object(self, obj: Object): 
        self._objects.append(obj) 

    def append_material(self, mat: Material): 
        self._matterials[mat.tag] = mat 

    def init(self, device:wgpu.GPUDevice):
        for obj in self._objects: 
            obj.onInit()  

        for obj in self._objects: 
            obj.init(device=device) 

    def update(self, canvas, event):
        self._cammera.update(canvas=canvas, event=event)

        for obj in self._objects:
            obj.onUpdate()


if __name__ == "__main__":
    # The client singleton code.

    s1 = Scene()
    s2 = Scene()

    if id(s1) == id(s2):
        print("Singleton works, both Scenes contain the same instance.")
    else:
        print("Singleton failed, Scenes contain different instances.") 
    
     