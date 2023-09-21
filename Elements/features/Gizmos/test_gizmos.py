from statistics import mode
from turtle import width
import unittest
import Elements.utils.normals as norm
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
from Elements.utils.helper_function import displayGUI_text

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

        self.emptymsg = """
Since this scene is empty no Gizmos appear
when TAB is pressed

Instructions:
Use the following keys to change transformation mode:
    T: translation
    R: Rotation
    S: Scaling
In Order to apply transformations on a selected 
Entity press and hold Left-alt-key + Left-mouse-button, 
then move the cursor anywhere to see the result

Additionally, you can change the Selected Entity by pressing TAB
                        """
        self.singlemsg = """
When you press TAB you can see that the Gizmos always remain on the 
same Entity

Instructions:
Use the following keys to change transformation mode:
    T: translation
    R: Rotation
    S: Scaling
In Order to apply transformations on a selected 
Entity press and hold Left-alt-key + Left-mouse-button, 
then move the cursor anywhere to see the result

Additionally, you can change the Selected Entity by pressing TAB
                         """
        self.multiplemsg = """
In this test the pink cube is parent of the yellow one. Therefore, when we apply a 
transformation to the parent, the same transformation is applied to its child

Instructions:
Use the following keys to change transformation mode:
    T: translation
    R: Rotation
    S: Scaling
In Order to apply transformations on a selected 
Entity press and hold Left-alt-key + Left-mouse-button, 
then move the cursor anywhere to see the result

Additionally, you can change the Selected Entity by pressing TAB
                           """

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
            [1.0, 0.0, 1.0, 1.0],
            [1.0, 0.0, 1.0, 1.0],
            [1.0, 0.0, 1.0, 1.0],
            [1.0, 0.0, 1.0, 1.0],
            [1.0, 0.0, 1.0, 1.0],
            [1.0, 0.0, 1.0, 1.0],
            [1.0, 0.0, 1.0, 1.0],
            [1.0, 0.0, 1.0, 1.0]
        ], dtype=np.float32)
        self.colorCube2 = np.array([
            [1.0, 1.0, 0.0, 1.0],
            [1.0, 1.0, 0.0, 1.0],
            [1.0, 1.0, 0.0, 1.0],
            [1.0, 1.0, 0.0, 1.0],
            [1.0, 1.0, 0.0, 1.0],
            [1.0, 1.0, 0.0, 1.0],
            [1.0, 1.0, 0.0, 1.0],
            [1.0, 1.0, 0.0, 1.0]
        ], dtype=np.float32)

        self.indexCube = np.array((1,0,3, 1,3,2, 
                  2,3,7, 2,7,6,
                  3,0,4, 3,4,7,
                  6,5,1, 6,1,2,
                  4,5,6, 4,6,7,
                  5,4,0, 5,0,1), np.uint32)
        
        self.vertex_pink, self.Index_pink, self.color_pink, self.normals_pink = norm.generateFlatNormalsMesh(self.vertexCube,self.indexCube,self.colorCube)
        self.vertex_yellow, self.Index_yellow, self.color_yellow, self.normals_yellow = norm.generateFlatNormalsMesh(self.vertexCube,self.indexCube,self.colorCube2)

        #Light
        self.Lposition = util.vec(0.0, 2.5, 1.2) #uniform lightpos
        self.Lambientcolor = util.vec(1.0, 1.0, 1.0) #uniform ambient color
        self.Lambientstr = 0.3 #uniform ambientStr
        self.LviewPos = util.vec(2.5, 2.8, 5.0) #uniform viewpos
        self.Lcolor = util.vec(1.0,1.0,1.0)
        self.Lintensity = 0.9
        #Material
        self.Mshininess = 0.4 
        self.Mcolor = util.vec(1.0, 0.0, 0.8)
        
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
            displayGUI_text(self.emptymsg)
            gizmos.update_ray_start()
            gizmos.update_view(view)
            gizmos.get_Event()
            gizmos.update_imgui()
            self.scene.render_post()
            
        self.scene.shutdown()

    def testSingle(self):
        """
        Test gizmos on a scene with a single element
        """
        node4_pink = self.scene.world.createEntity(Entity(name="node4_pink"))
        self.scene.world.addEntityChild(self.rootEntity, node4_pink)
        trans4_pink = self.scene.world.addComponent(node4_pink, BasicTransform(name="trans4_pink", trs=util.translate(-1.5,0.0,-1.5)))
        mesh4_pink = self.scene.world.addComponent(node4_pink, RenderMesh(name="mesh4_pink"))

        mesh4_pink.vertex_attributes.append(self.vertex_pink)
        mesh4_pink.vertex_attributes.append(self.color_pink)
        mesh4_pink.vertex_attributes.append(self.normals_pink)
        mesh4_pink.vertex_index.append(self.Index_pink)
        vArray4 = self.scene.world.addComponent(node4_pink, VertexArray())
        shaderDec4_pink = self.scene.world.addComponent(node4_pink, ShaderGLDecorator(Shader(vertex_source = Shader.VERT_PHONG_MVP, fragment_source=Shader.FRAG_PHONG)))
        
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

        #Set Uniform Variables for Light and material
        shaderDec4_pink.setUniformVariable(key='ambientColor',value=self.Lambientcolor,float3=True)
        shaderDec4_pink.setUniformVariable(key='ambientStr',value=self.Lambientstr,float1=True)
        shaderDec4_pink.setUniformVariable(key='viewPos',value=self.LviewPos,float3=True)
        shaderDec4_pink.setUniformVariable(key='lightPos',value=self.Lposition,float3=True)
        shaderDec4_pink.setUniformVariable(key='lightColor',value=self.Lcolor,float3=True)
        shaderDec4_pink.setUniformVariable(key='lightIntensity',value=self.Lintensity,float1=True)
        shaderDec4_pink.setUniformVariable(key='shininess',value=self.Mshininess,float1=True)
        shaderDec4_pink.setUniformVariable(key='matColor',value=self.Mcolor,float3=True)

        while running:
            running = self.scene.render()
            self.scene.world.traverse_visit(self.transUpdate, self.scene.world.root) 
            self.scene.world.traverse_visit(self.renderUpdate, self.scene.world.root)
            displayGUI_text(self.singlemsg)
            view =  gWindow._myCamera
            height = self.scene.renderWindow._windowHeight
            width = self.scene.renderWindow._windowWidth
            
            gizmos.update_screen_dimensions(window_width=width,window_height=height)
            gizmos.update_view(view)
            gizmos.update_ray_start()
            gizmos.get_Event()
            gizmos.update_imgui()

            model_cube = trans4_pink.l2world
            mvp_cube = projMat @ view @ model_cube

            shaderDec4_pink.setUniformVariable(key='modelViewProj', value=mvp_cube, mat4=True)
            shaderDec4_pink.setUniformVariable(key='model', value=model_cube, mat4=True)

            self.scene.render_post()
            
        self.scene.shutdown()

    def testMultiple(self):
        """
        Test gizmos on a scene with multiple elements, where one element is child of another
        """
        node4_pink = self.scene.world.createEntity(Entity(name="node4_pink"))
        self.scene.world.addEntityChild(self.rootEntity, node4_pink)
        trans4_pink = self.scene.world.addComponent(node4_pink, BasicTransform(name="trans4_pink", trs=util.translate(-2.0,0.5,0.0)))
        mesh4_pink = self.scene.world.addComponent(node4_pink, RenderMesh(name="mesh4_pink"))

        node4_yellow = self.scene.world.createEntity(Entity(name="node4_yellow"))
        self.scene.world.addEntityChild(node4_pink,node4_yellow)
        trans4_yellow = self.scene.world.addComponent(node4_yellow, BasicTransform(name="trans4_pink", trs=util.translate(2.0,0.0,0.0)))
        mesh4_yellow = self.scene.world.addComponent(node4_yellow, RenderMesh(name="mesh4_pink"))

        mesh4_pink.vertex_attributes.append(self.vertex_pink)
        mesh4_pink.vertex_attributes.append(self.color_pink)
        mesh4_pink.vertex_attributes.append(self.normals_pink)
        mesh4_pink.vertex_index.append(self.Index_pink)
        vArray_pink = self.scene.world.addComponent(node4_pink, VertexArray())
        shaderDec4_pink = self.scene.world.addComponent(node4_pink, ShaderGLDecorator(Shader(vertex_source = Shader.VERT_PHONG_MVP, fragment_source=Shader.FRAG_PHONG)))
        
        mesh4_yellow.vertex_attributes.append(self.vertex_yellow)
        mesh4_yellow.vertex_attributes.append(self.color_yellow)
        mesh4_yellow.vertex_attributes.append(self.normals_yellow)
        mesh4_yellow.vertex_index.append(self.Index_yellow)
        vArray4_yellow = self.scene.world.addComponent(node4_yellow, VertexArray())
        shaderDec4_yellow = self.scene.world.addComponent(node4_yellow, ShaderGLDecorator(Shader(vertex_source = Shader.VERT_PHONG_MVP, fragment_source=Shader.FRAG_PHONG)))

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

        #Set Uniform Variables for Light and material
        shaderDec4_pink.setUniformVariable(key='ambientColor',value=self.Lambientcolor,float3=True)
        shaderDec4_pink.setUniformVariable(key='ambientStr',value=self.Lambientstr,float1=True)
        shaderDec4_pink.setUniformVariable(key='viewPos',value=self.LviewPos,float3=True)
        shaderDec4_pink.setUniformVariable(key='lightPos',value=self.Lposition,float3=True)
        shaderDec4_pink.setUniformVariable(key='lightColor',value=self.Lcolor,float3=True)
        shaderDec4_pink.setUniformVariable(key='lightIntensity',value=self.Lintensity,float1=True)
        shaderDec4_pink.setUniformVariable(key='shininess',value=self.Mshininess,float1=True)
        shaderDec4_pink.setUniformVariable(key='matColor',value=self.Mcolor,float3=True)

        shaderDec4_yellow.setUniformVariable(key='ambientColor',value=self.Lambientcolor,float3=True)
        shaderDec4_yellow.setUniformVariable(key='ambientStr',value=self.Lambientstr,float1=True)
        shaderDec4_yellow.setUniformVariable(key='viewPos',value=self.LviewPos,float3=True)
        shaderDec4_yellow.setUniformVariable(key='lightPos',value=self.Lposition,float3=True)
        shaderDec4_yellow.setUniformVariable(key='lightColor',value=self.Lcolor,float3=True)
        shaderDec4_yellow.setUniformVariable(key='lightIntensity',value=self.Lintensity,float1=True)
        shaderDec4_yellow.setUniformVariable(key='shininess',value=self.Mshininess,float1=True)
        shaderDec4_yellow.setUniformVariable(key='matColor',value=self.Mcolor,float3=True)

        while running:
            running = self.scene.render()
            self.scene.world.traverse_visit(self.transUpdate, self.scene.world.root) 
            self.scene.world.traverse_visit(self.renderUpdate, self.scene.world.root)
            displayGUI_text(self.multiplemsg)
            view =  gWindow._myCamera
            height = self.scene.renderWindow._windowHeight
            width = self.scene.renderWindow._windowWidth
            
            gizmos.update_screen_dimensions(window_width=width,window_height=height)
            gizmos.update_view(view)
            gizmos.update_ray_start()
            gizmos.get_Event()
            gizmos.update_imgui()

            model_cube = trans4_pink.l2world
            model_cube2 = trans4_yellow.l2world

            mvp_cube = projMat @ view @ model_cube
            mvp_cube2 = projMat @ view @ model_cube2

            shaderDec4_pink.setUniformVariable(key='modelViewProj', value=mvp_cube, mat4=True)
            shaderDec4_pink.setUniformVariable(key='model', value=model_cube, mat4=True)

            shaderDec4_yellow.setUniformVariable(key='modelViewProj', value=mvp_cube2, mat4=True)
            shaderDec4_yellow.setUniformVariable(key='model', value=model_cube2, mat4=True)

            self.scene.render_post()
            
        self.scene.shutdown()