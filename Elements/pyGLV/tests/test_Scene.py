"""
Unit tests
Employing the unittest standard python test framework
https://docs.python.org/3/library/unittest.html
    
Elements.pyGLV (Computer Graphics for Deep Learning and Scientific Visualization)
@Copyright 2021-2022 Dr. George Papagiannakis

"""


from statistics import mode
from turtle import width
import unittest

import numpy as np
# from sympy import true

import Elements.pyECSS.utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, Camera, RenderMesh
from Elements.pyECSS.System import System, TransformSystem, CameraSystem, RenderSystem
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyECSS.ECSSManager import ECSSManager
from Elements.pyGLV.GUI.Viewer import SDL2Window, ImGUIDecorator, RenderGLStateSystem

from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray

from OpenGL.GL import GL_LINES

import OpenGL.GL as gl



class TestScene(unittest.TestCase):
    """Main body of Scene Unit Test class

    """
    def setUp(self):
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
        

        self.s1 = Scene()
        self.scene = Scene()    
        self.assertEqual(self.s1, self.scene)
        
        # Scenegraph with Entities, Components
        self.rootEntity = self.scene.world.createEntity(Entity(name="RooT"))
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
        
        
        self.axes = self.scene.world.createEntity(Entity(name="axes"))
        self.scene.world.addEntityChild(self.rootEntity, self.axes)
        self.axes_trans = self.scene.world.addComponent(self.axes, BasicTransform(name="axes_trans", trs=util.identity()))
        self.axes_mesh = self.scene.world.addComponent(self.axes, RenderMesh(name="axes_mesh"))
  
        # a simple triangle
        self.vertexData = np.array([
            [0.0, 0.0, 0.0, 1.0],
            [0.5, 1.0, 0.0, 1.0],
            [1.0, 0.0, 0.0, 1.0]
        ],dtype=np.float32) 
        self.colorVertexData = np.array([
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 1.0],
            [0.0, 0.0, 1.0, 1.0]
        ], dtype=np.float32)
        
        #Colored Axes
        self.vertexAxes = np.array([
            [0.0, 0.0, 0.0, 1.0],
            [1.0, 0.0, 0.0, 1.0],
            [0.0, 0.0, 0.0, 1.0],
            [0.0, 1.0, 0.0, 1.0],
            [0.0, 0.0, 0.0, 1.0],
            [0.0, 0.0, 1.0, 1.0]
        ],dtype=np.float32) 
        self.colorAxes = np.array([
            [1.0, 0.0, 0.0, 1.0],
            [1.0, 0.0, 0.0, 1.0],
            [0.0, 1.0, 0.0, 1.0],
            [0.0, 1.0, 0.0, 1.0],
            [0.0, 0.0, 1.0, 1.0],
            [0.0, 0.0, 1.0, 1.0]
        ], dtype=np.float32)
        
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
        self.index = np.array((0,1,2), np.uint32) #simple triangle
        self.indexAxes = np.array((0,1,2,3,4,5), np.uint32) #3 simple colored Axes as R,G,B lines
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
        
####################################################################################################
####################################################################################################
####################################################################################################    

    def test_init(self):
        """
        default constructor of Component class
        """
        print("TestScene:test_init START".center(100, '-'))
        
        #check is scenegraph was initialised correctly by the world::ECSSManager
        self.assertEqual(id(self.scene), id(self.s1))
        self.assertEqual(self.rootEntity, self.scene.world.root)
        self.assertIsInstance(self.transUpdate, TransformSystem)
        self.assertIsInstance(self.camUpdate, CameraSystem)
        self.assertIsInstance(self.renderUpdate, RenderGLShaderSystem)
        self.assertIn(self.entityCam1, self.rootEntity._children)
        self.assertIn(self.node4, self.rootEntity._children)
        self.assertIn(self.trans4, self.node4._children)
        self.assertIn(self.mesh4, self.node4._children)
        self.assertIn(self.orthoCam, self.entityCam2._children)
        
        #self.scene.world.root.print()
        self.scene.world.print()
    
        print("TestScene:test_init END".center(100, '-'))
        
