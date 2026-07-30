"""
Helper functions/classes behind example_picking_tutorial.py, in the same folder.

You do NOT need to understand this file to use it -- it exists so the tutorial script can read
like "add a cube here, add a sphere there" instead of being full of vertex buffers and shader
uniform names. If you're curious how add_cube() etc. actually work under the hood, keep reading;
otherwise just skip straight to example_picking_tutorial.py.

Four things live here:

  - SceneBuilder: one add_*() method per kind of object (cube, sphere, cylinder, cone, textured
    cube, terrain). Every object it creates is lit by every light in a LightManager and
    casts/receives real-time shadows (Elements.extensions.Shadows.ShadowShader).

  - LightManager: up to MAX_LIGHTS point/directional/spot lights (as in
    Elements.extensions.MultiLights_and_Normals's "Multi Lights" example), plus an ImGui panel to
    add/remove/edit them. Only lights[0] ("the primary light") can cast real-time shadows, and
    only while it's a Point light -- see its docstring for why.

  - ProjectionSettings: switches the camera between perspective and orthographic projection, with
    an ImGui panel that only shows the properties relevant to whichever one is selected.

  - OrbitCamera: turns "W/A/S/D rotates, +/- zooms, around whatever was last clicked" into three
    small pieces of state (radius, yaw, pitch) instead of it being spread across a main loop.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import sdl2
import imgui

import Elements.pyECSS.math_utilities as util
import Elements.utils.normals as norm
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, RenderMesh
from Elements.pyGLV.GL.VertexArray import VertexArray
from Elements.pyGLV.GL.Textures import Texture
from Elements.extensions.Shadows.ShadowShader import ShadowShader
from Elements.extensions.Shapes import geometry_factory
from Elements.definitions import SHADER_DIR


#: Fragment shader for every object SceneBuilder creates: Blinn-Phong lit by up to MAX_LIGHTS
#: point/directional/spot lights (same math as Elements.extensions.MultiLights_and_Normals's
#: PHONG_MULTI_LIGHTS.frag), plus real-time shadows sampled from a point-light cube map for
#: lights[0] only (same shadow math as ShadowShader.FRAG_POINT_PHONG). The vertex shader is
#: unchanged from ShadowShader.VERT_POINT_PHONG (SHADER_DIR / "PointPhong.vert") -- only the
#: lighting model in the fragment shader is different.
MULTI_LIGHT_FRAG = """
    #version 410
    #define MAX_LIGHTS 4

    struct Light {
        float type;     // 0 = point, 1 = directional, 2 = spot
        vec3 position;  // point & spot
        vec3 direction; // directional & spot
        vec3 color;
        float intensity;
        float cutoff;   // spot only, half-angle in degrees
    };

    out vec4 FragColor;
    in vec4 FragPos;
    in vec3 Normal;
    in vec2 TexCoords;
    in vec4 Color;

    uniform sampler2D ImageTexture;
    uniform bool useTexture;

    // Shadows: only ever sampled for lights[0], and only while it's a Point light.
    uniform samplerCube shadowMap;
    uniform float far_plane;
    uniform int uHasShadow;
    uniform int uSoftShadows;
    uniform float uPcfDisk;
    uniform float uShadowBias;

    uniform vec3 viewPos;
    uniform float numLights;
    uniform Light lights[MAX_LIGHTS];

    vec3 gridSamplingDisk[20] = vec3[](
       vec3(1, 1, 1), vec3( 1, -1, 1), vec3(-1, -1, 1), vec3(-1, 1, 1),
       vec3(1, 1, -1), vec3( 1, -1, -1), vec3(-1, -1, -1), vec3(-1, 1, -1),
       vec3(1, 1, 0), vec3( 1, -1, 0), vec3(-1, -1, 0), vec3(-1, 1, 0),
       vec3(1, 0, 1), vec3(-1, 0, 1), vec3( 1, 0, -1), vec3(-1, 0, -1),
       vec3(0, 1, 1), vec3( 0, -1, 1), vec3( 0, -1, -1), vec3( 0, 1, -1));

    float computeShadow(vec3 lightPos) {
        if (uHasShadow == 0) return 0.0;

        vec3 fragToLight = FragPos.xyz - lightPos;
        float currentDepth = length(fragToLight);
        float shadow = 0.0;

        if (uSoftShadows == 1) {
            int samples = 20;
            float diskRadius = (1.0 + (currentDepth / far_plane)) / 25.0;
            diskRadius *= max(uPcfDisk, 0.1);
            for (int i = 0; i < samples; ++i) {
                float val = texture(shadowMap, fragToLight + gridSamplingDisk[i] * diskRadius).r * far_plane;
                if (currentDepth - uShadowBias > val) shadow += 1.0;
            }
            shadow /= float(samples);
        } else {
            float val = texture(shadowMap, fragToLight).r * far_plane;
            if (currentDepth - uShadowBias > val) shadow = 1.0;
        }
        return shadow;
    }

    void main() {
        vec3 norm = normalize(Normal);
        vec3 viewDir = normalize(viewPos - FragPos.xyz);
        vec3 matColor = useTexture ? texture(ImageTexture, TexCoords).rgb : Color.rgb;

        vec3 result = vec3(0.0);
        int n = clamp(int(numLights), 0, MAX_LIGHTS);

        for (int i = 0; i < n; i++) {
            int type = int(lights[i].type);
            vec3 lightDir;
            if (type == 1) {
                lightDir = normalize(-lights[i].direction);        // directional: parallel rays
            } else {
                lightDir = normalize(lights[i].position - FragPos.xyz); // point & spot
            }

            if (type == 2) {
                // outside the spotlight's cone?
                float angle = degrees(acos(clamp(dot(normalize(lights[i].direction), -lightDir), -1.0, 1.0)));
                if (angle > lights[i].cutoff) continue;
            }

            float diffuseStr = max(dot(norm, lightDir), 0.0);
            vec3 diffuseProd = diffuseStr * lights[i].color;

            vec3 halfwayDir = normalize(lightDir + viewDir);
            float specularStr = pow(max(dot(norm, halfwayDir), 0.0), 64.0);
            vec3 specularProd = 0.5 * specularStr * lights[i].color;

            // Only the primary (index 0) Point light casts shadows in this simplified engine.
            float shadow = (i == 0 && type == 0) ? computeShadow(lights[i].position) : 0.0;

            result += (diffuseProd + specularProd) * lights[i].intensity * (1.0 - shadow);
        }

        vec3 ambientProd = 0.1 * matColor;
        FragColor = vec4(ambientProd + result * matColor, 1.0);
    }
