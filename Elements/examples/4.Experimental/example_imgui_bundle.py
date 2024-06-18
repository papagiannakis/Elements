import numpy as np
import os
import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, RenderMesh
from Elements.pyECSS.System import  TransformSystem
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GUI.Viewer import RenderGLStateSystem
from Elements.pyGLV.GUI.ImguiDecorator import IMGUIecssDecoratorBundle

from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray
import Elements.utils.normals as norm
from Elements.pyGLV.GL.Textures import get_texture_faces, get_single_texture_faces
from Elements.pyGLV.GL.Textures import Texture

from Elements.definitions import TEXTURE_DIR
from Elements.utils.Shortcuts import displayGUI_text


example_description = \
"This example's aim is to demostrate the latest additions \n\
to the framework of Elements"

Lposition = util.vec(5.0, 2.0, 2.0) #uniform lightpos
Lambientcolor = util.vec(1.0, 1.0, 1.0) #uniform ambient color
Lambientstr = 0.2 #uniform ambientStr
LviewPos = util.vec(2.5, 2.8, 5.0) #uniform viewpos
Lcolor = util.vec(1.0,1.0,1.0)
Lintensity = 0.8
#Material
Mshininess = 0.8 
Mcolor = util.vec(0.8, 0.0, 0.8)

winWidth = 1024
winHeight = 768

eye = util.vec(1, 0.54, 1.0)
target = util.vec(0.02, 0.14, 0.217)
up = util.vec(0.0, 1.0, 0.0)
view = util.lookat(eye, target, up)
projMat = util.perspective(50.0, 1.0, 1.0, 10.0)   

# Scenegraph with Entities, Components
scene = Scene()    
rootEntity = scene.world.createEntity(Entity(name="Root"))

skybox = scene.world.createEntity(Entity(name="Skybox"))
scene.world.addEntityChild(rootEntity, skybox)
transSkybox = scene.world.addComponent(skybox, BasicTransform(name="transSkybox", trs=util.identity())) #util.identity()
meshSkybox = scene.world.addComponent(skybox, RenderMesh(name="meshSkybox"))

red = scene.world.createEntity(Entity(name="Red"))
scene.world.addEntityChild(rootEntity, red)
trans4_red = scene.world.addComponent(red, BasicTransform(name="trans4_red", trs=util.identity() @ util.translate(3, 0, 3))) #util.identity()
mesh4_red = scene.world.addComponent(red, RenderMesh(name="mesh4_red"))

yellow = scene.world.createEntity(Entity(name="Yellow"))
scene.world.addEntityChild(rootEntity, yellow)
trans4_yellow = scene.world.addComponent(yellow, BasicTransform(name="trans4", trs=util.identity() @ util.translate(-3, 0, 3))) #util.identity()
mesh4_yellow = scene.world.addComponent(yellow, RenderMesh(name="mesh4"))

blue = scene.world.createEntity(Entity(name="Blue"))
scene.world.addEntityChild(rootEntity, blue)
trans4_blue = scene.world.addComponent(blue, BasicTransform(name="trans4_blue", trs=util.identity() @ util.translate(3, 0, -3))) #util.identity()
mesh4_blue = scene.world.addComponent(blue, RenderMesh(name="mesh4_blue"))

green = scene.world.createEntity(Entity(name="Green"))
scene.world.addEntityChild(rootEntity, green)
trans4_green = scene.world.addComponent(green, BasicTransform(name="trans4_green", trs=util.identity() @ util.translate(-3, 0, -3))) #util.identity()
mesh4_green = scene.world.addComponent(green, RenderMesh(name="mesh4_green"))

uoc = scene.world.createEntity(Entity(name="UOC"))
scene.world.addEntityChild(rootEntity, uoc)
trans4_uoc = scene.world.addComponent(uoc, BasicTransform(name="trans4_uoc", trs=util.identity())) #util.identity()
mesh4_uoc = scene.world.addComponent(uoc, RenderMesh(name="mesh4_uoc"))

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

