import os
import random
import numpy as np

from Elements.definitions import SHADER_DIR, TEXTURE_DIR, SKYBOX_DIR
import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, Camera, RenderMesh
from Elements.pyECSS.System import TransformSystem, CameraSystem
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GUI.Viewer import RenderGLStateSystem
from Elements.pyGLV.GUI.ImguiDecorator import ImGUIecssDecorator2
import imgui

from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray
from Elements.extensions.UV_Mapping.Gui import UVGui

from OpenGL.GL import GL_LINES
import OpenGL.GL as gl

import Elements.utils.normals as norm
from Elements.utils.terrain import generateTerrain
from Elements.utils.obj_to_mesh import obj_to_mesh

from Elements.utils.Shortcuts import displayGUI_text
from Elements.extensions.UV_Mapping.ObjectGenerator import UVObjectGenerator
from Elements.pyGLV.GL.Textures import Texture, get_texture_faces
from pathlib import Path



#from Elements.extensions.UV_Mapping.TextureMapping import TextureGUI
example_description = \
"This is the first examples that demonstrates the usage of the Camera System \n\
instead of the use of the lookAt function to create the view matrix. \n\
You may move the camera using the mouse or the Scenegraph. \n\n\
NOTE: To change any TRS via the ECSS GUI, only this TRS must be toggled on!\n\n\
You may see the ECS Scenegraph showing Entities & Components of the scene and \n\
various information about them. Hit ESC OR Close the window to quit." 

#Light
Lposition = util.vec(5.0, 2.0, 2.0) #uniform lightpos
Lambientcolor = util.vec(1.0, 1.0, 1.0) #uniform ambient color
Lambientstr = 0.3 #uniform ambientStr
LviewPos = util.vec(2.5, 2.8, 5.0) #uniform viewpos
Lcolor = util.vec(1.0,1.0,1.0)
Lintensity = 0.8
#Material
Mshininess = 0.4 
Mcolor = util.vec(0.8, 0.0, 0.8)

winWidth = 1200
winHeight = 800

scene = Scene()    

# Scenegraph with Entities, Components
rootEntity = scene.world.createEntity(Entity(name="RooT"))
entityCam1 = scene.world.createEntity(Entity(name="Entity1"))
scene.world.addEntityChild(rootEntity, entityCam1)
trans1 = scene.world.addComponent(entityCam1, BasicTransform(name="Entity1_TRS", trs=util.translate(0,0,-8)))

eye = util.vec(1, 0.54, 1.0)
target = util.vec(0.02, 0.14, 0.217)
up = util.vec(0.0, 1.0, 0.0)
view = util.lookat(eye, target, up)
 
projMat = util.perspective(50.0, 1.0, 1.0, 10.0)   

m = np.linalg.inv(projMat @ view)



skybox = scene.world.createEntity(Entity(name="Skybox"))
scene.world.addEntityChild(rootEntity, skybox)
transSkybox = scene.world.addComponent(skybox, BasicTransform(name="transSkybox", trs=util.identity())) #util.identity()
meshSkybox = scene.world.addComponent(skybox, RenderMesh(name="meshSkybox"))

#BASIC CUBE FOR THE SKYBOX
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


entityCam2 = scene.world.createEntity(Entity(name="Entity_Camera"))
scene.world.addEntityChild(entityCam1, entityCam2)
trans2 = scene.world.addComponent(entityCam2, BasicTransform(name="Camera_TRS", trs=util.identity()))
# orthoCam = scene.world.addComponent(entityCam2, Camera(util.ortho(-100.0, 100.0, -100.0, 100.0, 1.0, 100.0), "orthoCam","Camera","500"))
orthoCam = scene.world.addComponent(entityCam2, Camera(m, "orthoCam","Camera","500"))


# Systems
transUpdate = scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
camUpdate = scene.world.createSystem(CameraSystem("camUpdate", "CameraUpdate", "200"))
renderUpdate = scene.world.createSystem(RenderGLShaderSystem())
initUpdate = scene.world.createSystem(InitGLShaderSystem())



