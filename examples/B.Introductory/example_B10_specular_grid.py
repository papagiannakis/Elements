"""
A materials chart: what the two specular parameters actually do.

Sixteen identical spheres, identical light, identical viewing angle. The only thing that changes
across the grid is the material:

    columns, left -> right : specularExponent  4, 16, 64, 256    (highlight gets TIGHTER)
    rows,    top  -> bottom: shininess       0.2, 0.45, 0.7, 1.0 (highlight gets STRONGER)

The two are easy to confuse, and the names do not help:

  * specularExponent is the power the cosine is raised to. It controls the SIZE of the highlight
    and nothing else. Low values smear a broad sheen over most of the sphere, which reads as
    chalky and rough; high values shrink it to a dot, which reads as hard and polished.

  * shininess is a plain multiplier on the specular term. It controls how BRIGHT the highlight is
    and does not change its shape at all. Despite the name, it is not the "shininess exponent" of
    the textbooks -- that is specularExponent above.

Read one row left to right and only the size changes; read one column top to bottom and only the
intensity changes. Top-left is a dull rough surface, bottom-right a hard polished one.

Each sphere gets its own light position and its own viewer position, each offset from that
sphere's own centre by the same vector. That way every sphere is lit and viewed from an identical
relative angle, so the material is the only variable left in the image. With a single shared
light, spheres at the edges of the grid would be lit at a different angle from those in the
middle, and material differences could not be told apart from position differences. Orbiting still
works: the offset is recomputed from the live camera every frame.
"""

import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, RenderMesh
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GUI.ImguiDecorator import ImGUIDecorator
from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray

from Elements.extensions.Shapes import geometry_factory
from Elements.utils.Shortcuts import displayGUI_text
from Elements.definitions import SHADER_DIR

example_description = \
"Sixteen identical spheres; only the material changes.\n\n\
Left to right : specularExponent 4, 16, 64, 256\n\
                -- the highlight gets TIGHTER.\n\
Top to bottom : shininess 0.2, 0.45, 0.7, 1.0\n\
                -- the highlight gets BRIGHTER.\n\n\
specularExponent sets the highlight's SIZE, shininess only its\n\
INTENSITY. Despite the name, shininess is not the 'shininess exponent'\n\
of the textbooks -- that is specularExponent.\n\n\
Every sphere is lit and viewed from the same relative angle, so what\n\
you see is the material and nothing else.\n\n\
Hold the RIGHT mouse button to fly, F for wireframe.\n\
Hit ESC OR Close the window to quit."

# ---------------- the two axes of the chart ----------------

#: Columns. The exponent the specular cosine is raised to -- the SIZE of the highlight.
SPECULAR_EXPONENTS = [4.0, 16.0, 64.0, 256.0]

#: Rows. A flat multiplier on the specular term -- the STRENGTH of the highlight.
SHININESS_VALUES = [0.2, 0.45, 0.7, 1.0]

#: Swap to "BlinnPhong.frag" to draw the same chart with the Blinn-Phong model instead. Its
#: highlights come out noticeably wider at equal exponents -- Blinn-Phong needs roughly 4x Phong's
#: exponent for a highlight of the same size, so the chart shifts about one column to the left.
FRAGMENT_SHADER = "Phong.frag"

#: A fairly saturated red, as in the classic textbook version of this chart. The highlights come
#: out white on top of it: Phong.frag applies the surface colour to the ambient and diffuse terms
#: only, leaving the specular the colour of the light -- which is what non-metals actually do.
SPHERE_COLOR = (0.62, 0.07, 0.05)

#: Deliberately dense: this chart is about material parameters, so the mesh must not add faceting
#: of its own. example_B9_shading_comparison.py is the opposite case, where a coarse mesh is the
#: whole point.
SPHERE_LAT, SPHERE_LON = 32, 32

SPHERE_DIAMETER = 0.92
SPACING = 1.18

# ---------------- light ----------------

#: Where the light sits relative to EACH sphere's own centre -- up, left and in front, so the
#: highlight lands in the upper left of every ball.
LIGHT_OFFSET = util.vec(-1.7, 2.0, 2.6)

Lambientcolor = util.vec(1.0, 1.0, 1.0)
Lambientstr = 0.22
Lcolor = util.vec(1.0, 1.0, 1.0)
Lintensity = 0.9

