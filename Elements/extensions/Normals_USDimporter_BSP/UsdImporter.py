"""
USD import utilities, part of the Elements.pyECSS package

Elements.pyECSS (Entity Component Systems in a Scenegraph) package
@Copyright 2021-2022 Dr. George Papagiannakis

The USDImporter file, holds functionality for importing and exporting Elements scenes as .usd files

"""
from pxr import Usd, UsdGeom

from pxr import Usd, UsdGeom, UsdShade
import numpy as np

from Elements.pyECSS.Component import BasicTransform, RenderMesh
from Elements.pyECSS.Entity import Entity
from Elements.pyGLV.GL.Shader import ShaderGLDecorator, Shader
from Elements.pyGLV.GL.VertexArray import VertexArray
import Elements.pyECSS.math_utilities as util
import OpenGL.GL as gl
from pathlib import Path

"""
GlobalArray that holds all shaders of loaded objects.

"""

shaderDecs = []

"""
Helper function that creates a generic shader for an object that is loaded.
It is added to the global shaderDecs array.

"""


def InitShaderDec(shaderDec):
    global shaderDecs
    # Light
    Lposition = util.vec(2.0, 5.5, 2.0)  # uniform lightpos
    Lambientcolor = util.vec(1.0, 1.0, 1.0)  # uniform ambient color
    Lambientstr = 0.3  # uniform ambientStr
    LviewPos = util.vec(2.5, 2.8, 5.0)  # uniform viewpos
    Lcolor = util.vec(1.0, 1.0, 1.0)
    Lintensity = 0.8
    # Material
    Mshininess = 0.4
    Mcolor = util.vec(0.8, 0.0, 0.8)

    model_cube = util.scale(0.1) @ util.translate(0.0, 0.5, 0.0)
    projMat = util.perspective(50.0, 1.0, 1.0, 10.0)
    eye = util.vec(1, 0.54, 1.0)
    target = util.vec(0.02, 0.14, 0.217)
    up = util.vec(0.0, 1.0, 0.0)
    view = util.lookat(eye, target, up)
    tabletrs = util.translate(0, 0, 0)
    mvp_cube = projMat @ view @ tabletrs

    shaderDec.setUniformVariable(key='modelViewProj', value=mvp_cube, mat4=True)
    shaderDec.setUniformVariable(key='model', value=model_cube, mat4=True)
    shaderDec.setUniformVariable(key='ambientColor', value=Lambientcolor, float3=True)
    shaderDec.setUniformVariable(key='ambientStr', value=Lambientstr, float1=True)
    shaderDec.setUniformVariable(key='viewPos', value=LviewPos, float3=True)
    shaderDec.setUniformVariable(key='lightPos', value=Lposition, float3=True)
    shaderDec.setUniformVariable(key='lightColor', value=Lcolor, float3=True)
    shaderDec.setUniformVariable(key='lightIntensity', value=Lintensity, float1=True)
    shaderDec.setUniformVariable(key='shininess', value=Mshininess, float1=True)
    shaderDec.setUniformVariable(key='matColor', value=Mcolor, float3=True)
    shaderDecs.append(shaderDec)

def get_parent_name_blender(prim, stage):
    """
    Returns the name of the parent USD primitive for a given prim.
    If the prim has no valid parent, the function safely returns None.
    """
    parent_prim = prim.GetParent()

    # If the primitive has no parent or the parent is invalid, abort safely
    if not parent_prim or not parent_prim.IsValid():
        return None
    
    # Extract the parent primitive name
    name = parent_prim.GetName()
    return name if name else None

def triangulate(faceVertexCounts, faceVertexIndices):
    """
    Converts polygonal faces into triangles by using fan triangulation (triangles share a common vertex).
    """
    
    tris = []
    idx = 0
    for n in faceVertexCounts:
        # Extract the indices that belong to the current face
        face = faceVertexIndices[idx:idx+n]
        idx += n

        # fan triangulation: (0, i, i+1)
        for i in range(1, n-1):
            tris.extend([face[0], face[i], face[i+1]])
    return np.array(tris, dtype=np.int32)

def get_color(prim):
    """
    Extracts the diffuse RGB color of a USD primitive.
    """

    mat, _ = UsdShade.MaterialBindingAPI(prim).ComputeBoundMaterial()

    # Default color used when no material or color information is present
    default=(0.5, 0.5, 0.5)
    
    if not mat:
        return np.array(default, dtype=np.float32)

    # Retrieve the surface shader output
    surf = mat.GetSurfaceOutput()
    if not surf:
        return np.array(default, dtype=np.float32)

    # Get the connected shader source
    src = surf.GetConnectedSource()
    if not src:
        return np.array(default, dtype=np.float32)

    # Attempt to read the diffuse color input from the shader
    inp = UsdShade.Shader(src[0]).GetInput("diffuseColor")

    if inp is not None:
        v = inp.Get()
        if v is None:
            return np.array(default, dtype=np.float32)
    
    return np.array(v, dtype=np.float32)
    
