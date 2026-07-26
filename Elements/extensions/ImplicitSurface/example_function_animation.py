
'''
author: Kostis Lymperakis (kostis1101.github.io)

This example showcases the RealFunction3D class for real time
function animations. Every ~16 ms the function expression is
updated with a time parameter and the function surface will be updated
in real time. This shows a way to use parameters to control functions by
passing the values of the parameters in the string of the expression.
'''


from __future__         import annotations
from asyncore import dispatcher
from math import sin, cos, radians
from enum import Enum
from random import uniform;
import numpy as np

import imgui


import OpenGL.GL as gl;
import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.System import  TransformSystem, CameraSystem
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, RenderMesh
from Elements.pyECSS.Event import Event

from Elements.pyGLV.GUI.Viewer import  RenderGLStateSystem
from Elements.pyGLV.GUI.ImguiDecorator import ImGUIecssDecorator2

from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GL.SimpleCamera import SimpleCamera
from Elements.utils.terrain import generateTerrain
from Elements.utils.normals import Convert
from OpenGL.GL import GL_LINES

from Elements.utils.Shortcuts import displayGUI_text

from Elements.extensions.ImplicitSurface.marching_cubes import MarchingCubes, RealFunction3D, Surface3D_VERT, Surface3D_FRAG


import time

expression = "x**2 + y**2"
changed = False
minv = np.array([-5, -5, -5])
maxv = np.array([5, 5, 5])
res = [100, 100, 100]
scale = 1
last_must_save = False

inside_color = np.array([1, 0.67, 0.63])
outside_color = np.array([0.5, 0.74, 0.3])


class GameObjectEntity(Entity):
    def __init__(self, name=None, type=None, id=None) -> None:
        super().__init__(name, type, id);

        # Gameobject basic properties
        self._color          = [1, 0.5, 0.2, 1.0]; # this will be used as a uniform var
        # Create basic components of a primitive object
        self.trans          = BasicTransform(name="trans", trs=util.identity());
        self.mesh           = RenderMesh(name="mesh");
        # self.shaderDec      = ShaderGLDecorator(Shader(vertex_source=Shader.VERT_PHONG_MVP, fragment_source=Shader.FRAG_PHONG));
        self.shaderDec      = ShaderGLDecorator(Shader(vertex_source= Surface3D_VERT, fragment_source=Surface3D_FRAG));
        self.vArray         = VertexArray();
        # self.surface        = MarchingCubes(self.vArray);
        self.surface        = RealFunction3D(self.vArray);
        # Add components to entity
        scene = Scene();
        scene.world.createEntity(self);
        scene.world.addComponent(self, self.trans);
        scene.world.addComponent(self, self.mesh);
        scene.world.addComponent(self, self.shaderDec);
        scene.world.addComponent(self, self.vArray);

    @property
    def color(self):
        return self._color;
    @color.setter
    def color(self, colorArray):
        self._color = colorArray;

    def drawSelfGui(self, imgui):
        changed, value = imgui.color_edit3("Color", self.color[0], self.color[1], self.color[2]);
        self.color = [value[0], value[1], value[2], 1.0];

    def SetVertexAttributes(self, vertex, color, index, normals = None):
        self.mesh.vertex_attributes.append(vertex);
        self.mesh.vertex_attributes.append(color);
        if normals is not None:
            self.mesh.vertex_attributes.append(normals);
        self.mesh.vertex_index.append(index);


def main(imguiFlag = False):
    ##########################################################
    # Instantiate a simple complete ECSS with Entities, 
    # Components, Camera, Shader, VertexArray and RenderMesh
    #########################################################

    global N
    global avg

    start = time.time()
    
    winWidth = 1024
    winHeight = 1024
    
    scene = Scene()    

    # Initialize Systems used for this script
    transUpdate = scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
    camUpdate = scene.world.createSystem(CameraSystem("camUpdate", "CameraUpdate", "200"))
    renderUpdate = scene.world.createSystem(RenderGLShaderSystem())
    initUpdate = scene.world.createSystem(InitGLShaderSystem())
    
    # Scenegraph with Entities, Components
    rootEntity = scene.world.createEntity(Entity(name="Root"))

    # Spawn Camera
    mainCamera = SimpleCamera("Simple Camera")
    # Camera Settings
    mainCamera.trans2.trs = util.translate(0, 0, 13) # VIEW
    mainCamera.trans1.trs = util.rotate((1, 0, 0), -45); 

    #-----------------------------------------
    # Spawn Two Homes on top of each other
    surf = scene.world.createEntity(GameObjectEntity("Surface"))
    scene.world.addEntityChild(rootEntity, surf)
    
    # MAIN RENDERING LOOP
    running = True
    scene.init(imgui=True, windowWidth = winWidth, windowHeight = winHeight, windowTitle = "Elements: A CameraSystem Example", customImGUIdecorator = ImGUIecssDecorator2)

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

    # create surface (implicitly invokes JIT)
    surf.surface.update_surface(expression, minv, maxv, res)


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
    
    while running:


        if time.time() - start > 1 / 60:
            t = time.time()
            surf.surface.update_surface(f"0.5 * sin(cos(x) + {t}) - 0.5 * cos(sin(y) - {t})", [-5, -5, -5], [5, 5, 5], [70, 70, 70])
            start = time.time()

        scene.world.traverse_visit(transUpdate, scene.world.root) 
        scene.world.traverse_visit_pre_camera(camUpdate, mainCamera.camera)
        scene.world.traverse_visit(camUpdate, scene.world.root)

        view_dir = mainCamera.trans1.trs @ mainCamera.trans2.trs @ np.array([0, 0, 0, 1])

        surf.shaderDec.setUniformVariable(key='modelViewProj', value=surf.trans.l2cam, mat4=True);
        surf.shaderDec.setUniformVariable(key='colour_front', value=outside_color, float3=True);
        surf.shaderDec.setUniformVariable(key='colour_back', value=inside_color, float3=True);
        surf.shaderDec.setUniformVariable(key='view_pos', value=view_dir, float3=True);
        surf.shaderDec.setUniformVariable(key='model', value=surf.trans.trs, mat4=True);
        surf.shaderDec.setUniformVariable(key='specular_strength', value=0.3, float1=True);

        # call SDLWindow/ImGUI display() and ImGUI event input process
        running = scene.render()
        # call the GL State render System
        scene.world.traverse_visit(renderUpdate, scene.world.root)
        # ImGUI post-display calls and SDLWindow swap 
        scene.render_post()
        
    scene.shutdown()


if __name__ == "__main__":    
    main(imguiFlag = False)