####################################################################################################
####################################################################################################
####################################################################################################    
    def test_axes(self):
        """
        test_axes
        """
        print("TestScene:test_axes START".center(100, '-'))
        
        # 
        # MVP matrix calculation - 
        # now set directly at shader level!
        # should be autoamtically picked up at ECSS VertexArray level from Scenegraph System
        # same process as VertexArray is automatically populated from RenderMesh
        #
        model = util.translate(0.0,0.0,0.0)
        eye = util.vec(0.5, 0.5, 0.5)
        target = util.vec(0,0,0)
        up = util.vec(0.0, 1.0, 0.0)
        view = util.lookat(eye, target, up)
        
        # projMat = util.perspective(120.0, 1.33, 0.1, 100.0) 
        # projMat = util.ortho(-100.0, 100.0, -100.0, 100.0, -0.5, 100.0)
        projMat = util.ortho(-5.0, 5.0, -5.0, 5.0, 0.1, 100.0)
        
        mvpMat = projMat @ view @ model 
        
                
        # self.scene.world.print()

        ## ADD AXES TO THIS MESH - START ##
        
        
        # self.shaderDec_axes = self.scene.world.addComponent(self.axes, Shader())
        ## OR
        self.shaderDec_axes = self.scene.world.addComponent(self.axes, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))
        self.shaderDec_axes.setUniformVariable(key='modelViewProj', value=mvpMat, mat4=True)

        self.axes_mesh.vertex_attributes.append(self.vertexAxes) 
        self.axes_mesh.vertex_attributes.append(self.colorAxes)
        self.axes_mesh.vertex_index.append(self.indexAxes)
        self.axes_vArray = self.scene.world.addComponent(self.axes, VertexArray(primitive=GL_LINES)) # note the primitive change

        
        
        
        ## ADD AXES TO THIS MESH - END ##

        
        running = True
        # MAIN RENDERING LOOP
        self.scene.init(imgui=True, windowWidth = 1024, windowHeight = 768, windowTitle = "Elements test_axes")
        
        # pre-pass scenegraph to initialise all GL context dependent geometry, shader classes
        # needs an active GL context
        self.scene.world.traverse_visit(self.initUpdate, self.scene.world.root)
        
        while running:
            running = self.scene.render(running)
            self.scene.world.traverse_visit(self.renderUpdate, self.scene.world.root)
            self.scene.render_post()
            
        self.scene.shutdown()
        
        print("TestScene:test_axes END".center(100, '-'))

####################################################################################################  
####################################################################################################
####################################################################################################
    def test_renderTriangle(self):
        """
        First time to test a RenderSystem in a Scene with Shader and VertexArray components
        """
        print("TestScene:test_render START".center(100, '-'))
        
        # decorated components and systems with sample, default pass-through shader
        self.shaderDec4 = self.scene.world.addComponent(self.node4, Shader())
        # attach that simple triangle in a RenderMesh
        self.mesh4.vertex_attributes.append(self.vertexData) 
        self.mesh4.vertex_attributes.append(self.colorVertexData)
        self.mesh4.vertex_index.append(self.index)
        self.vArray4 = self.scene.world.addComponent(self.node4, VertexArray())

        
        ## ADD AXES TO THIS MESH ##
        self.axes = self.scene.world.createEntity(Entity(name="axes"))
        self.scene.world.addEntityChild(self.rootEntity, self.axes)
        self.axes_trans = self.scene.world.addComponent(self.axes, BasicTransform(name="axes_trans", trs=util.identity()))
        self.axes_mesh = self.scene.world.addComponent(self.axes, RenderMesh(name="axes_mesh"))
        self.shaderDec_axes = self.scene.world.addComponent(self.axes, Shader())
        self.axes_mesh.vertex_attributes.append(self.vertexAxes) 
        self.axes_mesh.vertex_attributes.append(self.colorAxes)
        self.axes_mesh.vertex_index.append(self.indexAxes)
        self.axes_vArray = self.scene.world.addComponent(self.axes, VertexArray(primitive=GL_LINES)) # note the primitive change


        # MAIN RENDERING LOOP
        running = True
        
        self.scene.init(imgui=True, windowWidth = 1024, windowHeight = 768, windowTitle = "Elements test_renderTriangle")
        self.scene.world.traverse_visit(self.initUpdate, self.scene.world.root)
        
        while running:
            running = self.scene.render(running)
            self.scene.world.traverse_visit(self.renderUpdate, self.scene.world.root)
            self.scene.render_post()
            
        self.scene.shutdown()
        
        print("TestScene:test_renderTriangle END".center(100, '-'))