def triangulate_in_corner_space(fvc):
    """
    Triangulates polygonal faces in corner space.

    Each face is described by a number of corners (fvc).
    The function produces triangle indices that refer directly
    to corner indices, not to shared vertices.
    """
    tris = []
    base = 0
    for cnt in fvc:
        for i in range(1, cnt - 1):
            tris += [base + 0, base + i, base + i + 1]
        base += cnt
    indices = np.array(tris, dtype=np.uint32)

    return indices

"""
Loads the .usd file, created with Blender, specified in path argument.
Adds the loaded entities and components to the argument scene.
Returns the new scene with all the new entities and components.
"""
def LoadScene_Blender(scene, path, colored_flag):
    stage = Usd.Stage.Open(path)
    prim_iter = iter(Usd.PrimRange.PreAndPostVisit(stage.GetPseudoRoot()))
    path_to_entity = {"/root": scene.world.root}  # map το USD /root
    for prim in prim_iter:
        if prim_iter.IsPostVisit():
            continue
        
        parent_entity_name = get_parent_name_blender(prim, stage)
        
        # Some entities that exist in some demos run with different shaders, as a result we do not load/save them
        if parent_entity_name == 'terrain' or parent_entity_name == 'axes' or parent_entity_name == 'coll' or parent_entity_name == 'LightPos':
            continue

        if prim.IsA(UsdGeom.Mesh):
            points = np.array(prim.GetAttribute('points').Get())
            n = len(points)

            rgb = get_color(prim)
            if rgb is not None:
                colors = np.repeat(rgb[None, :], n, axis=0)
            else:
                colors = np.ones((n, 3), dtype=np.float32)

            fvi = np.array(prim.GetAttribute('faceVertexIndices').Get(), dtype=np.int32)
            fvc = np.array(prim.GetAttribute('faceVertexCounts').Get(), dtype=np.int32)

            attr = prim.GetAttribute('normals')
            interpolation = attr.GetMetadata("interpolation")
            normals = np.array(attr.Get(), dtype=np.float32)

            if interpolation == "faceVarying":
                # ===== FLAT SHADING =====

                # unindex geometry
                points  = points[fvi]
                colors = colors[fvi]
                
                # triangulate in corner space
                indices = triangulate_in_corner_space(fvc)

            else:
                # ===== SMOOTH SHADING =====
                indices = triangulate(fvc, fvi).astype(np.uint32)
                normals = np.array(normals, dtype=np.float32)
                
            parent_entity_name = get_parent_name_blender(prim, stage)
            parent_path = str(prim.GetParent().GetPath())
            parent_entity = path_to_entity.get(parent_path)
            
            if parent_entity is None:
                continue

            game_object_mesh = scene.world.addComponent(parent_entity, RenderMesh(name=parent_entity_name + "_Mesh"))
            if game_object_mesh is None:
                continue

            game_object_mesh.vertex_attributes.append(points)
            if normals is not None and colored_flag == 1:
                game_object_mesh.vertex_attributes.append(normals * 0.5 + 0.5)
            else:
                game_object_mesh.vertex_attributes.append(colors)

            if normals is not None: game_object_mesh.vertex_attributes.append(normals)
            game_object_mesh.vertex_index.append(indices)

            scene.world.addComponent(parent_entity, VertexArray(primitive=gl.GL_TRIANGLES))
            
            shader_dec = scene.world.addComponent(parent_entity, ShaderGLDecorator(
                    Shader(vertex_import_file=Path(__file__).resolve().parent / "usd_shader.vert",
                        fragment_import_file=Path(__file__).resolve().parent / "usd_shader.frag")))

            InitShaderDec(shader_dec)
            shaderDecs.append(shader_dec)

        # Set Parent - Child relationship
        elif prim.IsA(UsdGeom.Xform):
            prim_path = str(prim.GetPath())
            if prim_path == "/root":
                continue

            entity = scene.world.createEntity(Entity(name=prim.GetName()))
            path_to_entity[prim_path] = entity

            # get transform matrix
            xformable = UsdGeom.Xformable(prim)
            M = xformable.GetLocalTransformation()
            trs = np.array(M, dtype=np.float32).T

            # Z-up -> Y-up
            C = util.rotate(axis=(1.0,0.0,0.0), angle=-90)
            Cinv = util.rotate(axis=(1.0,0.0,0.0), angle=90)
            trs = C @ trs @ Cinv 

            scene.world.addComponent(entity, BasicTransform(name=entity.name+"_TRS", trs=trs))
            
            # parent by path
            parent_path = str(prim.GetParent().GetPath())
            parent_entity = path_to_entity.get(parent_path, scene.world.root)
            print(f"Parent: {parent_entity.name} -> Child: {entity.name}")

            if parent_entity is not entity:
                scene.world.addEntityChild(parent_entity, entity)
    return shaderDecs