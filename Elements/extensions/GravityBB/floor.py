"""
Generating floor and adding bounding box to test gravity Collision with Texture !
    
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
from Elements.extensions.GravityBB.AABoundingBox import AABoundingBox
from Elements.pyGLV.GL.Textures import Texture

# Generates a floor with a bounding box WITH TEXTURE SHADER
def generate_floor_with_bb(rootEntity, size=12):
    scene = Scene()
    # ---------------------------
    # Generate floor = terrain
    
    vertexTerrain = [
        [-0.5, -0.5, 0.5, 1.0],
        [-0.5, 0.5, 0.5, 1.0],
        [0.5, 0.5, 0.5, 1.0],
        [0.5, -0.5, 0.5, 1.0], 
        [-0.5, -0.5, -0.5, 1.0], 
        [-0.5, 0.5, -0.5, 1.0], 
        [0.5, 0.5, -0.5, 1.0], 
        [0.5, -0.5, -0.5, 1.0]
    ];
    
    #index arrays for above vertex Arrays
    indexTerrain = np.array(
        (
            1,0,3, 1,3,2, 
            2,3,7, 2,7,6,
            3,0,4, 3,4,7,
            6,5,1, 6,1,2,
            4,5,6, 4,6,7,
            5,4,0, 5,0,1
        ),
        dtype=np.uint32
    )

    # Add terrain
    floor = scene.world.createEntity(Entity(name="floor"))
    scene.world.addEntityChild(rootEntity, floor)
    
    floor_trans = scene.world.addComponent(floor, BasicTransform(name="floor_trans", trs=util.identity()))
    floor_trans.trs = util.scale(size, 0.5, size)
    
    floor_mesh = scene.world.addComponent(floor, RenderMesh(name="floor_mesh"))
    floor_mesh.vertex_attributes.append(vertexTerrain)
    floor_mesh.vertex_attributes.append(Texture.CUBE_TEX_COORDINATES)
    floor_mesh.vertex_index.append(indexTerrain)
        
    vertices = floor_mesh.vertex_attributes[0]
    
    # create the bounding box of the floor  Gravity should be FALSE so that the floor wont just fall
    floor_bb = scene.world.addComponent(floor, AABoundingBox(name="floor_bb", vertices=vertices, hasGravity=False))
    
    scene.world.addComponent(floor, VertexArray())
    
    floor_shader = scene.world.addComponent(floor, ShaderGLDecorator(Shader(vertex_source = Shader.SIMPLE_TEXTURE_VERT, fragment_source=Shader.SIMPLE_TEXTURE_FRAG)))
    
    return floor_trans, floor_shader, floor_bb