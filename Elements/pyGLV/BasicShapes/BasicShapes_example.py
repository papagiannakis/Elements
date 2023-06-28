from __future__         import annotations
from asyncore import dispatcher
from math import sin, cos, radians
from enum import Enum
from random import uniform;
import numpy as np

import OpenGL.GL as gl;
import Elements.pyECSS.utilities as util
from Elements.pyECSS.System import  TransformSystem, CameraSystem
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform,  RenderMesh
from Elements.pyECSS.Event import Event

from Elements.pyGLV.GUI.Viewer import  RenderGLStateSystem,  ImGUIecssDecorator
from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GL.SimpleCamera import SimpleCamera

from Elements.pyGLV.BasicShapes import BasicShapes


def main(imguiFlag = False):
    ##########################################################
    # Instantiate a simple complete ECSS with Entities, 
    # Components, Camera, Shader, VertexArray and RenderMesh
    #########################################################
    
    #Material
    Mshininess = 0.4 
    Mcolor = util.vec(0.8, 0.0, 0.8)

    scene = Scene()    

    # Initialize Systems used for this script
    transUpdate = scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
    camUpdate = scene.world.createSystem(CameraSystem("camUpdate", "CameraUpdate", "200"))
    renderUpdate = scene.world.createSystem(RenderGLShaderSystem())
    initUpdate = scene.world.createSystem(InitGLShaderSystem())
    
    # Scenegraph with Entities, Components
    rootEntity = scene.world.createEntity(Entity(name="Root"))

    # Spawn Camera
    mainCamera = SimpleCamera("Simple Camera");
    # Camera Settings
    mainCamera.trans2.trs = util.translate(0, 0, 8) # VIEW
    mainCamera.trans1.trs = util.rotate((1, 0, 0), -45); 

    # Spawn Light
    ambientLight = BasicShapes.Light("Ambient Light");
    ambientLight.intensity = 0.1;
    scene.world.addEntityChild(rootEntity, ambientLight);
    pointLight = BasicShapes.PointLight();
    pointLight.trans.trs = util.translate(0.8, 1, 1)@util.scale(0.2)
    scene.world.addEntityChild(rootEntity, pointLight);

    # Spawn Two Homes on top of each other
    home = scene.world.createEntity(Entity("Home"));
    scene.world.addEntityChild(scene.world.root, home);
    trans = BasicTransform(name="trans", trs=util.identity());    
    scene.world.addComponent(home, trans);

    ### Spawn a few basic shapes

    cylinder = BasicShapes.CylinderSpawn()
    scene.world.addEntityChild(home, cylinder);
    torus = BasicShapes.TorusSpawn()
    scene.world.addEntityChild(home, torus);
    #cube = BasicShapes.CubeSpawn()
    #scene.world.addEntityChild(home, cube);
    #sphere = BasicShapes.SphereSpawn()
    #scene.world.addEntityChild(home, sphere);

    torus.trans.trs = util.translate(-1, 0, 0)@util.scale(0.5)
    cylinder.trans.trs = util.translate(0, 1, 0)@util.scale(0.5)
    #cube.trans.trs = util.translate(0.5, 0, 0)@util.scale(0.5)
    #sphere.trans.trs = util.translate(0, -0.5, 0)@util.scale(0.5)

    
    
    # MAIN RENDERING LOOP
    running = True
    scene.init(imgui=True, windowWidth = 1024, windowHeight = 800, windowTitle = "Elements: A CameraSystem Example", customImGUIdecorator = ImGUIecssDecorator)

    imGUIecss = scene.gContext


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
    scene.world.traverse_visit(initUpdate, scene.world.root)
    

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


    # pointLight.trans.trs = util.scale(0.2)
    while running:

        scene.world.traverse_visit(transUpdate, scene.world.root) 
        scene.world.traverse_visit_pre_camera(camUpdate, mainCamera.camera)
        scene.world.traverse_visit(camUpdate, scene.world.root)
        viewPos = mainCamera.trans2.l2world[:3, 3].tolist();
        lightPos = pointLight.trans.l2world[:3, 3].tolist();
        pointLight.shaderDec.setUniformVariable(key='modelViewProj', value=pointLight.trans.l2cam, mat4=True)
        for i in [1,2]:
            home.getChild(i).shaderDec.setUniformVariable(key='modelViewProj', value=home.getChild(i).trans.l2cam, mat4=True);
            home.getChild(i).shaderDec.setUniformVariable(key='model',value=home.getChild(i).trans.l2world,mat4=True)

            home.getChild(i).shaderDec.setUniformVariable(key='ambientColor', value=ambientLight.color, float3=True);
            home.getChild(i).shaderDec.setUniformVariable(key='ambientStr', value=ambientLight.intensity, float1=True);
            home.getChild(i).shaderDec.setUniformVariable(key='viewPos', value=viewPos, float3=True);
            home.getChild(i).shaderDec.setUniformVariable(key='lightPos', value=lightPos, float3=True);
            home.getChild(i).shaderDec.setUniformVariable(key='lightColor', value=np.array(pointLight.color), float3=True);
            home.getChild(i).shaderDec.setUniformVariable(key='lightIntensity', value=pointLight.intensity, float1=True);

            
            home.getChild(i).shaderDec.setUniformVariable(key='shininess',value=Mshininess,float1=True)
            home.getChild(i).shaderDec.setUniformVariable(key='matColor',value=Mcolor,float3=True)
            
                
        
        # call SDLWindow/ImGUI display() and ImGUI event input process
        running = scene.render(running)
        # call the GL State render System
        scene.world.traverse_visit(renderUpdate, scene.world.root)
        # ImGUI post-display calls and SDLWindow swap 
        scene.render_post()
        
    scene.shutdown()


if __name__ == "__main__":    
    main(imguiFlag = True)