####################################################################################################
####################################################################################################
####################################################################################################    



    def test_renderCube(self):
        """
        First time to test a RenderSystem in a Scene with Shader and VertexArray components
        """
        print("TestScene:test_renderCube START".center(100, '-'))
        
        model = util.translate(0.0,0.0,0.5)
        eye = util.vec(1.0, 1.0, 1.0)
        target = util.vec(0,0,0)
        up = util.vec(0.0, 1.0, 0.0)
        view = util.lookat(eye, target, up)
        
        # projMat = util.perspective(120.0, 1.33, 0.1, 100.0)
        projMat = util.ortho(-10.0, 10.0, -10.0, 10.0, -0.5, 10.0)

        mvpMat =  projMat @ view @ model
        
        ## ADD CUBE ##
        # attach a simple cube in a RenderMesh so that VertexArray can pick it up
        self.mesh4.vertex_attributes.append(self.vertexCube)
        self.mesh4.vertex_attributes.append(self.colorCube)
        self.mesh4.vertex_index.append(self.indexCube)
        self.vArray4 = self.scene.world.addComponent(self.node4, VertexArray())
        # decorated components and systems with sample, default pass-through shader with uniform MVP
        self.shaderDec4 = self.scene.world.addComponent(self.node4, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))
        self.shaderDec4.setUniformVariable(key='modelViewProj', value=mvpMat, mat4=True)

        
        self.scene.world.print()

        
        running = True
        # MAIN RENDERING LOOP
        self.scene.init(imgui=True, windowWidth = 1024, windowHeight = 768, windowTitle = "Elements Cube Scene")
        
        # pre-pass scenegraph to initialise all GL context dependent geometry, shader classes
        # needs an active GL context
        self.scene.world.traverse_visit(self.initUpdate, self.scene.world.root)
        
        while running:
            running = self.scene.render(running)
            self.scene.world.traverse_visit(self.renderUpdate, self.scene.world.root)
            self.scene.render_post()
            
        self.scene.shutdown()
        
        print("TestScene:test_renderCube END".center(100, '-'))

####################################################################################################
####################################################################################################
####################################################################################################    
    

    def test_renderTriangleEVENT(self):
        """
        test_renderTriangle_shader
        """
        model = util.translate(0.0,0.0,0.0)
        eye = util.vec(2.5, 2.5, 2.5)
        target = util.vec(0.0, 0.0, 0.0)
        up = util.vec(0.0, 1.0, 0.0)
        view = util.lookat(eye, target, up)
        
        # projMat = util.ortho(-10.0, 10.0, -10.0, 10.0, -1.0, 10.0)      
        projMat = util.perspective(90.0, 1.33, 0.1, 100)

        
        
        # attach that simple triangle in a RenderMesh
        self.mesh4.vertex_attributes.append(self.vertexData) 
        self.mesh4.vertex_attributes.append(self.colorVertexData)
        self.mesh4.vertex_index.append(self.index)
        self.vArray4 = self.scene.world.addComponent(self.node4, VertexArray())

        # self.shaderDec4 = self.scene.world.addComponent(self.node4, Shader())
        self.shaderDec4 = self.scene.world.addComponent(self.node4, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))
        # self.shaderDec4.setUniformVariable(key='modelViewProj', value=mvpMat, mat4=True)


        showaxes = 1
        ## ADD AXES TO THIS MESH - START##
        if showaxes :
            self.axes = self.scene.world.createEntity(Entity(name="axes"))
            self.scene.world.addEntityChild(self.rootEntity, self.axes)
            self.axes_trans = self.scene.world.addComponent(self.axes, BasicTransform(name="axes_trans", trs=util.identity()))
            self.axes_mesh = self.scene.world.addComponent(self.axes, RenderMesh(name="axes_mesh"))
            self.axes_mesh.vertex_attributes.append(self.vertexAxes) 
            self.axes_mesh.vertex_attributes.append(self.colorAxes)
            self.axes_mesh.vertex_index.append(self.indexAxes)
            self.axes_vArray = self.scene.world.addComponent(self.axes, VertexArray(primitive=GL_LINES)) # note the primitive change
            self.axes_shader = self.scene.world.addComponent(self.axes, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))
        

        running = True
        # MAIN RENDERING LOOP
        self.scene.init(imgui=True, windowWidth = 1024, windowHeight = 768, windowTitle = "Elements test_renderTriangle_shader")
        
        # pre-pass scenegraph to initialise all GL context dependent geometry, shader classes
        # needs an active GL context

        self.scene.world.traverse_visit(self.initUpdate, self.scene.world.root)
        
        eManager = self.scene.world.eventManager
        gWindow = self.scene.renderWindow
        gGUI = self.scene.gContext
        renderGLEventActuator = RenderGLStateSystem()
        eManager._subscribers['OnUpdateCamera'] = gWindow 
        eManager._actuators['OnUpdateCamera'] = renderGLEventActuator
        eManager._subscribers['OnUpdateWireframe'] = gWindow
        eManager._actuators['OnUpdateWireframe'] = renderGLEventActuator


        gWindow._myCamera = view
        mvpMat =  projMat @ view @ model 
        # self.shaderDec4.setUniformVariable(key='modelViewProj', value=mvpMat, mat4=True)

        while running:
            running = self.scene.render(running)
            self.scene.world.traverse_visit(self.renderUpdate, self.scene.world.root)
            view = gWindow._myCamera 
            mvpMat =  projMat @ view @ model
            self.shaderDec4.setUniformVariable(key='modelViewProj', value=mvpMat, mat4=True)
            self.axes_shader.setUniformVariable(key='modelViewProj', value=mvpMat, mat4=True)
            self.scene.render_post()
            
        self.scene.shutdown()
        
        print("TestScene:test_renderTriangle_shader END".center(100, '-'))

