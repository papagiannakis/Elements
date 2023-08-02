import numpy as np
import os
import time
import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, RenderMesh
from Elements.pyECSS.System import  TransformSystem
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray
import Elements.utils.normals as norm
from Elements.pyGLV.GL.Textures import get_texture_faces
from Elements.features.XR.ElementsXR import ElementsXR_program
from Elements.features.XR.GraphicsPlugin import XR_Shaders

from Elements.definitions import TEXTURE_DIR

"""
Note: Before running this example open steamVR, go to Settings -> OpenXR and press "SET STEAMVR AS OPENXR RUNTIME"
      Otherwise the graphics plugin will not find the OpenGL plugin.
      Tested with Windows Mixed Reality
"""

scene = Scene()

# Scenegraph with Entities, Components
rootEntity = scene.world.createEntity(Entity(name="RooT"))

skybox = scene.world.createEntity(Entity(name="Skybox"))
scene.world.addEntityChild(rootEntity, skybox)
transSkybox = scene.world.addComponent(skybox, BasicTransform(name="transSkybox", trs=util.identity)) #util.identity()
meshSkybox = scene.world.addComponent(skybox, RenderMesh(name="meshSkybox"))

#Cube
minbox = -20
maxbox = 20
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

# Systems
transUpdate = scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
renderUpdate = scene.world.createSystem(RenderGLShaderSystem())
initUpdate = scene.world.createSystem(InitGLShaderSystem())

vertexSkybox, indexSkybox, _ = norm.generateUniqueVertices(vertexSkybox,indexSkybox)

meshSkybox.vertex_attributes.append(vertexSkybox)
meshSkybox.vertex_index.append(indexSkybox)
vArraySkybox = scene.world.addComponent(skybox, VertexArray())
shaderSkybox = scene.world.addComponent(skybox, ShaderGLDecorator(Shader(vertex_source = XR_Shaders.STATIC_SKYBOX_VERT_XR, fragment_source=XR_Shaders.STATIC_SKYBOX_FRAG_XR)))

# MAIN RENDERING LOOP

exit_loop = False

program = ElementsXR_program()
program.createInstance("Elements: ElementsXR Demo")
program.InitializeSystem()
program.InitializeDevice(initUpdate)
program.InitializeSession()
program.create_Swapchains()

skybox_texture_locations = os.path.join(TEXTURE_DIR, "Skyboxes", "Sea")
front_img = os.path.join(skybox_texture_locations, "front.jpg")
right_img = os.path.join(skybox_texture_locations,"right.jpg")
left_img = os.path.join(skybox_texture_locations,"left.jpg")
back_img = os.path.join(skybox_texture_locations,"back.jpg")
bottom_img = os.path.join(skybox_texture_locations,"bottom.jpg")
top_img = os.path.join(skybox_texture_locations,"top.jpg")
mat_img = os.path.join(os.path.dirname(__file__), "textures", "dark_wood_texture.jpg")

face_data = get_texture_faces(front_img,back_img,top_img,bottom_img,left_img,right_img)

shaderSkybox.setUniformVariable(key='cubemap', value=face_data, texture3D=True)

while not exit_loop:
    exit_loop = program.poll_events()
    if program.session_running:
        program.render_frame(renderUpdate)
    else:
        time.sleep(0.250)