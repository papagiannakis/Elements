import numpy as np

import Elements.pyECSS.utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, RenderMesh
from Elements.pyECSS.System import  TransformSystem
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GUI.Viewer import RenderGLStateSystem

from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray
from Elements.pyGLV.utils.terrain import generateTerrain

#from OpenGL.GL import GL_LINES
from OpenGL.GL import GL_LINES
from OpenGL.GL import GL_POINTS

import OpenGL.GL as gl

import Elements.pyGLV.voronoi.voronoi as voronoi

import random
#gl.glPointSize(1.)



scene = Scene()    

# Scenegraph with Entities, Components
rootEntity = scene.world.createEntity(Entity(name="RooT"))
entityCam1 = scene.world.createEntity(Entity(name="entityCam1"))
scene.world.addEntityChild(rootEntity, entityCam1)
trans1 = scene.world.addComponent(entityCam1, BasicTransform(name="trans1", trs=util.identity()))

node4 = scene.world.createEntity(Entity(name="node4"))
scene.world.addEntityChild(rootEntity, node4)
trans4 = scene.world.addComponent(node4, BasicTransform(name="trans4", trs=util.identity())) #util.identity()
mesh4 = scene.world.addComponent(node4, RenderMesh(name="mesh4"))

# Systems
transUpdate = scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
# camUpdate = scene.world.createSystem(CameraSystem("camUpdate", "CameraUpdate", "200"))
renderUpdate = scene.world.createSystem(RenderGLShaderSystem())
initUpdate = scene.world.createSystem(InitGLShaderSystem())

# Create Voronoi Diagram. Mesh and Points.
samplepoints = voronoi.random_points_in_square(10,1.0)
mesh_vertices, mesh_indices, mesh_color, point_list, point_indices, point_colors = voronoi.voronoi_diagram(samplepoints)

## ADD Voronoi Colors ##
# attach a simple cube in a RenderMesh so that VertexArray can pick it up
mesh4.vertex_attributes.append(mesh_vertices)
mesh4.vertex_attributes.append(mesh_color)
mesh4.vertex_index.append(mesh_indices)
vArray4 = scene.world.addComponent(node4, VertexArray())
shaderDec4 = scene.world.addComponent(node4, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))

## ADD POINTS ##
points = scene.world.createEntity(Entity(name="points"))
scene.world.addEntityChild(rootEntity, points)
points_trans = scene.world.addComponent(points, BasicTransform(name="points_trans", trs=util.identity()))
points_mesh = scene.world.addComponent(points, RenderMesh(name="points_mesh"))
points_mesh.vertex_attributes.append(point_list)
points_mesh.vertex_attributes.append(point_colors)
points_mesh.vertex_index.append(point_indices)
points_vArray = scene.world.addComponent(points, VertexArray(primitive=GL_POINTS)) # note the primitive change
points_shader = scene.world.addComponent(points, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))


# MAIN RENDERING LOOP

running = True
scene.init(imgui=True, windowWidth = 1024, windowHeight = 768, windowTitle = "Elements: A Working Event Manager", openGLversion = 4)
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



eye = util.vec(.5, .5, 1.5)
target = util.vec(0.5, 0.5, 0.0)
up = util.vec(0.0, 1.0, 0.0)
view = util.lookat(eye, target, up)

projMat = util.perspective(50.0, 1.0, 0.01, 10.0)

gWindow._myCamera = view # otherwise, an imgui slider must be moved to properly update


model_cube = trans4.trs


model_terrain_axes = util.translate(0.0,0.0,0.0) ## COMPLETELY OVERRIDE OBJECT's TRS

while running:
    running = scene.render(running)
    scene.world.traverse_visit(renderUpdate, scene.world.root)
    view =  gWindow._myCamera # updates view via the imgui
    mvp_cube = projMat @ view @ model_cube
    mvp_terrain_axes = projMat @ view @ model_terrain_axes
    points_shader.setUniformVariable(key='modelViewProj', value=mvp_terrain_axes, mat4=True)
    shaderDec4.setUniformVariable(key='modelViewProj', value=mvp_cube, mat4=True)
    scene.render_post()
    
scene.shutdown()