"""


def create_cube_geometry():
    """The 8 corners/12 triangles of a 1x1x1 cube, sitting on top of y=0 (not centered on it)."""
    vertices = np.array([
        [-0.5, 0.0, 0.5, 1.0],
        [-0.5, 1.0, 0.5, 1.0],
        [0.5, 1.0, 0.5, 1.0],
        [0.5, 0.0, 0.5, 1.0],
        [-0.5, 0.0, -0.5, 1.0],
        [-0.5, 1.0, -0.5, 1.0],
        [0.5, 1.0, -0.5, 1.0],
        [0.5, 0.0, -0.5, 1.0],
    ])
    indices = np.array((
        1, 0, 3, 1, 3, 2,
        2, 3, 7, 2, 7, 6,
        3, 0, 4, 3, 4, 7,
        6, 5, 1, 6, 1, 2,
        4, 5, 6, 4, 6, 7,
        5, 4, 0, 5, 0, 1,
    ), np.uint32)
    return vertices, indices


class SceneBuilder:
    """
    Every add_*() call below spawns one Entity: a position, a shape, and (color=... or a real
    image) a look. Every one of them is automatically lit and shadowed by the scene's point light
    -- you don't set that up per-object.

    `position` is always the (x, y, z) of the object's *center*. `scale` is either one number
    (uniform) or an (sx, sy, sz) triple.

    self.objects: dict of name -> BasicTransform for every add_*() call (except add_terrain), so
    the tutorial script can look up "what did the user just click?" by name.
    """

    def __init__(self, scene, root_entity):
        self.scene = scene
        self.root_entity = root_entity
        self.objects = {}
        self._shaders = []
        self._shaders_by_name = {}

    # ---- the actual shapes ------------------------------------------------------------------

    def add_cube(self, name, position, scale=1.0, color=(0.8, 0.2, 0.2)):
        """A single flat-colored cube."""
        scale = (scale, scale, scale) if isinstance(scale, (int, float)) else tuple(scale)
        vertices, indices = create_cube_geometry()
        colors = np.array([[*color, 1.0]] * len(vertices), dtype=np.float32)
        vertices, indices, colors, normals = norm.generateFlatNormalsMesh(vertices, indices, colors)
        trs = util.translate(*position) @ util.scale(*scale)
        return self._add_entity(name, trs, vertices, indices, colors, normals)

    def add_sphere(self, name, position, scale=1.0, color=(0.8, 0.8, 0.8), lat=24, lon=24):
        """A UV sphere. `lat`/`lon` control how round it looks (more = smoother, slower to build)."""
        return self.add_shape(name, "sphere", position, scale=scale, color=color, lat=lat, lon=lon)

    def add_cylinder(self, name, position, scale=1.0, color=(0.8, 0.8, 0.8), radius=0.5, height=1.0, segments=24):
        return self.add_shape(
            name, "cylinder", position, scale=scale, color=color, radius=radius, height=height, segments=segments
        )

    def add_cone(self, name, position, scale=1.0, color=(0.8, 0.8, 0.8), radius=0.5, height=1.0, segments=24):
        return self.add_shape(
            name, "cone", position, scale=scale, color=color, radius=radius, height=height, segments=segments
        )

    def add_torus(self, name, position, scale=1.0, color=(0.8, 0.8, 0.8), radius=0.5, tube_radius=None,
                   major_segments=30, minor_segments=20):
        """A torus (ring/donut) -- `radius` is the distance from its center to the middle of the
        tube, `tube_radius` is the tube's own thickness (defaults to 35% of `radius`)."""
        shape_params = dict(radius=radius, major_segments=major_segments, minor_segments=minor_segments)
        if tube_radius is not None:
            shape_params["tube_radius"] = tube_radius
        return self.add_shape(name, "torus", position, scale=scale, color=color, **shape_params)

    def add_shape(self, name, shape_type, position, scale=1.0, color=(0.8, 0.8, 0.8), **shape_params):
        """
        The general-purpose version of add_sphere()/add_cylinder()/add_cone()/add_torus(): builds
        anything Elements.extensions.Shapes.geometry_factory knows how to make --
        shape_type is one of "sphere", "cylinder", "cone", "torus", "pyramid",
        "triangular_pyramid", "plane", "rectangular_prism" (a box; "cube" also works but
        add_cube() above is the simpler way to get one). Extra keyword arguments (radius=,
        height=, segments=, lat=, lon=, ...) are forwarded straight to geometry_factory -- see
        that file for what each shape accepts.
        """
        scale = [scale, scale, scale] if isinstance(scale, (int, float)) else list(scale)
        params = {"scale": scale, "color": list(color), **shape_params}
        vertices, indices, colors, normals = geometry_factory.build_render_mesh(shape_type, params)
        return self._add_entity(name, util.translate(*position), vertices, indices, colors, normals)

    def add_textured_cube(self, name, position, scale=1.0):
        """
        A cube wrapped in a real image instead of a flat color. Two steps, because binding an
        image needs a GL window to already exist:
            builder.add_textured_cube("Dice", position=(0, 0.5, 0))     # anytime
            ... scene.init(...) ...
            builder.apply_texture("Dice", TEXTURE_DIR / "3x3.jpg")      # only after scene.init()
        """
        scale_vec = [scale, scale, scale]
        raw_vertices, raw_indices, uv = geometry_factory.create_textured_mesh("cube", {"scale": scale_vec})
        # ShadowShader always expects a per-vertex color even when it's about to be overridden by
        # a texture; plain white keeps the lighting math correct without tinting the image.
        placeholder_colors = np.ones((raw_vertices.shape[0], 4), dtype=np.float32)
        vertices, indices, colors, normals = norm.generateFlatNormalsMesh(raw_vertices, raw_indices, placeholder_colors)
        return self._add_entity(
            name, util.translate(*position), vertices, indices, colors, normals,
            uv=np.asarray(uv, dtype=np.float32), textured=True,
        )

    def add_terrain(self, size=(12.0, 9.0), thickness=0.05, color=(0.55, 0.55, 0.58)):
        """
        The ground plane every object sits on (its top surface is at y ~= 0). It has a little
        real thickness rather than being a flat, zero-thickness quad: without it, the underside
        is literally the same surface as the top (just viewed from behind), so it shows the exact
        same shadows as the top when seen from below ground -- with real thickness, the
        underside is its own separate, physically-lower surface that just renders as a plain
        dark slab instead.
        """
        width, depth = size
        vertices, indices, colors, normals = geometry_factory.build_render_mesh(
            "rectangular_prism", {"scale": [width, thickness, depth], "color": list(color)}
        )
        # the extra -0.001 keeps the top surface from sitting *exactly* at the same height as
        # objects resting on it (e.g. add_cube()'s base), which would cause z-fighting flicker
        trs = util.translate(0, -0.5 * thickness - 0.001, 0)
        return self._add_entity("Terrain", trs, vertices, indices, colors, normals, pickable=False)

    # ---- one-time setup / per-frame updates -------------------------------------------------

    def init_shaders(self):
        """Call once, right after scene.init(): compiles every add_*() call's shader. (Needs a
        live GL context, which is why it can't happen inside add_*() itself.)"""
        for shader in self._shaders:
            shader.init()

    def apply_texture(self, name, image_path):
        """Bind an image to a cube made with add_textured_cube(name, ...). Call after
        scene.init(), for the same reason as init_shaders()."""
        texture = Texture(image_path)
        self._shaders_by_name[name].setUniformVariable(key="ImageTexture", value=texture, texture=True)
        return texture

    def update_lighting(
        self, projection, view, light_manager, view_position,
        *, shadows_enabled=True, soft_shadows=True, pcf_radius=0.5, shadow_bias=0.15,
    ):
        """
        Call once per frame, before rendering, to push the camera/lights/shadow-quality settings
        to every object add_*() has created so far. (Each object's own position -- the "model"
        matrix -- and the shadow map itself are handled separately, inside ShadowMappingSystem.)
        """
        has_shadow = shadows_enabled and light_manager.primary.light_type == "point"
        for shader in self._shaders:
            shader.setUniformVariable(key="projection", value=projection, mat4=True)
            shader.setUniformVariable(key="view", value=view, mat4=True)
            shader.setUniformVariable(key="uHasShadow", value=1 if has_shadow else 0, boolean=True)
            shader.setUniformVariable(key="uSoftShadows", value=1 if soft_shadows else 0, boolean=True)
            shader.setUniformVariable(key="uPcfDisk", value=pcf_radius, float1=True)
            shader.setUniformVariable(key="uShadowBias", value=shadow_bias, float1=True)
            light_manager.apply_to(shader, view_position)

    # ---- shared plumbing every add_*() method above delegates to ---------------------------

    def _add_entity(self, name, trs, vertices, indices, colors, normals, uv=None, textured=False, pickable=True):
        entity = self.scene.world.createEntity(Entity(name=name))
        self.scene.world.addEntityChild(self.root_entity, entity)
        trans = self.scene.world.addComponent(entity, BasicTransform(name=f"{name}_TRS", trs=trs))
        mesh = self.scene.world.addComponent(entity, RenderMesh(name=f"{name}_Mesh"))

        mesh.vertex_attributes.append(vertices)
        mesh.vertex_attributes.append(colors)
        mesh.vertex_attributes.append(normals)
        mesh.vertex_attributes.append(uv if uv is not None else np.zeros((vertices.shape[0], 2), dtype=np.float32))
        mesh.vertex_index.append(indices)

        self.scene.world.addComponent(entity, VertexArray())
        shader = self.scene.world.addComponent(
            entity,
            ShadowShader(name=f"{name}_Shader", vertex_import_file=SHADER_DIR / "PointPhong.vert", fragment_source=MULTI_LIGHT_FRAG),
        )
        shader.setUniformVariable(key="useTexture", value=1 if textured else 0, boolean=True)

        self._shaders.append(shader)
        self._shaders_by_name[name] = shader
        if pickable:
            self.objects[name] = trans
        return trans, shader


