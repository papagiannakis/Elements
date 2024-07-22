"""
Unit tests
Employing the unittest standard python test framework
https://docs.python.org/3/library/unittest.html
    
Elements.pyGLV (Computer Graphics for Deep Learning and Scientific Visualization)
@Copyright 2021-2022 Dr. George Papagiannakis

"""
import unittest

import numpy as np
# from sympy import true

import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, Camera, RenderMesh
from Elements.pyECSS.System import TransformSystem, CameraSystem
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GUI.Viewer import RenderGLStateSystem
from Elements.pyGLV.GUI.ImguiDecorator import IMGUIecssDecoratorBundle

from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray
from Elements.pyGLV.GL.FrameBuffer import FrameBuffer
import Elements.pyGLV.GUI.SceneWindow as swindow
from imgui_bundle import imguizmo  # type: ignore
from imgui_bundle import imgui_node_editor as ed # type: ignore

from OpenGL.GL import GL_LINES

from Elements.utils.Shortcuts import displayGUI_text


class TestEntityManagement(unittest.TestCase):
    """Main body of Scene Unit Test class

    """
    def setUp(self):
        """
        Common setup for all imgui bundle unit tests
        
        Scenegraph for unit tests:
        
        root
            |          
            node4   
            |--------------|----------|--------------|           
            trans4,        mesh4,     shaderDec4     vArray4                                          
                                                                                                           
        """

        self.s1 = Scene()
        self.scene = Scene()
        self.assertEqual(self.s1, self.scene)

        self.framebuffer = FrameBuffer();
        self.assertEqual(self.framebuffer, self.scene._buffer); # checking singleton instance of framebuffer
        
        # Scenegraph with Entities, Components
        self.rootEntity = self.scene.world.createEntity(Entity(name="RooT"))
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
        self.renderUpdate = self.scene.world.createSystem(RenderGLShaderSystem())
        self.initUpdate = self.scene.world.createSystem(InitGLShaderSystem())

    def test_init(self):
        """
        default constructor of Component class
        """
        print("TestScene:test_init START".center(100, '-'))

        self.assertEqual(id(self.scene), id(self.s1))
        self.assertEqual(self.rootEntity, self.scene.world.root)
        self.assertIsInstance(self.transUpdate, TransformSystem)
        self.assertIsInstance(self.renderUpdate, RenderGLShaderSystem)
        self.assertIn(self.node4, self.rootEntity._children)
        self.assertIn(self.trans4, self.node4._children)
        self.assertIn(self.mesh4, self.node4._children)
        
        self.scene.world.print()
    
        print("TestScene:test_init END".center(100, '-'))

    def test_addEntity(self):
        """
        Add Entity after the example has been initiated
        """
        print("TestScene:test_addEntity START".center(100, '-'))
        
        model = util.translate(0.0,0.0,0.5)
        eye = util.vec(1.0, 1.0, 1.0)
        target = util.vec(0,0,0)
        up = util.vec(0.0, 1.0, 0.0)
        view = util.lookat(eye, target, up)

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
        self.scene.init(imgui=True, windowWidth = 1024, windowHeight = 768, windowTitle = "Elements Add Cube Scene", customImGUIdecorator=IMGUIecssDecoratorBundle)
        
        # pre-pass scenegraph to initialise all GL context dependent geometry, shader classes
        # needs an active GL context
        self.scene.world.traverse_visit(self.initUpdate, self.scene.world.root)
        
        message = "This should be a Scene with a simple colored cube and a multicolored cube added dynamically (hidden).\
                     \nCamera movement is NOT possible. Hit ESC or close the window to exit."
        cnt = 0;
        while running:
            running = self.scene.render()
            displayGUI_text(message)
            self.scene.world.traverse_visit(self.renderUpdate, self.scene.world.root)
            self.scene.render_post()
            cnt += 1
            if cnt == 30:
                new = swindow.shapes["Cube"]();
                new.shaderDec.setUniformVariable(key='modelViewProj', value=mvpMat, mat4=True);
                swindow.update_needed = True;
                swindow.add = True;

                self.scene.gContext.node_editor.selected_parent = new.parent;
                self.scene.gContext.node_editor.name = new.name;
                self.scene.gContext.node_editor.addNode(new)
                self.scene.gContext.node_editor.generate(new);
        
                self.assertIn(new, self.scene.world.root._children);
                self.assertNotEqual( self.scene.gContext.node_editor.findNodeByName(new.name), None);
            
        self.scene.shutdown()
        
        print("TestScene:test_addEntity END".center(100, '-'))


    def test_removeEntity(self):
        """
        Remove entity after the example has been initiated
        """
        print("TestScene:test_removeEntity START".center(100, '-'))
        
        model = util.translate(0.0,0.0,0.5)
        eye = util.vec(1.0, 1.0, 1.0)
        target = util.vec(0,0,0)
        up = util.vec(0.0, 1.0, 0.0)
        view = util.lookat(eye, target, up)

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
        self.scene.init(imgui=True, windowWidth = 1024, windowHeight = 768, windowTitle = "Elements Remove Cube Scene", customImGUIdecorator=IMGUIecssDecoratorBundle)
        
        # pre-pass scenegraph to initialise all GL context dependent geometry, shader classes
        # needs an active GL context
        self.scene.world.traverse_visit(self.initUpdate, self.scene.world.root)
        
        message = "This should be an empty Scene as the cube is removed dynamically after being spawn. \
                  \nCamera movement is NOT possible. Hit ESC or close the window to exit."
        cnt = 0;
        while running:
            running = self.scene.render()
            displayGUI_text(message)
            self.scene.world.traverse_visit(self.renderUpdate, self.scene.world.root)
            self.scene.render_post()
            cnt += 1
            if cnt == 30:
                self.scene.world.root.remove(self.node4);
                self.assertNotIn(self.node4, self.scene.world.root._children);
            
        self.scene.shutdown()
        
        print("TestScene:test_removeEntity END".center(100, '-'))
