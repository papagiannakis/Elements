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
from Elements.pyGLV.GL.Textures import Texture, get_texture_faces
from Elements.features.XR.ElementsXR import ElementsXR_program
from Elements.features.XR.GraphicsPlugin import XR_Shaders

from Elements.definitions import TEXTURE_DIR

"""
Note: Before running this example open steamVR, go to Settings -> OpenXR and press "SET STEAMVR AS OPENXR RUNTIME"
      Otherwise the graphics plugin will not find the OpenGL plugin.
      Tested with Windows Mixed Reality
"""

GROUND_TEX_COORDINATES = [
    [0.0, 0.0],
    [1.0, 0.0],
    [1.0, 1.0],
    [0.0, 0.0],
    [1.0, 1.0],
    [0.0, 1.0]]

scene = Scene()

# Scenegraph with Entities, Components
rootEntity = scene.world.createEntity(Entity(name="RooT"))

skybox = scene.world.createEntity(Entity(name="Skybox"))
scene.world.addEntityChild(rootEntity, skybox)
transSkybox = scene.world.addComponent(skybox, BasicTransform(name="transSkybox", trs=util.identity)) #util.identity()
meshSkybox = scene.world.addComponent(skybox, RenderMesh(name="meshSkybox"))

ground = scene.world.createEntity(Entity(name="ground"))
scene.world.addEntityChild(rootEntity, ground)
ground_trans = scene.world.addComponent(ground, BasicTransform(name="ground_trans", trs=util.translate(0.0,-0.5,0.0)))
ground_mesh = scene.world.addComponent(ground, RenderMesh(name="ground_mesh"))

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

vertexground = np.array([
    [-5.0, 0.0, -5.0, 1.0],
    [3.0, 0.0, -5.0, 1.0],
    [3.0, 0.0, 5.0, 1.0],
    [-5.0, 0.0, 5.0, 1.0]
],dtype=np.float32)

indexground = np.array((2,1,0,2,0,3),np.uint32)

# Systems
transUpdate = scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
renderUpdate = scene.world.createSystem(RenderGLShaderSystem())
initUpdate = scene.world.createSystem(InitGLShaderSystem())

vertexSkybox, indexSkybox, _ = norm.generateUniqueVertices(vertexSkybox,indexSkybox)

meshSkybox.vertex_attributes.append(vertexSkybox)
meshSkybox.vertex_index.append(indexSkybox)
vArraySkybox = scene.world.addComponent(skybox, VertexArray())
shaderSkybox = scene.world.addComponent(skybox, ShaderGLDecorator(Shader(vertex_source = XR_Shaders.STATIC_SKYBOX_VERT_XR, fragment_source=XR_Shaders.STATIC_SKYBOX_FRAG_XR)))

vertexground, indexground, _ = norm.generateUniqueVertices(vertexground,indexground)

# Add ground
ground_mesh.vertex_attributes.append(vertexground) 
ground_mesh.vertex_attributes.append(GROUND_TEX_COORDINATES)
ground_mesh.vertex_index.append(indexground)
ground_vArray = scene.world.addComponent(ground, VertexArray())
ground_shader = scene.world.addComponent(ground, ShaderGLDecorator(Shader(vertex_source = Shader.SIMPLE_TEXTURE_VERT, fragment_source=Shader.SIMPLE_TEXTURE_FRAG)))


# MAIN RENDERING LOOP

exit_loop = False

program = ElementsXR_program()
program.Initialize("Elements: ElementsXR Demo",initUpdate)

skybox_texture_locations = os.path.join(TEXTURE_DIR, "Skyboxes", "Sea")
front_img = os.path.join(skybox_texture_locations, "front.jpg")
right_img = os.path.join(skybox_texture_locations,"right.jpg")
left_img = os.path.join(skybox_texture_locations,"left.jpg")
back_img = os.path.join(skybox_texture_locations,"back.jpg")
bottom_img = os.path.join(skybox_texture_locations,"bottom.jpg")
top_img = os.path.join(skybox_texture_locations,"top.jpg")
mat_img = os.path.join(os.path.dirname(__file__), "textures", "dark_wood_texture.jpg")

face_data = get_texture_faces(front_img,back_img,top_img,bottom_img,left_img,right_img)
texturePath = os.path.join(TEXTURE_DIR, "black_stones_floor.jpg")
texture = Texture(texturePath)

shaderSkybox.setUniformVariable(key='cubemap', value=face_data, texture3D=True)
ground_shader.setUniformVariable(key='ImageTexture', value=texture, texture=True)

while not exit_loop:
    #scene.world.traverse_visit(transUpdate,scene.world.root)
    exit_loop = program.poll_events()

    model_ground = ground.getChild(0).trs

    ground_shader.setUniformVariable(key='model', value=model_ground, mat4=True)

    if program.session_running:
        program.render_frame(renderUpdate)
    else:
        time.sleep(0.250)