_LIGHT_TYPES = ("point", "directional", "spot")


@dataclass
class Light:
    """One light: light_type is "point", "directional" or "spot". `position` is used by point
    and spot; `direction` by directional and spot; `cutoff_degrees` (half-angle of the cone) only
    by spot."""

    name: str
    light_type: str = "point"
    position: list = field(default_factory=lambda: [4.0, 8.0, 5.0])
    direction: list = field(default_factory=lambda: [0.0, -1.0, 0.0])
    color: list = field(default_factory=lambda: [1.0, 1.0, 1.0])
    intensity: float = 1.0
    cutoff_degrees: float = 20.0


class LightManager:
    """
    Up to MAX_LIGHTS lights (point/directional/spot -- see Light above), with an ImGui panel
    (draw_panel()) to add/remove/edit them at runtime.

    lights[0] is "the primary light": its position is what ShadowMappingSystem generates the
    real-time shadow map from. This simplified engine only supports ONE shadow-casting light, and
    only while it's a Point light (real-time shadows for Directional/Spot lights need a
    differently-shaped depth map that this scene's ShadowMappingSystem isn't set up for) --
    switching lights[0] to Directional or Spot still lights the scene, it just stops casting
    shadows until it's switched back to Point.
    """

    MAX_LIGHTS = 4

    def __init__(self, position=(4.0, 8.0, 5.0), color=(1.0, 1.0, 1.0)):
        self.lights = [Light("Light_0", "point", list(position), [0.0, -1.0, 0.0], list(color))]

    @property
    def primary(self):
        return self.lights[0]

    def add_light(self, light_type="point"):
        if len(self.lights) >= self.MAX_LIGHTS:
            return None
        light = Light(f"Light_{len(self.lights)}", light_type)
        self.lights.append(light)
        return light

    def remove_light(self, index):
        """index 0 (the primary, shadow-casting light) can't be removed."""
        if index <= 0 or index >= len(self.lights):
            return
        del self.lights[index]

    def apply_to(self, shader, view_position):
        """Push every light's uniforms to one object's shader. Called by
        SceneBuilder.update_lighting() -- you don't need to call this yourself."""
        shader.setUniformVariable(key="viewPos", value=view_position, float3=True)
        shader.setUniformVariable(key="numLights", value=float(len(self.lights)), float1=True)
        for i, light in enumerate(self.lights):
            shader.setUniformVariable(key=f"lights[{i}].type", value=float(_LIGHT_TYPES.index(light.light_type)), float1=True)
            shader.setUniformVariable(key=f"lights[{i}].position", value=light.position, float3=True)
            shader.setUniformVariable(key=f"lights[{i}].direction", value=light.direction, float3=True)
            shader.setUniformVariable(key=f"lights[{i}].color", value=light.color, float3=True)
            shader.setUniformVariable(key=f"lights[{i}].intensity", value=light.intensity, float1=True)
            shader.setUniformVariable(key=f"lights[{i}].cutoff", value=light.cutoff_degrees, float1=True)

    def draw_panel(self):
        """Draws the "Lights" ImGui window. Returns whether it's still open (wire this up the
        same way as the Shadow Settings panel in the tutorial script)."""
        expanded, opened = imgui.begin("Lights", True)
        imgui.text(f"{len(self.lights)}/{self.MAX_LIGHTS} lights")
        imgui.separator()

        to_remove = None
        for i, light in enumerate(self.lights):
            suffix = "  [shadow-casting]" if i == 0 else ""
            if imgui.tree_node(f"{light.name} ({light.light_type}){suffix}##light{i}"):
                type_index = _LIGHT_TYPES.index(light.light_type)
                changed, type_index = imgui.combo(f"Type##type{i}", type_index, list(_LIGHT_TYPES))
                if changed:
                    light.light_type = _LIGHT_TYPES[type_index]
                if i == 0 and light.light_type != "point":
                    imgui.text_colored("Shadows need this light to be Point -- off until then.", 1.0, 0.6, 0.2)

                if light.light_type in ("point", "spot"):
                    _, position = imgui.drag_float3(f"Position##pos{i}", *light.position, 0.1)
                    light.position = list(position)
                if light.light_type in ("directional", "spot"):
                    _, direction = imgui.drag_float3(f"Direction##dir{i}", *light.direction, 0.05, -1.0, 1.0)
                    light.direction = list(direction)

                _, color = imgui.color_edit3(f"Color##col{i}", *light.color)
                light.color = list(color)
                _, light.intensity = imgui.slider_float(f"Intensity##int{i}", light.intensity, 0.0, 5.0)
                if light.light_type == "spot":
                    _, light.cutoff_degrees = imgui.slider_float(f"Cutoff (deg)##cut{i}", light.cutoff_degrees, 1.0, 90.0)

                if i > 0 and imgui.button(f"Remove##rm{i}"):
                    to_remove = i
                imgui.tree_pop()

        if to_remove is not None:
            self.remove_light(to_remove)

        imgui.separator()
        if len(self.lights) < self.MAX_LIGHTS:
            if imgui.button("Add Point"):
                self.add_light("point")
            imgui.same_line()
            if imgui.button("Add Directional"):
                self.add_light("directional")
            imgui.same_line()
            if imgui.button("Add Spot"):
                self.add_light("spot")
        else:
            imgui.text(f"Max {self.MAX_LIGHTS} lights reached")

        imgui.end()
        return opened


