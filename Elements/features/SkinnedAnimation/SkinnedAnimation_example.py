from __future__         import annotations
from asyncore import dispatcher
from math import sin, cos, radians
from enum import Enum
from random import uniform;
import numpy as np

import OpenGL.GL as gl;
import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.System import  TransformSystem, CameraSystem
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, RenderMesh
from Elements.pyECSS.Event import Event
from Elements.features.SkinnedAnimation.SkinnedAnimation import Keyframe, AnimationComponents
from Elements.features.SkinnedAnimation.SkinnedAnimationSystem import SkinnedAnimationSystem
#from AnimationComponent import Keyframe, AnimationComponents
from Elements.definitions import MODEL_DIR

from Elements.pyGLV.GUI.Viewer import  RenderGLStateSystem,  ImGUIecssDecorator
from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GL.SimpleCamera import SimpleCamera
from Elements.utils.normals import generateFlatNormalsMesh, generateNormals
from Elements.pyGLV.GL.Textures import Texture
from SkinnedAnimation import *
from Elements.definitions import TEXTURE_DIR



class Light(Entity):
    def __init__(self, name=None, type=None, id=None) -> None:
        super().__init__(name, type, id);
        # Add variables for light
        self.color = [1, 1, 1];
        self.intensity = 1;

    def drawSelfGui(self, imgui):
        changed, value = imgui.slider_float("Intensity", self.intensity, 0, 10, "%.1f", 1);
        self.intensity = value;

        changed, value = imgui.color_edit3("Color", self.color[0], self.color[1], self.color[2]);
        self.color = [value[0], value[1], value[2]];
        None;


class PointLight(Light):
    def __init__(self, name=None, type=None, id=None) -> None:
        super().__init__(name, type, id);

        # Create basic components of a primitive object
        self.trans          = BasicTransform(name="trans", trs=util.identity());
        scene = Scene();
        scene.world.createEntity(self);
        scene.world.addComponent(self, self.trans);


        vertices = [
            [-0.5, -0.5, 0.5, 1.0],
            [-0.5, 0.5, 0.5, 1.0],
            [0.5, 0.5, 0.5, 1.0],
            [0.5, -0.5, 0.5, 1.0], 
            [-0.5, -0.5, -0.5, 1.0], 
            [-0.5, 0.5, -0.5, 1.0], 
            [0.5, 0.5, -0.5, 1.0], 
            [0.5, -0.5, -0.5, 1.0]
        ]

        colors =  [self.color] * len(vertices)
        colors = np.array(colors)

        self.mesh       = RenderMesh(name="mesh");
        self.shaderDec  = ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG))
        self.vArray     = VertexArray();

        scene.world.addComponent(self, self.mesh);
        scene.world.addComponent(self, self.shaderDec);
        scene.world.addComponent(self, self.vArray);


        #index arrays for above vertex Arrays
        indices = np.array(
            (
                1,0,3, 1,3,2, 
                2,3,7, 2,7,6,
                3,0,4, 3,4,7,
                6,5,1, 6,1,2,
                4,5,6, 4,6,7,
                5,4,0, 5,0,1
            ),
            dtype=np.uint32
        ) #rhombus out of two triangles

        vertices, colors, indices, normals = IndexedConverter().Convert(vertices, colors, indices, produceNormals=True);
        self.mesh.vertex_attributes.append(vertices);
        self.mesh.vertex_attributes.append(colors);
        if normals is not None:
            self.mesh.vertex_attributes.append(normals);
        self.mesh.vertex_index.append(indices);

    def drawSelfGui(self, imgui):
        super().drawSelfGui(imgui);


class IndexedConverter():

    # Assumes triangulated buffers. Produces indexed results that support
    # normals as well.
    def Convert(self, vertices, colors, indices, produceNormals=True):

        iVertices = [];
        iColors = [];
        iNormals = [];
        iIndices = [];
        for i in range(0, len(indices), 3):
            iVertices.append(vertices[indices[i]]);
            iVertices.append(vertices[indices[i + 1]]);
            iVertices.append(vertices[indices[i + 2]]);
            iColors.append(colors[indices[i]]);
            iColors.append(colors[indices[i + 1]]);
            iColors.append(colors[indices[i + 2]]);


            iIndices.append(i);
            iIndices.append(i + 1);
            iIndices.append(i + 2);

        if produceNormals:
            for i in range(0, len(indices), 3):
                iNormals.append(util.calculateNormals(vertices[indices[i]], vertices[indices[i + 1]], vertices[indices[i + 2]]));
                iNormals.append(util.calculateNormals(vertices[indices[i]], vertices[indices[i + 1]], vertices[indices[i + 2]]));
                iNormals.append(util.calculateNormals(vertices[indices[i]], vertices[indices[i + 1]], vertices[indices[i + 2]]));

        iVertices = np.array( iVertices, dtype=np.float32 )
        iColors   = np.array( iColors,   dtype=np.float32 )
        iIndices  = np.array( iIndices,  dtype=np.uint32  )

        iNormals  = np.array( iNormals,  dtype=np.float32 )

        return iVertices, iColors, iIndices, iNormals;


