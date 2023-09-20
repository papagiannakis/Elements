"""
Example using bounding boxes components and a gravity collision system
    
@author Nikos Iliakis csd4375
"""
from __future__         import annotations
import numpy as np

import OpenGL.GL as gl;
import Elements.pyECSS.math_utilities as util
import random as rand
from Elements.pyECSS.System import  TransformSystem, CameraSystem
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform,  RenderMesh
from Elements.pyECSS.Event import Event

from Elements.pyGLV.GUI.Viewer import  RenderGLStateSystem,  ImGUIecssDecorator
from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GL.SimpleCamera import SimpleCamera
from Elements.utils.normals import Convert

from AABoundingBox import AABoundingBox
from GravityCollisonSystem import GravityCollisionSystem
from floor import generate_floor_with_bb
from floor import create_max_points_list
from floor import create_min_points_list


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
    gravitycollisionSystem = scene.world.createSystem(GravityCollisionSystem())
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
    home1 = scene.world.createEntity(Entity("Cubes"))
    scene.world.addEntityChild(rootEntity, home1)

    trans = BasicTransform(name="trans", trs=util.identity());    
    scene.world.addComponent(home1, trans)
    
    # Generating floor with bounding box so that the objects can collide
    floor_trans, floor_shader, floor_bb = generate_floor_with_bb(rootEntity)
    
    # Spawning 10 cubes with random transformations with bounding boxes
    for i in range(0, 10):
        cube: GameObjectEntity = CubeSpawn()
        scene.world.addEntityChild(home1, cube)
        cube.trans.trs = util.translate(rand.uniform(-4, 4), 0, rand.uniform(-4, 4))
        #cube.trans.trs = cube.trans.trs @ util.rotate(axis=[0, 0, rand.randint(0, 1),], angle = rand.uniform(0,180))
        cube.trans.trs = cube.trans.trs @ util.scale(rand.uniform(0.2, 1),rand.uniform(0.2, 1),rand.uniform(0.2, 1)) 
        scene.world.addComponent(cube, AABoundingBox(name="AABoundingBox",
                                        min_points=create_min_points_list(cube.mesh.vertex_attributes[0]), 
                                        max_points=create_max_points_list(cube.mesh.vertex_attributes[0]),
                                        floor= floor_bb))
        
    home1.getChild(0).trs = util.translate(0, 2, 0)

    
    # MAIN RENDERING LOOP
    running = True
    scene.init(imgui=True, windowWidth = winWidth, windowHeight = winHeight, windowTitle = "Elements: A CameraSystem Example", customImGUIdecorator = ImGUIecssDecorator)

    #imGUIecss = scene.gContext


    # ---------------------------------------------------------
    #   Run pre render GLInit traversal for once!
    #   pre-pass scenegraph to initialise all GL context dependent geometry, shader classes
    #   needs an active GL context
    # ---------------------------------------------------------
    
    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
    gl.glDisable(gl.GL_CULL_FACE);

    # gl.glDepthMask(gl.GL_FALSE);  
    gl.glEnable(gl.GL_DEPTH_TEST);
    gl.glDepthFunc(gl.GL_LESS);
    scene.world.traverse_visit(initUpdate, rootEntity)
    

    ############################################
    # Instantiate all Event-related key objects
    ############################################
    
    # instantiate new EventManager
    # need to pass that instance to all event publishers e.g. ImGUIDecorator
    eManager = scene.world.eventManager
    gWindow = scene.renderWindow
    gGUI = scene.gContext
    
    #simple Event actuator System
    renderGLEventActuator = RenderGLStateSystem()
    
    #setup Events and add them to the EventManager
    updateTRS = Event(name="OnUpdateTRS", id=100, value=None)
    updateBackground = Event(name="OnUpdateBackground", id=200, value=None)
    eManager._events[updateTRS.name] = updateTRS
    eManager._events[updateBackground.name] = updateBackground


    eManager._subscribers[updateTRS.name] = gGUI
    eManager._subscribers[updateBackground.name] = gGUI
   
    eManager._subscribers['OnUpdateWireframe'] = gWindow
    eManager._actuators['OnUpdateWireframe'] = renderGLEventActuator
    eManager._subscribers['OnUpdateCamera'] = gWindow
    eManager._actuators['OnUpdateCamera'] = renderGLEventActuator
    

    # Add RenderWindow to the EventManager publishers
    eManager._publishers[updateBackground.name] = gGUI
    
    while running:
        # Here we traverse with the gravity Collision System
        scene.world.traverse_visit(gravitycollisionSystem, scene.world.root)
        
        scene.world.traverse_visit(transUpdate, scene.world.root) 
        scene.world.traverse_visit_pre_camera(camUpdate, mainCamera.camera)
        scene.world.traverse_visit(camUpdate, scene.world.root)
        for i in range(1, 10):
            home1.getChild(i).shaderDec.setUniformVariable(key='modelViewProj', value=home1.getChild(i).trans.l2cam, mat4=True);
            home1.getChild(i).shaderDec.setUniformVariable(key='my_color;', value=[0.4, 0.4, 0.4, 1.0], float4=True);
        
        floor_shader.setUniformVariable(key='modelViewProj', value=floor_trans.l2cam, mat4=True);  
        
        # call SDLWindow/ImGUI display() and ImGUI event input process
        running = scene.render()
        # call the GL State render System
        scene.world.traverse_visit(renderUpdate, scene.world.root)
        
        # ImGUI post-display calls and SDLWindow swap 
        scene.render_post()
        
    scene.shutdown()


if __name__ == "__main__":    
    main(imguiFlag = False)