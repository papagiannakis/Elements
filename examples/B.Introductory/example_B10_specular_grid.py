"""
A materials chart: what the two specular parameters actually do.

Sixteen identical spheres, identical light, identical viewing angle. The only thing that changes
across the grid is the material:

    columns, left -> right : specularExponent  4, 16, 64, 256   (highlight gets *tighter*)
    rows,    top  -> bottom: shininess       0.2, 0.45, 0.7, 1.0 (highlight gets *stronger*)

The two are easy to confuse, and the names do not help:

  * specularExponent is the power the cosine is raised to. It controls the *size* of the highlight
    and nothing else. Low values smear a broad sheen over most of the sphere -- a chalky, rough
    look. High values shrink it to a tiny dot, which reads as hard and polished. This is the
    parameter that used to be hard-coded to 32 in every Elements lighting shader; it is now the
    `specularExponent` uniform.

  * shininess is a plain multiplier on the specular term. It controls how *bright* the highlight
    is, and does not change its shape at all. Despite its name it is not the "shininess exponent"
    that computer-graphics texts usually mean -- that is specularExponent above.

Read one row left to right and only the size changes; read one column top to bottom and only the
intensity changes. The top-left sphere is a dull, rough surface; the bottom-right is a hard,
polished one.

A note on how the chart is built, because it matters: each sphere is given its own light position
and its own viewer position, each offset from that sphere's own centre by the same vector. That
way every sphere is lit and viewed from an identical relative angle, and the *only* variable left
in the image is the material. If a single shared light position were used instead, spheres at the
edges of the grid would be lit at a different angle from those in the middle, and you could not
tell material differences apart from position differences. Orbiting the camera still works: the
offset is recomputed from the live camera every frame, so all sixteen highlights move together.

Hit ESC or close the window to quit.
"""

import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, RenderMesh
from Elements.pyECSS.System import TransformSystem
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GUI.Viewer import RenderGLStateSystem
from Elements.pyGLV.GUI.ImguiDecorator import ImGUIDecorator
from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray

from Elements.utils.Shortcuts import displayGUI_text
from Elements.definitions import SHADER_DIR

import Elements.extensions.Normals_USDimporter_BSP.normals as norm
from Elements.extensions.Shapes.geometry_factory import create_sphere


# ================================================================================================
# The two axes of the chart
# ================================================================================================

#: Columns. The exponent the specular cosine is raised to -- the *size* of the highlight.
SPECULAR_EXPONENTS = [4.0, 16.0, 64.0, 256.0]

#: Rows. A flat multiplier on the specular term -- the *strength* of the highlight.
SHININESS_VALUES = [0.2, 0.45, 0.7, 1.0]

#: Swap to "BlinnPhong.frag" to draw the same chart with the Blinn-Phong model instead. Its
#: highlights come out noticeably wider at equal exponents -- Blinn-Phong needs roughly 4x Phong's
#: exponent for a highlight of the same size, so the whole chart shifts about one column to the left.
FRAGMENT_SHADER = "Phong.frag"

#: A fairly saturated red, as in the classic textbook version of this chart. The highlights come
#: out white on top of it: Phong.frag applies the surface colour to the ambient and diffuse terms
#: only, leaving the specular the colour of the light -- which is what non-metals actually do.
SPHERE_COLOR = (0.62, 0.07, 0.05)

#: Sphere tessellation. Deliberately dense: this chart is about material parameters, so the mesh
#: should not be coarse enough to add faceting of its own. See example_B9_shading_comparison.py
#: for the opposite case, where a coarse mesh is the whole point.
SPHERE_LAT, SPHERE_LON = 32, 32

SPHERE_DIAMETER = 0.92
SPACING = 1.18

#: Where the light sits relative to *each* sphere's own centre -- up, left and in front, so the
#: highlight lands in the upper-left of every ball.
LIGHT_OFFSET = util.vec(-1.7, 2.0, 2.6)

Lambientcolor = util.vec(1.0, 1.0, 1.0)
Lambientstr = 0.22
Lcolor = util.vec(1.0, 1.0, 1.0)
Lintensity = 0.9

winWidth = 1200
winHeight = 800

scene = Scene()
rootEntity = scene.world.createEntity(Entity(name="RooT"))


# ================================================================================================
# Build the grid
# ================================================================================================

raw_v, raw_i, raw_c = create_sphere({
    "lat": SPHERE_LAT, "lon": SPHERE_LON, "scale": [2.0, 2.0, 2.0], "color": list(SPHERE_COLOR)})
# Smooth normals: a specular highlight on a faceted sphere would be about the mesh, not the material.
v, i, c, n = norm.generateSmoothNormalsMesh(raw_v, raw_i, raw_c)

extent = raw_v[:, :3].max(axis=0) - raw_v[:, :3].min(axis=0)
sphere_scale = SPHERE_DIAMETER / float(extent.max())

n_cols = len(SPECULAR_EXPONENTS)
n_rows = len(SHININESS_VALUES)

#: (centre, shader, exponent, shininess) per sphere, filled in below.
spheres = []