# Generate skybox cube
vertexSkybox, indexSkybox, _ = norm.generateUniqueVertices(vertexSkybox,indexSkybox)

meshSkybox.vertex_attributes.append(vertexSkybox)
meshSkybox.vertex_index.append(indexSkybox)
vArraySkybox = scene.world.addComponent(skybox, VertexArray())
shaderSkybox = scene.world.addComponent(skybox, ShaderGLDecorator(Shader(vertex_import_file = SHADER_DIR / "StaticSkybox.vert", fragment_import_file=SHADER_DIR / "StaticSkybox.frag")))


sphere = []
number_of_spheres = 3
#Generate Spheres with UV mapping capabilities
for i in range(number_of_spheres):
    s = UVObjectGenerator.Sphere(name=f"Sphere_{i}")
    sphere.append(s)  # ✓ Adds to the list
    scene.world.addEntityChild(rootEntity, sphere[i])



sphere[0].trans.trs = util.translate(0 , 0.25, 0) @ util.scale(1, 1, 1)
sphere[1].trans.trs = util.translate(2, 0.25, 2) @ util.scale(0.5, 0.5, 0.5)
sphere[2].trans.trs = util.translate(-2, 0.25, 2) @ util.scale(0.5, 0.5, 0.5)

# Generate Cylinder with UV mapping
cylinder = UVObjectGenerator.Cylinder(name="Cylinder")
scene.world.addEntityChild(rootEntity, cylinder)
cylinder.trans.trs = util.translate(3, 0.25, -2) @ util.scale(0.5, 1.0, 0.5)



uv_gui = UVGui()
# MAIN RENDERING LOOP

running = True
scene.init(imgui=True, windowWidth = winWidth, windowHeight = winHeight, windowTitle = "Elements: Let There Be Light", openGLversion = 4, customImGUIdecorator = ImGUIecssDecorator2)

# pre-pass scenegraph to initialise all GL context dependent geometry, shader classes
# needs an active GL context
scene.world.traverse_visit(initUpdate, scene.world.root)

################### EVENT MANAGER ###################

eManager = scene.world.eventManager
gWindow = scene.renderWindow
gGUI = scene.gContext

renderGLEventActuator = RenderGLStateSystem()


eManager._subscribers['OnUpdateWireframe'] = gWindow
eManager._actuators['OnUpdateWireframe'] = renderGLEventActuator
eManager._subscribers['OnUpdateCamera'] = gWindow 
eManager._actuators['OnUpdateCamera'] = renderGLEventActuator


eye = util.vec(2.5, 2.5, 2.5)
target = util.vec(0.0, 0.0, 0.0)
up = util.vec(0.0, 1.0, 0.0)
view = util.lookat(eye, target, up)
# projMat = util.ortho(-10.0, 10.0, -10.0, 10.0, -1.0, 10.0)  
# projMat = util.perspective(90.0, 1.33, 0.1, 100)  
projMat = util.perspective(50.0, winWidth/winHeight, 0.01, 100.0)   

gWindow._myCamera = view # otherwise, an imgui slider must be moved to properly update



# Any folder under SKYBOX_DIR works -- Cloudy, Day_Sunless, Sea, Stars.
skybox_texture_locations = SKYBOX_DIR / "Stars"
front_img = skybox_texture_locations / "front.png"
right_img = skybox_texture_locations / "right.png"
left_img = skybox_texture_locations / "left.png"
back_img = skybox_texture_locations / "back.png"
bottom_img = skybox_texture_locations / "bottom.png"
top_img = skybox_texture_locations / "top.png"


face_data = get_texture_faces(front_img,back_img,top_img,bottom_img,left_img,right_img)

shaderSkybox.setUniformVariable(key='cubemap', value=face_data, texture3D=True)


