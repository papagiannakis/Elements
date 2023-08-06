from statistics import mode
from turtle import width
import unittest

import numpy as np
# from sympy import true

import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, Camera, RenderMesh
from Elements.pyECSS.System import System, TransformSystem, CameraSystem, RenderSystem
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyECSS.ECSSManager import ECSSManager
from Elements.pyGLV.GUI.Viewer import SDL2Window, ImGUIDecorator, RenderGLStateSystem

from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray
from Elements.features.Gizmos.Gizmos import Gizmos

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
            [0.0, 0.0, 1.0, 1.0],
            [0.0, 0.0, 1.0, 1.0],
            [0.0, 0.0, 1.0, 1.0],
            [0.0, 0.0, 1.0, 1.0],
            [0.0, 0.0, 1.0, 1.0],
            [0.0, 0.0, 1.0, 1.0],
            [0.0, 0.0, 1.0, 1.0],
            [0.0, 0.0, 1.0, 1.0]
        ], dtype=np.float32)
        self.colorCube2 = np.array([
            [0.0, 1.0, 0.0, 1.0],
            [0.0, 1.0, 0.0, 1.0],
            [0.0, 1.0, 0.0, 1.0],
            [0.0, 1.0, 0.0, 1.0],
            [0.0, 1.0, 0.0, 1.0],
            [0.0, 1.0, 0.0, 1.0],
            [0.0, 1.0, 0.0, 1.0],
            [0.0, 1.0, 0.0, 1.0]
        ], dtype=np.float32)

        self.indexCube = np.array((1,0,3, 1,3,2, 
                  2,3,7, 2,7,6,
                  3,0,4, 3,4,7,
                  6,5,1, 6,1,2,
                  4,5,6, 4,6,7,
                  5,4,0, 5,0,1), np.uint32) 
        
    def testInitialization(self):
        fov = 50.0
        width=1000
        height=1000
        aspect_ratio = 1.0
        near = 0.01
        far = 10.0
        projMat = util.perspective(fov, aspect_ratio, near, far)

        eye = util.vec(2.5, 2.5, 2.5)
        target = util.vec(0,0,0)
        up = util.vec(0.0, 1.0, 0.0)
        view = util.lookat(eye, target, up)

        gizmos = Gizmos(self.rootEntity)

        gizmos_entities = ["Gizmos_X","Gizmos_X_trans","Gizmos_X_mesh",
                                "Gizmos_Y","Gizmos_Y_trans","Gizmos_Y_mesh",
                                "Gizmos_Z","Gizmos_Z_trans","Gizmos_Z_mesh",
                                "Gizmos_x_S_line","Gizmos_x_S_line_trans","Gizmos_x_S_line_mesh",
                                "Gizmos_y_S_line","Gizmos_y_S_line_trans","Gizmos_y_S_line_mesh",
                                "Gizmos_z_S_line","Gizmos_z_S_line_trans","Gizmos_z_S_line_mesh",
                                "Gizmos_x_S_cube","Gizmos_x_S_cube_trans","Gizmos_x_S_cube_mesh",
                                "Gizmos_y_S_cube","Gizmos_y_S_cube_trans","Gizmos_y_S_cube_mesh",
                                "Gizmos_z_S_cube","Gizmos_z_S_cube_trans","Gizmos_z_S_cube_mesh"]

        for element in self.scene.world.root:
            if element is not None and element.name in gizmos_entities:
                gizmos_entities.remove(element.name)

        #make sure that all gizmos components are in the scene
        self.assertEqual(len(gizmos_entities),0)

        gizmos.update_projection(projMat)
        gizmos.update_screen_dimensions(window_width=width,window_height=height)
        gizmos.update_view(view)
        self.assertTrue(np.array_equiv(gizmos.projection,projMat))
        self.assertEqual(gizmos.screen_width,width)
        self.assertEqual(gizmos.screen_height,height)
        self.assertTrue(np.array_equiv(gizmos.view,view))

    def test_bounding_box_intersection(self):
        """
        Test if the bounding box intersection is working correctly
        """

        gizmos = Gizmos(self.rootEntity)
        start = util.vec(2.0,2.0,2.0,0.0)
        end = util.vec(0.0,0.0,0.0,0.0)
        direction = end - start
        minbb = util.vec(-1.0,-1.0,-1.0,1.0)
        maxbb = util.vec(1.0,1.0,1.0,1.0)
        model = util.identity()

        res, intersection_point = gizmos.testRayBoundingBoxIntesection(start,direction,minbb,maxbb,model)
        self.assertTrue(res)
    
    def testEmpty(self):
        """
        Test Gizmos on an empty scene
        """
        eye = util.vec(2.5, 2.5, 2.5)
        target = util.vec(0,0,0)
        up = util.vec(0.0, 1.0, 0.0)
        view = util.lookat(eye, target, up)

        fov = 50.0
        aspect_ratio = 1.0
        near = 0.01
        far = 10.0
        projMat = util.perspective(fov, aspect_ratio, near, far) 

        gizmos = Gizmos(self.rootEntity)
        cameraName = self.entityCam1.name
        gizmos.set_camera_in_use(cameraName)
        gizmos.update_projection(projMat)
        gizmos.update_view(view)
        gizmos.update_screen_dimensions(window_width=1024,window_height=768)

        running = True
        # MAIN RENDERING LOOP
        self.scene.init(imgui=True, windowWidth = 1024, windowHeight = 768, windowTitle = "Elements test_gizmos_Empty_Scene")

        self.scene.world.traverse_visit(self.initUpdate,self.scene.world.root)

        while running:
            running = self.scene.render()
            self.scene.world.traverse_visit(self.transUpdate, self.scene.world.root) 
            self.scene.world.traverse_visit(self.renderUpdate, self.scene.world.root)
            gizmos.update_ray_init_position()
            gizmos.update_view(view)
            gizmos.get_Event()
            gizmos.update_imgui()
            self.scene.render_post()
            
        self.scene.shutdown()

    def testSingle(self):
        """
        Test gizmos on a scene with a single element
        """
        node4 = self.scene.world.createEntity(Entity(name="node4"))
        self.scene.world.addEntityChild(self.rootEntity, node4)
        trans4 = self.scene.world.addComponent(node4, BasicTransform(name="trans4", trs=util.translate(0.0,0.5,-0.5)))
        mesh4 = self.scene.world.addComponent(node4, RenderMesh(name="mesh4"))

        mesh4.vertex_attributes.append(self.vertexCube)
        mesh4.vertex_attributes.append(self.colorCube)
        mesh4.vertex_index.append(self.indexCube)
        vArray4 = self.scene.world.addComponent(node4, VertexArray())
        shaderDec4 = self.scene.world.addComponent(node4, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))
        
        eye = util.vec(2.5, 2.5, 2.5)
        target = util.vec(0,0,0)
        up = util.vec(0.0, 1.0, 0.0)
        view = util.lookat(eye, target, up)

        fov = 50.0
        aspect_ratio = 1.0
        near = 0.01
        far = 10.0
        projMat = util.perspective(fov, aspect_ratio, near, far) 

        gizmos = Gizmos(self.rootEntity)
        gizmos.set_camera_in_use("entityCam1")
        gizmos.update_projection(projMat)
        gizmos.update_view(view)
        gizmos.update_screen_dimensions(window_width=1024,window_height=768)

        running = True
        self.scene.init(imgui=True, windowWidth = 1024, windowHeight = 768, windowTitle = "Elements test_gizmos_Single_Element")

        self.scene.world.traverse_visit(self.initUpdate,self.scene.world.root)

        eManager = self.scene.world.eventManager
        gWindow = self.scene.renderWindow
        gGUI = self.scene.gContext

        renderGLEventActuator = RenderGLStateSystem()


        eManager._subscribers['OnUpdateWireframe'] = gWindow
        eManager._actuators['OnUpdateWireframe'] = renderGLEventActuator
        eManager._subscribers['OnUpdateCamera'] = gWindow 
        eManager._actuators['OnUpdateCamera'] = renderGLEventActuator

        gWindow._myCamera = view

        while running:
            running = self.scene.render()
            self.scene.world.traverse_visit(self.transUpdate, self.scene.world.root) 
            self.scene.world.traverse_visit(self.renderUpdate, self.scene.world.root)
            view =  gWindow._myCamera
            height = self.scene.renderWindow._windowHeight
            width = self.scene.renderWindow._windowWidth
            
            gizmos.update_screen_dimensions(window_width=width,window_height=height)
            gizmos.update_view(view)
            gizmos.update_ray_init_position()
            gizmos.get_Event()
            gizmos.update_imgui()

            model_cube = trans4.l2world
            mvp_cube = projMat @ view @ model_cube

            shaderDec4.setUniformVariable(key='modelViewProj', value=mvp_cube, mat4=True)

            self.scene.render_post()
            
        self.scene.shutdown()

    def testMultiple(self):
        """
        Test gizmos on a scene with multiple elements, where one element is child of another
        """
        node4 = self.scene.world.createEntity(Entity(name="node4"))
        self.scene.world.addEntityChild(self.rootEntity, node4)
        trans4 = self.scene.world.addComponent(node4, BasicTransform(name="trans4", trs=util.translate(0.0,0.5,-1.5)))
        mesh4 = self.scene.world.addComponent(node4, RenderMesh(name="mesh4"))

        node4_2 = self.scene.world.createEntity(Entity(name="node4_2"))
        self.scene.world.addEntityChild(node4, node4_2)
        trans4_2 = self.scene.world.addComponent(node4_2, BasicTransform(name="trans4_2", trs=util.translate(0.0,0.0,1.5)))
        mesh4_2 = self.scene.world.addComponent(node4_2, RenderMesh(name="mesh4_2"))

        mesh4.vertex_attributes.append(self.vertexCube)
        mesh4.vertex_attributes.append(self.colorCube)
        mesh4.vertex_index.append(self.indexCube)
        vArray4 = self.scene.world.addComponent(node4, VertexArray())
        shaderDec4 = self.scene.world.addComponent(node4, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))

        mesh4_2.vertex_attributes.append(self.vertexCube)
        mesh4_2.vertex_attributes.append(self.colorCube2)
        mesh4_2.vertex_index.append(self.indexCube)
        vArray4_2 = self.scene.world.addComponent(node4_2, VertexArray())
        shaderDec4_2 = self.scene.world.addComponent(node4_2, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))


        eye = util.vec(2.5, 2.5, 2.5)
        target = util.vec(0,0,0)
        up = util.vec(0.0, 1.0, 0.0)
        view = util.lookat(eye, target, up)

        fov = 50.0
        aspect_ratio = 1.0
        near = 0.01
        far = 10.0
        projMat = util.perspective(fov, aspect_ratio, near, far) 

        gizmos = Gizmos(self.rootEntity)
        gizmos.set_camera_in_use("entityCam1")
        gizmos.update_projection(projMat)
        gizmos.update_view(view)
        gizmos.update_screen_dimensions(window_width=1024,window_height=768)

        running = True
        self.scene.init(imgui=True, windowWidth = 1024, windowHeight = 768, windowTitle = "Elements test_gizmos_Multiple_Elements")

        self.scene.world.traverse_visit(self.initUpdate,self.scene.world.root)

        eManager = self.scene.world.eventManager
        gWindow = self.scene.renderWindow
        gGUI = self.scene.gContext

        renderGLEventActuator = RenderGLStateSystem()


        eManager._subscribers['OnUpdateWireframe'] = gWindow
        eManager._actuators['OnUpdateWireframe'] = renderGLEventActuator
        eManager._subscribers['OnUpdateCamera'] = gWindow 
        eManager._actuators['OnUpdateCamera'] = renderGLEventActuator

        gWindow._myCamera = view

        while running:
            running = self.scene.render()
            self.scene.world.traverse_visit(self.transUpdate, self.scene.world.root) 
            self.scene.world.traverse_visit(self.renderUpdate, self.scene.world.root)
            view =  gWindow._myCamera
            height = self.scene.renderWindow._windowHeight
            width = self.scene.renderWindow._windowWidth
            
            gizmos.update_screen_dimensions(window_width=width,window_height=height)
            gizmos.update_view(view)
            gizmos.update_ray_init_position()
            gizmos.get_Event()
            gizmos.update_imgui()
            model_cube = trans4.l2world
            model_cube2 = trans4_2.l2world

            mvp_cube = projMat @ view @ model_cube
            mvp_cube2 = projMat @ view @ model_cube2

            shaderDec4.setUniformVariable(key='modelViewProj', value=mvp_cube, mat4=True)
            shaderDec4_2.setUniformVariable(key='modelViewProj', value=mvp_cube2, mat4=True)

            self.scene.render_post()
            
        self.scene.shutdown()