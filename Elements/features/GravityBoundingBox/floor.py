"""
Generating floor with existing function generateTerrain but adding bounding box to test gravity Collision
    
@author Nikos Iliakis csd4375
"""
from __future__         import annotations
import Elements.pyECSS.math_utilities as util
import numpy as np
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform,  RenderMesh

from Elements.pyGLV.GL.Shader import Shader, ShaderGLDecorator
from Elements.pyGLV.GL.VertexArray import VertexArray
from Elements.pyGLV.GL.Scene import Scene
from Elements.utils.terrain import generateTerrain
from OpenGL.GL import GL_LINES
from AABoundingBox import AABoundingBox

# Generates a floor with a bounding box
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
        
    vertices = floor_mesh.vertex_attributes[0]
    
    # create the bounding box of the floor    
    floor_bb = scene.world.addComponent(floor, AABoundingBox(name="floor_bb", vertices=vertices, hasGravity=False))
        
    floor_shader = scene.world.addComponent(floor, ShaderGLDecorator(Shader(vertex_source=Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))

    scene.world.addComponent(floor, VertexArray(primitive=GL_LINES))
    


    return floor_trans, floor_shader, floor_bb