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

from OpenGL.GL import GL_LINES

from Elements.utils.Shortcuts import displayGUI_text


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

        self.framebuffer = FrameBuffer();
        self.assertEqual(self.framebuffer, self.scene._buffer); # checking singleton instance of framebuffer
        
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

        self.eyes = [
            [2.8, 2.8, 0],
            [2.3, 2.3, -2.3],
            [0, 2.8, -2.8],
            [-2.3, 2.3, -2.3],
            [-2.8, 2.8, 0],
            [-2.3, 2.3, 2.3],
            [0, 2.8, 2.8],
            [2.3, 2.3, 2.3]
        ]

    def test_init(self):
        """
        default constructor of Component class
        """
        print("TestScene:test_init START".center(100, '-'))

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
        
        self.scene.world.print()
    
        print("TestScene:test_init END".center(100, '-'))


    def test_axes(self):
        """
        test_axes
        """
        print("TestScene:test_axes START".center(100, '-'))
        
        model = util.translate(0.0,0.0,0.0)
        eye = util.vec(0.5, 0.5, 0.5)
        target = util.vec(0,0,0)
        up = util.vec(0.0, 1.0, 0.0)
        view = util.lookat(eye, target, up)
        
        projMat = util.ortho(-5.0, 5.0, -5.0, 5.0, 0.1, 100.0)
        
        mvpMat = projMat @ view @ model 
        
        self.shaderDec_axes = self.scene.world.addComponent(self.axes, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))
        self.shaderDec_axes.setUniformVariable(key='modelViewProj', value=mvpMat, mat4=True)

        self.axes_mesh.vertex_attributes.append(self.vertexAxes) 
        self.axes_mesh.vertex_attributes.append(self.colorAxes)
        self.axes_mesh.vertex_index.append(self.indexAxes)
        self.axes_vArray = self.scene.world.addComponent(self.axes, VertexArray(primitive=GL_LINES)) # note the primitive change

        running = True
        # MAIN RENDERING LOOP
        self.scene.init(imgui=True, windowWidth = 1024, windowHeight = 768, windowTitle = "Elements test_axes", customImGUIdecorator = IMGUIecssDecoratorBundle);
        self.assertIsInstance(self.scene.gContext, IMGUIecssDecoratorBundle);

        self.scene.world.traverse_visit(self.initUpdate, self.scene.world.root)
        
        message = "This should be a Scene with simple colored axes. \nCamera movement is NOT possible. Hit ESC or close the window to exit."

        while running:
            running = self.scene.render()
            displayGUI_text(message)
            self.scene.world.traverse_visit(self.renderUpdate, self.scene.world.root)
            self.scene.render_post()
            
        self.scene.shutdown()
        
        print("TestScene:test_axes END".center(100, '-'))


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
        
        message = "This should be a Scene with a simple colored triangle. \nCamera movement is NOT possible. Hit ESC or close the window to exit."
        while running:
            running = self.scene.render()
            displayGUI_text(message)
            self.scene.world.traverse_visit(self.renderUpdate, self.scene.world.root)
            self.scene.render_post()
            
        self.scene.shutdown()
        
        print("TestScene:test_renderTriangle END".center(100, '-')) 


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
        
        message = "This should be a Scene with a simple colored cube. \nCamera movement is NOT possible. Hit ESC or close the window to exit."

        while running:
            running = self.scene.render()
            displayGUI_text(message)
            self.scene.world.traverse_visit(self.renderUpdate, self.scene.world.root)
            self.scene.render_post()
            
        self.scene.shutdown()
        
        print("TestScene:test_renderCube END".center(100, '-'))

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
        self.scene.init(imgui=True, windowWidth = 1024, windowHeight = 768, windowTitle = "Elements Cube Scene", customImGUIdecorator=IMGUIecssDecoratorBundle)
        
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
        self.scene.init(imgui=True, windowWidth = 1024, windowHeight = 768, windowTitle = "Elements Cube Scene")
        
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

    def test_cameraMovement(self):
        """
        Moving animation on set intervals to test camera and gizmo movement
        """
        print("TestScene:test_cameraMovement START".center(100, '-'))
        
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
        self.scene.init(imgui=True, windowWidth = 1024, windowHeight = 768, windowTitle = "Elements Cube Scene", customImGUIdecorator=IMGUIecssDecoratorBundle)
        
        # pre-pass scenegraph to initialise all GL context dependent geometry, shader classes
        # needs an active GL context
        self.scene.world.traverse_visit(self.initUpdate, self.scene.world.root)
        
        message = "This should be an empty Scene as the cube is removed dynamically after being spawn. \
                  \nCamera movement is NOT possible. Hit ESC or close the window to exit."
        cnt = 0;
        currEye = 0;
        while running:
            running = self.scene.render()
            displayGUI_text(message)
            self.scene.world.traverse_visit(self.transUpdate, self.scene.world.root)
            self.scene.world.update_entity_values(self.scene.world.root, 1024, 768)
            self.scene.world.traverse_visit(self.renderUpdate, self.scene.world.root)
            self.scene.render_post()
            # cnt += 1
            # if cnt == 30:
            #     cnt = 0;
            #     currEye += 1;
            #     self.scene.gContext._eye = np.array(self.eyes[currEye], np.float32);
            #     self.scene.gContext._updateCamera.value = np.array(util.lookat(self.scene.gContext._eye, self.scene.gContext._target, self.scene.gContext._up), np.float32)

            #     if self.scene.gContext._wrapeeWindow.eventManager is not None:
            #         self.scene.gContext.wrapeeWindow.eventManager.notify(self.scene.gContext, self.scene.gContext._updateCamera)

            
        self.scene.shutdown()
        
        print("TestScene:test_cameraMovement END".center(100, '-'))
 