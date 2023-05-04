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
from Elements.pyGLV.Gizmos.Gizmos import Gizmos

from OpenGL.GL import GL_LINES

import OpenGL.GL as gl

class TestGizmos(unittest.TestCase):
    """
    ...
    """

    def setUp(self):

        self.scene = Scene()
        self.rootEntity = self.scene.world.createEntity(Entity(name="RooT"))
        self.entityCam1 = self.scene.world.createEntity(Entity(name="entityCam1"))
        self.scene.world.addEntityChild(self.rootEntity, self.entityCam1)
        self.trans1 = self.scene.world.addComponent(self.entityCam1, BasicTransform(name="trans1", trs=util.translate(2.5, 2.5, 2.5)))

        self.transUpdate = self.scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
        self.camUpdate = self.scene.world.createSystem(CameraSystem("camUpdate", "CameraUpdate", "200"))
        self.renderUpdate = self.scene.world.createSystem(RenderGLShaderSystem())
        self.initUpdate = self.scene.world.createSystem(InitGLShaderSystem())
    
    def testEmpty(self):
        """
        Test Gizmos on an empty scene
        """
        eye = util.vec(0.5, 0.5, 0.5)
        target = util.vec(0,0,0)
        up = util.vec(0.0, 1.0, 0.0)
        view = util.lookat(eye, target, up)

        fov = 50.0
        aspect_ratio = 1.0
        near = 0.01
        far = 10.0
        projMat = util.perspective(fov, aspect_ratio, near, far) 

        gizmos = Gizmos(self.rootEntity,projMat,view)
        gizmos.set_camera_in_use("entityCam1")

        running = True
        # MAIN RENDERING LOOP
        self.scene.init(imgui=True, windowWidth = 1024, windowHeight = 768, windowTitle = "Elements test_gizmos_Empty_Scene")

        self.scene.world.traverse_visit(self.initUpdate,self.scene.world.root)

        while running:
            running = self.scene.render(running)
            self.scene.world.traverse_visit(self.renderUpdate, self.scene.world.root)
            gizmos.update_mouse_position()
            gizmos.get_keyboard_Event()
            gizmos.update_gizmos()
            gizmos.update_imgui()
            self.scene.render_post()
            
        self.scene.shutdown()

    def testSingle(self):
        """
        Test gizmos on a scene with a single element
        """
        pass

    def testMultiple(self):
        """
        Test gizmos on a scene with multiple elements
        """
        pass