
import os
import numpy as np

import Elements.pyECSS.utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, Camera, RenderMesh
from Elements.pyECSS.System import TransformSystem, CameraSystem
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GUI.Viewer import RenderGLStateSystem, ImGUIecssDecorator

from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray

from OpenGL.GL import GL_LINES
import OpenGL.GL as gl

import Elements.pyGLV.utils.normals as norm
from Elements.pyGLV.utils.terrain import generateTerrain
from Elements.pyGLV.utils.obj_to_mesh import obj_to_mesh

#Task code
from Elements.pyGLV.Slicing import Slicing



#Light
Lposition = util.vec(2.0, 5.5, 2.0) #uniform lightpos
Lambientcolor = util.vec(1.0, 1.0, 1.0) #uniform ambient color
Lambientstr = 0.3 #uniform ambientStr
LviewPos = util.vec(2.5, 2.8, 5.0) #uniform viewpos
Lcolor = util.vec(1.0,1.0,1.0)
Lintensity = 0.8
#Material
Mshininess = 0.4 
Mcolor = util.vec(0.8, 0.0, 0.8)


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
# projMat = util.ortho(-10.0, 10.0, -10.0, 10.0, -1.0, 10.0)  
# projMat = util.perspective(90.0, 1.33, 0.1, 100)  
projMat = util.perspective(50.0, 1.0, 1.0, 10.0)   

m = np.linalg.inv(projMat @ view)


entityCam2 = scene.world.createEntity(Entity(name="Entity_Camera"))
scene.world.addEntityChild(entityCam1, entityCam2)
trans2 = scene.world.addComponent(entityCam2, BasicTransform(name="Camera_TRS", trs=util.identity()))
# orthoCam = scene.world.addComponent(entityCam2, Camera(util.ortho(-100.0, 100.0, -100.0, 100.0, 1.0, 100.0), "orthoCam","Camera","500"))
orthoCam = scene.world.addComponent(entityCam2, Camera(m, "orthoCam","Camera","500"))

node4 = scene.world.createEntity(Entity(name="Object"))
scene.world.addEntityChild(rootEntity, node4)
trans4 = scene.world.addComponent(node4, BasicTransform(name="Object_TRS", trs=util.identity() ))
mesh4 = scene.world.addComponent(node4, RenderMesh(name="Object_mesh"))

# a simple triangle
vertexData = np.array([
    [0.0, 0.0, 0.0, 1.0],
    [0.5, 1.0, 0.0, 1.0],
    [1.0, 0.0, 0.0, 1.0]
],dtype=np.float32) 
colorVertexData = np.array([
    [1.0, 0.0, 0.0, 0.0],
    [0.0, 1.0, 0.0, 1.0],
    [0.0, 0.0, 1.0, 1.0]
], dtype=np.float32)

#Colored Axes
vertexAxes = np.array([
    [0.0, 0.0, 0.0, 1.0],
    [1.5, 0.0, 0.0, 1.0],
    [0.0, 0.0, 0.0, 1.0],
    [0.0, 1.5, 0.0, 1.0],
    [0.0, 0.0, 0.0, 1.0],
    [0.0, 0.0, 1.5, 1.0]
],dtype=np.float32) 
colorAxes = np.array([
    [1.0, 0.0, 0.0, 1.0],
    [1.0, 0.0, 0.0, 1.0],
    [0.0, 1.0, 0.0, 1.0],
    [0.0, 1.0, 0.0, 1.0],
    [0.0, 0.0, 1.0, 1.0],
    [0.0, 0.0, 1.0, 1.0]
], dtype=np.float32)


#index arrays for above vertex Arrays
index = np.array((0,1,2), np.uint32) #simple triangle
indexAxes = np.array((0,1,2,3,4,5), np.uint32) #3 simple colored Axes as R,G,B lines


# Systems
transUpdate = scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
camUpdate = scene.world.createSystem(CameraSystem("camUpdate", "CameraUpdate", "200"))
renderUpdate = scene.world.createSystem(RenderGLShaderSystem())
initUpdate = scene.world.createSystem(InitGLShaderSystem())



## object load 
dirname = os.path.dirname(__file__)

# NOTICE THAT OBJECTS WITH UVs are currently NOT SUPPORTED
# obj_to_import = os.path.join(dirname, "models", "teapot.obj")
obj_to_import = os.path.join(dirname, "models", "cow.obj")
# obj_to_import = os.path.join(dirname, "models", "teddy.obj")


### Load and translate mesh.
obj_color = [168/255, 168/255 , 210/255, 1.0]
vert , ind, col = obj_to_mesh(obj_to_import, color=obj_color)

# Find boundingbox and translate half of the z-dimension to make room for the contours
upper = Slicing.get_highest_coords(vert)
lower = Slicing.get_lowest_coords(vert)
z_diff = upper[2]-lower[2]
vertices, indices, colors, normals = norm.generateSmoothNormalsMesh(vert , ind, col)
slice_vertices = Slicing.translate_z(vertices,-(z_diff/2))
vertices = Slicing.translate_z(vertices, z_diff/2)


