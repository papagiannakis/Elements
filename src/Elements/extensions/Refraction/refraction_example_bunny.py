import numpy as np
import imgui
import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, RenderMesh
from Elements.pyECSS.System import TransformSystem
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GUI.Viewer import RenderGLStateSystem
from Elements.pyGLV.GUI.ImguiDecorator import ImGUIecssDecorator2
from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray
import Elements.utils.normals as norm
from Elements.pyGLV.GL.Textures import get_texture_faces
from Elements.definitions import TEXTURE_DIR
import OpenGL.GL as gl
from pathlib import Path
from Elements.extensions.Refraction.refraction_component import create_refractive_entity   # Import refraction component factory function
from Elements.utils.Shortcuts import displayGUI_text

example_description = \
"Refraction Example - Glass Bunny\n\
Demonstrates light refraction through a complex 3D model (Stanford Bunny).\n\
The bunny is loaded from an OBJ file and rendered with refractive properties.\n\
Refractive index can be adjusted in real-time via GUI slider."

# Get the directory of the script
script_dir = Path(__file__).parent
bunny_path = str(script_dir / "bunny.obj")

# Storage for parsed geometry data
vertices = []    # Vertex positions (x, y, z)
indices = []     # Triangle indices

# Parse OBJ file (we only need vertices and faces, normals will be calculated)
with open(bunny_path, 'r') as f:
    for line in f:
        line = line.strip()
        
        # Skip empty lines and comments
        if not line or line.startswith('#'):
            continue
            
        parts = line.split()
        if not parts:
            continue
            
        # Parse vertex position (v x y z)
        if parts[0] == 'v':
            try:
                x = float(parts[1]) if len(parts) > 1 and parts[1] else 0.0
                y = float(parts[2]) if len(parts) > 2 and parts[2] else 0.0
                z = float(parts[3]) if len(parts) > 3 and parts[3] else 0.0
                vertices.append([x, y, z, 1.0])  # Add homogeneous coordinate
            except (ValueError, IndexError):
                continue
                
        # Parse face (f v1 v2 v3 or f v1/vt1/vn1 v2/vt2/vn2 v3/vt3/vn3)
        elif parts[0] == 'f':
            try:
                face_indices = []
                # Only take first 3 vertices (triangulate if needed)
                for i in range(1, min(4, len(parts))):
                    # Extract vertex index (handle v, v/vt, v/vt/vn formats)
                    idx_str = parts[i].split('/')[0]
                    if idx_str:
                        # OBJ indices are 1-based, convert to 0-based
                        face_indices.append(int(idx_str) - 1)
                
                # Add triangle if we have 3 valid indices
                if len(face_indices) == 3:
                    indices.extend(face_indices)
            except (ValueError, IndexError):
                continue

# Convert to numpy arrays in the format expected by create_refractive_entity
vertexBunny = np.array(vertices, dtype=np.float32)
indexBunny = np.array(indices, dtype=np.uint32)


# Skybox geometry
minb, maxb = -30, 30
vSky = np.array([
    [minb, minb, maxb, 1], 
    [minb, maxb, maxb, 1], 
    [maxb, maxb, maxb, 1], 
    [maxb, minb, maxb, 1], 
    [minb, minb, minb, 1], 
    [minb, maxb, minb, 1], 
    [maxb, maxb, minb, 1], 
    [maxb, minb, minb, 1]
], dtype=np.float32)

# Cube indices for skybox
indexCube = np.array((1,0,3, 1,3,2, 
                      2,3,7, 2,7,6, 
                      3,0,4, 3,4,7, 
                      6,5,1, 6,1,2, 
                      4,5,6, 4,6,7, 
                      5,4,0, 5,0,1), np.uint32)

# Create scene and root entity
scene = Scene()    
root = scene.world.createEntity(Entity(name="RooT"))

# skybox entity
skybox = scene.world.createEntity(Entity(name="Skybox"))
scene.world.addEntityChild(root, skybox)

# Add transform component
transSkybox = scene.world.addComponent(
    skybox, 
    BasicTransform(name="transSkybox", trs=util.identity())
)

# Add mesh component and generate skybox geometry
meshSkybox = scene.world.addComponent(skybox, RenderMesh(name="meshSkybox"))
vS, iS, _ = norm.generateUniqueVertices(vSky, indexCube)
meshSkybox.vertex_attributes.append(vS)
meshSkybox.vertex_index.append(iS)

# Add vertex array and skybox shader
scene.world.addComponent(skybox, VertexArray())
shaderSkybox = scene.world.addComponent(skybox, ShaderGLDecorator(Shader(vertex_source=Shader.STATIC_SKYBOX_VERT, fragment_source=Shader.STATIC_SKYBOX_FRAG)))

# Create glass bunny using factory function from refraction_component
# This handles all the mesh setup, normal calculation, and shader assignment
bunny_ent, bunny_trans, bunny_shader = create_refractive_entity(scene, root, "GlassBunny", vertexBunny, indexBunny)