####################################################################################################
####################################################################################################
####################################################################################################
    def test_renderAxesTerrain(self):
        """
        First time to test a RenderSystem in a Scene with Shader and VertexArray components
        """
        print("TestScene:test_render START".center(100, '-'))
        
        # decorated components and systems with sample, default pass-through shader
        # self.shaderDec4 = self.scene.world.addComponent(self.node4, Shader())

        # OR
        # model = util.translate(0.0,0.0,0.0)
        # eye = util.vec(0.5, 0.5, 0.5)
        # target = util.vec(0.0, 0.0, 1.0)
        # up = util.vec(0.0, 1.0, 0.0)
        # view = util.lookat(eye, target, up)


        model = util.translate(0.0,0.0,0.0)
        eye = util.vec(1.5, 1.5, 1.5)
        target = util.vec(0.0, 0.0, 0.0)
        up = util.vec(0.0, 1.0, 0.0)
        view = util.lookat(eye, target, up)
        # projMat = util.ortho(-10.0, 10.0, -10.0, 10.0, -1.0, 10.0)
        
        projMat = util.perspective(90.0, 1, 0.1, 1000)
        # projMat = util.perspective(90.0, 1, 0.01, 100.0) ## THIS WAS THE ORIGINAL
        print("\nprojMat =", projMat)
        
        mvpMat = projMat @ view @ model

        self.shaderDec4 = self.scene.world.addComponent(self.node4, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))
        self.shaderDec4.setUniformVariable(key='modelViewProj', value=mvpMat, mat4=True)

        from Elements.pyGLV.utils.terrain import generateTerrain
        self.vertexTerrain, self.indexTerrain, self.colorTerrain = generateTerrain(size=2,N=5,uniform_color = [0.2,0.2,0.2,1.0])

        
        

        # # attach terrain data to the RenderMesh
        self.mesh4.vertex_attributes.append(self.vertexTerrain) 
        self.mesh4.vertex_attributes.append(self.colorTerrain)
        self.mesh4.vertex_index.append(self.indexTerrain)
        self.vArray4 = self.scene.world.addComponent(self.node4, VertexArray(primitive=GL_LINES))
    

        
        ## ADD AXES TO THIS MESH ##
        self.axes = self.scene.world.createEntity(Entity(name="axes"))
        self.scene.world.addEntityChild(self.rootEntity, self.axes)
        self.axes_trans = self.scene.world.addComponent(self.axes, BasicTransform(name="axes_trans", trs=util.identity()))
        self.axes_mesh = self.scene.world.addComponent(self.axes, RenderMesh(name="axes_mesh"))
        


        self.axes_mesh.vertex_attributes.append(self.vertexAxes) 
        self.axes_mesh.vertex_attributes.append(self.colorAxes)
        self.axes_mesh.vertex_index.append(self.indexAxes)
        self.axes_vArray = self.scene.world.addComponent(self.axes, VertexArray(primitive=GL_LINES)) # note the primitive change for lines

        # self.shaderDec_axes = self.scene.world.addComponent(self.axes, Shader())
        # OR
        self.shaderDec4 = self.scene.world.addComponent(self.axes, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))
        self.shaderDec4.setUniformVariable(key='modelViewProj', value=mvpMat, mat4=True)


        running = True
        # MAIN RENDERING LOOP
        self.scene.init(imgui=True, windowWidth = 1024, windowHeight = 768, windowTitle = "Elements test_renderAxesTerrain")
        self.scene.world.traverse_visit(self.initUpdate, self.scene.world.root)
        
        while running:
            running = self.scene.render(running)
            self.scene.world.traverse_visit(self.renderUpdate, self.scene.world.root)
            self.scene.render_post()
            
        self.scene.shutdown()
        
        print("TestScene:test_renderAxesTerrainEND".center(100, '-'))