for row, shininess in enumerate(SHININESS_VALUES):
    for col, exponent in enumerate(SPECULAR_EXPONENTS):
        x = (col - (n_cols - 1) / 2.0) * SPACING
        y = ((n_rows - 1) / 2.0 - row) * SPACING
        centre = util.vec(x, y, 0.0)

        name = f"Sphere_e{int(exponent)}_s{int(shininess * 100)}"
        entity = scene.world.createEntity(Entity(name=name))
        scene.world.addEntityChild(rootEntity, entity)

        trans = scene.world.addComponent(entity, BasicTransform(
            name=f"{name}_TRS",
            trs=util.translate(x, y, 0.0) @ util.scale(sphere_scale, sphere_scale, sphere_scale)))
        mesh = scene.world.addComponent(entity, RenderMesh(name=f"{name}_mesh"))
        # Attribute order must match Phong.vert's layout(location=...): 0 position, 1 colour, 2 normal.
        mesh.vertex_attributes.append(v)
        mesh.vertex_attributes.append(c)
        mesh.vertex_attributes.append(n)
        mesh.vertex_index.append(i)
        scene.world.addComponent(entity, VertexArray())
        shader = scene.world.addComponent(entity, ShaderGLDecorator(Shader(
            vertex_import_file=SHADER_DIR / "Phong.vert",
            fragment_import_file=SHADER_DIR / FRAGMENT_SHADER)))

        spheres.append((centre, trans, shader, exponent, shininess))


# ================================================================================================
# Systems and main loop
# ================================================================================================

transUpdate = scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
renderUpdate = scene.world.createSystem(RenderGLShaderSystem())
initUpdate = scene.world.createSystem(InitGLShaderSystem())

running = True
scene.init(imgui=True, windowWidth=winWidth, windowHeight=winHeight,
           windowTitle="Elements: Specular Exponent vs Shininess",
           openGLversion=4, customImGUIdecorator=ImGUIDecorator)

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

# Straight on, far enough back for the whole grid to fit. Eye and target share the same x/y, so
# the view direction stays parallel to -Z (no perspective skew across the grid); the shared offset
# just slides the grid clear of the ImGui panels in the top-left and along the bottom.
eye = util.vec(-0.62, 0.30, 7.3)
target = util.vec(-0.62, 0.30, 0.0)
up = util.vec(0.0, 1.0, 0.0)
view = util.lookat(eye, target, up)
projMat = util.perspective(50.0, winWidth / winHeight, 0.01, 100.0)

gWindow._myCamera = view  # otherwise, an imgui slider must be moved to properly update
gWindow._cameraEye = eye  # seed the world-space eye, so viewPos is correct before the first camera move

example_description = (
    "Sixteen identical spheres; only the material changes.\n\n"
    "Left to right : specularExponent 4, 16, 64, 256\n"
    "                -- the highlight gets TIGHTER.\n"
    "Top to bottom : shininess 0.2, 0.45, 0.7, 1.0\n"
    "                -- the highlight gets BRIGHTER.\n\n"
    "specularExponent sets the highlight's size, shininess only\n"
    "its intensity. Despite the name, shininess is not the\n"
    "'shininess exponent' of the textbooks -- that is the former.\n\n"
    "Move the camera with the mouse or the GUI. Hit ESC to quit."
)

while running:
    running = scene.render()
    displayGUI_text(example_description)
    scene.world.traverse_visit(transUpdate, scene.world.root)

    view = gWindow._myCamera
    # Offset of the live camera from the centre of the grid (which sits at the origin). Adding
    # this to each sphere's own centre gives every sphere the same relative viewer direction,
    # while still following the camera as you orbit -- see the note in the module docstring.
    view_offset = gWindow._cameraEye

    for centre, trans, shader, exponent, shininess in spheres:
        shader.setUniformVariable(key='modelViewProj', value=projMat @ view @ trans.l2world, mat4=True)
        shader.setUniformVariable(key='model', value=trans.l2world, mat4=True)
        shader.setUniformVariable(key='ambientColor', value=Lambientcolor, float3=True)
        shader.setUniformVariable(key='ambientStr', value=Lambientstr, float1=True)
        # Per-sphere light and viewer, both offset from this sphere's centre: identical lighting
        # geometry everywhere, so the material is the only variable in the picture.
        shader.setUniformVariable(key='viewPos', value=centre + view_offset, float3=True)
        shader.setUniformVariable(key='lightPos', value=centre + LIGHT_OFFSET, float3=True)
        shader.setUniformVariable(key='lightColor', value=Lcolor, float3=True)
        shader.setUniformVariable(key='lightIntensity', value=Lintensity, float1=True)
        # The two parameters this example is about.
        shader.setUniformVariable(key='shininess', value=shininess, float1=True)
        shader.setUniformVariable(key='specularExponent', value=exponent, float1=True)

    # Render after the uniforms are set, so this frame draws with this frame's camera.
    scene.world.traverse_visit(renderUpdate, scene.world.root)
    scene.render_post()

scene.shutdown()
