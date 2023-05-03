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

from scipy.spatial import Voronoi

from OpenGL.GL import GL_LINES
from OpenGL.GL import GL_POINTS

import OpenGL.GL as gl


import random
#gl.glPointSize(1.)


def random_points_in_square(n, side_length):
    points = []
    for i in range(n):
        x = random.uniform(0, side_length)
        y = random.uniform(0, side_length)
        points.append((x, y))
    return points

def add_third_coordinate(points):
    return [(x, y, 0, 1) for x, y in points]


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

node4 = scene.world.createEntity(Entity(name="node4"))
scene.world.addEntityChild(rootEntity, node4)
trans4 = scene.world.addComponent(node4, BasicTransform(name="trans4", trs=util.identity())) #util.identity()
mesh4 = scene.world.addComponent(node4, RenderMesh(name="mesh4"))

axes = scene.world.createEntity(Entity(name="axes"))
scene.world.addEntityChild(rootEntity, axes)
axes_trans = scene.world.addComponent(axes, BasicTransform(name="axes_trans", trs=util.identity()))
axes_mesh = scene.world.addComponent(axes, RenderMesh(name="axes_mesh"))

points = scene.world.createEntity(Entity(name="points"))
scene.world.addEntityChild(rootEntity,points)
points_trans = scene.world.addComponent(points, BasicTransform(name="points_trans", trs=util.identity()))
points_mesh = scene.world.addComponent(points, RenderMesh(name="points_mesh"))

#Colored Axes
vertexAxes = np.array([
    [0.0, 0.0, 0.0, 1.0],
    [1.0, 0.0, 0.0, 1.0],
    [0.0, 0.0, 0.0, 1.0],
    [0.0, 1.0, 0.0, 1.0],
    [0.0, 0.0, 0.0, 1.0],
    [0.0, 0.0, 1.0, 1.0]
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
indexAxes = np.array((0,1,2,3,4,5), np.uint32) #3 simple colored Axes as R,G,B lines

### Generate Random Points
point_list = random_points_in_square(100,1)

point_list.append([.5,5])
point_list.append([.5,-5])
point_list.append([5,.5])
point_list.append([-5,.5])

vor = Voronoi(point_list)
vertices = add_third_coordinate(vor.vertices)
voronoi = []

for region in vor.regions:
    for i in range(len(region)):
        pair = (region[i], region[(i+1) % len(region)])
        if pair[0] != -1 and pair[1] != -1:
            voronoi.append(vertices[pair[0]])
            voronoi.append(vertices[pair[1]])

colors = np.array([(1.,1.,1.,1.)] * len(voronoi))
voronoi = np.array(voronoi)
indices = np.array(range(len(voronoi)))

### Mesh for colored faces. Pick relevant regions.
relevant_regions =[]
for region in vor.regions:
    if not (-1 in region) and len(region) != 0:
        relevant_regions.append(region)
#use same vertices.
mesh_vertices = []
mesh_indices = []
mesh_color = []

for region in relevant_regions:
    color = list(np.random.choice(range(256), size=4))
    color[0] = color[0]/256.
    color[1] = color[1]/256.
    color[2] = color[2]/256.
    color[3] = 1.
    print(color)
    for i in range(1,len(region)-1):
        tri = (region[0], region[(i)], region[(i+1)])
        mesh_vertices.append(vertices[tri[0]])
        mesh_vertices.append(vertices[tri[1]])
        mesh_vertices.append(vertices[tri[2]])
        mesh_color.append(color)
        mesh_color.append(color)
        mesh_color.append(color)
        
mesh_indices = np.array(range(len(mesh_vertices)))

print(len(mesh_indices))
print(len(mesh_color))


# For point rendering
point_list = np.array(add_third_coordinate(point_list))
for i in range(len(point_list)):
    point_list[i][2] = 0.01
point_colors = np.array([(0.,0.,0.,1.)] * len(point_list))
point_indices = np.array(range(len(point_list)))

# Systems
transUpdate = scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
# camUpdate = scene.world.createSystem(CameraSystem("camUpdate", "CameraUpdate", "200"))
renderUpdate = scene.world.createSystem(RenderGLShaderSystem())
initUpdate = scene.world.createSystem(InitGLShaderSystem())


## ADD Voronoi Colors ##
# attach a simple cube in a RenderMesh so that VertexArray can pick it up
mesh4.vertex_attributes.append(mesh_vertices)
mesh4.vertex_attributes.append(mesh_color)
mesh4.vertex_index.append(mesh_indices)
vArray4 = scene.world.addComponent(node4, VertexArray())
shaderDec4 = scene.world.addComponent(node4, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))



# Generate terrain
vertexTerrain, indexTerrain, colorTerrain= generateTerrain(size=4,N=20)
# Add terrain
terrain = scene.world.createEntity(Entity(name="terrain"))
scene.world.addEntityChild(rootEntity, terrain)
terrain_trans = scene.world.addComponent(terrain, BasicTransform(name="terrain_trans", trs=util.identity()))
terrain_mesh = scene.world.addComponent(terrain, RenderMesh(name="terrain_mesh"))
#terrain_mesh.vertex_attributes.append(vertexTerrain) 
#terrain_mesh.vertex_attributes.append(colorTerrain)
#terrain_mesh.vertex_index.append(indexTerrain)
terrain_vArray = scene.world.addComponent(terrain, VertexArray(primitive=GL_LINES))
terrain_shader = scene.world.addComponent(terrain, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))
# terrain_shader.setUniformVariable(key='modelViewProj', value=mvpMat, mat4=True)

