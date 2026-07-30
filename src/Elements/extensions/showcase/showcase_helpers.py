"""
Helper classes behind example_picking_showcase.py, in the same folder. Each class below is a
self-contained "how do I do X" demo (load an OBJ with a shading toggle, a cubemap skybox, a
refractive material, a reflective material) that a course example can just import and call --
you don't need to read this file to use it, only if you're curious how a given feature works.

Every class follows the same two-step pattern as SceneBuilder in scene_helpers.py, and for the
same reason: Texture/Texture3D (and a couple of the factory functions below) issue real OpenGL
calls (glGenTextures, ...) in their own constructors, which needs a GL context to already exist.
So: build entities/meshes any time, but only bind actual images/cubemaps *after* scene.init().

  - ObjGallery: swap a single entity between a few OBJ models (default Teapot/Cow/Teddy) and
    between smooth/flat shading, as in Normals_USDimporter_BSP/cow_example.py.

  - Skybox: a big cube around the scene textured with a 6-image cube map, as in
    examples/2.Intermediate/example_10_cube_mapping.py -- off by default, texture set swappable.

  - RefractionShowcase: a "glass" object (Snell's-law refraction of the skybox), as in
    Refraction/refraction_example_bunny.py -- refractive index and which model to use are both
    swappable at runtime.

  - ReflectionShowcase: a "mirror" object (reflects the skybox, optionally tinted), as in
    environment_mapping/environment_mapping_pigs.py -- which model, and its tint color/strength
    (with Gold/Chrome/Blue presets), are both swappable at runtime.

Note on Refraction/ReflectionShowcase: both only reflect/refract the *skybox* cubemap, never
other scene objects (the nearby cubes/spheres won't show up in the pig or the glass model) --
this is inherent to static environment mapping (one pre-baked cubemap texture, sampled by
direction) and matches both reference examples above exactly, not a bug in this file. Making
other objects show up too needs a *dynamic* cubemap -- re-rendering the whole scene from each
reflective object's position, in all 6 directions, every frame -- which is a much bigger feature
(extra FBO/render-target plumbing, 6x render passes per affected object) than swapping textures.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import imgui

import Elements.pyECSS.math_utilities as util
# Elements.utils.normals's generateFlatNormalsMesh decides whether to explode a mesh into
# per-triangle vertices by checking the *vertex position array* for exact duplicate rows -- a
# check that silently does the wrong thing (falls back to smooth-like accumulated normals) the
# moment a model happens to have even one coincidental duplicate vertex position anywhere (teapot
# and cow both do). Normals_USDimporter_BSP's version checks the *index array* for shared
# indices instead, which is what actually determines whether triangles share vertices, so it
# doesn't have that failure mode -- it's what Normals_USDimporter_BSP/cow_example.py itself uses.
import Elements.extensions.Normals_USDimporter_BSP.normals as norm
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, RenderMesh
from Elements.pyGLV.GL.VertexArray import VertexArray
from Elements.pyGLV.GL.Shader import Shader, ShaderGLDecorator
from Elements.pyGLV.GL.Textures import get_texture_faces, Texture3D
from Elements.definitions import MODEL_DIR, TEXTURE_DIR, SHADER_DIR
from Elements.extensions.Refraction.refraction_component import create_refractive_entity
from Elements.extensions.environment_mapping.environment_mapping import EnvironmentMapping

#: Refraction/refraction_example_bunny.py's bunny.obj and environment_mapping_pigs.py's pig model
#: both live next to their own example script, not under Elements.definitions.MODEL_DIR.
_EXTENSIONS_DIR = Path(__file__).resolve().parent.parent
BUNNY_PATH = _EXTENSIONS_DIR / "Refraction" / "bunny.obj"
PIG_PATH = _EXTENSIONS_DIR / "environment_mapping" / "pigs" / "models" / "pighighpoly1.obj"

#: Anywhere far outside the view frustum/far-clip-plane: the standard "hide this entity" trick
#: already used elsewhere in Elements (e.g. MultiLights_and_Normals's mul_lights_3cubes_flat.py).
#: Deliberately a translation, not a scale-to-zero -- a zero-scale model matrix is singular, and
#: refraction/reflection's shaders need to invert it (for the normal matrix), which would crash.
_HIDDEN_OFFSET = (100000.0, 100000.0, 100000.0)


# ================================================================================================
# Shared OBJ loading (used by all four classes below)
# ================================================================================================

_raw_obj_cache = {}


def _load_obj_raw(path):
    """
    Minimal, robust Wavefront OBJ reader: pulls vertex positions ("v x y z") and faces ("f ..."),
    accepting v, v/vt and v/vt/vn face-index formats. Faces with more than 3 vertices (quads,
    n-gons) are fan-triangulated -- (v0,v1,v2), (v0,v2,v3), ... -- the same convention
    Elements.utils.objimporter.wavefront.Wavefront uses for quads; reading only a face's first 3
    vertices, as an earlier version of this function did, silently drops half the surface of any
    quad-only mesh (e.g. environment_mapping_pigs.py's pighighpoly1.obj, which is 100% quads).
    Based on the parser in Refraction/refraction_example_bunny.py, generalized here so every
    model in this file (teapot/cow/teddy/sphere/bunny/pig) goes through the same, more tolerant
    reader instead of Elements.utils.obj_to_mesh's stricter "v1//vn1" assumption.
    Cached by path -- switching back to a model you've already picked doesn't re-read the file.
    """
    key = str(path)
    if key in _raw_obj_cache:
        return _raw_obj_cache[key]

    vertices = []
    indices = []
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if parts[0] == "v":
                try:
                    vertices.append([float(parts[1]), float(parts[2]), float(parts[3]), 1.0])
                except (ValueError, IndexError):
                    continue
            elif parts[0] == "f":
                try:
                    face = [int(p.split("/")[0]) - 1 for p in parts[1:]]
                    for i in range(1, len(face) - 1):
                        indices.extend((face[0], face[i], face[i + 1]))
                except (ValueError, IndexError):
                    continue

    result = (np.array(vertices, dtype=np.float32), np.array(indices, dtype=np.uint32))
    _raw_obj_cache[key] = result
    return result


def load_obj_mesh(path, color=(0.66, 0.66, 0.82)):
    """(vertices, indices, colors) for one OBJ file -- colors is a flat per-vertex color, since
    plain Wavefront files don't carry one. Add normals afterwards, e.g. with
    Elements.utils.normals.generateSmoothNormalsMesh/generateFlatNormalsMesh."""
    vertices, indices = _load_obj_raw(path)
    colors = np.array([[*color, 1.0]] * len(vertices), dtype=np.float32)
    return vertices, indices, colors


def _skybox_box_geometry(size):
    lo, hi = -size, size
    vertices = np.array([
        [lo, lo, hi, 1.0], [lo, hi, hi, 1.0], [hi, hi, hi, 1.0], [hi, lo, hi, 1.0],
        [lo, lo, lo, 1.0], [lo, hi, lo, 1.0], [hi, hi, lo, 1.0], [hi, lo, lo, 1.0],
    ], dtype=np.float32)
    indices = np.array((
        1, 0, 3, 1, 3, 2, 2, 3, 7, 2, 7, 6, 3, 0, 4, 3, 4, 7,
        6, 5, 1, 6, 1, 2, 4, 5, 6, 4, 6, 7, 5, 4, 0, 5, 0, 1,
    ), np.uint32)
    return vertices, indices


def load_cubemap(texture_set_name):
    """A Texture3D for one of TEXTURE_DIR/Skyboxes/<name>'s front/back/top/bottom/left/right.jpg.
    Call only after scene.init() -- Texture3D() issues real GL calls in its own constructor."""
    folder = TEXTURE_DIR / "Skyboxes" / texture_set_name
    face_data = get_texture_faces(
        folder / "front.jpg", folder / "back.jpg", folder / "top.jpg",
        folder / "bottom.jpg", folder / "left.jpg", folder / "right.jpg",
    )
    return Texture3D(face_data)


# ================================================================================================
# 1. ObjGallery
# ================================================================================================

class ObjGallery:
    """
    A single OBJ-model entity you can swap between a few named models, and toggle between smooth
    and flat shading -- as in Normals_USDimporter_BSP/cow_example.py. Lit by a plain single-light
    Phong shader (SHADER_DIR / "Phong.frag"): not shadow-mapped, and only lit by one light (lights[0] of
    whatever LightManager you pass to update_lighting()), unlike SceneBuilder's objects.
    """

    #: (obj path, uniform scale) -- 0.1 for teapot/cow matches the scale already used elsewhere in
    #: Elements (objectPicker_example.py, Normals_USDimporter_BSP/cow_example.py); teddy/sphere
    #: are untested elsewhere, adjust here if they look mis-sized.
    DEFAULT_MODELS = {
        "Teapot": (MODEL_DIR / "teapot.obj", 0.1),
        "Cow": (MODEL_DIR / "cow.obj", 0.1),
        # teddy.obj's raw bounding box is ~5x cow's, so it needs a much smaller scale to end up a
        # similar size once placed in the scene.
        "Teddy": (MODEL_DIR / "teddy.obj", 0.02),
    }

    def __init__(self, scene, root_entity, position=(0.0, 0.0, 0.0), color=(168 / 255, 168 / 255, 210 / 255),
                 models=None, scale_multiplier=1.0):
        self.scene = scene
        self.models = dict(models or self.DEFAULT_MODELS)
        self.position = position
        self.color = color
        self.scale_multiplier = scale_multiplier
        self.current_name = next(iter(self.models))
        self.smooth = True
        self.show_normals_as_color = False
        self._cache = {}

        self.entity = scene.world.createEntity(Entity(name="ObjGallery"))
        scene.world.addEntityChild(root_entity, self.entity)
        self.trans = scene.world.addComponent(self.entity, BasicTransform(name="ObjGallery_TRS", trs=util.identity()))
        self.mesh = scene.world.addComponent(self.entity, RenderMesh(name="ObjGallery_Mesh"))
        scene.world.addComponent(self.entity, VertexArray())
        self.shader = scene.world.addComponent(
            self.entity, ShaderGLDecorator(Shader(vertex_import_file=SHADER_DIR / "Phong.vert", fragment_import_file=SHADER_DIR / "Phong.frag"))
        )
        self._apply_mesh()

    @property
    def pickable_objects(self):
        """{entity_name: BasicTransform} -- merge into the same lookup as SceneBuilder's
        builder.objects so a picking-buffer click on this entity can orbitCamera.focus_on() it."""
        return {self.entity.name: self.trans}

    def _mesh_data(self, name):
        if name not in self._cache:
            path, scale = self.models[name]
            vertices, indices, colors = load_obj_mesh(path, self.color)
            v_smooth, i_smooth, c_smooth, n_smooth = norm.generateSmoothNormalsMesh(vertices, indices, colors)
            v_flat, i_flat, c_flat, n_flat = norm.generateFlatNormalsMesh(vertices, indices, colors)
            self._cache[name] = {
                "scale": scale,
                # Every model's own local origin sits somewhere different relative to its base
                # (teapot.obj's is already at its base; cow.obj/teddy.obj's are well above it) --
                # min_y (in local/object space, before scaling) is how far below the origin each
                # model's lowest point is, so _apply_mesh() can lift each one by just enough to
                # keep its base at self.position's y instead of the terrain cutting through it.
                "min_y": float(vertices[:, 1].min()),
                # cn_* is normal*0.5+0.5 -- normal components run -1..1, colors need to be 0..1, so
                # this is the standard "normal as color" debug-view remap, as in cow_example.py.
                "smooth": (v_smooth, i_smooth, c_smooth, n_smooth, n_smooth * 0.5 + 0.5),
                "flat": (v_flat, i_flat, c_flat, n_flat, n_flat * 0.5 + 0.5),
            }
        return self._cache[name]

    def _apply_mesh(self):
        data = self._mesh_data(self.current_name)
        v, i, c, n, cn = data["smooth" if self.smooth else "flat"]
        self.mesh.vertex_attributes = [v, cn if self.show_normals_as_color else c, n]
        self.mesh.vertex_index = [i]
        s = data["scale"] * self.scale_multiplier
        lift = -data["min_y"] * s
        x, y, z = self.position
        self.trans.trs = util.translate(x, y + lift, z) @ util.scale(s, s, s)

    def update_lighting(self, light_manager, view_position, ambient_color=(1.0, 1.0, 1.0), ambient_strength=0.3, shininess=0.4):
        """Call once per frame."""
        primary = light_manager.primary
        self.shader.setUniformVariable(key="ambientColor", value=ambient_color, float3=True)
        self.shader.setUniformVariable(key="ambientStr", value=ambient_strength, float1=True)
        self.shader.setUniformVariable(key="viewPos", value=view_position, float3=True)
        self.shader.setUniformVariable(key="lightPos", value=primary.position, float3=True)
        self.shader.setUniformVariable(key="lightColor", value=primary.color, float3=True)
        self.shader.setUniformVariable(key="lightIntensity", value=primary.intensity, float1=True)
        self.shader.setUniformVariable(key="shininess", value=shininess, float1=True)
        self.shader.setUniformVariable(key="matColor", value=self.color, float3=True)

    def update_transform(self, projection, view):
        """Call once per frame."""
        mvp = projection @ view @ self.trans.l2world
        self.shader.setUniformVariable(key="modelViewProj", value=mvp, mat4=True)
        self.shader.setUniformVariable(key="model", value=self.trans.l2world, mat4=True)

    def draw_panel(self):
        """
        Draws the "Object Viewer" ImGui window. Returns (opened, changed): `changed` is True the
        frame you switch object/shading, which means the caller must re-run
        scene.world.traverse_visit(initUpdate, scene.world.root) right afterwards to re-upload
        the new mesh to the GPU -- exactly what cow_example.py does in its own main loop.
        """
        expanded, opened = imgui.begin("Object Viewer", True)
        names = list(self.models.keys())
        idx = names.index(self.current_name)
        changed_obj, idx = imgui.combo("Object", idx, names)
        shading_idx = 0 if self.smooth else 1
        changed_shade, shading_idx = imgui.combo("Shading", shading_idx, ["Smooth", "Flat"])
        changed_normals, self.show_normals_as_color = imgui.checkbox("Normals as Color", self.show_normals_as_color)
        imgui.end()

        changed = changed_normals
        if changed_obj and names[idx] != self.current_name:
            self.current_name = names[idx]
            changed = True
        new_smooth = shading_idx == 0
        if changed_shade and new_smooth != self.smooth:
            self.smooth = new_smooth
            changed = True
        if changed:
            self._apply_mesh()
        return opened, changed


# ================================================================================================
# 2. Skybox
# ================================================================================================

#: SHADER_DIR / "StaticSkybox.vert"/".frag" (example_10_cube_mapping.py's skybox shader) always draws --
#: it has no "model" uniform at all (deliberately: a skybox always surrounds the camera,
#: ignoring any transform), so there's no transform-based trick to hide it with. This is the
#: same fragment shader plus one line so it can actually be turned off.
#: plain Shader/ShaderGLDecorator (unlike ShadowShader) has no boolean uniform helper, only
#: float/mat -- so "enabled" is a float (1.0/0.0) here, not a GLSL bool.
_SKYBOX_FRAG_TOGGLEABLE = """
    #version 410
    out vec4 FragColor;
    in vec3 TexCoords;
    uniform samplerCube cubemap;
    uniform float enabled;
    void main() {
        if (enabled < 0.5) discard;
        FragColor = texture(cubemap, TexCoords);
    }
"""


class Skybox:
    """
    A big cube around the whole scene, textured with a 6-image cube map (as in
    examples/2.Intermediate/example_10_cube_mapping.py). Off by default (pass enabled=True to
    start with it on); its texture set (a folder under TEXTURE_DIR/Skyboxes) is swappable at
    runtime and cached once loaded.
    """

    #: Skyboxes/Day_Sunless isn't shipped with matching front/back/top/bottom/left/right.jpg
    #: files (only .png), so load_cubemap() 404s on it -- left out until that asset exists.
    DEFAULT_TEXTURE_SETS = ("Sea", "Cloudy")

    def __init__(self, scene, root_entity, size=30.0, texture_sets=None, enabled=False):
        self.scene = scene
        self.texture_sets = list(texture_sets or self.DEFAULT_TEXTURE_SETS)
        self.enabled = enabled
        self.current_set = self.texture_sets[0]
        self._cubemap_cache = {}

        self.entity = scene.world.createEntity(Entity(name="Skybox"))
        scene.world.addEntityChild(root_entity, self.entity)
        self.trans = scene.world.addComponent(self.entity, BasicTransform(name="Skybox_TRS", trs=util.identity()))
        mesh = scene.world.addComponent(self.entity, RenderMesh(name="Skybox_Mesh"))

        vertices, indices = _skybox_box_geometry(size)
        vertices, indices, _ = norm.generateUniqueVertices(vertices, indices)
        mesh.vertex_attributes.append(vertices)
        mesh.vertex_index.append(indices)
        scene.world.addComponent(self.entity, VertexArray())
        self.shader = scene.world.addComponent(
            self.entity, ShaderGLDecorator(Shader(vertex_import_file=SHADER_DIR / "StaticSkybox.vert", fragment_source=_SKYBOX_FRAG_TOGGLEABLE))
        )

    def load_textures(self):
        """Call once, after scene.init() -- Texture3D() needs a live GL context."""
        self.set_texture_set(self.current_set)

    @property
    def cubemap(self):
        """The currently-active Texture3D, e.g. to share with RefractionShowcase/ReflectionShowcase
        so they reflect/refract the same sky. None until load_textures() has been called."""
        return self._cubemap_cache.get(self.current_set)

    def set_texture_set(self, name):
        if name not in self._cubemap_cache:
            self._cubemap_cache[name] = load_cubemap(name)
        self.current_set = name
        self.shader.component.texture3DDict["cubemap"] = self._cubemap_cache[name]

    def update(self, projection, view):
        """Call once per frame."""
        self.shader.setUniformVariable(key="Proj", value=projection, mat4=True)
        self.shader.setUniformVariable(key="View", value=view, mat4=True)
        self.shader.setUniformVariable(key="enabled", value=1.0 if self.enabled else 0.0, float1=True)

    def draw_panel(self):
        """Draws the "Skybox" ImGui window. Returns (opened, texture_changed) -- if
        texture_changed, the caller may want to rebind the same cubemap to
        RefractionShowcase/ReflectionShowcase via their load_textures(skybox.cubemap)."""
        expanded, opened = imgui.begin("Skybox", True)
        _, self.enabled = imgui.checkbox("Enabled", self.enabled)
        idx = self.texture_sets.index(self.current_set)
        changed_set, idx = imgui.combo("Texture Set", idx, self.texture_sets)
        if changed_set:
            self.set_texture_set(self.texture_sets[idx])
        imgui.end()
        return opened, changed_set


# ================================================================================================
# 3. RefractionShowcase
# ================================================================================================

class RefractionShowcase:
    """
    A refractive ("glass") object -- Snell's-law bending of the skybox behind it -- as in
    Refraction/refraction_example_bunny.py. Every model in `models` is built once up front (the
    bunny is ~35k triangles, so switching to/from it has no load hitch); only the picked one is
    ever visible or lit, the rest are parked far away (see _HIDDEN_OFFSET above).
    """

    #: (obj path, uniform scale), picked from each model's raw bounding box so they all end up a
    #: comparable size once placed in the scene -- 2x the size that comparison originally landed
    #: on, so the showcase object reads clearly against the rest of the scene.
    DEFAULT_MODELS = {
        "Bunny": (BUNNY_PATH, 1.0),
        "Teapot": (MODEL_DIR / "teapot.obj", 0.4),
        "Cow": (MODEL_DIR / "cow.obj", 0.25),
        "Teddy": (MODEL_DIR / "teddy.obj", 0.07),
        "Sphere": (MODEL_DIR / "sphere.obj", 0.8),
    }

    def __init__(self, scene, root_entity, position=(0.0, 0.0, 0.0), models=None):
        self.scene = scene
        self.models = dict(models or self.DEFAULT_MODELS)
        self.position = position
        self.current_name = "Bunny" if "Bunny" in self.models else next(iter(self.models))
        self.ref_index = 1.52  # glass
        self.ratio = 1.0 / self.ref_index

        self.entities = {}  # name -> (entity, trans, shader, scale, min_y)
        for name, (path, scale) in self.models.items():
            vertices, indices = _load_obj_raw(path)
            _entity, trans, shader = create_refractive_entity(scene, root_entity, f"Refraction_{name}", vertices, indices)
            # Every model's own local origin sits somewhere different relative to its base --
            # min_y (in local/object space, before scaling) is how far below the origin each
            # model's lowest point is, so _apply_visibility() can lift each one by just enough to
            # keep its base at self.position's y instead of sinking into the terrain, the same fix
            # ObjGallery already applies for its own models.
            min_y = float(vertices[:, 1].min())
            self.entities[name] = (_entity, trans, shader, scale, min_y)
        self._apply_visibility()

    @property
    def pickable_objects(self):
        """{entity_name: BasicTransform} for every model variant (hidden ones included -- they're
        parked off-screen, see _HIDDEN_OFFSET, so only the visible one is ever actually clickable)
        -- merge into the same lookup as SceneBuilder's builder.objects."""
        return {entity.name: trans for entity, trans, _shader, _scale, _min_y in self.entities.values()}

    def load_textures(self, cubemap):
        """Bind the shared environment cubemap (a Texture3D, e.g. skybox.cubemap) to every model
        variant. Call after scene.init()."""
        for _entity, _trans, shader, _scale, _min_y in self.entities.values():
            shader.component.texture3DDict["cubemap"] = cubemap

    def set_model(self, name):
        if name == self.current_name:
            return
        self.current_name = name
        self._apply_visibility()

    def _apply_visibility(self):
        for name, (_entity, trans, _shader, scale, min_y) in self.entities.items():
            if name == self.current_name:
                x, y, z = self.position
                trans.trs = util.translate(x, y - scale * min_y, z) @ util.scale(scale, scale, scale)
            else:
                trans.trs = util.translate(*_HIDDEN_OFFSET)

    def update(self, projection, view, camera_eye):
        """
        Call once per frame. Updates every model variant (not just the visible one): each
        shader's own "model" uniform must track its own (possibly off-screen) transform, or a
        previously-visible model would keep rendering at its old position once hidden.
        """
        for _entity, trans, shader, _scale, _min_y in self.entities.values():
            model = trans.l2world
            shader.setUniformVariable(key="projection", value=projection, mat4=True)
            shader.setUniformVariable(key="view", value=view, mat4=True)
            shader.setUniformVariable(key="model", value=model, mat4=True)
            shader.setUniformVariable(key="normalMatrix", value=np.linalg.inv(np.transpose(model)), mat4=True)
            shader.setUniformVariable(key="camPos", value=camera_eye, float3=True)
            shader.setUniformVariable(key="u_Ratio", value=self.ratio, float1=True)

    def draw_panel(self):
        """Draws the "Refraction" ImGui window. Returns whether it's still open."""
        expanded, opened = imgui.begin("Refraction", True)
        names = list(self.models.keys())
        idx = names.index(self.current_name)
        changed, idx = imgui.combo("Object", idx, names)
        if changed:
            self.set_model(names[idx])

        imgui.separator()
        _, self.ref_index = imgui.slider_float("Refractive Index", self.ref_index, 1.0, 2.5)
        self.ratio = 1.0 / self.ref_index
        imgui.text(f"Ratio 1/R: {self.ratio:.4f}")
        imgui.separator()
        imgui.text("Air 1.00   Water 1.33   Glass 1.52   Diamond 2.42")
        imgui.end()
        return opened


# ================================================================================================
# 4. ReflectionShowcase
# ================================================================================================

class ReflectionShowcase:
    """
    A reflective ("mirror") object -- reflects the skybox, optionally tinted -- as in
    environment_mapping/environment_mapping_pigs.py. Every model in `models` is built once up
    front; only the picked one is ever visible, the rest are parked far away.

    Unlike the other three classes, this one's shader can only be created *after* scene.init():
    EnvironmentMapping.apply() creates a real GL texture (a 1x1 placeholder cubemap) even if you
    don't give it one yet, so build_shaders() has to run once a GL context exists -- see its
    docstring.
    """

    PRESETS = {
        "Gold": ((1.0, 0.8, 0.0), 0.7),
        "Chrome": ((1.0, 1.0, 1.0), 0.0),
        "Blue": ((0.2, 0.2, 1.0), 0.5),
    }

    #: (obj path, uniform scale), picked from each model's raw bounding box so they all end up a
    #: comparable size once placed in the scene -- 2x the size that comparison originally landed
    #: on, so the showcase object reads clearly against the rest of the scene.
    DEFAULT_MODELS = {
        "Pig": (PIG_PATH, 1.5),
        "Teapot": (MODEL_DIR / "teapot.obj", 0.4),
        "Cow": (MODEL_DIR / "cow.obj", 0.25),
        "Teddy": (MODEL_DIR / "teddy.obj", 0.07),
        "Sphere": (MODEL_DIR / "sphere.obj", 0.8),
    }

    def __init__(self, scene, root_entity, position=(0.0, 0.0, 0.0), models=None):
        self.scene = scene
        self.root_entity = root_entity
        self.models = dict(models or self.DEFAULT_MODELS)
        self.position = position
        self.current_name = "Pig" if "Pig" in self.models else next(iter(self.models))
        preset_color, preset_strength = self.PRESETS["Gold"]
        self.tint_color = list(preset_color)
        self.tint_strength = preset_strength

        self.entities = {}  # name -> (entity, trans, scale, min_y) -- shaders come later, see build_shaders()
        for name, (path, scale) in self.models.items():
            vertices, indices, colors = load_obj_mesh(path)
            v, i, c, n = norm.generateSmoothNormalsMesh(vertices, indices, colors)
            entity = scene.world.createEntity(Entity(name=f"Reflection_{name}"))
            scene.world.addEntityChild(root_entity, entity)
            trans = scene.world.addComponent(entity, BasicTransform(name=f"Reflection_{name}_TRS", trs=util.identity()))
            mesh = scene.world.addComponent(entity, RenderMesh(name=f"Reflection_{name}_Mesh"))
            mesh.vertex_attributes.extend([v, c, n])
            mesh.vertex_index.append(i)
            scene.world.addComponent(entity, VertexArray())
            # Every model's own local origin sits somewhere different relative to its base --
            # min_y (in local/object space, before scaling) is how far below the origin each
            # model's lowest point is, so _apply_visibility() can lift each one by just enough to
            # keep its base at self.position's y instead of sinking into the terrain, the same fix
            # ObjGallery already applies for its own models.
            min_y = float(vertices[:, 1].min())
            self.entities[name] = (entity, trans, scale, min_y)

        self.shaders = {}  # filled in by build_shaders()
        self._apply_visibility()

    @property
    def pickable_objects(self):
        """{entity_name: BasicTransform} for every model variant (hidden ones included -- they're
        parked off-screen, see _HIDDEN_OFFSET, so only the visible one is ever actually clickable)
        -- merge into the same lookup as SceneBuilder's builder.objects."""
        return {entity.name: trans for entity, trans, _scale, _min_y in self.entities.values()}

    def build_shaders(self, cubemap):
        """
        Attaches the reflection shader (EnvironmentMapping.apply()) to every model variant. Call
        after scene.init(), then run scene.world.traverse_visit(initUpdate, scene.world.root)
        again afterwards so InitGLShaderSystem compiles these newly-added shaders too.
        """
        for name, (entity, _trans, _scale, _min_y) in self.entities.items():
            self.shaders[name] = EnvironmentMapping.apply(
                entity, self.scene, cubemap=cubemap, tint_color=self.tint_color, tint_strength=self.tint_strength
            )

    def rebind_cubemap(self, cubemap):
        """Update every model variant's environment map, e.g. after Skybox's texture set changes.
        Call after build_shaders()."""
        for shader in self.shaders.values():
            shader.component.texture3DDict["environmentMap"] = cubemap

    def set_model(self, name):
        if name == self.current_name:
            return
        self.current_name = name
        self._apply_visibility()

    def set_preset(self, preset_name):
        color, strength = self.PRESETS[preset_name]
        self.tint_color = list(color)
        self.tint_strength = strength
        self._apply_tint()

    def _apply_visibility(self):
        for name, (_entity, trans, scale, min_y) in self.entities.items():
            if name == self.current_name:
                x, y, z = self.position
                trans.trs = util.translate(x, y - scale * min_y, z) @ util.scale(scale, scale, scale)
            else:
                trans.trs = util.translate(*_HIDDEN_OFFSET)

    def _apply_tint(self):
        shader = self.shaders.get(self.current_name)
        if shader is None:
            return
        shader.setUniformVariable(key="tintColor", value=self.tint_color, float3=True)
        shader.setUniformVariable(key="tintStrength", value=self.tint_strength, float1=True)

    def update(self, projection, view, camera_eye):
        """Call once per frame, after build_shaders(). Updates every model variant, for the same
        reason as RefractionShowcase.update()."""
        for name, (_entity, trans, _scale, _min_y) in self.entities.items():
            shader = self.shaders.get(name)
            if shader is None:
                continue
            mvp = projection @ view @ trans.l2world
            shader.setUniformVariable(key="modelViewProj", value=mvp, mat4=True)
            shader.setUniformVariable(key="model", value=trans.l2world, mat4=True)
            shader.setUniformVariable(key="viewPos", value=camera_eye, float3=True)

    def draw_panel(self):
        """Draws the "Reflection" ImGui window. Returns whether it's still open."""
        expanded, opened = imgui.begin("Reflection", True)
        names = list(self.models.keys())
        idx = names.index(self.current_name)
        changed, idx = imgui.combo("Object", idx, names)
        if changed:
            self.set_model(names[idx])

        imgui.separator()
        imgui.text("Presets:")
        for preset_name in self.PRESETS:
            if imgui.button(preset_name):
                self.set_preset(preset_name)
            imgui.same_line()
        imgui.new_line()

        changed_c, tint = imgui.color_edit3("Tint Color", *self.tint_color)
        if changed_c:
            self.tint_color = list(tint)
            self._apply_tint()
        changed_s, self.tint_strength = imgui.slider_float("Tint Strength", self.tint_strength, 0.0, 1.0)
        if changed_s:
            self._apply_tint()
        imgui.end()
        return opened
