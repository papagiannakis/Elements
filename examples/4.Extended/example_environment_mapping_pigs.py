import time
import numpy as np
import OpenGL.GL as gl
from pathlib import Path
import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, RenderMesh
from Elements.pyECSS.System import TransformSystem
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GUI.Viewer import RenderGLStateSystem
from Elements.pyGLV.GUI.ImguiDecorator import ImGUIecssDecorator2
from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray
from Elements.pyGLV.GL.Textures import get_texture_faces, Texture, Texture3D
from Elements.utils.normals import generateSmoothNormalsMesh, generateUniqueVertices
from Elements.utils.objimporter.wavefront import Wavefront
from Elements.utils.Shortcuts import displayGUI_text
from Elements.definitions import MODEL_DIR, SHADER_DIR
from Elements.extensions.environment_mapping import EnvironmentMapping

example_description = \
"Three Reflection Pigs floating around Battersea Power Station. \n\
Three copies of the same pig model (Gold, Chrome and Blue) are rendered with \n\
the EnvironmentMapping shader, each using a different tint color/strength, \n\
and float up and down while rotating above a reflective cubemap skybox. \n\
You may move the camera using the mouse or the GUI."

# basic configuration
WIN_WIDTH, WIN_HEIGHT = 1200, 800
ENV_MAP_DIR = Path(__file__).parent
SKYBOX_DIR = ENV_MAP_DIR / "pigs"/ "pigImage"
MODEL_PATH = ENV_MAP_DIR / "pigs"/ "models" / "pighighpoly1.obj"
#MODEL_PATH = MODEL_DIR / "cow.obj"

SKYBOX_IMAGES = {
    'front': SKYBOX_DIR / "front.png",
    'back':  SKYBOX_DIR / "back.png",
    'top':   SKYBOX_DIR / "top.png",
    'bottom': SKYBOX_DIR / "bottom.png",
    'left':  SKYBOX_DIR / "left.png",
    'right': SKYBOX_DIR / "right.png",
}


scene = Scene()
rootEntity = scene.world.createEntity(Entity(name="Root"))
root_trans = scene.world.addComponent(rootEntity, BasicTransform(name="root_trans", trs=util.scale(0.6, 0.6, 0.6)))
transUpdate = scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
renderUpdate = scene.world.createSystem(RenderGLShaderSystem())
initUpdate = scene.world.createSystem(InitGLShaderSystem())

# ground entity
ground = scene.world.createEntity(Entity(name="ground"))
scene.world.addEntityChild(rootEntity, ground)

g_size, g_y = 50.0, -50.0
g_verts = np.array([[-g_size, g_y, -g_size, 1.0], [g_size, g_y, -g_size, 1.0],    [g_size, g_y, g_size, 1.0], [-g_size, g_y, g_size, 1.0]], dtype=np.float32)
g_uvs = np.array([[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]], dtype=np.float32)
g_inds = np.array([0, 1, 2, 0, 2, 3], np.uint32)

ground_trans = scene.world.addComponent(ground, BasicTransform(name="ground_trans", trs=util.identity()))
ground_mesh = scene.world.addComponent(ground, RenderMesh(name="ground_mesh"))
ground_mesh.vertex_attributes.extend([g_verts, g_uvs])
ground_mesh.vertex_index.append(g_inds)
scene.world.addComponent(ground, VertexArray())
ground_shader = scene.world.addComponent(ground, ShaderGLDecorator(Shader(vertex_import_file=SHADER_DIR / "SimpleTextureMVP.vert", fragment_import_file=SHADER_DIR / "SimpleTexture.frag")))

# skybox entity
skybox = scene.world.createEntity(Entity(name="Skybox"))
scene.world.addEntityChild(rootEntity, skybox)

minbox, maxbox = -50.0, 50.0
sb_verts = np.array([
    [minbox, minbox, minbox, 1.0], [minbox, maxbox, minbox, 1.0],
    [maxbox, maxbox, minbox, 1.0], [maxbox, minbox, minbox, 1.0],
    [minbox, minbox, maxbox, 1.0], [minbox, maxbox, maxbox, 1.0],
    [maxbox, maxbox, maxbox, 1.0], [maxbox, minbox, maxbox, 1.0]
], dtype=np.float32)
sb_inds = np.array((1, 0, 3, 1, 3, 2, 2, 3, 7, 2, 7, 6, 3, 0, 4, 3, 4, 7,
                    6, 5, 1, 6, 1, 2, 4, 5, 6, 4, 6, 7, 5, 4, 0, 5, 0, 1), np.uint32)

sb_verts, sb_inds, _ = generateUniqueVertices(sb_verts, sb_inds)

skybox_trans = scene.world.addComponent(skybox, BasicTransform(name="skybox_trans", trs=util.identity()))
skybox_mesh = scene.world.addComponent(skybox, RenderMesh(name="skybox_mesh"))
skybox_mesh.vertex_attributes.append(sb_verts)
skybox_mesh.vertex_index.append(sb_inds)
scene.world.addComponent(skybox, VertexArray())
skybox_shader = scene.world.addComponent(skybox, ShaderGLDecorator(
    Shader(vertex_import_file=SHADER_DIR / "StaticSkybox.vert", fragment_import_file=SHADER_DIR / "StaticSkybox.frag")))