winWidth = 1200
winHeight = 800

# ---------------- the geometry, built once and shared by all sixteen ----------------

raw_v, raw_i, raw_c = geometry_factory.create_sphere({
    "lat": SPHERE_LAT, "lon": SPHERE_LON, "scale": [2.0, 2.0, 2.0], "color": list(SPHERE_COLOR)})
# Smooth normals: a highlight on a faceted sphere would be about the mesh, not the material.
v, i, c, n = geometry_factory.build_smooth_shaded_mesh(raw_v, raw_i, raw_c)

extent = raw_v[:, :3].max(axis=0) - raw_v[:, :3].min(axis=0)
sphere_scale = SPHERE_DIAMETER / float(extent.max())

# ---------------- the scene: RooT -> a 4 x 4 grid of spheres ----------------

scene = Scene()
rootEntity = scene.world.createEntity(Entity(name="RooT"))

n_cols = len(SPECULAR_EXPONENTS)
n_rows = len(SHININESS_VALUES)

#: (centre, BasicTransform, ShaderGLDecorator, exponent, shininess) per sphere.
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
            name=f"{name}_trans", trs=util.translate(x, y, 0.0) @ util.scale(sphere_scale)))
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

# ---------------- systems ----------------

initUpdate = scene.world.createSystem(InitGLShaderSystem())
renderUpdate = scene.world.createSystem(RenderGLShaderSystem())

# MAIN RENDERING LOOP

running = True
scene.init(imgui=True, windowWidth = winWidth, windowHeight = winHeight,
           windowTitle = "Elements: Specular Exponent vs Shininess", openGLversion = 4,
           customImGUIdecorator = ImGUIDecorator)

# pre-pass scenegraph to initialise all GL context dependent geometry, shader classes
# needs an active GL context
scene.world.traverse_visit(initUpdate, scene.world.root)

# ---------------- the window, the GUI and the camera ----------------

gWindow = scene.renderWindow
gGUI = scene.gContext

# Straight on, far enough back for the whole grid to fit. Eye and target share the same x/y, so the
# view direction stays parallel to -Z (no perspective skew across the grid); the shared offset just
# slides the grid clear of the ImGui panels in the top left and along the bottom.
eye = util.vec(-0.62, 0.30, 7.3)
target = util.vec(-0.62, 0.30, 0.0)
up = util.vec(0.0, 1.0, 0.0)
# also stores eye/target/up, which the mouse camera reads and the shaders need below as viewPos
gGUI.createViewMatrix(eye, target, up)

projMat = util.perspective(50.0, winWidth/winHeight, 0.01, 100.0)

while running:
    running = scene.render()
    displayGUI_text(example_description)

    view = gWindow._myCamera
    # Offset of the live camera from the centre of the grid, which sits at the origin. Adding it to
    # each sphere's own centre gives every sphere the same relative viewer direction, while still
    # following the camera as you orbit.
    view_offset = gWindow._cameraEye

    for centre, trans, shader, exponent, shininess in spheres:
        shader.setUniformVariable(key='modelViewProj', value=projMat @ view @ trans.trs, mat4=True)
        shader.setUniformVariable(key='model',value=trans.trs,mat4=True)
        shader.setUniformVariable(key='ambientColor',value=Lambientcolor,float3=True)
        shader.setUniformVariable(key='ambientStr',value=Lambientstr,float1=True)
        # Per-sphere light and viewer, both offset from this sphere's centre: identical lighting
        # geometry everywhere, so the material is the only variable in the picture.
        shader.setUniformVariable(key='viewPos',value=centre + view_offset,float3=True)
        shader.setUniformVariable(key='lightPos',value=centre + LIGHT_OFFSET,float3=True)
        shader.setUniformVariable(key='lightColor',value=Lcolor,float3=True)
        shader.setUniformVariable(key='lightIntensity',value=Lintensity,float1=True)
        # the two parameters this example is about
        shader.setUniformVariable(key='shininess',value=shininess,float1=True)
        shader.setUniformVariable(key='specularExponent',value=exponent,float1=True)

    # render after the uniforms are set, so this frame draws with this frame's camera
    scene.world.traverse_visit(renderUpdate, scene.world.root)
    scene.render_post()

scene.shutdown()
