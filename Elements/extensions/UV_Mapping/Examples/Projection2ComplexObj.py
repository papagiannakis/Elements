import os
import random
import numpy as np

from Elements.definitions import MODEL_DIR, TEXTURE_DIR
import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, Camera, RenderMesh
from Elements.pyECSS.System import TransformSystem, CameraSystem
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GUI.Viewer import RenderGLStateSystem
from Elements.pyGLV.GUI.ImguiDecorator import ImGUIecssDecorator2

from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray

from OpenGL.GL import GL_LINES
import OpenGL.GL as gl
import imgui

import Elements.utils.normals as norm
from Elements.utils.terrain import generateTerrain
from Elements.utils.obj_to_mesh import obj_to_mesh

from Elements.utils.Shortcuts import displayGUI_text
from Elements.extensions.UV_Mapping.ObjectGenerator import UVObjectGenerator
from Elements.extensions.UV_Mapping.Gui import UVGui
from Elements.extensions.UV_Mapping import ObjectGenerator
from build.lib.Elements.pyGLV.GL.Textures import Texture, get_texture_faces


#from Elements.extensions.UV_Mapping.TextureMapping import TextureGUI
example_description = \
"This is the  examples demonstates the two-step UV mapping onto a complex object.  " \
"\n\The Seam moves with the offset U value. WE can watch it move throught the object and how it interacts with it." \

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

obj = scene.world.createEntity(Entity(name="Object"))
scene.world.addEntityChild(rootEntity, obj)
obj_trans = scene.world.addComponent(obj, BasicTransform(name="Object_TRS", trs=util.scale(0.1, 0.1, 0.1) ))
obj_mesh = scene.world.addComponent(obj, RenderMesh(name="Object_mesh"))

eye = util.vec(1, 0.54, 1.0)
target = util.vec(0.02, 0.14, 0.217)
up = util.vec(0.0, 1.0, 0.0)
view = util.lookat(eye, target, up)
 
projMat = util.perspective(50.0, 1.0, 1.0, 10.0)   

m = np.linalg.inv(projMat @ view)




# Generate terrain

vertexTerrain, indexTerrain, colorTerrain= generateTerrain(size=4,N=20)
# Add terrain
terrain = scene.world.createEntity(Entity(name="terrain"))
scene.world.addEntityChild(rootEntity, terrain)
terrain_trans = scene.world.addComponent(terrain, BasicTransform(name="terrain_trans", trs=util.identity()))
terrain_mesh = scene.world.addComponent(terrain, RenderMesh(name="terrain_mesh"))
terrain_mesh.vertex_attributes.append(vertexTerrain) 
terrain_mesh.vertex_attributes.append(colorTerrain)
terrain_mesh.vertex_index.append(indexTerrain)
terrain_vArray = scene.world.addComponent(terrain, VertexArray(primitive=GL_LINES))
terrain_shader = scene.world.addComponent(terrain, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))
# terrain_shader.setUniformVariable(key='modelViewProj', value=mvpMat, mat4=True)



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




## object load 
# NOTICE THAT OBJECTS WITH UVs are currently NOT SUPPORTED
# obj_to_import = MODEL_DIR / "teapot.obj"
#obj_to_import = MODEL_DIR / "obj.obj"
obj_to_import = MODEL_DIR / "teddy.obj"

obj_color = [168/255, 168/255 , 210/255, 1.0]
vert , ind, col = obj_to_mesh(obj_to_import, color=obj_color)
vertices, indices, colors, normals = norm.generateSmoothNormalsMesh(vert , ind, col)

# Auto-detect and apply correct UV projection
uvs, proj_type = UVObjectGenerator.AutoProjectUV(vertices, return_type=True)
print(f"Object detected as: {proj_type}")  # See which projection was chosen


obj_mesh.vertex_attributes.append(vertices)
obj_mesh.vertex_attributes.append(normals)
obj_mesh.vertex_attributes.append(uvs)

obj_mesh.vertex_index.append(indices)
vArray4 = scene.world.addComponent(obj, VertexArray())
shaderDec4 = scene.world.addComponent(obj, ShaderGLDecorator(Shader(vertex_source = ObjectGenerator.TEXTURE_VERT, fragment_source=ObjectGenerator.TEXTURE_FRAG)))


uv_gui = UVGui()

# MAIN RENDERING LOOP

running = True
scene.init(imgui=True, windowWidth = winWidth, windowHeight = winHeight, windowTitle = "Two-Step UV Mapping onto a Complex Object", openGLversion = 4, customImGUIdecorator = ImGUIecssDecorator2)

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

model_terrain_axes = util.translate(0.0,-1.8,0.0)
terrain_trans.trs = model_terrain_axes


texture = Texture(TEXTURE_DIR / "fur.jpg")
shaderDec4.setUniformVariable(key='ImageTexture', value=texture, texture=True)

model_cube = util.scale(0.1) @ util.translate(0.0,0.5,0.0)


##############################################################
##DONE NOW THE TEXTURE IS READY TO BE USED IN THE SHADER ACCORDING TO THE UVS OF THE OBJECT##########

while running:
    running = scene.render()
    displayGUI_text(example_description)
    
    # Draw the UV texture control GUI
    uv_gui.draw(imgui, obj_trans, vertices, obj_mesh, vArray4)
    
    scene.world.traverse_visit_pre_camera(camUpdate, orthoCam)
    scene.world.traverse_visit(camUpdate, scene.world.root)
    
    mvp_terrain = projMat @ view @ terrain_trans.trs
    view =  gWindow._myCamera # updates view via the imgui
    
    terrain_shader.setUniformVariable(key='modelViewProj', value=mvp_terrain, mat4=True)

    
    shaderDec4.setUniformVariable(key='model', value=obj_trans.trs, mat4=True)
    shaderDec4.setUniformVariable(key='View', value=view, mat4=True)
    shaderDec4.setUniformVariable(key='Proj', value=projMat, mat4=True)
    shaderDec4.setUniformVariable(key='ambientColor',value=Lambientcolor,float3=True)
    shaderDec4.setUniformVariable(key='ambientStr',value=Lambientstr,float1=True)
    shaderDec4.setUniformVariable(key='viewPos',value=LviewPos,float3=True)
    shaderDec4.setUniformVariable(key='lightPos',value=Lposition,float3=True)
    shaderDec4.setUniformVariable(key='lightColor',value=Lcolor,float3=True)
    shaderDec4.setUniformVariable(key='lightIntensity',value=Lintensity,float1=True)
    shaderDec4.setUniformVariable(key='shininess',value=Mshininess,float1=True)
    shaderDec4.setUniformVariable(key='matColor',value=Mcolor,float3=True)


    scene.world.traverse_visit(renderUpdate, scene.world.root) 
    scene.render_post()
    
scene.shutdown()