####################################################################################################
####################################################################################################
####################################################################################################
    def test_renderAxesTerrainEVENT(self):
        """
        First time to test a RenderSystem in a Scene with Shader and VertexArray components
        """
        print("TestScene:test_render START".center(100, '-'))
        
        


        model = util.translate(0.0,0.0,0.0)
        eye = util.vec(2.5, 2.5, 2.5)
        target = util.vec(0.0, 0.0, 0.0)
        up = util.vec(0.0, 1.0, 0.0)
        view = util.lookat(eye, target, up)

        # projMat = util.ortho(-10.0, 10.0, -10.0, 10.0, -1.0, 10.0)
        projMat = util.perspective(90.0, 1.33, 0.1, 100)
        # projMat = util.perspective(90.0, 1, 0.01, 100.0) 

        
        
        # mvpMat =  projMat @ view @ model

        self.shaderDec4 = self.scene.world.addComponent(self.node4, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))
        # self.shaderDec4.setUniformVariable(key='modelViewProj', value=mvpMat, mat4=True)

        from Elements.pyGLV.utils.terrain import generateTerrain
        self.vertexTerrain, self.indexTerrain, self.colorTerrain= generateTerrain(size=2,N=20)
        
        

        # # attach terrain data to the RenderMesh
        self.mesh4.vertex_attributes.append(self.vertexTerrain) 
        self.mesh4.vertex_attributes.append(self.colorTerrain)
        self.mesh4.vertex_index.append(self.indexTerrain)
        # self.vArray4 = self.scene.world.addComponent(self.node4, VertexArray())
        self.vArray4 = self.scene.world.addComponent(self.node4, VertexArray(primitive=GL_LINES))

        
        ## ADD AXES TO THIS MESH ##
        self.axes = self.scene.world.createEntity(Entity(name="axes"))
        self.scene.world.addEntityChild(self.rootEntity, self.axes)
        self.axes_trans = self.scene.world.addComponent(self.axes, BasicTransform(name="axes_trans", trs=util.identity()))
        self.axes_mesh = self.scene.world.addComponent(self.axes, RenderMesh(name="axes_mesh"))
        


        self.axes_mesh.vertex_attributes.append(self.vertexAxes) 
        self.axes_mesh.vertex_attributes.append(self.colorAxes)
        self.axes_mesh.vertex_index.append(self.indexAxes)
        self.axes_vArray = self.scene.world.addComponent(self.axes, VertexArray(primitive=GL_LINES)) # note the primitive change

        # self.shaderDec_axes = self.scene.world.addComponent(self.axes, Shader())
        # OR
        self.shaderDec42 = self.scene.world.addComponent(self.axes, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))
        # self.shaderDec42.setUniformVariable(key='modelViewProj', value=mvpMat, mat4=True)


        running = True
        # MAIN RENDERING LOOP
        self.scene.init(imgui=True, windowWidth = 1024, windowHeight = 768, windowTitle = "Elements test_renderAxesTerrainEVENT")
        
        # pre-pass scenegraph to initialise all GL context dependent geometry, shader classes
        # needs an active GL context


        self.scene.world.traverse_visit(self.initUpdate, self.scene.world.root)
        
        ################### EVENT MANAGER 
        # instantiate new EventManager
        # need to pass that instance to all event publishers e.g. ImGUIDecorator
        eManager = self.scene.world.eventManager
        gWindow = self.scene.renderWindow
        gGUI = self.scene.gContext
    
        renderGLEventActuator = RenderGLStateSystem()
        
        #setup Events and add them to the EventManager
        # updateTRS = Event(name="OnUpdateTRS", id=100, value=None)
        # updateBackground = Event(name="OnUpdateBackground", id=200, value=None)
        # #updateWireframe = Event(name="OnUpdateWireframe", id=201, value=None)
        

        # eManager._events[updateTRS.name] = updateTRS
        # eManager._events[updateBackground.name] = updateBackground
        #eManager._events[updateWireframe.name] = updateWireframe # this is added inside ImGUIDecorator
        
        # Add RenderWindow to the EventManager subscribers
        # @GPTODO
        # values of these Dicts below should be List items, not objects only 
        #   use subscribe(), publish(), actuate() methhods
        #
        # eManager._subscribers[updateTRS.name] = gGUI
        # eManager._subscribers[updateBackground.name] = gGUI
        
        eManager._subscribers['OnUpdateWireframe'] = gWindow
        eManager._actuators['OnUpdateWireframe'] = renderGLEventActuator
        eManager._subscribers['OnUpdateCamera'] = gWindow 
        eManager._actuators['OnUpdateCamera'] = renderGLEventActuator
        # END
        # Add RenderWindow to the EventManager publishers
        # eManager._publishers[updateBackground.name] = gGUI

        gWindow._myCamera = view
        mvpMat = projMat @ view @ model

        while running:
            running = self.scene.render(running)
            self.scene.world.traverse_visit(self.renderUpdate, self.scene.world.root)
            view = gWindow._myCamera
            mvpMat = projMat @ view @ model
            self.shaderDec4.setUniformVariable(key='modelViewProj', value=mvpMat, mat4=True)
            self.shaderDec42.setUniformVariable(key='modelViewProj', value=mvpMat, mat4=True)
            self.scene.render_post()
            
        self.scene.shutdown()
        
        print("TestScene:test_renderAxesTerrainEVENT END".center(100, '-'))

