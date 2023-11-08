
from Elements.pyECSS.Component import Component, BasicTransform, RenderMesh
from Elements.pyECSS.System import System, TransformSystem, CameraSystem
from Elements.pyECSS.Entity import Entity
from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray
from Elements.pyGLV.GL.Scene import Scene
import Elements.pyECSS.math_utilities as util
import numpy as np
from Elements.pyGLV.GUI.Viewer import ImGUIecssDecorator
from Elements.pyGLV.GL.SimpleCamera import SimpleCamera


class CUBE():
    vertices = np.array([
        [-0.5, -0.5, 0.5, 1.0],
        [-0.5, 0.5, 0.5, 1.0],
        [0.5, 0.5, 0.5, 1.0],
        [0.5, -0.5, 0.5, 1.0], 
        [-0.5, -0.5, -0.5, 1.0], 
        [-0.5, 0.5, -0.5, 1.0], 
        [0.5, 0.5, -0.5, 1.0], 
        [0.5, -0.5, -0.5, 1.0]
        ],dtype=np.float32) 
    colors = np.array([
        [0.0, 0.0, 0.0, 1.0],
        [1.0, 0.0, 0.0, 1.0],
        [1.0, 1.0, 0.0, 1.0],
        [0.0, 1.0, 0.0, 1.0],
        [0.0, 0.0, 1.0, 1.0],
        [1.0, 0.0, 1.0, 1.0],
        [1.0, 1.0, 1.0, 1.0],
        [0.0, 1.0, 1.0, 1.0]
        ], dtype=np.float32)
    indices = np.array((1,0,3, 1,3,2, 
                  2,3,7, 2,7,6,
                  3,0,4, 3,4,7,
                  6,5,1, 6,1,2,
                  4,5,6, 4,6,7,
                  5,4,0, 5,0,1), np.uint32) #rhombus out of two triangles

class Rotate(Component):
    
    def __init__(self, name=None, type=None, id=None, angles = None, speed = None):
        
        super().__init__(name, type, id)
        if angles is None:
          self._eulerAngles = np.array([0,0.1,0])
        else:
          if isinstance(angles, list):
            self._eulerAngles = np.array(angles)
          else:
            self._eulerAngles = angles

        if speed is None:
          self._speed = 1
        else:
          self._speed = speed

    def show(self):
        if (isinstance(self.parent,Entity)) == False:
            print('This is a rotation component. Euler Angles: ' + str(self._eulerAngles) + ', Speed: ' + str(self._speed) )
        else:
            print('This is a rotation component, attached to entity'  + self.parent.name + ': Euler Angles: ' + str(self._eulerAngles) + ', Speed: ' + str(self._speed)  )
        # print("----------------------------")


    #We have to override update() but there is no implementation in this example
    def update(self, **kwargs):
        pass
    
    #The accept method is important to call the applyRotation2BasicTransform()
    def accept(self, system: System):
        system.applyRotation2BasicTransform(self)

    #We have to override init() but there is no implementation in this example
    def init(self):
        pass

class RotateSystem(System):
    
    def __init__(self, name=None, type=None, id=None):
        super().__init__(name, type, id)
        
    def applyRotation2BasicTransform(self, component: Rotate):
        
        #check if the visitor visits a node that it should not
        if (isinstance(component, Rotate)) == False:
            return #in Python due to duck typing we need to check this!
        print(self.getClassName(), ": applyRotation2BasicTransform is called on component: ", component.name)
        
        rot = util.eulerAnglesToRotationMatrix(component._speed * component._eulerAngles)
        transformComponent = component.parent.getChildByType("BasicTransform")
        transformComponent.trs = rot @ transformComponent.trs
        print("rot", rot)
        print("transformComponent:", transformComponent.name)
        print('Visited:', component.parent.name, ': New trs is: \n', transformComponent.trs)





import numpy as np

import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.System import  TransformSystem, CameraSystem
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform,  RenderMesh
from Elements.pyECSS.Event import Event

from Elements.pyGLV.GUI.Viewer import   ImGUIecssDecorator
from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GL.SimpleCamera import SimpleCamera
from Elements.utils.normals import Convert
from OpenGL.GL import GL_LINES

from Elements.utils.Shortcuts import displayGUI_text
example_description = \
"This is an example of the rotation system. The cube is \n\
rotating based on the information of a \n\
component that holds the rotation information."  


class GameObjectEntity(Entity):
    def __init__(self, name=None, type=None, id=None) -> None:
        super().__init__(name, type, id);

        # Gameobject basic properties
        self._color          = [1, 0.5, 0.2, 1.0]; # this will be used as a uniform var
        # Create basic components of a primitive object
        self.trans          = BasicTransform(name="trans", trs=util.identity());
        self.mesh           = RenderMesh(name="mesh");
        # self.shaderDec      = ShaderGLDecorator(Shader(vertex_source=Shader.VERT_PHONG_MVP, fragment_source=Shader.FRAG_PHONG));
        self.shaderDec      = ShaderGLDecorator(Shader(vertex_source= Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG));
        self.vArray         = VertexArray();
        # Add components to entity
        scene = Scene();
        scene.world.createEntity(self);
        scene.world.addComponent(self, self.trans);
        scene.world.addComponent(self, self.mesh);
        scene.world.addComponent(self, self.shaderDec);
        scene.world.addComponent(self, self.vArray);

    @property
    def color(self):
        return self._color;
    @color.setter
    def color(self, colorArray):
        self._color = colorArray;

    def drawSelfGui(self, imgui):
        changed, value = imgui.color_edit3("Color", self.color[0], self.color[1], self.color[2]);
        self.color = [value[0], value[1], value[2], 1.0];

    def SetVertexAttributes(self, vertex, color, index, normals = None):
        self.mesh.vertex_attributes.append(vertex);
        self.mesh.vertex_attributes.append(color);
        if normals is not None:
            self.mesh.vertex_attributes.append(normals);
        self.mesh.vertex_index.append(index);