@dataclass
class ProjectionSettings:
    """
    Switches the camera between perspective and orthographic projection. matrix() returns the
    current projection matrix; draw_panel() draws an ImGui window with only the properties
    relevant to whichever mode is selected (fovy/aspect for perspective; the view-box edges for
    orthographic -- near/far are shared by both).
    """

    mode: str = "perspective"  # "perspective" | "orthographic"
    fovy: float = 50.0
    aspect: float = 16.0 / 9.0
    near: float = 0.01
    far: float = 100.0
    left: float = -8.0
    right: float = 8.0
    bottom: float = -6.0
    top: float = 6.0

    def matrix(self):
        if self.mode == "perspective":
            return util.perspective(self.fovy, self.aspect, self.near, self.far)
        return util.ortho(self.left, self.right, self.bottom, self.top, self.near, self.far)

    def draw_panel(self):
        """Draws the "Projection" ImGui window. Returns whether it's still open."""
        expanded, opened = imgui.begin("Projection", True)

        mode_index = 0 if self.mode == "perspective" else 1
        changed, mode_index = imgui.combo("Type", mode_index, ["Perspective", "Orthographic"])
        if changed:
            self.mode = "perspective" if mode_index == 0 else "orthographic"
        imgui.separator()

        if self.mode == "perspective":
            _, self.fovy = imgui.slider_float("Field of View (deg)", self.fovy, 10.0, 120.0)
            # Read-only: the caller's main loop sets this from the live window size every frame
            # (scene.renderWindow._windowWidth / _windowHeight), so anything meant to fill the
            # whole screen (e.g. a skybox) still does after a resize. A drag_float here would
            # just get overwritten the very next frame.
            imgui.text(f"Aspect Ratio (w/h): {self.aspect:.3f}  (follows window size)")
            _, self.near = imgui.drag_float("Near", self.near, 0.01, 0.001, 10.0)
            _, self.far = imgui.drag_float("Far", self.far, 1.0, 1.0, 1000.0)
        else:
            _, self.left = imgui.drag_float("Left", self.left, 0.1, -50.0, 0.0)
            _, self.right = imgui.drag_float("Right", self.right, 0.1, 0.0, 50.0)
            _, self.bottom = imgui.drag_float("Bottom", self.bottom, 0.1, -50.0, 0.0)
            _, self.top = imgui.drag_float("Top", self.top, 0.1, 0.0, 50.0)
            _, self.near = imgui.drag_float("Near", self.near, 0.01, 0.001, 50.0)
            _, self.far = imgui.drag_float("Far", self.far, 1.0, 1.0, 1000.0)

        imgui.end()
        return opened


