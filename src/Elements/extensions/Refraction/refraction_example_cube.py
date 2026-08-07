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
from Elements.definitions import SHADER_DIR, TEXTURE_DIR
from Elements.extensions.Refraction.refraction_component import create_refractive_entity   # Import refraction component factory function
from Elements.utils.Shortcuts import displayGUI_text

example_description = \
"Refraction Example - Glass Cube\n\
Demonstrates light refraction through a glass cube using environment mapping.\n\
The refractive index can be adjusted in real-time via GUI slider."


# Cube vertices 
vertexCube = np.array([
    [-0.5, -0.5,  0.5, 1.0], 
    [-0.5,  0.5,  0.5, 1.0], 
    [ 0.5,  0.5,  0.5, 1.0], 
    [ 0.5, -0.5,  0.5, 1.0],
    [-0.5, -0.5, -0.5, 1.0], 
    [-0.5,  0.5, -0.5, 1.0], 
    [ 0.5,  0.5, -0.5, 1.0], 
    [ 0.5, -0.5, -0.5, 1.0]
], dtype=np.float32)

# Cube triangle indices 
indexCube = np.array((
    1,0,3, 1,3,2,
    2,3,7, 2,7,6,
    3,0,4, 3,4,7,
    6,5,1, 6,1,2,
    4,5,6, 4,6,7,
    5,4,0, 5,0,1
), np.uint32)

# Skybox vertices
minb, maxb = -30, 30
vSky = np.array([
    [minb, minb, maxb, 1.0], 
    [minb, maxb, maxb, 1.0], 
    [maxb, maxb, maxb, 1.0], 
    [maxb, minb, maxb, 1.0], 
    [minb, minb, minb, 1.0], 
    [minb, maxb, minb, 1.0], 
    [maxb, maxb, minb, 1.0], 
    [maxb, minb, minb, 1.0]
], dtype=np.float32)

# Create scene and root entity
scene = Scene()    
root = scene.world.createEntity(Entity(name="RooT"))

# Create skybox entity
skybox = scene.world.createEntity(Entity(name="Skybox"))
scene.world.addEntityChild(root, skybox)

# Add transform (no transformation needed - skybox follows camera)
transSkybox = scene.world.addComponent(skybox, BasicTransform(name="transSkybox", trs=util.identity()))

# Add mesh component and generate skybox geometry
meshSkybox = scene.world.addComponent(skybox, RenderMesh(name="meshSkybox"))
vS, iS, _ = norm.generateUniqueVertices(vSky, indexCube)
meshSkybox.vertex_attributes.append(vS)
meshSkybox.vertex_index.append(iS)

# Add vertex array and skybox shader
scene.world.addComponent(skybox, VertexArray())
shaderSkybox = scene.world.addComponent(skybox, ShaderGLDecorator(Shader(vertex_import_file=SHADER_DIR / "StaticSkybox.vert", fragment_import_file=SHADER_DIR / "StaticSkybox.frag")))

# Create glass cube using factory function from refraction_component
# Returns: entity, transform component, shader decorator
cube_ent, cube_trans, cube_shader = create_refractive_entity(scene, root, "GlassCube", vertexCube, indexCube)

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
    windowTitle="Refraction - Glass Cube", 
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

# Set initial camera position (looking at cube from angle)
gWindow._myCamera = util.lookat(
    util.vec(2.5, 2.5, 2.5),    # Camera position
    util.vec(0, 0, 0),          # Look at origin
    util.vec(0, 1, 0)           # Up vector
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
cube_shader.setUniformVariable(key='cubemap', value=face_data, texture3D=True)

# Initial refractive index (glass = 1.52)
ref_index = 1.52
running = True

while running:
    # Process events and render frame
    running = scene.render()
    
    # Update all transforms in scene hierarchy
    scene.world.traverse_visit(transUpdate, root)
    
    # Get current view matrix (updated by camera controller)
    view = gWindow._myCamera 
    
    # Calculate projection matrix (perspective)
    projMat = util.perspective(50.0, 1.0, 0.01, 100.0)
    
    # Extract camera position from view matrix (needed for refraction calculation)
    inv_view = np.linalg.inv(view)
    cam_eye = inv_view[:3, 3]

    # GUI - REFRACTION CONTROL
    imgui.begin("Refraction Control", True)
    displayGUI_text(example_description)
    imgui.separator()
    
    # Slider for refractive index (1.0 = air, 2.5 = diamond)
    _, ref_index = imgui.slider_float("R", ref_index, 1.0, 2.5)
    
    # Calculate refraction ratio (air/material)
    ratio = 1.0 / ref_index
    
    imgui.separator()
    imgui.text(f"Material Refractive Index R: {ref_index:.3f}")
    imgui.text(f"Refraction Ratio 1/R: {ratio:.3f}")
    imgui.separator()
    
    # Reference values for common materials
    imgui.text("Common Materials Refractive Indexes:")
    imgui.text("  Air:     1.00")
    imgui.text("  Water:   1.33")
    imgui.text("  Glass:   1.52")
    imgui.text("  Diamond: 2.42")
    imgui.end()
    
    # Set matrices (Standard.vert expects: projection, view, model, normalMatrix)
    cube_shader.setUniformVariable(key='projection', value=projMat, mat4=True)
    cube_shader.setUniformVariable(key='view', value=view, mat4=True)
    cube_shader.setUniformVariable(key='model', value=cube_trans.l2world, mat4=True)
    
    # Calculate normal matrix (transpose of inverse model matrix)
    # Used to correctly transform normals for lighting calculations
    model_matrix = cube_trans.l2world
    normal_matrix_4x4 = np.linalg.inv(np.transpose(model_matrix))
    cube_shader.setUniformVariable(key='normalMatrix', value=normal_matrix_4x4, mat4=True)
    
    # Set refraction-specific uniforms
    cube_shader.setUniformVariable(key='camPos', value=cam_eye, float3=True)
    cube_shader.setUniformVariable(key='u_Ratio', value=ratio, float1=True)
    
    # Skybox only needs projection and view (no model transform)
    shaderSkybox.setUniformVariable(key='Proj', value=projMat, mat4=True)
    shaderSkybox.setUniformVariable(key='View', value=view, mat4=True)
    
    # Render all entities with their shaders
    scene.world.traverse_visit(renderUpdate, root)
    
    # Post-render 
    scene.render_post()

scene.shutdown()