def CubeSpawn(cubename = "Cube"): 
    cube = GameObjectEntity(cubename);
    vertices = [
        [-0.5, -0.5, 0.5, 1.0],
        [-0.5, 0.5, 0.5, 1.0],
        [0.5, 0.5, 0.5, 1.0],
        [0.5, -0.5, 0.5, 1.0], 
        [-0.5, -0.5, -0.5, 1.0], 
        [-0.5, 0.5, -0.5, 1.0], 
        [0.5, 0.5, -0.5, 1.0], 
        [0.5, -0.5, -0.5, 1.0]
    ];
    colors = [
        [1.0, 0.0, 0.0, 1.0],
        [1.0, 0.5, 0.0, 1.0],
        [1.0, 0.0, 0.5, 1.0],
        [0.5, 1.0, 0.0, 1.0],
        [0.0, 1.0, 1.5, 1.0],
        [0.0, 1.0, 1.0, 1.0],
        [0.0, 1.0, 0.0, 1.0],
        [0.0, 1.0, 0.0, 1.0]                    
    ];
    # OR
    # colors =  [cube.color] * len(vertices) 
    
    
    #index arrays for above vertex Arrays
    indices = np.array(
        (
            1,0,3, 1,3,2, 
            2,3,7, 2,7,6,
            3,0,4, 3,4,7,
            6,5,1, 6,1,2,
            4,5,6, 4,6,7,
            5,4,0, 5,0,1
        ),
        dtype=np.uint32
    ) #rhombus out of two triangles

    vertices, colors, indices, normals = Convert(vertices, colors, indices, produceNormals=True);
    cube.SetVertexAttributes(vertices, colors, indices, normals);
    
    return cube;




def main(imguiFlag = False):
    ##########################################################
    # Instantiate a simple complete ECSS with Entities, 
    # Components, Camera, Shader, VertexArray and RenderMesh
    #########################################################
    
    winWidth = 1024
    winHeight = 1024
    
    scene = Scene()    

    # Initialize Systems used for this script
    transUpdate = scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
    camUpdate = scene.world.createSystem(CameraSystem("camUpdate", "CameraUpdate", "200"))
    renderUpdate = scene.world.createSystem(RenderGLShaderSystem())
    initUpdate = scene.world.createSystem(InitGLShaderSystem())
    
    # Scenegraph with Entities, Components
    rootEntity = scene.world.createEntity(Entity(name="Root"))

    # Spawn Camera
    mainCamera = SimpleCamera("Simple Camera")
    # Camera Settings
    mainCamera.trans2.trs = util.translate(0, 0, 8) # VIEW
    mainCamera.trans1.trs = util.rotate((1, 0, 0), -45); 

    #-----------------------------------------
    # Spawn Two Homes on top of each other
    home1 = scene.world.createEntity(Entity("Home"))
    scene.world.addEntityChild(rootEntity, home1)

    trans = BasicTransform(name="trans", trs=util.identity());    
    scene.world.addComponent(home1, trans)
    
    cube_bot: GameObjectEntity = CubeSpawn("BOT CUBE")
    scene.world.addEntityChild(home1, cube_bot)
    rotComponent = scene.world.addComponent(cube_bot, Rotate(angles = [0,0.5,0.5], speed = 0.05))
    
    cube_top: GameObjectEntity = CubeSpawn()
    scene.world.addEntityChild(home1, cube_top)
    
    home1.getChild(0).trs = util.translate(0, 0, 0)
    cube_top.trans.trs = util.translate(0, 1, 0)
    cube_top.name = "TOP CUBE"
    
    
   
    # MAIN RENDERING LOOP
    running = True
    scene.init(imgui=True, windowWidth = winWidth, windowHeight = winHeight, windowTitle = "Elements: A CameraSystem Example", customImGUIdecorator = ImGUIecssDecorator)


    rotSystem = scene.world.createSystem(RotateSystem())
    scene.world.traverse_visit(initUpdate, rootEntity)
    

    
    while running:

        scene.world.traverse_visit(transUpdate, scene.world.root) 
        scene.world.traverse_visit_pre_camera(camUpdate, mainCamera.camera)
        scene.world.traverse_visit(camUpdate, scene.world.root)
        scene.world.traverse_visit(rotSystem, scene.world.root)
        # print(home1.getChild(1).trans.trs)
        # home1.getChild(1).trans.trs = home1.getChild(1).trans.trs @ util.scale (1.1)
        home1.getChild(1).shaderDec.setUniformVariable(key='modelViewProj', value=home1.getChild(1).trans.l2cam, mat4=True);
        home1.getChild(2).shaderDec.setUniformVariable(key='modelViewProj', value=home1.getChild(2).trans.l2cam, mat4=True);
        

        
        # call SDLWindow/ImGUI display() and ImGUI event input process
        running = scene.render()
        displayGUI_text(example_description)
        # call the GL State render System
        scene.world.traverse_visit(renderUpdate, scene.world.root)
        # ImGUI post-display calls and SDLWindow swap 
        scene.render_post()
        
    scene.shutdown()


if __name__ == "__main__":    
    main(imguiFlag = True)