mesh4.vertex_attributes.append(vertices)
mesh4.vertex_attributes.append(colors)
mesh4.vertex_attributes.append(normals)
mesh4.vertex_index.append(indices)
vArray4 = scene.world.addComponent(node4, VertexArray())
shaderDec4 = scene.world.addComponent(node4, ShaderGLDecorator(Shader(vertex_source = Shader.VERT_PHONG_MVP, fragment_source=Shader.FRAG_PHONG)))

###
contours_vertices = Slicing.create_contours(slice_vertices,indices,.025)
contours_color = np.array([(1.,1.,1.,1.)] * len(contours_vertices))
contours_indices = np.array(range(len(contours_vertices)))

## ADD CONTOURS ##
contours = scene.world.createEntity(Entity(name="contours"))
scene.world.addEntityChild(rootEntity, contours)
contours_trans = scene.world.addComponent(contours, BasicTransform(name="contours_trans", trs=util.identity()))
contours_mesh = scene.world.addComponent(contours, RenderMesh(name="contours_mesh"))
contours_mesh.vertex_attributes.append(contours_vertices) 
contours_mesh.vertex_attributes.append(contours_color)
contours_mesh.vertex_index.append(contours_indices)
contours_vArray = scene.world.addComponent(contours, VertexArray(primitive=GL_LINES)) # note the primitive change
contours_shader = scene.world.addComponent(contours, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))


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

## ADD AXES ##
axes = scene.world.createEntity(Entity(name="axes"))
scene.world.addEntityChild(rootEntity, axes)
axes_trans = scene.world.addComponent(axes, BasicTransform(name="axes_trans", trs=util.translate(0.0, 0.001, 0.0))) #util.identity()
axes_mesh = scene.world.addComponent(axes, RenderMesh(name="axes_mesh"))
axes_mesh.vertex_attributes.append(vertexAxes) 
axes_mesh.vertex_attributes.append(colorAxes)
axes_mesh.vertex_index.append(indexAxes)
axes_vArray = scene.world.addComponent(axes, VertexArray(primitive=gl.GL_LINES)) # note the primitive change

# shaderDec_axes = scene.world.addComponent(axes, Shader())
# OR
axes_shader = scene.world.addComponent(axes, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))
# axes_shader.setUniformVariable(key='modelViewProj', value=mvpMat, mat4=True)


# MAIN RENDERING LOOP

running = True
scene.init(imgui=True, windowWidth = 1200, windowHeight = 800, windowTitle = "Elements: Tea anyone?", openGLversion = 4, customImGUIdecorator = ImGUIecssDecorator)

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


eye = util.vec(10, 10, 10)
target = util.vec(0.0, 0.0, 0.0)
up = util.vec(0.0, 1.0, 0.0)
view = util.lookat(eye, target, up)
# projMat = util.ortho(-10.0, 10.0, -10.0, 10.0, -1.0, 10.0)  
# projMat = util.perspective(90.0, 1.33, 0.1, 100)  
projMat = util.perspective(50.0, 1200/800, 0.01, 100.0)   

gWindow._myCamera = view # otherwise, an imgui slider must be moved to properly update

model_terrain_axes = util.translate(0.0,0.0,0.0)
model_cube = util.translate(0.0,0.5,0.0)



while running:
    running = scene.render(running)
    scene.world.traverse_visit(renderUpdate, scene.world.root)
    scene.world.traverse_visit_pre_camera(camUpdate, orthoCam)
    scene.world.traverse_visit(camUpdate, scene.world.root)
    view =  gWindow._myCamera # updates view via the imgui
    # mvp_cube = projMat @ view @ model_cube
    mvp_cube = projMat @ view @ trans4.trs
    mvp_terrain = projMat @ view @ terrain_trans.trs
    mvp_axes = projMat @ view @ axes_trans.trs
    axes_shader.setUniformVariable(key='modelViewProj', value=mvp_axes, mat4=True)
    contours_shader.setUniformVariable(key='modelViewProj', value=mvp_axes, mat4=True)
    terrain_shader.setUniformVariable(key='modelViewProj', value=mvp_terrain, mat4=True)

    shaderDec4.setUniformVariable(key='modelViewProj', value=mvp_cube, mat4=True)
    shaderDec4.setUniformVariable(key='model',value=model_cube,mat4=True)
    shaderDec4.setUniformVariable(key='ambientColor',value=Lambientcolor,float3=True)
    shaderDec4.setUniformVariable(key='ambientStr',value=Lambientstr,float1=True)
    shaderDec4.setUniformVariable(key='viewPos',value=LviewPos,float3=True)
    shaderDec4.setUniformVariable(key='lightPos',value=Lposition,float3=True)
    shaderDec4.setUniformVariable(key='lightColor',value=Lcolor,float3=True)
    shaderDec4.setUniformVariable(key='lightIntensity',value=Lintensity,float1=True)
    shaderDec4.setUniformVariable(key='shininess',value=Mshininess,float1=True)
    shaderDec4.setUniformVariable(key='matColor',value=Mcolor,float3=True)


    scene.render_post()
    
scene.shutdown()