####################################################################################################
####################################################################################################
####################################################################################################    

    def test_renderCubeAxesEVENT(self):
        """
        test_renderCubeAxesEVENT
        """
        print("TestScene:test_renderCubeAxesEVENT START".center(100, '-'))
        
        ################# 
        # ADD ENTITIES  #
        #################    

        ## ADD CUBE ##
        # attach a simple cube in a RenderMesh so that VertexArray can pick it up
        self.mesh4.vertex_attributes.append(self.vertexCube)
        self.mesh4.vertex_attributes.append(self.colorCube)
        self.mesh4.vertex_index.append(self.indexCube)
        self.vArray4 = self.scene.world.addComponent(self.node4, VertexArray())
        self.shaderDec4 = self.scene.world.addComponent(self.node4, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))


        
        ## ADD AXES ##
        self.axes = self.scene.world.createEntity(Entity(name="axes"))
        self.scene.world.addEntityChild(self.rootEntity, self.axes)
        self.axes_trans = self.scene.world.addComponent(self.axes, BasicTransform(name="axes_trans", trs=util.identity()))
        self.axes_mesh = self.scene.world.addComponent(self.axes, RenderMesh(name="axes_mesh"))
        self.axes_mesh.vertex_attributes.append(self.vertexAxes) 
        self.axes_mesh.vertex_attributes.append(self.colorAxes)
        self.axes_mesh.vertex_index.append(self.indexAxes)
        self.axes_vArray = self.scene.world.addComponent(self.axes, VertexArray(primitive=GL_LINES)) # note the primitive change
        self.axes_shader = self.scene.world.addComponent(self.axes, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))

        
        # INITIATE SCENE#

        self.scene.init(imgui=True, windowWidth = 1024, windowHeight = 768, windowTitle = "Elements test_renderAxesTerrainEVENT")
        self.scene.world.traverse_visit(self.initUpdate, self.scene.world.root)

        ################# 
        # EVENT MANAGER #
        #################
        
        eManager = self.scene.world.eventManager
        gWindow = self.scene.renderWindow
        gGUI = self.scene.gContext
    
        renderGLEventActuator = RenderGLStateSystem()
        eManager._subscribers['OnUpdateWireframe'] = gWindow
        eManager._actuators['OnUpdateWireframe'] = renderGLEventActuator
        eManager._subscribers['OnUpdateCamera'] = gWindow 
        eManager._actuators['OnUpdateCamera'] = renderGLEventActuator    



        

        # CAMERA SETTINGS #
        
        eye = util.vec(2.5, 2.5, 2.5)
        target = util.vec(0.0, 0.0, 0.0)
        up = util.vec(0.0, 1.0, 0.0)
        view = util.lookat(eye, target, up)
        # projMat = util.ortho(-10.0, 10.0, -10.0, 10.0, -1.0, 10.0)  
        # projMat = util.perspective(90.0, 1.33, 0.1, 100)  
        projMat = util.perspective(50.0, 1.0, 1.0, 10.0)   
        
        model_terrain_axes = util.translate(0.0,0.0,0.0)
        model_cube = util.scale(0.3) @ util.translate(0.0,0.5,0.0)

        gWindow._myCamera = view # otherwise, an imgui slider must be moved to properly update
        
        
        # MAIN RENDERING LOOP #
        
        running = True
        
        while running:
            running = self.scene.render(running)
            self.scene.world.traverse_visit(self.renderUpdate, self.scene.world.root)
            view =  gWindow._myCamera # updates view via the imgui
            mvp_cube = projMat @ view @ model_cube
            mvp_terrain_axes = projMat @ view @ model_terrain_axes
            self.axes_shader.setUniformVariable(key='modelViewProj', value=mvp_terrain_axes, mat4=True)
            self.shaderDec4.setUniformVariable(key='modelViewProj', value=mvp_cube, mat4=True)
            self.scene.render_post()
            
        self.scene.shutdown()
        
        print("TestScene:test_renderCubeAxesEVENT END".center(100, '-'))