colorRed = np.array([
    [1.0, 0.0, 0.0, 1.0],
    [1.0, 0.0, 0.0, 1.0],
    [1.0, 0.0, 0.0, 1.0],
    [1.0, 0.0, 0.0, 1.0],
    [1.0, 0.0, 0.0, 1.0],
    [1.0, 0.0, 0.0, 1.0],
    [1.0, 0.0, 0.0, 1.0],
    [1.0, 0.0, 0.0, 1.0]
], dtype=np.float32)

colorYellow = np.array([
    [1.0, 0.0, 1.0, 1.0],
    [1.0, 0.0, 1.0, 1.0],
    [1.0, 0.0, 1.0, 1.0],
    [1.0, 0.0, 1.0, 1.0],
    [1.0, 0.0, 1.0, 1.0],
    [1.0, 0.0, 1.0, 1.0],
    [1.0, 0.0, 1.0, 1.0],
    [1.0, 0.0, 1.0, 1.0]
], dtype=np.float32)

colorGreen = np.array([
    [0.0, 1.0, 0.0, 1.0],
    [0.0, 1.0, 0.0, 1.0],
    [0.0, 1.0, 0.0, 1.0],
    [0.0, 1.0, 0.0, 1.0],
    [0.0, 1.0, 0.0, 1.0],
    [0.0, 1.0, 0.0, 1.0],
    [0.0, 1.0, 0.0, 1.0],
    [0.0, 1.0, 0.0, 1.0]
], dtype=np.float32)

colorBlue = np.array([
    [0.0, 0.0, 1.0, 1.0],
    [0.0, 0.0, 1.0, 1.0],
    [0.0, 0.0, 1.0, 1.0],
    [0.0, 0.0, 1.0, 1.0],
    [0.0, 0.0, 1.0, 1.0],
    [0.0, 0.0, 1.0, 1.0],
    [0.0, 0.0, 1.0, 1.0],
    [0.0, 0.0, 1.0, 1.0]
], dtype=np.float32)

#index Array for Cube
indexCube = np.array((1,0,3, 1,3,2, 
                  2,3,7, 2,7,6,
                  3,0,4, 3,4,7,
                  6,5,1, 6,1,2,
                  4,5,6, 4,6,7,
                  5,4,0, 5,0,1), np.uint32) #rhombus out of two triangles

# Systems
transUpdate = scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
renderUpdate = scene.world.createSystem(RenderGLShaderSystem())
initUpdate = scene.world.createSystem(InitGLShaderSystem())

# SKYBOX
meshSkybox.vertex_attributes.append(vertexSkybox)
meshSkybox.vertex_index.append(indexSkybox)
vArraySkybox = scene.world.addComponent(skybox, VertexArray())
shaderSkybox = scene.world.addComponent(skybox, ShaderGLDecorator(Shader(vertex_source = Shader.STATIC_SKYBOX_VERT, fragment_source=Shader.STATIC_SKYBOX_FRAG)))

# COLORED CUBES
vertices, indices, colors, normals = norm.generateSmoothNormalsMesh(vertexCube , indexCube, colorRed)
mesh4_red.vertex_attributes.append(vertices)
mesh4_red.vertex_attributes.append(colors)
mesh4_red.vertex_attributes.append(normals)
mesh4_red.vertex_index.append(indices)
vArray4_red = scene.world.addComponent(red, VertexArray())
shaderDec4_red = scene.world.addComponent(red, ShaderGLDecorator(Shader(vertex_source = Shader.VERT_PHONG_MVP, fragment_source=Shader.FRAG_PHONG)))

vertices, indices, colors, normals = norm.generateSmoothNormalsMesh(vertexCube , indexCube, colorYellow)
mesh4_yellow.vertex_attributes.append(vertices)
mesh4_yellow.vertex_attributes.append(colors)
mesh4_yellow.vertex_attributes.append(normals)
mesh4_yellow.vertex_index.append(indices)
vArray4_yellow = scene.world.addComponent(yellow, VertexArray())
shaderDec4_yellow = scene.world.addComponent(yellow, ShaderGLDecorator(Shader(vertex_source = Shader.VERT_PHONG_MVP, fragment_source=Shader.FRAG_PHONG)))

