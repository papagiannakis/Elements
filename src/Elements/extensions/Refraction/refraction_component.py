"""
Refraction Component for Elements Framework
Creates refractive entities (glass, water, diamond) with environment mapping.
Uses Standard.vert from Elements and a custom refraction fragment shader.
Optimized for both small meshes (cube) and large meshes (bunny).
"""
import numpy as np
import Elements.utils.normals as norm
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, RenderMesh
from Elements.pyGLV.GL.VertexArray import VertexArray
from Elements.pyGLV.GL.Shader import Shader, ShaderGLDecorator 
import Elements.pyECSS.math_utilities as util
from pathlib import Path
from Elements.definitions import SHADER_DIR

# Locate and load the standard vertex shader
SHADER_DIR = Path(__file__).parent.parent.parent / "files" / "shaders"
STANDARD_VERT_PATH = SHADER_DIR / "Standard.vert"

# Read the Standard.vert shader file
with open(STANDARD_VERT_PATH, 'r') as f: REFRACTION_VERT = f.read()

# Custom fragment shader implementing refraction (Snell's Law)
# Inputs match Standard.vert outputs
REFRACTION_FRAG = (SHADER_DIR / "Refraction.frag").read_text()

def create_refractive_entity(scene, parent, name, vertices, indices):
    """
    Factory function to create an entity with refractive material properties.
    
    This function creates a complete ECS entity with:
    - Transform component for positioning
    - RenderMesh component with vertex data and normals
    - Custom refraction shader (Standard.vert + refraction fragment)
    
    Optimized for both small meshes (cube) and large meshes (bunny 70k+ vertices).
    
    Args:
        scene (Scene): The Elements Scene object
        parent (Entity): Parent entity to attach this entity to
        name (str): Name identifier for the entity
        vertices (ndarray): Vertex positions array (Nx4 with homogeneous coordinates)
        indices (ndarray): Triangle indices array
        
    Returns:
        tuple: (entity, transform_component, shader_decorator)
            - entity: The created Entity object
            - transform_component: BasicTransform component for manipulation
            - shader_decorator: ShaderGLDecorator for setting uniforms
    """
    
    # Create the entity in the ECS world
    entity = scene.world.createEntity(Entity(name=name))
    
    # Attach to parent in scene hierarchy
    scene.world.addEntityChild(parent, entity)
    
    # Add transform component (identity matrix = no transformation initially)
    trans = scene.world.addComponent(
        entity, 
        BasicTransform(name=f"trans_{name}", trs=util.identity())
    )
    
    # Add mesh component to hold vertex data
    mesh_comp = scene.world.addComponent(
        entity, 
        RenderMesh(name=f"mesh_{name}")
    )
    
    # Check if this is a large mesh (like the bunny)
    num_vertices = len(vertices)
    is_large_mesh = num_vertices > 10000  # Threshold for large meshes
    
    if is_large_mesh:
        # For large meshes: Skip generateUniqueVertices (too slow)
        # Work directly with the provided data
        pos_data = np.array(vertices)[:, :3].astype(np.float32)
        i = np.array(indices, dtype=np.uint32)
        n = None  # Will calculate normals manually
        
        print(f"[REFRACTION] Large mesh detected ({num_vertices} vertices), using optimized path.")
        print(f"It may take some time, please wait...")
    else:
        # For small meshes: Use generateUniqueVertices
        result = norm.generateUniqueVertices(vertices, indices)
        
        # Unpack based on return type
        if len(result) == 3:
            v, i, n = result  # Vertices, indices, normals
        else:
            v, i = result     # Only vertices and indices
            n = None
        
        # Convert vertices to float32 array and extract XYZ
        pos_data = np.array(v)[:, :3].astype(np.float32)
    

    # Check if normals were provided
    if n is None or len(n) == 0:
        # Calculate normals manually using smooth shading
        
        # Initialize zero normals for each vertex
        indices_array = np.array(i, dtype=np.uint32)
        num_verts = len(pos_data)
        norm_data = np.zeros((num_verts, 3), dtype=np.float32)
        
        # Iterate through each triangle face
        for face_idx in range(0, len(indices_array), 3):
            # Get the three vertex indices for this triangle
            i0, i1, i2 = indices_array[face_idx:face_idx+3]
            
            # Get vertex positions
            v0 = pos_data[i0]
            v1 = pos_data[i1]
            v2 = pos_data[i2]
            
            # Calculate two edge vectors of the triangle
            edge1 = v1 - v0
            edge2 = v2 - v0
            
            # Cross product gives the face normal (perpendicular to triangle)
            face_normal = np.cross(edge1, edge2)
            
            # Normalize the face normal to unit length
            length = np.linalg.norm(face_normal)
            if length > 0:
                face_normal = face_normal / length
            
            # Accumulate this face normal to all three vertices of the triangle
            # This creates smooth shading by averaging normals at shared vertices
            norm_data[i0] += face_normal
            norm_data[i1] += face_normal
            norm_data[i2] += face_normal
        
        # Normalize all accumulated normals to unit length
        for idx in range(num_verts):
            length = np.linalg.norm(norm_data[idx])
            if length > 0.0001:
                norm_data[idx] = norm_data[idx] / length
            else:
                norm_data[idx] = np.array([0.0, 1.0, 0.0])  # Default to up vector
    else:
        # Use the provided normals
        norm_data = np.array(n).reshape(-1, 3).astype(np.float32)
    
    print(f"[REFRACTION] Entity '{name}': {len(pos_data)} vertices, {len(norm_data)} normals, {len(i)} indices")
    
    # Add position data to mesh (layout location 0 in shader)
    mesh_comp.vertex_attributes.append(pos_data)
    
    # Add normal data to mesh (layout location 1 in shader)
    mesh_comp.vertex_attributes.append(norm_data)
    
    # Add index buffer for triangle drawing
    mesh_comp.vertex_index.append(i)
    
    # Create and attach VertexArray component (manages GPU buffers)
    scene.world.addComponent(entity, VertexArray())
    
    # Create shader with Standard.vert and custom refraction fragment
    shader_dec = scene.world.addComponent(entity, ShaderGLDecorator(Shader(vertex_source=REFRACTION_VERT, fragment_source=REFRACTION_FRAG)))
    
    # Return entity and components for further manipulation
    return entity, trans, shader_dec