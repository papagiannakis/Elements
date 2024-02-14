import unittest
import numpy as np

import OpenGL.GL as gl;
import Elements.pyECSS.math_utilities as util
import random as rand
from Elements.pyECSS.System import  TransformSystem, CameraSystem
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform
from Elements.pyECSS.Event import Event

from Elements.pyGLV.GUI.Viewer import  RenderGLStateSystem
from Elements.pyGLV.GUI.ImguiDecorator import ImGUIecssDecorator
from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GL.SimpleCamera import SimpleCamera

from Elements.extensions.GravityBB.AABoundingBox import AABoundingBox
from Elements.extensions.GravityBB.GravityCollisonSystem import GravityCollisionSystem
from Elements.extensions.GravityBB.example_GravityCollisionWithBB import GameObjectEntity
from Elements.extensions.GravityBB.example_GravityCollisionWithBB import CubeSpawn
from Elements.extensions.GravityBB.floor import generate_floor_with_bb
from Elements.utils.Shortcuts import displayGUI_text

from Elements.pyGLV.GL.Textures import Texture
from Elements.definitions import TEXTURE_DIR

class TestMainFunction(unittest.TestCase):
    def test_gravity_collision_on_floor_with_cubes(self):
        ##########################################################
        # Instantiate a simple complete ECSS with Entities, 
        # Components, Camera, Shader, VertexArray and RenderMesh
        #########################################################
        
        example_description = \
"This example shows the application of gravity on objects with \n\
axis aligned bounding boxes. As well as the collision between \n\
the bounding boxes of the cubes and the floor. The moment a cube hits \n\
the floor it is considered as part of it and more cubes can collide with it \n\
In this example we test only 3 cubes \n\
You may move the camera using the mouse or the GUI. \n\
You may see the ECS Scenegraph showing Entities & Components of the scene and \n\
various information about them. Hit ESC OR Close the window to quit." 
        
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
        mainCamera.trans2.trs = util.translate(0, 0, 12) # VIEW
        mainCamera.trans1.trs = util.rotate((1, 0, 0), -45); 

        Cubes = scene.world.createEntity(Entity("Cubes"))
        scene.world.addEntityChild(rootEntity, Cubes)

        trans = BasicTransform(name="trans", trs=util.identity());    
        scene.world.addComponent(Cubes, trans)
        
        # Generating floor with bounding box so that the objects can collide
        floor_trans, floor_shader, floor_bb = generate_floor_with_bb(rootEntity)

        collisionObjectList = [floor_bb] # NEED TO PASS THE SAME LIST TO ALL OF THEM
        number_of_cubes_in_scene = 3
        
        # Spawning 3 cubes with random transformations with bounding boxes
        for i in range(0, number_of_cubes_in_scene):
            cube: GameObjectEntity = CubeSpawn()
            scene.world.addEntityChild(Cubes, cube)
            cube.trans.trs = util.translate(0, (i + 1)*5, 0)
            #cube.trans.trs = cube.trans.trs @ util.rotate(axis= [rand.randint(0,1), rand.randint(0,1), rand.randint(0,1)], angle = rand.uniform(0,360))
            #cube.trans.trs = cube.trans.trs @ util.scale(rand.uniform(0.2, 1),rand.uniform(0.2, 1),rand.uniform(0.2, 1)) 
            scene.world.addComponent(cube, AABoundingBox(name="AABoundingBox",
                                            vertices = cube.mesh.vertex_attributes[0],
                                            objectCollisionList = collisionObjectList,
                                            density= 0.005))
            
            
        Cubes.getChild(0).trs = util.translate(0, 0, 0)

        
        # MAIN RENDERING LOOP
        running = True
        scene.init(imgui=True, windowWidth = 1024, windowHeight = 768, windowTitle = "Elements: A CameraSystem Example", customImGUIdecorator = ImGUIecssDecorator)

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
        
        texturePath = TEXTURE_DIR / "dark_wood_texture.jpg"
        texture = Texture(texturePath)
        floor_shader.setUniformVariable(key='ImageTexture', value=texture, texture=True)

        # Add RenderWindow to the EventManager publishers
        eManager._publishers[updateBackground.name] = gGUI
        
        while running:
            running = scene.render()
            scene.world.traverse_visit(renderUpdate, scene.world.root)
            
            displayGUI_text(example_description)
            
            # Here we traverse with the gravity Collision System
            scene.world.traverse_visit(gravitycollisionSystem, scene.world.root)
            scene.world.traverse_visit(transUpdate, scene.world.root) 
            scene.world.traverse_visit_pre_camera(camUpdate, mainCamera.camera)
            scene.world.traverse_visit(camUpdate, scene.world.root)
            
            for i in range(1, number_of_cubes_in_scene + 1):
                Cubes.getChild(i).shaderDec.setUniformVariable(key='modelViewProj', value=Cubes.getChild(i).trans.l2cam, mat4=True);
                Cubes.getChild(i).shaderDec.setUniformVariable(key='model', value=Cubes.getChild(i).trans.trs, mat4=True)

                Cubes.getChild(i).shaderDec.setUniformVariable(key='ambientColor', value=[1, 0.5, 0.3], float3=True)
                Cubes.getChild(i).shaderDec.setUniformVariable(key='ambientStr', value=0.5, float1=True)
                
                Cubes.getChild(i).shaderDec.setUniformVariable(key='viewPos', value=mainCamera.trans2.trs, float3=True)
                Cubes.getChild(i).shaderDec.setUniformVariable(key='lightPos', value=[0, 4, 0], float3=True)
                Cubes.getChild(i).shaderDec.setUniformVariable(key='lightColor', value=[0.5, 0.5, 0.5], float3=True)
                Cubes.getChild(i).shaderDec.setUniformVariable(key='lightIntensity', value=3, float1=True)
                
                Cubes.getChild(i).shaderDec.setUniformVariable(key='shininess', value=0, float1=True)
                Cubes.getChild(i).shaderDec.setUniformVariable(key='matColor', value=[0.4, 0.4, 0.4], float3=True)
                
            floor_shader.setUniformVariable(key='model', value=floor_trans.l2cam, mat4=True)
            floor_shader.setUniformVariable(key='View', value=util.identity(), mat4=True)
            floor_shader.setUniformVariable(key='Proj', value=util.identity(), mat4=True)
        
            
            # ImGUI post-display calls and SDLWindow swap 
            scene.render_post()
            
        scene.shutdown()