## ADD AXES ##
axes = scene.world.createEntity(Entity(name="axes"))
scene.world.addEntityChild(rootEntity, axes)
axes_trans = scene.world.addComponent(axes, BasicTransform(name="axes_trans", trs=util.identity()))
axes_mesh = scene.world.addComponent(axes, RenderMesh(name="axes_mesh"))
axes_mesh.vertex_attributes.append(voronoi) 
axes_mesh.vertex_attributes.append(colors)
axes_mesh.vertex_index.append(indices)
axes_vArray = scene.world.addComponent(axes, VertexArray(primitive=GL_LINES)) # note the primitive change

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

# shaderDec_axes = scene.world.addComponent(axes, Shader())
# OR
axes_shader = scene.world.addComponent(axes, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))
# axes_shader.setUniformVariable(key='modelViewProj', value=mvpMat, mat4=True)


# MAIN RENDERING LOOP

running = True
scene.init(imgui=True, windowWidth = 1024, windowHeight = 768, windowTitle = "Elements: A Working Event Manager", openGLversion = 4)

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
# MANOS END
# Add RenderWindow to the EventManager publishers
# eManager._publishers[updateBackground.name] = gGUI


eye = util.vec(.5, .5, 1.5)
target = util.vec(0.5, 0.5, 0.0)
up = util.vec(0.0, 1.0, 0.0)
view = util.lookat(eye, target, up)
# projMat = util.ortho(-10.0, 10.0, -10.0, 10.0, -1.0, 10.0) ## WORKING
# projMat = util.perspective(90.0, 1.33, 0.1, 100) ## WORKING
projMat = util.perspective(50.0, 1.0, 0.01, 10.0) ## WORKING 

gWindow._myCamera = view # otherwise, an imgui slider must be moved to properly update


model_cube = trans4.trs
# OR
# model_cube = util.scale(0.3) @ util.translate(0.0,0.5,0.0) ## COMPLETELY OVERRIDE OBJECT's TRS
# OR
# model_cube =  trans4.trs @ util.scale(0.3) @ util.translate(0.0,0.5,0.0) ## TAMPER WITH OBJECT's TRS

model_terrain_axes = terrain.getChild(0).trs # notice that terrain.getChild(0) == terrain_trans
# OR 
# model_terrain_axes = util.translate(0.0,0.0,0.0) ## COMPLETELY OVERRIDE OBJECT's TRS

while running:
    running = scene.render(running)
    scene.world.traverse_visit(renderUpdate, scene.world.root)
    view =  gWindow._myCamera # updates view via the imgui
    mvp_cube = projMat @ view @ model_cube
    mvp_terrain_axes = projMat @ view @ model_terrain_axes
    axes_shader.setUniformVariable(key='modelViewProj', value=mvp_terrain_axes, mat4=True)
    points_shader.setUniformVariable(key='modelViewProj', value=mvp_terrain_axes, mat4=True)
    terrain_shader.setUniformVariable(key='modelViewProj', value=mvp_terrain_axes, mat4=True)
    shaderDec4.setUniformVariable(key='modelViewProj', value=mvp_cube, mat4=True)
    scene.render_post()
    
scene.shutdown()