#LOAD THE TEXTURE AFTER THE OPENGL CONTEXT IS CREATED!!!!
texturePath1 = TEXTURE_DIR / "2k_sun.jpg"
texturePath2 = TEXTURE_DIR / "2k_mars.jpg"
texturePath3 = TEXTURE_DIR / "earth.jpg"
texturePath4 = TEXTURE_DIR / "2k_moon.jpg"

texture1 = Texture(texturePath1)
texture2 = Texture(texturePath2)
texture3 = Texture(texturePath3)
texture4 = Texture(texturePath4)

textures = [texture1, texture2, texture3]


for i in range(number_of_spheres):
    sphere[i].shaderDec.setUniformVariable(key='ImageTexture', value=textures[i], texture=True)

# Set cylinder texture
cylinder.shaderDec.setUniformVariable(key='ImageTexture', value=texture4, texture=True)

##############################################################
##DONE NOW THE TEXTURE IS READY TO BE USED IN THE SHADER ACCORDING TO THE UVS OF THE OBJECT##########

while running:
    running = scene.render()
    displayGUI_text(example_description)
    scene.world.traverse_visit_pre_camera(camUpdate, orthoCam)
    scene.world.traverse_visit(camUpdate, scene.world.root)
    view =  gWindow._myCamera # updates view via the imgui
    
    
    uv_gui.draw(imgui, sphere[0].trans, sphere[0].mesh.vertex_attributes[0], sphere[0].mesh, sphere[0].vArray)

    view =  gWindow._myCamera 
    for i in range(number_of_spheres):
        sphere[i].shaderDec.setUniformVariable(key='model', value=sphere[i].trans.trs, mat4=True)
        sphere[i].shaderDec.setUniformVariable(key='View', value=view, mat4=True)
        sphere[i].shaderDec.setUniformVariable(key='Proj', value=projMat, mat4=True)
        sphere[i].shaderDec.setUniformVariable(key='ambientColor',value=Lambientcolor,float3=True)
        sphere[i].shaderDec.setUniformVariable(key='ambientStr',value=Lambientstr,float1=True)
        sphere[i].shaderDec.setUniformVariable(key='viewPos',value=LviewPos,float3=True)
        sphere[i].shaderDec.setUniformVariable(key='lightPos',value=Lposition,float3=True)
        sphere[i].shaderDec.setUniformVariable(key='lightColor',value=Lcolor,float3=True)
        sphere[i].shaderDec.setUniformVariable(key='lightIntensity',value=Lintensity,float1=True)
        sphere[i].shaderDec.setUniformVariable(key='shininess',value=Mshininess,float1=True)

    # Set cylinder shader uniforms
    cylinder.shaderDec.setUniformVariable(key='model', value=cylinder.trans.trs, mat4=True)
    cylinder.shaderDec.setUniformVariable(key='View', value=view, mat4=True)
    cylinder.shaderDec.setUniformVariable(key='Proj', value=projMat, mat4=True)
    cylinder.shaderDec.setUniformVariable(key='ambientColor',value=Lambientcolor,float3=True)
    cylinder.shaderDec.setUniformVariable(key='ambientStr',value=Lambientstr,float1=True)
    cylinder.shaderDec.setUniformVariable(key='viewPos',value=LviewPos,float3=True)
    cylinder.shaderDec.setUniformVariable(key='lightPos',value=Lposition,float3=True)
    cylinder.shaderDec.setUniformVariable(key='lightColor',value=Lcolor,float3=True)
    cylinder.shaderDec.setUniformVariable(key='lightIntensity',value=Lintensity,float1=True)
    cylinder.shaderDec.setUniformVariable(key='shininess',value=Mshininess,float1=True)

    shaderSkybox.setUniformVariable(key='Proj', value=projMat, mat4=True)
    shaderSkybox.setUniformVariable(key='View', value=view, mat4=True)

    scene.world.traverse_visit(renderUpdate, scene.world.root) 
    scene.render_post()
    
scene.shutdown()