# load model once for the three pigs
print(f"Loading model geometry: {MODEL_PATH}")
imported_model = Wavefront(str(MODEL_PATH), calculate_smooth_normals=False)
mesh_data = imported_model.get_mesh(0)

# Process
m_verts = np.array(mesh_data.vertices, dtype=np.float32)
if m_verts.shape[1] == 3:
    ones = np.ones((m_verts.shape[0], 1), dtype=np.float32)
    m_verts = np.hstack([m_verts, ones])

m_inds = np.array(mesh_data.indices, dtype=np.uint32)
m_colors = np.array([[0.8, 0.8, 0.9, 1.0] for _ in range(len(m_verts))], dtype=np.float32)
m_verts, m_inds, m_colors, m_normals = generateSmoothNormalsMesh(m_verts, m_inds, m_colors)

# helper to create pigs
def create_pig(name, offset_x, tint_color, tint_strength):
    """Creates a pig entity """
    entity = scene.world.createEntity(Entity(name=name))
    scene.world.addEntityChild(rootEntity, entity)
    
    trans = scene.world.addComponent(entity, BasicTransform(
        name=f"{name}_trans", 
        trs=util.translate(offset_x, 0.5, 0.0) @ util.scale(0.5, 0.5, 0.5)
    ))
    
    # reuse the preloaded mesh data
    mesh = scene.world.addComponent(entity, RenderMesh(name=f"{name}_mesh"))
    mesh.vertex_attributes.extend([m_verts, m_colors, m_normals])
    mesh.vertex_index.append(m_inds)
    scene.world.addComponent(entity, VertexArray())
    
    return entity, trans, tint_color, tint_strength

# create Pigs - Three different ones
pigs = []

# Pig 1
pigs.append(create_pig("Pig_Gold", -3.0, (1.0, 0.8, 0.0), 0.7))


pigs.append(create_pig("Pig_Chrome", 0.0, (1.0, 1.0, 1.0), 0.0))

pigs.append(create_pig("Pig_Blue", 3.0, (0.2, 0.2, 1.0), 0.5))


# scene initialization
scene.init(imgui=True, windowWidth=WIN_WIDTH, windowHeight=WIN_HEIGHT, windowTitle="Elements: Three Little Reflection Pigs", customImGUIdecorator=ImGUIecssDecorator2, openGLversion=4)


#Textures & Shaders
face_data = get_texture_faces(**SKYBOX_IMAGES)
cubemap = Texture3D(face_data)
skybox_shader.component.texture3DDict['cubemap'] = cubemap

if SKYBOX_IMAGES['bottom'].exists():
    ground_texture = Texture(SKYBOX_IMAGES['bottom'])
    ground_shader.setUniformVariable(key='ImageTexture', value=ground_texture, texture=True)

# Shaders to all my pigs
pig_shaders = []
for entity, trans, t_color, t_strength in pigs:
    shader = EnvironmentMapping.apply(entity, scene, tint_color=t_color,tint_strength=t_strength,cubemap=cubemap )
    pig_shaders.append(shader)


gl.glEnable(gl.GL_DEPTH_TEST)
scene.world.traverse_visit(initUpdate, scene.world.root)

eManager = scene.world.eventManager
renderGLEventActuator = RenderGLStateSystem()
eManager._subscribers['OnUpdateWireframe'] = scene.renderWindow
eManager._actuators['OnUpdateWireframe'] = renderGLEventActuator
eManager._subscribers['OnUpdateCamera'] = scene.renderWindow
eManager._actuators['OnUpdateCamera'] = renderGLEventActuator

projMat = util.perspective(50.0, WIN_WIDTH/WIN_HEIGHT, 0.01, 200.0)

running = True
while running:
    running = scene.render()
    displayGUI_text(example_description)
    
    scene.world.traverse_visit(transUpdate, scene.world.root)
    curr_time = time.time()
    
    view = scene.renderWindow._myCamera
    camera_pos = util.inverse(view)[:3, 3]

    #  Ground & Skybox
    mvp_ground = projMat @ view @ ground_trans.l2world
    ground_shader.setUniformVariable(key='modelViewProj', value=mvp_ground, mat4=True)
    skybox_shader.setUniformVariable(key='Proj', value=projMat, mat4=True)
    skybox_shader.setUniformVariable(key='View', value=view, mat4=True)

    # All Pigs 
    for i, (entity, trans, _, _) in enumerate(pigs):
        # Animation 
        phase = i * 1.5
        
        rotation_angle = (curr_time * 20.0) % 360.0
        float_offset = np.sin(curr_time * 2.0 + phase) * 0.3
        base_height = 0.5 
        base_x = (i - 1) * 3.0 # Positions: -3, 0, 3
        
        # Update Transform
        trans.trs = util.translate(base_x, base_height + float_offset, 0.0) @ util.rotate((0, 1, 0), rotation_angle) @  util.scale(0.5, 0.5, 0.5)

        shader = pig_shaders[i]
        mvp = projMat @ view @ trans.l2world
        shader.setUniformVariable(key='modelViewProj', value=mvp, mat4=True)
        shader.setUniformVariable(key='model', value=trans.l2world, mat4=True)
        shader.setUniformVariable(key='viewPos', value=camera_pos, float3=True)
    
    scene.world.traverse_visit(renderUpdate, scene.world.root)
    scene.render_post()

scene.shutdown()