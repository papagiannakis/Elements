from __future__         import annotations
import Elements.pyECSS.math_utilities as util
import numpy as np
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform,  RenderMesh

from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GL.SimpleCamera import SimpleCamera
from Elements.utils.terrain import generateTerrain
from Elements.utils.normals import Convert
from OpenGL.GL import GL_LINES
from AABoundingBox import AABoundingBox

#MYCHANGE
# Finds minimum value of an axis in a vertice dataset (default axis = 0 (meaning x axis))
def find_min_axis(vertices, axis=0):
    return np.min(vertices[:, axis])

# Finds maximum value of an axis in a vertice dataset (default axis = 0 (meaning x axis))
def find_max_axis(vertices, axis=0):
    return np.max(vertices[:, axis])

def create_min_points_list(vertices):
    return [find_min_axis(vertices, axis=0), find_min_axis(vertices, axis=1),find_min_axis(vertices, axis=2), 1]

def create_max_points_list(vertices):
    return [find_max_axis(vertices, axis=0), find_max_axis(vertices, axis=1), find_max_axis(vertices, axis=2), 1]


def generate_floor_with_bb(rootEntity, size=6,N=300,uniform_color = [0.4,0.4,0.4,0.5]):
    scene = Scene()
    # ---------------------------
    # Generate floor = terrain
    vertexTerrain, indexTerrain, colorTerrain = generateTerrain(size, N)
    # Add terrain
    floor = scene.world.createEntity(Entity(name="floor"))
    scene.world.addEntityChild(rootEntity, floor)
    
    floor_trans = scene.world.addComponent(floor, BasicTransform(name="floor_trans", trs=util.identity()))
    
    floor_mesh = scene.world.addComponent(floor, RenderMesh(name="floor_mesh"))
    floor_mesh.vertex_attributes.append(vertexTerrain)
    floor_mesh.vertex_attributes.append(colorTerrain)
    floor_mesh.vertex_index.append(indexTerrain)
    floor_mesh._AddedBB = True #IMPORTANT !
    
    vertices = floor_mesh.vertex_attributes[0]
    floor_bb = scene.world.addComponent(floor, AABoundingBox(name="floor_bb", min_points=create_min_points_list(vertices), max_points=create_max_points_list(vertices)))
    
        
    floor_shader = scene.world.addComponent(floor, ShaderGLDecorator(Shader(vertex_source=Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))

    scene.world.addComponent(floor, VertexArray(primitive=GL_LINES))
    


    return floor_trans, floor_shader, floor_bb