####################################################################################################
####################################################################################################
####################################################################################################    

    def test_renderCubeAxesTerrainEVENT(self):
        

        """
        test_renderCubeAxesTerrainEVENT
        """
        print("TestScene:test_renderCubeAxesTerrainEVENT START".center(100, '-'))
        
        ## ADD CUBE ##
        # attach a simple cube in a RenderMesh so that VertexArray can pick it up
        self.mesh4.vertex_attributes.append(self.vertexCube)
        self.mesh4.vertex_attributes.append(self.colorCube)
        self.mesh4.vertex_index.append(self.indexCube)
        self.vArray4 = self.scene.world.addComponent(self.node4, VertexArray())
        self.shaderDec4 = self.scene.world.addComponent(self.node4, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))
        
        

        # Generate terrain
        from Elements.pyGLV.utils.terrain import generateTerrain
        self.vertexTerrain, self.indexTerrain, self.colorTerrain= generateTerrain(size=4,N=20)
        # Add terrain
        self.terrain = self.scene.world.createEntity(Entity(name="terrain"))
        self.scene.world.addEntityChild(self.rootEntity, self.terrain)
        self.terrain_trans = self.scene.world.addComponent(self.terrain, BasicTransform(name="terrain_trans", trs=util.identity()))
        self.terrain_mesh = self.scene.world.addComponent(self.terrain, RenderMesh(name="terrain_mesh"))
        self.terrain_mesh.vertex_attributes.append(self.vertexTerrain) 
        self.terrain_mesh.vertex_attributes.append(self.colorTerrain)
        self.terrain_mesh.vertex_index.append(self.indexTerrain)
        self.terrain_vArray = self.scene.world.addComponent(self.terrain, VertexArray(primitive=GL_LINES))
        self.terrain_shader = self.scene.world.addComponent(self.terrain, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))
        # self.terrain_shader.setUniformVariable(key='modelViewProj', value=mvpMat, mat4=True)
        
        ## ADD AXES ##
        self.axes = self.scene.world.createEntity(Entity(name="axes"))
        self.scene.world.addEntityChild(self.rootEntity, self.axes)
        self.axes_trans = self.scene.world.addComponent(self.axes, BasicTransform(name="axes_trans", trs=util.identity()))
        self.axes_mesh = self.scene.world.addComponent(self.axes, RenderMesh(name="axes_mesh"))
        self.axes_mesh.vertex_attributes.append(self.vertexAxes) 
        self.axes_mesh.vertex_attributes.append(self.colorAxes)
        self.axes_mesh.vertex_index.append(self.indexAxes)
        self.axes_vArray = self.scene.world.addComponent(self.axes, VertexArray(primitive=GL_LINES)) # note the primitive change

        # self.shaderDec_axes = self.scene.world.addComponent(self.axes, Shader())
        # OR
        self.axes_shader = self.scene.world.addComponent(self.axes, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))
        # self.axes_shader.setUniformVariable(key='modelViewProj', value=mvpMat, mat4=True)


        running = True
        # MAIN RENDERING LOOP
        self.scene.init(imgui=True, windowWidth = 1024, windowHeight = 768, windowTitle = "Elements test_renderAxesTerrainEVENT")
        
        # pre-pass scenegraph to initialise all GL context dependent geometry, shader classes
        # needs an active GL context

        # vArrayAxes.primitive = gl.GL_LINES

        self.scene.world.traverse_visit(self.initUpdate, self.scene.world.root)
        
        ################### EVENT MANAGER 
        # instantiate new EventManager
        # need to pass that instance to all event publishers e.g. ImGUIDecorator
        eManager = self.scene.world.eventManager
        gWindow = self.scene.renderWindow
        gGUI = self.scene.gContext
    
        renderGLEventActuator = RenderGLStateSystem()
        
        #setup Events and add them to the EventManager
        # updateTRS = Event(name="OnUpdateTRS", id=100, value=None)
        # updateBackground = Event(name="OnUpdateBackground", id=200, value=None)
        # #updateWireframe = Event(name="OnUpdateWireframe", id=201, value=None)
        

        # eManager._events[updateTRS.name] = updateTRS
        # eManager._events[updateBackground.name] = updateBackground
        #eManager._events[updateWireframe.name] = updateWireframe # this is added inside ImGUIDecorator
        
        # Add RenderWindow to the EventManager subscribers
        # @GPTODO
        # values of these Dicts below should be List items, not objects only 
        #   use subscribe(), publish(), actuate() methhods
        #
        # eManager._subscribers[updateTRS.name] = gGUI
        # eManager._subscribers[updateBackground.name] = gGUI
        
        eManager._subscribers['OnUpdateWireframe'] = gWindow
        eManager._actuators['OnUpdateWireframe'] = renderGLEventActuator
        eManager._subscribers['OnUpdateCamera'] = gWindow 
        eManager._actuators['OnUpdateCamera'] = renderGLEventActuator
        # END
        # Add RenderWindow to the EventManager publishers
        # eManager._publishers[updateBackground.name] = gGUI

        
        eye = util.vec(2.5, 2.5, 2.5)
        target = util.vec(0.0, 0.0, 0.0)
        up = util.vec(0.0, 1.0, 0.0)
        view = util.lookat(eye, target, up)
        # projMat = util.ortho(-10.0, 10.0, -10.0, 10.0, -1.0, 10.0)  
        # projMat = util.perspective(90.0, 1.33, 0.1, 100)  
        projMat = util.perspective(50.0, 1.0, 1.0, 10.0)   
        
        gWindow._myCamera = view # otherwise, an imgui slider must be moved to properly update

        model_terrain_axes = util.translate(0.0,0.0,0.0)
        model_cube = util.scale(0.3) @ util.translate(0.0,0.5,0.0)

        while running:
            running = self.scene.render(running)
            self.scene.world.traverse_visit(self.renderUpdate, self.scene.world.root)
            view =  gWindow._myCamera # updates view via the imgui
            mvp_cube = projMat @ view @ model_cube
            mvp_terrain_axes = projMat @ view @ model_terrain_axes
            self.axes_shader.setUniformVariable(key='modelViewProj', value=mvp_terrain_axes, mat4=True)
            self.terrain_shader.setUniformVariable(key='modelViewProj', value=mvp_terrain_axes, mat4=True)
            self.shaderDec4.setUniformVariable(key='modelViewProj', value=mvp_cube, mat4=True)
            self.scene.render_post()
            
        self.scene.shutdown()
        
        print("TestScene:test_renderCubeAxesTerrainEVENT END".center(100, '-'))


