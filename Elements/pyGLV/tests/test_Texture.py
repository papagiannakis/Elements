
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
import os
import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, Camera, RenderMesh
from Elements.pyECSS.System import  TransformSystem, CameraSystem
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GUI.Viewer import RenderGLStateSystem

from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray
import Elements.utils.normals as norm
from Elements.pyGLV.GL.Textures import Texture
from Elements.utils.helper_function import displayGUI_text
from Elements.definitions import TEXTURE_DIR

from OpenGL.GL import GL_LINES

class TestScene(unittest.TestCase):
    """Main body of Scene Unit Test class

    """
    def setUp(self):
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

    def test_texture(self):

        self.vertices, self.indices, _ = norm.generateUniqueVertices(self.vertexCube,self.indexCube)

        # Systems
        self.transUpdate = self.scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
        # camUpdate = scene.world.createSystem(CameraSystem("camUpdate", "CameraUpdate", "200"))
        self.renderUpdate = self.scene.world.createSystem(RenderGLShaderSystem())
        self.initUpdate = self.scene.world.createSystem(InitGLShaderSystem())


        ## ADD CUBE ##
        # attach a simple cube in a RenderMesh so that VertexArray can pick it up
        self.mesh4.vertex_attributes.append(self.vertices)
        self.mesh4.vertex_attributes.append(Texture.CUBE_TEX_COORDINATES)
        self.mesh4.vertex_index.append(self.indices)
        self.vArray4 = self.scene.world.addComponent(self.node4, VertexArray())
        self.shaderDec4 = self.scene.world.addComponent(self.node4, ShaderGLDecorator(Shader(vertex_source = Shader.SIMPLE_TEXTURE_VERT, fragment_source=Shader.SIMPLE_TEXTURE_FRAG)))


        running = True
        self.scene.init(imgui=True, windowWidth = 1024, windowHeight = 768, windowTitle = "Elements: Textures example", openGLversion = 4)

        # pre-pass scenegraph to initialise all GL context dependent geometry, shader classes
        # needs an active GL context
        self.scene.world.traverse_visit(self.initUpdate, self.scene.world.root)

        ################### EVENT MANAGER ###################

        eManager = self.scene.world.eventManager
        gWindow = self.scene.renderWindow
        renderGLEventActuator = RenderGLStateSystem()
        eManager._subscribers['OnUpdateCamera'] = gWindow 
        eManager._actuators['OnUpdateCamera'] = renderGLEventActuator
        eManager._subscribers['OnUpdateWireframe'] = gWindow
        eManager._actuators['OnUpdateWireframe'] = renderGLEventActuator

        self.eye = util.vec(2.5, 2.5, 2.5)
        self.target = util.vec(0.0, 0.0, 0.0)
        self.up = util.vec(0.0, 1.0, 0.0)
        self.view = util.lookat(self.eye, self.target, self.up)
        self.projMat = util.perspective(50.0, 1.0, 0.01, 10.0)   

        gWindow._myCamera = self.view # otherwise, an imgui slider must be moved to properly update


        self.model_cube = self.trans4.trs
        
        texturePath = TEXTURE_DIR / "uoc_logo.png"
        texture = Texture(texturePath)
        self.shaderDec4.setUniformVariable(key='ImageTexture', value=texture, texture=True)

        message = "This is a Scene containing a cube with a texture. \nCamera movement is possible via the mouse or the GUI. \nHit ESC or close the window to exit."

        while running:
            running = self.scene.render()
            displayGUI_text(message)
            self.scene.world.traverse_visit(self.renderUpdate, self.scene.world.root)
            self.view =  gWindow._myCamera 
            self.shaderDec4.setUniformVariable(key='model', value=self.model_cube, mat4=True)
            self.shaderDec4.setUniformVariable(key='View', value=self.view, mat4=True)
            self.shaderDec4.setUniformVariable(key='Proj', value=self.projMat, mat4=True)
            self.scene.render_post()
            
        self.scene.shutdown()