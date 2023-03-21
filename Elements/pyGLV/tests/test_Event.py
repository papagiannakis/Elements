"""
Unit tests
Employing the unittest standard python test framework
https://docs.python.org/3/library/unittest.html
    
Elements.pyGLV (Computer Graphics for Deep Learning and Scientific Visualization)
@Copyright 2021-2022 Dr. George Papagiannakis

"""


import unittest
import time
import numpy as np

import Elements.pyECSS.utilities as util
from Elements.pyECSS.System import System, TransformSystem, CameraSystem
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, Camera, RenderMesh
from Elements.pyECSS.Event import Event, EventManager
from Elements.pyGLV.GUI.Viewer import SDL2Window, ImGUIDecorator, RenderGLStateSystem
from Elements.pyECSS.ECSSManager import ECSSManager
from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray
from Elements.pyGLV.GL.Scene import Scene

class TestEvent(unittest.TestCase):
    
    def setUp(self):
        """
        setup common scene for Event testing
        """ 
        
        
        #
        # Instantiate a simple complete ECSS with Entities, Components, Camera, Shader, VertexArray and RenderMesh
        #
        """
        Common setup for all unit tests
        
        Scenegraph for unit tests:
        
        root
            |---------------------------|           
            entityCam1,                 node4,      
            |-------|                    |--------------|----------|--------------|           
            trans1, entityCam2           trans4,        mesh4,     shaderDec4     vArray4
                    |                               
                    ortho, trans2                   
                                                                
        """
        
        self.scene = Scene()    
        
        # Scenegraph with Entities, Components
        self.rootEntity = self.scene.world.createEntity(Entity(name="Root"))
        self.entityCam1 = self.scene.world.createEntity(Entity(name="entityCam1"))
        self.scene.world.addEntityChild(self.rootEntity, self.entityCam1)
        self.trans1 = self.scene.world.addComponent(self.entityCam1, BasicTransform(name="trans1", trs=util.identity()))
        
        self.entityCam2 = self.scene.world.createEntity(Entity(name="entityCam2"))
        self.scene.world.addEntityChild(self.entityCam1, self.entityCam2)
        self.trans2 = self.scene.world.addComponent(self.entityCam2, BasicTransform(name="trans2", trs=util.identity()))
        self.orthoCam = self.scene.world.addComponent(self.entityCam2, Camera(util.ortho(-100.0, 100.0, -100.0, 100.0, 1.0, 100.0), "orthoCam","Camera","500"))
        
        self.node4 = self.scene.world.createEntity(Entity(name="node4"))
        self.scene.world.addEntityChild(self.rootEntity, self.node4)
        self.trans4 = self.scene.world.addComponent(self.node4, BasicTransform(name="trans4", trs=util.identity()))
        self.mesh4 = self.scene.world.addComponent(self.node4, RenderMesh(name="mesh4"))
        
        #Simple Cube
        self.vertexCube = np.array([
            [-0.5, -0.5, 0.5, 1.0],
            [-0.5, 0.5, 0.5, 1.0],
            [0.5, 0.5, 0.5, 1.0],
            [0.5, -0.5, 0.5, 1.0], 
            [-0.5, -0.5, -0.5, 1.0], 
            [-0.5, 0.5, -0.5, 1.0], 
            [0.5, 0.5, -0.5, 1.0], 
            [0.5, -0.5, -0.5, 1.0]
        ],dtype=np.float32) 
        self.colorCube = np.array([
            [0.0, 0.0, 0.0, 1.0],
            [1.0, 0.0, 0.0, 1.0],
            [1.0, 1.0, 0.0, 1.0],
            [0.0, 1.0, 0.0, 1.0],
            [0.0, 0.0, 1.0, 1.0],
            [1.0, 0.0, 1.0, 1.0],
            [1.0, 1.0, 1.0, 1.0],
            [0.0, 1.0, 1.0, 1.0]
        ], dtype=np.float32)
        
        #index arrays for above vertex Arrays
        self.indexCube = np.array((1,0,3, 1,3,2, 
                          2,3,7, 2,7,6,
                          3,0,4, 3,4,7,
                          6,5,1, 6,1,2,
                          4,5,6, 4,6,7,
                          5,4,0, 5,0,1), np.uint32) #rhombus out of two triangles
        # Systems
        self.transUpdate = self.scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
        self.camUpdate = self.scene.world.createSystem(CameraSystem("camUpdate", "CameraUpdate", "200"))
        self.renderUpdate = self.scene.world.createSystem(RenderGLShaderSystem())
        self.initUpdate = self.scene.world.createSystem(InitGLShaderSystem())
        
        
    
    def test_init(self):
        """simple tests for Event dataclass
        """
        print("TestEvent:test_init START".center(100, '-'))
        
        trsMat = util.translate(10.0,20.0,30.0)
        e = Event("OnUpdate", 100, trsMat)
        
        mT = np.array([
            [1.0,0.0,0.0,10.0],
            [0.0,1.0,0.0,20.0],
            [0.0,0.0,1.0,30.0],
            [0.0,0.0,0.0,1.0],
        ],dtype=np.float,order='F')
        
        self.assertEqual(mT.tolist(), e.value.tolist())
        self.assertEqual(e.name, "OnUpdate")
        self.assertEqual(e.id, 100)
        np.testing.assert_array_equal(e.value,mT)
        
        e.id = 101
        self.assertEqual(e.id, 101)
        
        print(e.value)
        print("\n Event e: ",e)
        
        print("TestEvent:test_init END".center(100, '-'))
        
        
    @unittest.skip("test_notify_ImGUIDecorator() is not using ECSS, skipping the test")    
    def test_notify_ImGUIDecorator(self):
        """simple Event notification from GUI
        """
        print("TestEvent:test_notify_ImGUIDecorator() START".center(100, '-'))
        
        #simple eventManager
        eManager = EventManager()
        #simple RenderWindow
        gWindow = SDL2Window(windowTitle="RenderWindow Event Testing", eventManager = eManager)
        gGUI = ImGUIDecorator(gWindow)
        #simple Event actuator System
        renderGLEventActuator = RenderGLStateSystem()
        
        #setup Events and add them to the EventManager
        updateTRS = Event(name="OnUpdateTRS", id=100, value=None)
        updateBackground = Event(name="OnUpdateBackground", id=200, value=None)
        #updateWireframe = Event(name="OnUpdateWireframe", id=201, value=None)
        eManager._events[updateTRS.name] = updateTRS
        eManager._events[updateBackground.name] = updateBackground
        
        eManager._subscribers[updateTRS.name] = gGUI
        eManager._subscribers[updateBackground.name] = gGUI
        # this is a special case below:
        # this event is published in ImGUIDecorator and the subscriber is SDLWindow
        eManager._subscribers['OnUpdateWireframe'] = gWindow
        eManager._actuators['OnUpdateWireframe'] = renderGLEventActuator
        
        # Add RenderWindow to the EventManager publishers
        eManager._publishers[updateBackground.name] = gGUI
        
        gGUI.init() #calls ImGUIDecorator::init()-->SDL2Window::init()
        gGUI.wrapeeWindow.eventManager.print()
        
        running = True
        # MAIN RENDERING LOOP
        while running:
            gGUI.display()
            running = gGUI.event_input_process(running)
            gGUI.display_post()
        gGUI.shutdown()
        
        print("TestEvent:test_notify_ImGUIDecorator() END".center(100, '-'))
        
    @unittest.skip("test_renderCubeWithEvents is legacy code, skipping the test")
    def test_renderCubeWithEvents(self):
        """a simple Cube with also some event handling
        """
        print("TestEvent:test_renderCubeWithEvents() START".center(100, '-'))
        

        
        # 
        # MVP matrix calculation - 
        # now set directly here only for Testing
        # otherwise automatically picked up at ECSS VertexArray level from the Scenegraph System
        # same process as VertexArray is automatically populated from RenderMesh
        #
        model = util.translate(0.0,0.0,0.0)
        eye = util.vec(-0.5, -0.5, -0.5)
        target = util.vec(1.0, 1.0, 1.0)
        up = util.vec(0.0, 1.0, 0.0)
        view = util.lookat(eye, target, up)
        #projMat = util.frustum(-10.0, 10.0,-10.0,10.0, -1.0, 10)
        # projMat = util.perspective(120.0, 1.33, 0.1, 100.0)
        projMat = util.ortho(-10.0, 10.0, -10.0, 10.0, -1.0, 10.0)
        #projMat = util.ortho(-5.0, 5.0, -5.0, 5.0, -1.0, 5.0)
        mvpMat = model @ view @ projMat
        
        #
        # setup ECSS nodes pre-systems
        #
        self.orthoCam.projMat = projMat
        self.trans2.trs = view
        self.trans1.trs = model
        #l2cMat = self.node4.l2cam
        
        # decorated components and systems with sample, default pass-through shader with uniform MVP
        self.shaderDec4 = self.scene.world.addComponent(self.node4, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))
        # direct uniform variable shader setup
        self.shaderDec4.setUniformVariable(key='modelViewProj', value=mvpMat, mat4=True)
        
        # attach a simple cube in a RenderMesh so that VertexArray can pick it up
        self.mesh4.vertex_attributes.append(self.vertexCube)
        self.mesh4.vertex_attributes.append(self.colorCube)
        self.mesh4.vertex_index.append(self.indexCube)
        self.vArray4 = self.scene.world.addComponent(self.node4, VertexArray())
        
        self.scene.world.print()
        self.scene.world.eventManager.print()
        
        running = True
        # MAIN RENDERING LOOP
        self.scene.init(imgui=True, windowWidth = 1024, windowHeight = 768, windowTitle = "Elements Cube ECSS Scene")
        
        # ---------------------------------------------------------
        # run Systems in the scenegraph
        # root node is accessed via ECSSManagerObject.root property
        # normally these are run within the rendering loop (except 4th GLInit  System)
        # --------------------------------------------------------
        # 1. L2W traversal
        self.scene.world.traverse_visit(self.transUpdate, self.scene.world.root) 
        # 2. pre-camera Mr2c traversal
        self.scene.world.traverse_visit_pre_camera(self.camUpdate, self.orthoCam)
        # 3. run proper Ml2c traversal
        self.scene.world.traverse_visit(self.camUpdate, self.scene.world.root)
        # 4. run pre render GLInit traversal for once!
        #   pre-pass scenegraph to initialise all GL context dependent geometry, shader classes
        #   needs an active GL context
        self.scene.world.traverse_visit(self.initUpdate, self.scene.world.root)
        
        #
        # setup ECSS nodes after-systems
        #
        l2cMat = self.trans4.l2cam
        print(f'\nl2cMat: \n{l2cMat}')
        print(f'\nmvpMat: \n{mvpMat}')
        print(self.trans4)
        
        # self.shaderDec4.setUniformVariable(key='modelViewProj', value=l2cMat, mat4=True)
        
        # UnitTest mvp mat directly set here with the one extracted/calculated from ECSS
        #np.testing.assert_array_almost_equal(l2cMat,mvpMat,decimal=5)
        #np.testing.assert_array_almost_equal(mvpMat,l2cMat)
        
        ############################################
        # Instantiate all Event-related key objects
        ############################################
        
        # instantiate new EventManager
        # need to pass that instance to all event publishers e.g. ImGUIDecorator
        eManager = self.scene.world.eventManager
        gWindow = self.scene.renderWindow
        gGUI = self.scene.gContext
        

        # print("\nManos3: ", gWindow._myCamera)
        #simple Event actuator System
        renderGLEventActuator = RenderGLStateSystem()
        
        #setup Events and add them to the EventManager
        updateTRS = Event(name="OnUpdateTRS", id=100, value=None)
        updateBackground = Event(name="OnUpdateBackground", id=200, value=None)
        #updateWireframe = Event(name="OnUpdateWireframe", id=201, value=None)
        

        eManager._events[updateTRS.name] = updateTRS
        eManager._events[updateBackground.name] = updateBackground
        #eManager._events[updateWireframe.name] = updateWireframe # this is added inside ImGUIDecorator
        
        # Add RenderWindow to the EventManager subscribers
        # @GPTODO
        # values of these Dicts below should be List items, not objects only 
        #   use subscribe(), publish(), actuate() methhods
        #
        eManager._subscribers[updateTRS.name] = gGUI
        eManager._subscribers[updateBackground.name] = gGUI
        # this is a special case below:
        # this event is published in ImGUIDecorator and the subscriber is SDLWindow
        eManager._subscribers['OnUpdateWireframe'] = gWindow
        eManager._actuators['OnUpdateWireframe'] = renderGLEventActuator
        
        # MANOS START
        eManager._subscribers['OnUpdateCamera'] = gWindow #CHOOSE THE CORRECT ONE
        eManager._actuators['OnUpdateCamera'] = renderGLEventActuator #CHOOSE THE CORRECT ONE
        # MANOS END
        # Add RenderWindow to the EventManager publishers
        eManager._publishers[updateBackground.name] = gGUI
        
        # print (gWindow._myCamera)

        while running:
            running = self.scene.render(running)
            self.scene.world.traverse_visit(self.renderUpdate, self.scene.world.root)
            mvpMat = gWindow._myCamera
            self.shaderDec4.setUniformVariable(key='modelViewProj', value=mvpMat, mat4=True)
            self.scene.render_post()
            # print("\nManos3: ", gWindow._myCamera)
            
        self.scene.shutdown()
        
        
        print("TestEvent:test_renderCubeWithEvents() END".center(100, '-'))