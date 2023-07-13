import numpy as np
import os
import time
import Elements.pyECSS.utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, RenderMesh
from Elements.pyECSS.System import  TransformSystem
from Elements.pyGLV.GL.Scene import Scene

from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray
import Elements.pyGLV.utils.normals as norm
from Elements.pyGLV.GL.Textures import get_texture_faces, get_single_texture_faces

from Elements.pyGLV.XR.ElementsXR import ElementsXR_program
from Elements.pyGLV.XR.options import options, Blend_Mode, View_Configuration, Form_factor


"""
Note: Work in progress
"""

scene = Scene()    

# Scenegraph with Entities, Components
rootEntity = scene.world.createEntity(Entity(name="RooT"))
entityCam1 = scene.world.createEntity(Entity(name="entityCam1"))
scene.world.addEntityChild(rootEntity, entityCam1)
trans1 = scene.world.addComponent(entityCam1, BasicTransform(name="trans1", trs=util.identity()))

entityCam2 = scene.world.createEntity(Entity(name="entityCam2"))
scene.world.addEntityChild(entityCam1, entityCam2)
trans2 = scene.world.addComponent(entityCam2, BasicTransform(name="trans2", trs=util.identity()))
# orthoCam = scene.world.addComponent(entityCam2, Camera(util.ortho(-100.0, 100.0, -100.0, 100.0, 1.0, 100.0), "orthoCam","Camera","500"))

skybox = scene.world.createEntity(Entity(name="Skybox"))
scene.world.addEntityChild(rootEntity, skybox)
transSkybox = scene.world.addComponent(skybox, BasicTransform(name="transSkybox", trs=util.identity)) #util.identity()
meshSkybox = scene.world.addComponent(skybox, RenderMesh(name="meshSkybox"))

node4 = scene.world.createEntity(Entity(name="node4"))
scene.world.addEntityChild(rootEntity, node4)
trans4 = scene.world.addComponent(node4, BasicTransform(name="trans4", trs=util.identity())) #util.identity()
mesh4 = scene.world.addComponent(node4, RenderMesh(name="mesh4"))

#Cube
minbox = -30
maxbox = 30
vertexSkybox = np.array([
    [minbox, minbox, maxbox, 1.0],
    [minbox, maxbox, maxbox, 1.0],
    [maxbox, maxbox, maxbox, 1.0],
    [maxbox, minbox, maxbox, 1.0], 
    [minbox, minbox, minbox, 1.0], 
    [minbox, maxbox, minbox, 1.0], 
    [maxbox, maxbox, minbox, 1.0], 
    [maxbox, minbox, minbox, 1.0]
],dtype=np.float32)

#index array for Skybox
indexSkybox = np.array((1,0,3, 1,3,2, 
                  2,3,7, 2,7,6,
                  3,0,4, 3,4,7,
                  6,5,1, 6,1,2,
                  4,5,6, 4,6,7,
                  5,4,0, 5,0,1), np.uint32) 

#Simple Cube
vertexCube = np.array([
    [-0.5, -0.5, 0.5, 1.0],
    [-0.5, 0.5, 0.5, 1.0],
    [0.5, 0.5, 0.5, 1.0],
    [0.5, -0.5, 0.5, 1.0], 
    [-0.5, -0.5, -0.5, 1.0], 
    [-0.5, 0.5, -0.5, 1.0], 
    [0.5, 0.5, -0.5, 1.0], 
    [0.5, -0.5, -0.5, 1.0]
],dtype=np.float32)

#index Array for Cube
indexCube = np.array((1,0,3, 1,3,2, 
                  2,3,7, 2,7,6,
                  3,0,4, 3,4,7,
                  6,5,1, 6,1,2,
                  4,5,6, 4,6,7,
                  5,4,0, 5,0,1), np.uint32) 


# Systems
transUpdate = scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
renderUpdate = scene.world.createSystem(RenderGLShaderSystem())
initUpdate = scene.world.createSystem(InitGLShaderSystem())

vertexSkybox, indexSkybox, _ = norm.generateUniqueVertices(vertexSkybox,indexSkybox)

vertexCube, indexCube, _ = norm.generateUniqueVertices(vertexCube,indexCube)

meshSkybox.vertex_attributes.append(vertexSkybox)
meshSkybox.vertex_index.append(indexSkybox)
vArraySkybox = scene.world.addComponent(skybox, VertexArray())
shaderSkybox = scene.world.addComponent(skybox, ShaderGLDecorator(Shader(vertex_source = Shader.STATIC_SKYBOX_VERT, fragment_source=Shader.STATIC_SKYBOX_FRAG)))

mesh4.vertex_attributes.append(vertexCube)
mesh4.vertex_index.append(indexCube)
vArray4 = scene.world.addComponent(node4, VertexArray())
shaderDec4 = scene.world.addComponent(node4, ShaderGLDecorator(Shader(vertex_source = Shader.TEXTURE_3D_VERT, fragment_source=Shader.TEXTURE_3D_FRAG)))

# MAIN RENDERING LOOP

exit = False
#scene.init(imgui=True, windowWidth = 1024, windowHeight = 768, windowTitle = "Elements: ElementsXR Example", openGLversion = 4)

program = ElementsXR_program()
program.createInstance("Elements: ElementsXR Demo")
program.InitializeSystem()
program.InitializeDevice(initUpdate)
program.InitializeSession()
program.create_Swapchains()

front_img = os.path.join(os.path.dirname(__file__), "Skyboxes", "Cloudy", "front.jpg")
right_img = os.path.join(os.path.dirname(__file__), "Skyboxes", "Cloudy", "right.jpg")
left_img = os.path.join(os.path.dirname(__file__), "Skyboxes", "Cloudy", "left.jpg")
back_img = os.path.join(os.path.dirname(__file__), "Skyboxes", "Cloudy", "back.jpg")
bottom_img = os.path.join(os.path.dirname(__file__), "Skyboxes", "Cloudy", "bottom.jpg")
top_img = os.path.join(os.path.dirname(__file__), "Skyboxes", "Cloudy", "top.jpg")
mat_img = os.path.join(os.path.dirname(__file__), "textures", "dark_wood_texture.jpg")

face_data = get_texture_faces(front_img,back_img,top_img,bottom_img,left_img,right_img)
face_data_2 = get_single_texture_faces(mat_img)

shaderSkybox.setUniformVariable(key='cubemap', value=face_data, texture3D=True)
shaderDec4.setUniformVariable(key='cubemap', value=face_data_2, texture3D=True)

model_cube = util.translate(0.0,0.5,0.0)

shaderDec4.setUniformVariable(key='model', value=model_cube, mat4=True)

while not exit:
    exit = program.poll_events()
    if program.session_running:
        print("Calling Render Frame")
        program.render_frame(renderUpdate,scene)
        print("After Render Frame")
    else:
        time.sleep(0.250)
    print(exit)
    
#scene.shutdown()