# System to initialize OpenGL shaders
initUpdate = scene.world.createSystem(InitGLShaderSystem())
# System to update transform matrices
transUpdate = scene.world.createSystem(TransformSystem("transUpdate"))
# System to render meshes with shaders
renderUpdate = scene.world.createSystem(RenderGLShaderSystem())

# Initialize scene with ImGui support
scene.init(
    imgui=True, 
    windowWidth=1024, 
    windowHeight=768, 
    windowTitle="Refraction - Glass Bunny", 
    customImGUIdecorator=ImGUIecssDecorator2, 
    openGLversion=4
)

# Initialize all shaders
scene.world.traverse_visit(initUpdate, root)

# Get event manager and window
eManager = scene.world.eventManager
gWindow = scene.renderWindow
renderGLEventActuator = RenderGLStateSystem()

# Register camera event handlers
eManager._subscribers['OnUpdateWireframe'] = gWindow
eManager._actuators['OnUpdateWireframe'] = renderGLEventActuator
eManager._subscribers['OnUpdateCamera'] = gWindow 
eManager._actuators['OnUpdateCamera'] = renderGLEventActuator

# Set initial camera position (user-defined perfect view)
gWindow._myCamera = util.lookat(
    util.vec(0, 0, 4.5),      # Camera position 
    util.vec(0, 0.05, 0),     # Look at bunny center
    util.vec(0, 1, 0)         # Up vector
)

# Load cubemap textures for environment mapping
sky_path = TEXTURE_DIR / "Skyboxes" / "Sea"
face_data = get_texture_faces(
    sky_path / "front.jpg", 
    sky_path / "back.jpg", 
    sky_path / "top.jpg", 
    sky_path / "bottom.jpg", 
    sky_path / "left.jpg", 
    sky_path / "right.jpg"
)

# Bind cubemap to both skybox and cube shaders
shaderSkybox.setUniformVariable(key='cubemap', value=face_data, texture3D=True)
bunny_shader.setUniformVariable(key='cubemap', value=face_data, texture3D=True)


# Initial refractive index (glass = 152)
ref_index = 1.52
running = True

while running:
    # Process events and render frame
    running = scene.render()
    
    # Update transforms
    scene.world.traverse_visit(transUpdate, root)
    
    # Get view matrix and calculate projection
    view = gWindow._myCamera 
    projMat = util.perspective(50.0, 1.0, 0.01, 100.0)
    
    # Extract camera position for refraction calculation
    inv_view = np.linalg.inv(view)
    cam_eye = inv_view[:3, 3]
    
    # Disable backface culling for refractive objects
    # This ensures both front and back faces are rendered
    # Important for transparent/refractive materials to avoid holes
    gl.glDisable(gl.GL_CULL_FACE)
    
    # GUI - REFRACTION CONTROL
    imgui.begin("Glass Bunny Control")
    displayGUI_text(example_description)
    imgui.separator()
    
   # Slider for refractive index (1.0 = air, 2.5 = diamond)
    _, ref_index = imgui.slider_float("R", ref_index, 1.0, 2.5)

    # Calculate refraction ratio (air/material)
    ratio = 1.0 / ref_index

    imgui.separator()
    imgui.text(f"Material Refractive Index R: {ref_index:.3f}")
    imgui.text(f"Refraction Ratio 1/R: {ratio:.4f}")
    imgui.separator()
    
    # Reference values for common materials
    imgui.text("Common Materials Refractive Indexes:")
    imgui.text("  Air:     1.00")
    imgui.text("  Water:   1.33")
    imgui.text("  Glass:   1.52")
    imgui.text("  Diamond: 2.42")
    imgui.end()
    
    # Set transformation matrices (Standard.vert uses: projection, view, model, normalMatrix)
    bunny_shader.setUniformVariable(key='projection', value=projMat, mat4=True)
    bunny_shader.setUniformVariable(key='view', value=view, mat4=True)
    bunny_shader.setUniformVariable(key='model', value=bunny_trans.l2world, mat4=True)
    
    # Calculate normal matrix (transpose of inverse model matrix)
    # Used to correctly transform normals for lighting calculations
    model_matrix = bunny_trans.l2world
    normal_matrix_4x4 = np.linalg.inv(np.transpose(model_matrix))
    bunny_shader.setUniformVariable(key='normalMatrix', value=normal_matrix_4x4, mat4=True)
    
    # Set refraction-specific uniforms
    bunny_shader.setUniformVariable(key='camPos', value=cam_eye, float3=True)
    bunny_shader.setUniformVariable(key='u_Ratio', value=ratio, float1=True)
    
    # Skybox only needs projection and view (no model transform)
    shaderSkybox.setUniformVariable(key='Proj', value=projMat, mat4=True)
    shaderSkybox.setUniformVariable(key='View', value=view, mat4=True)
    
    # Render all entities with their shaders
    scene.world.traverse_visit(renderUpdate, root)

    # Post-render
    scene.render_post()

scene.shutdown()