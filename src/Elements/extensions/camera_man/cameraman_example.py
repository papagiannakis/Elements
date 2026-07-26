# Giorgos Vitsos csd5369

import numpy as np
import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, RenderMesh
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GUI.Viewer import RenderGLStateSystem
from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray
from Elements.pyGLV.GL.Textures import Texture
from Elements.definitions import TEXTURE_DIR
import cameraman_logic as cam


# Scenegraph
scene = Scene()

root = scene.world.createEntity(Entity(name="Root"))

sphere = scene.world.createEntity(Entity(name="sphere"))
scene.world.addEntityChild(root, sphere)

sphere_transform = scene.world.addComponent(
    sphere, BasicTransform(name="sphere_Transform", trs=util.translate(0, 0, 0))
)

sphere_mesh = scene.world.addComponent(
    sphere, RenderMesh(name="sphere_mesh")
)

# Sphere
segments = 64
rings = 32
radius = 1

vertices_sphere = []
uvs_sphere = []
colors_sphere = []
indices_sphere = []

for i in range(rings + 1):
    phi = np.pi * i / rings
    v = 1 - i / rings

    for j in range(segments + 1):
        theta = 2 * np.pi * j / segments
        u = 1 - (j / segments)

        x = radius * np.sin(phi) * np.cos(theta)
        y = radius * np.cos(phi)
        z = radius * np.sin(phi) * np.sin(theta)

        vertices_sphere.append([x, y, z, 1.0])
        uvs_sphere.append([u, v])
        colors_sphere.append([1.0, 1.0, 1.0, 1.0])

for i in range(rings):
    for j in range(segments):
        first = i * (segments + 1) + j
        second = first + segments + 1

        indices_sphere.extend([first, second, first + 1])
        indices_sphere.extend([second, second + 1, first + 1])

vertices_sphere = np.array(vertices_sphere, dtype=np.float32)
uvs_sphere = np.array(uvs_sphere, dtype=np.float32)
colors_sphere = np.array(colors_sphere, dtype=np.float32)
indices_sphere = np.array(indices_sphere, dtype=np.uint32)

sphere_mesh.vertex_attributes.append(vertices_sphere)
sphere_mesh.vertex_attributes.append(uvs_sphere)
sphere_mesh.vertex_attributes.append(colors_sphere)
sphere_mesh.vertex_index.append(indices_sphere)

sphere_vao = scene.world.addComponent(sphere, VertexArray())

sphere_shader = scene.world.addComponent(
    sphere,
    ShaderGLDecorator(
        Shader(
            vertex_source=Shader.SIMPLE_TEXTURE_VERT,
            fragment_source=Shader.SIMPLE_TEXTURE_FRAG
        )
    )
)

# Systems
renderUpdate = scene.world.createSystem(RenderGLShaderSystem())
initUpdate = scene.world.createSystem(InitGLShaderSystem())

# Initialize
scene.init(
    imgui=True,
    windowWidth=1000,
    windowHeight=800,
    windowTitle="CameraMan Project",
    openGLversion=4
)

# Ready Bezier control points
cam.set_control_points([
    [8, 4, 8],
    [4, 6, 0],
    [0, 3, -6],
    [-6, 4, 0],
    [0, 2, 6]
])

# Texture
texturePath = TEXTURE_DIR / "earth.jpg"
texture = Texture(texturePath)
sphere_shader.setUniformVariable("ImageTexture", texture, texture=True)

# Main loop
scene.world.traverse_visit(initUpdate, scene.world.root)

running = True

while running:

    running = scene.render()
    cam.run_camera(sphere_transform, sphere_shader)
    scene.world.traverse_visit(renderUpdate, scene.world.root)
    scene.render_post()

scene.shutdown()