def _orbit_target_of(trans):
    """A point just above an object's own origin -- roughly its "middle" -- to orbit around."""
    world = trans.l2world
    target = np.array(world[:3, 3], dtype=np.float32)
    target[1] += 0.5 * np.linalg.norm(world[:3, 1])
    return target


def _orbit_state_from_eye(eye, orbit_target):
    """The inverse of the math in OrbitCamera._eye_from_orbit_state(): given where the camera
    currently is, what (radius, yaw, pitch) around orbit_target produced that?"""
    offset = np.array(eye, dtype=np.float32) - orbit_target
    radius = max(0.1, np.linalg.norm(offset))
    yaw = np.arctan2(offset[2], offset[0])
    pitch = np.arctan2(offset[1], np.linalg.norm(offset[[0, 2]]))
    return radius, yaw, pitch


class OrbitCamera:
    """
    A camera that free-flies (via the GUI/mouse, same as any other Elements scene) until you call
    focus_on(trans) -- e.g. because the user clicked something with the picking buffer -- at which
    point handle_keys() lets W/A/S/D rotate around it and +/- zoom in and out. focus_on_point(xyz)
    does the same around a fixed world-space point instead of an entity's transform, e.g. for
    picking-buffer clicks that don't land on a trackable object (the skybox, empty space).
    """

    def __init__(self, window, scene_context, eye, target, up,
                 speed=0.025, zoom_speed=0.35, pitch_limit=1.25, follow_lerp=0.12):
        self.window = window
        self.scene_context = scene_context
        self.up = np.array(up, dtype=np.float32)
        self.speed = speed
        self.zoom_speed = zoom_speed
        self.pitch_limit = pitch_limit
        self.follow_lerp = follow_lerp

        self.target_trans = None  # a BasicTransform we're tracking; None if not orbiting one
        self._fixed_point = None  # or a fixed world-space point instead -- see focus_on_point()
        self.orbit_target = np.array(target, dtype=np.float32)
        self._push_view(eye, target)
        self.orbit_radius, self.orbit_yaw, self.orbit_pitch = _orbit_state_from_eye(self.eye, self.orbit_target)

    @property
    def eye(self):
        return np.array(self.window._cameraEye, dtype=np.float32)

    @property
    def view(self):
        return self.window._myCamera

    def focus_on(self, target_trans):
        """Start orbiting around this BasicTransform (call this from your picking-click handler)."""
        self.target_trans = target_trans
        self._fixed_point = None

    def focus_on_point(self, point):
        """Start orbiting around a fixed world-space point (e.g. the origin) instead of an
        entity's transform -- for picking-buffer clicks with nothing to track (the skybox,
        empty space)."""
        self.target_trans = None
        self._fixed_point = np.array(point, dtype=np.float32)

    def handle_keys(self, key_states):
        """Call once per frame with sdl2.SDL_GetKeyboardState(None). No-op until focus_on()/
        focus_on_point() has been called at least once."""
        if self.target_trans is None and self._fixed_point is None:
            return

        eye = self.eye
        desired_target = _orbit_target_of(self.target_trans) if self.target_trans is not None else self._fixed_point
        delta = desired_target - self.orbit_target
        if np.linalg.norm(delta) > 1e-4:
            # the target moved (or we just started orbiting it): smoothly catch up to it
            self.orbit_target = self.orbit_target + self.follow_lerp * delta
            self._push_view(eye, self.orbit_target)

        self.orbit_radius, self.orbit_yaw, self.orbit_pitch = _orbit_state_from_eye(eye, self.orbit_target)

        changed = False
        if key_states[sdl2.SDL_SCANCODE_A]:
            self.orbit_yaw -= self.speed
            changed = True
        if key_states[sdl2.SDL_SCANCODE_D]:
            self.orbit_yaw += self.speed
            changed = True
        if key_states[sdl2.SDL_SCANCODE_W]:
            self.orbit_pitch += self.speed
            changed = True
        if key_states[sdl2.SDL_SCANCODE_S]:
            self.orbit_pitch -= self.speed
            changed = True
        if key_states[sdl2.SDL_SCANCODE_EQUALS] or key_states[sdl2.SDL_SCANCODE_KP_PLUS]:
            self.orbit_radius = max(0.5, self.orbit_radius - self.zoom_speed)
            changed = True
        if key_states[sdl2.SDL_SCANCODE_MINUS] or key_states[sdl2.SDL_SCANCODE_KP_MINUS]:
            self.orbit_radius += self.zoom_speed
            changed = True

        if changed:
            self.orbit_pitch = np.clip(self.orbit_pitch, -self.pitch_limit, self.pitch_limit)
            self._push_view(self._eye_from_orbit_state(), self.orbit_target)

    def _eye_from_orbit_state(self):
        cos_pitch = np.cos(self.orbit_pitch)
        return self.orbit_target + np.array([
            self.orbit_radius * cos_pitch * np.cos(self.orbit_yaw),
            self.orbit_radius * np.sin(self.orbit_pitch),
            self.orbit_radius * cos_pitch * np.sin(self.orbit_yaw),
        ], dtype=np.float32)

    def _push_view(self, eye, target):
        view_matrix = util.lookat(eye, target, self.up)
        self.window._myCamera = view_matrix
        self.window._cameraEye = np.array(eye, dtype=np.float32)
        self.window._cameraTarget = np.array(target, dtype=np.float32)
        if self.scene_context is not self.window:
            self.scene_context._eye = tuple(np.array(eye, dtype=np.float32))
            self.scene_context._target = tuple(np.array(target, dtype=np.float32))
            self.scene_context._up = tuple(self.up)
        return view_matrix