vertices, indices, colors, normals = norm.generateSmoothNormalsMesh(vertexCube , indexCube, colorBlue)
mesh4_blue.vertex_attributes.append(vertices)
mesh4_blue.vertex_attributes.append(colors)
mesh4_blue.vertex_attributes.append(normals)
mesh4_blue.vertex_index.append(indices)
vArray4_blue = scene.world.addComponent(blue, VertexArray())
shaderDec4_blue = scene.world.addComponent(blue, ShaderGLDecorator(Shader(vertex_source = Shader.VERT_PHONG_MVP, fragment_source=Shader.FRAG_PHONG)))

vertices, indices, colors, normals = norm.generateSmoothNormalsMesh(vertexCube , indexCube, colorGreen)
mesh4_green.vertex_attributes.append(vertices)
mesh4_green.vertex_attributes.append(colors)
mesh4_green.vertex_attributes.append(normals)
mesh4_green.vertex_index.append(indices)
vArray4_green = scene.world.addComponent(green, VertexArray())
shaderDec4_green = scene.world.addComponent(green, ShaderGLDecorator(Shader(vertex_source = Shader.VERT_PHONG_MVP, fragment_source=Shader.FRAG_PHONG)))

# TEXTURED CUBE
vertices, indices, _, normals = norm.generateFlatNormalsMesh(vertexCube , indexCube)

mesh4_uoc.vertex_attributes.append(vertices)
mesh4_uoc.vertex_attributes.append(normals)
mesh4_uoc.vertex_attributes.append(Texture.CUBE_TEX_COORDINATES)
mesh4_uoc.vertex_index.append(indices)
vArray4_uoc = scene.world.addComponent(uoc, VertexArray())
shaderDec4_uoc = scene.world.addComponent(uoc, ShaderGLDecorator(Shader(vertex_source = Shader.SIMPLE_TEXTURE_PHONG_VERT, fragment_source=Shader.SIMPLE_TEXTURE_PHONG_FRAG)))


# MAIN RENDERING LOOP

running = True
scene.init(imgui=True, windowWidth = winWidth, windowHeight = winHeight, windowTitle = "Elements: IMGUI Bundle Example", customImGUIdecorator = IMGUIecssDecoratorBundle, openGLversion = 4)


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
projMat = util.perspective(50.0, 1.0, 0.01, 100.0)   

gWindow._myCamera = view # otherwise, an imgui slider must be moved to properly update

# skybox_texture_locations = TEXTURE_DIR / "Skyboxes" / "Cloudy"
skybox_texture_locations = TEXTURE_DIR / "Skyboxes" / "Sea"
front_img = skybox_texture_locations / "front.jpg"
right_img = skybox_texture_locations / "right.jpg"
left_img = skybox_texture_locations / "left.jpg"
back_img = skybox_texture_locations / "back.jpg"
bottom_img = skybox_texture_locations / "bottom.jpg"
top_img = skybox_texture_locations / "top.jpg"

face_data = get_texture_faces(front_img,back_img,top_img,bottom_img,left_img,right_img)
shaderSkybox.setUniformVariable(key='cubemap', value=face_data, texture3D=True)

texturePath = TEXTURE_DIR / "uoc_logo.png"
texture = Texture(texturePath)
shaderDec4_uoc.setUniformVariable(key='ImageTexture', value=texture, texture=True)

while running:
    running = scene.render()
    displayGUI_text(example_description)
    scene.world.traverse_visit(transUpdate, scene.world.root)    
    
    view =  gWindow._myCamera # updates view via the imgui

    # scene.world.update_entity_values(rootEntity, winWidth, winHeight);
    scene.world.update_entity_values(rootEntity, winWidth, winHeight, True, Lambientcolor, Lambientstr, LviewPos, Lposition, Lcolor, Lintensity, Mshininess)
   
    scene.world.traverse_visit(renderUpdate, scene.world.root) 
    
    scene.render_post()

scene.shutdown()