def main(imguiFlag = False):
    ##########################################################
    # Instantiate a simple complete ECSS with Entities, 
    # Components, Camera, Shader, VertexArray and RenderMesh
    ##########################################################

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
    rootEntity = scene.world.createEntity(Entity(name = "Root"))

    # Spawn Camera
    mainCamera = SimpleCamera("Simple Camera");
    # Camera Settings
    mainCamera.trans2.trs = util.translate(0, 0, 8) # VIEW
    mainCamera.trans1.trs = util.rotate((1, 0, 0), -45); 

    # Spawn Light
    ambientLight = Light("Ambient Light");
    ambientLight.intensity = 0.1;
    scene.world.addEntityChild(rootEntity, ambientLight);
    pointLight = PointLight();
    pointLight.trans.trs = util.translate(0.8, 1, 1) @ util.scale(0.2)
    scene.world.addEntityChild(rootEntity, pointLight);

    #Spawn Animated AstroBoy
    node4 = scene.world.createEntity(Entity(name="Object"))
    scene.world.addEntityChild(rootEntity, node4)
    trans4 = scene.world.addComponent(node4, BasicTransform(name="Object_TRS", trs=util.scale(0.1)@util.translate(0,0,0) ))
    mesh4 = scene.world.addComponent(node4, RenderMesh(name="Object_mesh"))
    key1 = scene.world.addComponent(node4, Keyframe(name="Object_key_1"))
    key2 = scene.world.addComponent(node4, Keyframe(name="Object_key_2"))
    key3 = scene.world.addComponent(node4, Keyframe(name="Object_key_3"))

    ac = scene.world.addComponent(node4, AnimationComponents(name="Animation_Components"))
    # key1=key1.array_MM[0], key2=key2.array_MM[0], key3=key3.array_MM[0]
    obj_to_import = MODEL_DIR / "astroBoy_walk.dae"
    #print(str(obj_to_import))
    vertices, colors, boneWeight, boneID, faces = animation_initialize(obj_to_import, ac, key1, key2, key3)

    testAnim = SkinnedAnimationSystem()

    ac.key1 = key1.array_MM[0]
    ac.key2 = key2.array_MM[0]
    ac.key3 = key3.array_MM[0]

    # print(ac.key2)
    #print(np.array(key1.rotate, np.dtype(float)))
    #Generating normals
    #v, i, c, normals = generateFlatNormalsMesh(vertices , faces, colors)
    normals = generateNormals(vertices, faces)

    # testAnim = SkinnedAnimationSystem()
    # testAnim.keyframes = [key1.array_MM[0],key2.array_MM[0]]
    #print(testAnim.keyframes)

    TEX_COORDINATES = [
    [0.0, 0.0],
    [1.0, 0.0],
    [1.0, 1.0],
    [0.0, 0.0],
    [1.0, 1.0],
    [0.0, 1.0]]

    #Passing vertices, colors, normals, bone weights, bone ids to the Shader
    mesh4.vertex_attributes.append(vertices)
    #mesh4.vertex_attributes.append(TEX_COORDINATES*int(len(i)/6))colors
    mesh4.vertex_attributes.append(colors)
    mesh4.vertex_attributes.append(normals)
    mesh4.vertex_attributes.append(boneWeight)
    mesh4.vertex_attributes.append(boneID)
    mesh4.vertex_index.append(faces)
    vArray4 = scene.world.addComponent(node4, VertexArray())
    #shaderDec4 = scene.world.addComponent(node4, ShaderGLDecorator(Shader(vertex_source = Shader.ANIMATION_SIMPLE_TEXTURE_PHONG_VERT, fragment_source=Shader.SIMPLE_TEXTURE_PHONG_FRAG)))
    shaderDec4 = scene.world.addComponent(node4, ShaderGLDecorator(Shader(vertex_source = Shader.VERT_ANIMATION, fragment_source=Shader.FRAG_PHONG)))

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
    
    #texturePath = TEXTURE_DIR / "dark_wood_texture.jpg"
    #shaderDec4.setUniformVariable(key='ImageTexture', value=str(texturePath), texture=True)


    shaderDec4.setUniformVariable(key='BB', value=ac.bones[0], arraymat4=True)
    shaderDec4.setUniformVariable(key='ambientColor', value=ambientLight.color, float3=True);
    shaderDec4.setUniformVariable(key='ambientStr', value=ambientLight.intensity, float1=True);
    
    shaderDec4.setUniformVariable(key='lightColor', value=np.array(pointLight.color), float3=True);
    shaderDec4.setUniformVariable(key='lightIntensity', value=pointLight.intensity, float1=True);

    shaderDec4.setUniformVariable(key='shininess',value=Mshininess,float1=True)
    shaderDec4.setUniformVariable(key='matColor',value=Mcolor,float3=True)

    # pointLight.trans.trs = util.scale(0.2)
    while running:

        scene.world.traverse_visit(transUpdate, scene.world.root) 
        scene.world.traverse_visit_pre_camera(camUpdate, mainCamera.camera)
        scene.world.traverse_visit(camUpdate, scene.world.root)
        viewPos = mainCamera.trans2.l2world[:3, 3].tolist();
        lightPos = pointLight.trans.l2world[:3, 3].tolist();
        pointLight.shaderDec.setUniformVariable(key='modelViewProj', value=pointLight.trans.l2cam, mat4=True)
        #for i in [1,2]:

        MM = testAnim.apply2AnimationComponents(ac)

        #print(MM)
        shaderDec4.setUniformVariable(key='modelViewProj', value=trans4.l2cam, mat4=True);
        shaderDec4.setUniformVariable(key='model',value=trans4.l2world,mat4=True)

        
        shaderDec4.setUniformVariable(key='MM', value=MM, arraymat4=True)

        shaderDec4.setUniformVariable(key='viewPos', value=viewPos, float3=True);
        shaderDec4.setUniformVariable(key='lightPos', value=lightPos, float3=True);
        
        # call SDLWindow/ImGUI display() and ImGUI event input process
        running = scene.render()
        # call the GL State render System
        scene.world.traverse_visit(renderUpdate, scene.world.root)
        # animationGUI()
        # ImGUI post-display calls and SDLWindow swap 
        scene.render_post()

    scene.shutdown()


if __name__ == "__main__":    
    main(imguiFlag = True)