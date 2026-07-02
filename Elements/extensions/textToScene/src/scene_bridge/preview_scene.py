import sys as _sys
_elements_root = r"C:\Users\yanni\Documents\GitHub\Elements"
if _elements_root not in _sys.path:
    _sys.path.insert(0, _elements_root)

import numpy as np

import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, Camera, RenderMesh
from Elements.pyECSS.System import TransformSystem, CameraSystem
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GUI.Viewer import RenderGLStateSystem
from Elements.pyGLV.GUI.ImguiDecorator import ImGUIecssDecorator2
from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray
from Elements.pyGLV.GL.Textures import Texture 
import Elements.utils.normals as norm

from Elements.utils.terrain import generateTerrain
from Elements.definitions import TEXTURE_DIR

from Elements.utils.Shortcuts import displayGUI_text

import OpenGL.GL as gl

TEXTURE_VERTEX_SHADER = """
#version 410
layout (location=0) in vec4 vPos;
layout (location=1) in vec2 vTexCoord;
layout (location=2) in vec3 vNormal;

out vec2 fragTexCoord;
out vec3 fragNormal;
out vec3 fragPos;

uniform mat4 model;
uniform mat4 view;
uniform mat4 proj;

void main()
{
    vec4 worldPos = model * vPos;
    fragPos = worldPos.xyz;
    fragNormal = mat3(transpose(inverse(model))) * vNormal;
    fragTexCoord = vTexCoord;
    gl_Position = proj * view * worldPos;
}
"""
TEXTURE_FRAGMENT_SHADER = """
#version 410
in vec2 fragTexCoord;
in vec3 fragNormal;
in vec3 fragPos;

out vec4 outputColor;

uniform sampler2D texSampler;
uniform vec3  Lambientcolor;
uniform float Lambientstr;
uniform vec3  LviewPos;
uniform vec3  Lposition;
uniform vec3  Lcolor;
uniform float Lintensity;

void main()
{
    vec4  texColor  = texture(texSampler, fragTexCoord);
    vec3  norm      = normalize(fragNormal);
    vec3  ambient   = Lambientstr * Lambientcolor * texColor.rgb;
    vec3  lightDir  = normalize(Lposition - fragPos);
    float diff      = max(dot(norm, lightDir), 0.0);
    vec3  diffuse   = diff * Lcolor * Lintensity * texColor.rgb;
    vec3  viewDir   = normalize(LviewPos - fragPos);
    vec3  reflDir   = reflect(-lightDir, norm);
    float spec      = pow(max(dot(viewDir, reflDir), 0.0), 32.0);
    vec3  specular  = 0.2 * spec * Lcolor * Lintensity;
    outputColor = vec4(ambient + diffuse + specular, texColor.a);
}
"""
example_description = "Generated scene from hierarchical IR"

# Ambient / view defaults
Lambientcolor = util.vec(1.0, 1.0, 1.0)
Lambientstr = 0.3
LviewPos = util.vec(2.5, 2.8, 5.0)

# Material
Mshininess = 0.4

# Active light

activeLightPos = util.vec(2.0, 5.5, 2.0)
activeLightColor = util.vec(1.0, 1.0, 1.0)
activeLightIntensity = 0.8


winWidth = 1200
winHeight = 800

scene = Scene()

rootEntity = scene.world.createEntity(Entity(name="RooT"))

entityCam1 = scene.world.createEntity(Entity(name="Entity1"))
scene.world.addEntityChild(rootEntity, entityCam1)
scene.world.addComponent(
    entityCam1,
    BasicTransform(name="Entity1_TRS", trs=util.translate(0, 0, -8))
)

eye = util.vec(2.5, 2.5, 2.5)
target = util.vec(0.0, 0.0, 0.0)
up = util.vec(0.0, 1.0, 0.0)
view = util.lookat(eye, target, up)
projMat = util.perspective(50.0, winWidth / winHeight, 0.01, 100.0)

m = np.linalg.inv(projMat @ view)

entityCam2 = scene.world.createEntity(Entity(name="Entity_Camera"))
scene.world.addEntityChild(entityCam1, entityCam2)
scene.world.addComponent(entityCam2, BasicTransform(name="Camera_TRS", trs=util.identity()))
orthoCam = scene.world.addComponent(entityCam2, Camera(m, "orthoCam", "Camera", "500"))

transUpdate = scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
camUpdate = scene.world.createSystem(CameraSystem("camUpdate", "CameraUpdate", "200"))
renderUpdate = scene.world.createSystem(RenderGLShaderSystem())
initUpdate = scene.world.createSystem(InitGLShaderSystem())


# ===== mesh_object: cube_1 =====

vertices_1 = np.array([[0.5, -0.5, -0.5, 1.0], [-0.5, -0.5, -0.5, 1.0], [-0.5, 0.5, -0.5, 1.0], [0.5, -0.5, -0.5, 1.0], [-0.5, 0.5, -0.5, 1.0], [0.5, 0.5, -0.5, 1.0], [0.5, 0.5, -0.5, 1.0], [-0.5, 0.5, -0.5, 1.0], [-0.5, 0.5, 0.5, 1.0], [0.5, 0.5, -0.5, 1.0], [-0.5, 0.5, 0.5, 1.0], [0.5, 0.5, 0.5, 1.0], [-0.5, 0.5, -0.5, 1.0], [-0.5, -0.5, -0.5, 1.0], [-0.5, -0.5, 0.5, 1.0], [-0.5, 0.5, -0.5, 1.0], [-0.5, -0.5, 0.5, 1.0], [-0.5, 0.5, 0.5, 1.0], [0.5, 0.5, 0.5, 1.0], [0.5, -0.5, 0.5, 1.0], [0.5, -0.5, -0.5, 1.0], [0.5, 0.5, 0.5, 1.0], [0.5, -0.5, -0.5, 1.0], [0.5, 0.5, -0.5, 1.0], [-0.5, -0.5, 0.5, 1.0], [0.5, -0.5, 0.5, 1.0], [0.5, 0.5, 0.5, 1.0], [-0.5, -0.5, 0.5, 1.0], [0.5, 0.5, 0.5, 1.0], [-0.5, 0.5, 0.5, 1.0], [0.5, -0.5, 0.5, 1.0], [-0.5, -0.5, 0.5, 1.0], [-0.5, -0.5, -0.5, 1.0], [0.5, -0.5, 0.5, 1.0], [-0.5, -0.5, -0.5, 1.0], [0.5, -0.5, -0.5, 1.0]], dtype=np.float32)
indices_1 = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35], dtype=np.uint32)
colors_1 = np.array([[0.699999988079071, 0.699999988079071, 0.699999988079071, 1.0], [0.699999988079071, 0.699999988079071, 0.699999988079071, 1.0], [0.699999988079071, 0.699999988079071, 0.699999988079071, 1.0], [0.699999988079071, 0.699999988079071, 0.699999988079071, 1.0], [0.699999988079071, 0.699999988079071, 0.699999988079071, 1.0], [0.699999988079071, 0.699999988079071, 0.699999988079071, 1.0], [0.699999988079071, 0.699999988079071, 0.699999988079071, 1.0], [0.699999988079071, 0.699999988079071, 0.699999988079071, 1.0], [0.699999988079071, 0.699999988079071, 0.699999988079071, 1.0], [0.699999988079071, 0.699999988079071, 0.699999988079071, 1.0], [0.699999988079071, 0.699999988079071, 0.699999988079071, 1.0], [0.699999988079071, 0.699999988079071, 0.699999988079071, 1.0], [0.699999988079071, 0.699999988079071, 0.699999988079071, 1.0], [0.699999988079071, 0.699999988079071, 0.699999988079071, 1.0], [0.699999988079071, 0.699999988079071, 0.699999988079071, 1.0], [0.699999988079071, 0.699999988079071, 0.699999988079071, 1.0], [0.699999988079071, 0.699999988079071, 0.699999988079071, 1.0], [0.699999988079071, 0.699999988079071, 0.699999988079071, 1.0], [0.699999988079071, 0.699999988079071, 0.699999988079071, 1.0], [0.699999988079071, 0.699999988079071, 0.699999988079071, 1.0], [0.699999988079071, 0.699999988079071, 0.699999988079071, 1.0], [0.699999988079071, 0.699999988079071, 0.699999988079071, 1.0], [0.699999988079071, 0.699999988079071, 0.699999988079071, 1.0], [0.699999988079071, 0.699999988079071, 0.699999988079071, 1.0], [0.699999988079071, 0.699999988079071, 0.699999988079071, 1.0], [0.699999988079071, 0.699999988079071, 0.699999988079071, 1.0], [0.699999988079071, 0.699999988079071, 0.699999988079071, 1.0], [0.699999988079071, 0.699999988079071, 0.699999988079071, 1.0], [0.699999988079071, 0.699999988079071, 0.699999988079071, 1.0], [0.699999988079071, 0.699999988079071, 0.699999988079071, 1.0], [0.699999988079071, 0.699999988079071, 0.699999988079071, 1.0], [0.699999988079071, 0.699999988079071, 0.699999988079071, 1.0], [0.699999988079071, 0.699999988079071, 0.699999988079071, 1.0], [0.699999988079071, 0.699999988079071, 0.699999988079071, 1.0], [0.699999988079071, 0.699999988079071, 0.699999988079071, 1.0], [0.699999988079071, 0.699999988079071, 0.699999988079071, 1.0]], dtype=np.float32)
normals_1 = np.array([[0.0, 0.0, -1.0, 0.0], [0.0, 0.0, -1.0, 0.0], [0.0, 0.0, -1.0, 0.0], [0.0, 0.0, -1.0, 0.0], [0.0, 0.0, -1.0, 0.0], [0.0, 0.0, -1.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 1.0, -0.0, 0.0], [0.0, 1.0, -0.0, 0.0], [0.0, 1.0, -0.0, 0.0], [-1.0, 0.0, 0.0, 0.0], [-1.0, 0.0, 0.0, 0.0], [-1.0, 0.0, 0.0, 0.0], [-1.0, 0.0, 0.0, 0.0], [-1.0, 0.0, 0.0, 0.0], [-1.0, 0.0, 0.0, 0.0], [1.0, 0.0, 0.0, 0.0], [1.0, 0.0, 0.0, 0.0], [1.0, 0.0, 0.0, 0.0], [1.0, 0.0, 0.0, 0.0], [1.0, 0.0, 0.0, 0.0], [1.0, 0.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 1.0, 0.0], [-0.0, -1.0, 0.0, 0.0], [-0.0, -1.0, 0.0, 0.0], [-0.0, -1.0, 0.0, 0.0], [0.0, -1.0, -0.0, 0.0], [0.0, -1.0, -0.0, 0.0], [0.0, -1.0, -0.0, 0.0]], dtype=np.float32)


node_1 = scene.world.createEntity(Entity(name="cube_1"))
scene.world.addEntityChild(rootEntity, node_1)

trans_1 = scene.world.addComponent(
    node_1,
    BasicTransform(name="cube_1_TRS", trs=util.translate(0.0, 0.5, 0.0) @ util.identity())
)

mesh_1 = scene.world.addComponent(node_1, RenderMesh(name="cube_1_mesh"))
mesh_1.vertex_attributes.append(vertices_1)
mesh_1.vertex_attributes.append(colors_1)
mesh_1.vertex_attributes.append(normals_1)
mesh_1.vertex_index.append(indices_1)

scene.world.addComponent(node_1, VertexArray())

shader_1 = scene.world.addComponent(
    node_1,
    ShaderGLDecorator(
        Shader(
            vertex_source=Shader.VERT_PHONG_MVP,
            fragment_source=Shader.FRAG_PHONG
        )
    )
)


# ===== mesh_object: cone_1 =====

vertices_2 = np.array([[0.0, 0.5, 0.0, 1.0], [0.5, -0.5, 0.0, 1.0], [0.4755282700061798, -0.5, 0.15450850129127502, 1.0], [0.404508501291275, -0.5, 0.29389262199401855, 1.0], [0.29389262199401855, -0.5, 0.404508501291275, 1.0], [0.15450850129127502, -0.5, 0.4755282700061798, 1.0], [3.0616171314629196e-17, -0.5, 0.5, 1.0], [-0.15450850129127502, -0.5, 0.4755282700061798, 1.0], [-0.29389262199401855, -0.5, 0.404508501291275, 1.0], [-0.404508501291275, -0.5, 0.29389262199401855, 1.0], [-0.4755282700061798, -0.5, 0.15450850129127502, 1.0], [-0.5, -0.5, 6.123234262925839e-17, 1.0], [-0.4755282700061798, -0.5, -0.15450850129127502, 1.0], [-0.404508501291275, -0.5, -0.29389262199401855, 1.0], [-0.29389262199401855, -0.5, -0.404508501291275, 1.0], [-0.15450850129127502, -0.5, -0.4755282700061798, 1.0], [-9.184850732644269e-17, -0.5, -0.5, 1.0], [0.15450850129127502, -0.5, -0.4755282700061798, 1.0], [0.29389262199401855, -0.5, -0.404508501291275, 1.0], [0.404508501291275, -0.5, -0.29389262199401855, 1.0], [0.4755282700061798, -0.5, -0.15450850129127502, 1.0], [0.0, -0.5, 0.0, 1.0], [0.5, -0.5, 0.0, 1.0], [0.4755282700061798, -0.5, 0.15450850129127502, 1.0], [0.404508501291275, -0.5, 0.29389262199401855, 1.0], [0.29389262199401855, -0.5, 0.404508501291275, 1.0], [0.15450850129127502, -0.5, 0.4755282700061798, 1.0], [3.0616171314629196e-17, -0.5, 0.5, 1.0], [-0.15450850129127502, -0.5, 0.4755282700061798, 1.0], [-0.29389262199401855, -0.5, 0.404508501291275, 1.0], [-0.404508501291275, -0.5, 0.29389262199401855, 1.0], [-0.4755282700061798, -0.5, 0.15450850129127502, 1.0], [-0.5, -0.5, 6.123234262925839e-17, 1.0], [-0.4755282700061798, -0.5, -0.15450850129127502, 1.0], [-0.404508501291275, -0.5, -0.29389262199401855, 1.0], [-0.29389262199401855, -0.5, -0.404508501291275, 1.0], [-0.15450850129127502, -0.5, -0.4755282700061798, 1.0], [-9.184850732644269e-17, -0.5, -0.5, 1.0], [0.15450850129127502, -0.5, -0.4755282700061798, 1.0], [0.29389262199401855, -0.5, -0.404508501291275, 1.0], [0.404508501291275, -0.5, -0.29389262199401855, 1.0], [0.4755282700061798, -0.5, -0.15450850129127502, 1.0]], dtype=np.float32)
indices_2 = np.array([0, 2, 1, 0, 3, 2, 0, 4, 3, 0, 5, 4, 0, 6, 5, 0, 7, 6, 0, 8, 7, 0, 9, 8, 0, 10, 9, 0, 11, 10, 0, 12, 11, 0, 13, 12, 0, 14, 13, 0, 15, 14, 0, 16, 15, 0, 17, 16, 0, 18, 17, 0, 19, 18, 0, 20, 19, 0, 1, 20, 21, 22, 23, 21, 23, 24, 21, 24, 25, 21, 25, 26, 21, 26, 27, 21, 27, 28, 21, 28, 29, 21, 29, 30, 21, 30, 31, 21, 31, 32, 21, 32, 33, 21, 33, 34, 21, 34, 35, 21, 35, 36, 21, 36, 37, 21, 37, 38, 21, 38, 39, 21, 39, 40, 21, 40, 41, 21, 41, 22], dtype=np.uint32)
colors_2 = np.array([[1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0]], dtype=np.float32)
normals_2 = np.array([[0.0, 1.0, 5.720957574339991e-08, 0.0], [0.8944271802902222, 0.4472135901451111, 0.0, 0.0], [0.8506508469581604, 0.44721361994743347, 0.27639317512512207, 0.0], [0.7236067652702332, 0.4472135901451111, 0.5257311463356018, 0.0], [0.5257311463356018, 0.4472135901451111, 0.7236067652702332, 0.0], [0.27639317512512207, 0.44721361994743347, 0.8506508469581604, 0.0], [0.0, 0.4472135901451111, 0.8944271802902222, 0.0], [-0.27639317512512207, 0.44721361994743347, 0.8506508469581604, 0.0], [-0.5257311463356018, 0.4472135901451111, 0.7236067652702332, 0.0], [-0.7236067652702332, 0.4472135901451111, 0.5257311463356018, 0.0], [-0.8506508469581604, 0.44721361994743347, 0.27639317512512207, 0.0], [-0.8944271802902222, 0.4472135901451111, 0.0, 0.0], [-0.8506508469581604, 0.44721361994743347, -0.27639317512512207, 0.0], [-0.7236067652702332, 0.4472135901451111, -0.5257311463356018, 0.0], [-0.5257311463356018, 0.4472135901451111, -0.7236067652702332, 0.0], [-0.27639317512512207, 0.44721361994743347, -0.8506508469581604, 0.0], [0.0, 0.4472135901451111, -0.8944271802902222, 0.0], [0.27639317512512207, 0.44721361994743347, -0.8506508469581604, 0.0], [0.5257311463356018, 0.4472135901451111, -0.7236067652702332, 0.0], [0.7236067652702332, 0.4472135901451111, -0.5257311463356018, 0.0], [0.8506508469581604, 0.44721361994743347, -0.27639317512512207, 0.0], [0.0, -1.0, 0.0, 0.0], [0.0, -1.0, 0.0, 0.0], [0.0, -1.0, 0.0, 0.0], [0.0, -1.0, 0.0, 0.0], [0.0, -1.0, 0.0, 0.0], [0.0, -1.0, 0.0, 0.0], [0.0, -1.0, 0.0, 0.0], [0.0, -1.0, 0.0, 0.0], [0.0, -1.0, 0.0, 0.0], [0.0, -1.0, 0.0, 0.0], [0.0, -1.0, 0.0, 0.0], [0.0, -1.0, 0.0, 0.0], [0.0, -1.0, 0.0, 0.0], [0.0, -1.0, 0.0, 0.0], [0.0, -1.0, 0.0, 0.0], [0.0, -1.0, 0.0, 0.0], [0.0, -1.0, 0.0, 0.0], [0.0, -1.0, 0.0, 0.0], [0.0, -1.0, 0.0, 0.0], [0.0, -1.0, 0.0, 0.0], [0.0, -1.0, 0.0, 0.0]], dtype=np.float32)


node_2 = scene.world.createEntity(Entity(name="cone_1"))
scene.world.addEntityChild(rootEntity, node_2)

trans_2 = scene.world.addComponent(
    node_2,
    BasicTransform(name="cone_1_TRS", trs=util.translate(1.5, 0.5, 0.0) @ util.identity())
)

mesh_2 = scene.world.addComponent(node_2, RenderMesh(name="cone_1_mesh"))
mesh_2.vertex_attributes.append(vertices_2)
mesh_2.vertex_attributes.append(colors_2)
mesh_2.vertex_attributes.append(normals_2)
mesh_2.vertex_index.append(indices_2)

scene.world.addComponent(node_2, VertexArray())

shader_2 = scene.world.addComponent(
    node_2,
    ShaderGLDecorator(
        Shader(
            vertex_source=Shader.VERT_PHONG_MVP,
            fragment_source=Shader.FRAG_PHONG
        )
    )
)


# ===== mesh_object: cube_2 =====

vertices_3 = np.array([[0.5, -0.5, -0.5, 1.0], [-0.5, -0.5, -0.5, 1.0], [-0.5, 0.5, -0.5, 1.0], [0.5, -0.5, -0.5, 1.0], [-0.5, 0.5, -0.5, 1.0], [0.5, 0.5, -0.5, 1.0], [0.5, 0.5, -0.5, 1.0], [-0.5, 0.5, -0.5, 1.0], [-0.5, 0.5, 0.5, 1.0], [0.5, 0.5, -0.5, 1.0], [-0.5, 0.5, 0.5, 1.0], [0.5, 0.5, 0.5, 1.0], [-0.5, 0.5, -0.5, 1.0], [-0.5, -0.5, -0.5, 1.0], [-0.5, -0.5, 0.5, 1.0], [-0.5, 0.5, -0.5, 1.0], [-0.5, -0.5, 0.5, 1.0], [-0.5, 0.5, 0.5, 1.0], [0.5, 0.5, 0.5, 1.0], [0.5, -0.5, 0.5, 1.0], [0.5, -0.5, -0.5, 1.0], [0.5, 0.5, 0.5, 1.0], [0.5, -0.5, -0.5, 1.0], [0.5, 0.5, -0.5, 1.0], [-0.5, -0.5, 0.5, 1.0], [0.5, -0.5, 0.5, 1.0], [0.5, 0.5, 0.5, 1.0], [-0.5, -0.5, 0.5, 1.0], [0.5, 0.5, 0.5, 1.0], [-0.5, 0.5, 0.5, 1.0], [0.5, -0.5, 0.5, 1.0], [-0.5, -0.5, 0.5, 1.0], [-0.5, -0.5, -0.5, 1.0], [0.5, -0.5, 0.5, 1.0], [-0.5, -0.5, -0.5, 1.0], [0.5, -0.5, -0.5, 1.0]], dtype=np.float32)
indices_3 = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35], dtype=np.uint32)
colors_3 = np.array([[1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0]], dtype=np.float32)
normals_3 = np.array([[0.0, 0.0, -1.0, 0.0], [0.0, 0.0, -1.0, 0.0], [0.0, 0.0, -1.0, 0.0], [0.0, 0.0, -1.0, 0.0], [0.0, 0.0, -1.0, 0.0], [0.0, 0.0, -1.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 1.0, -0.0, 0.0], [0.0, 1.0, -0.0, 0.0], [0.0, 1.0, -0.0, 0.0], [-1.0, 0.0, 0.0, 0.0], [-1.0, 0.0, 0.0, 0.0], [-1.0, 0.0, 0.0, 0.0], [-1.0, 0.0, 0.0, 0.0], [-1.0, 0.0, 0.0, 0.0], [-1.0, 0.0, 0.0, 0.0], [1.0, 0.0, 0.0, 0.0], [1.0, 0.0, 0.0, 0.0], [1.0, 0.0, 0.0, 0.0], [1.0, 0.0, 0.0, 0.0], [1.0, 0.0, 0.0, 0.0], [1.0, 0.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 1.0, 0.0], [-0.0, -1.0, 0.0, 0.0], [-0.0, -1.0, 0.0, 0.0], [-0.0, -1.0, 0.0, 0.0], [0.0, -1.0, -0.0, 0.0], [0.0, -1.0, -0.0, 0.0], [0.0, -1.0, -0.0, 0.0]], dtype=np.float32)


node_3 = scene.world.createEntity(Entity(name="cube_2"))
scene.world.addEntityChild(rootEntity, node_3)

trans_3 = scene.world.addComponent(
    node_3,
    BasicTransform(name="cube_2_TRS", trs=util.translate(3.0, 0.5, 0.0) @ util.identity())
)

mesh_3 = scene.world.addComponent(node_3, RenderMesh(name="cube_2_mesh"))
mesh_3.vertex_attributes.append(vertices_3)
mesh_3.vertex_attributes.append(colors_3)
mesh_3.vertex_attributes.append(normals_3)
mesh_3.vertex_index.append(indices_3)

scene.world.addComponent(node_3, VertexArray())

shader_3 = scene.world.addComponent(
    node_3,
    ShaderGLDecorator(
        Shader(
            vertex_source=Shader.VERT_PHONG_MVP,
            fragment_source=Shader.FRAG_PHONG
        )
    )
)


# ===== mesh_object: cylinder_1 =====

vertices_4 = np.array([[0.5, -0.5, 0.0, 1.0], [0.5, 0.5, 0.0, 1.0], [0.4755282700061798, -0.5, 0.15450850129127502, 1.0], [0.4755282700061798, 0.5, 0.15450850129127502, 1.0], [0.404508501291275, -0.5, 0.29389262199401855, 1.0], [0.404508501291275, 0.5, 0.29389262199401855, 1.0], [0.29389262199401855, -0.5, 0.404508501291275, 1.0], [0.29389262199401855, 0.5, 0.404508501291275, 1.0], [0.15450850129127502, -0.5, 0.4755282700061798, 1.0], [0.15450850129127502, 0.5, 0.4755282700061798, 1.0], [3.0616171314629196e-17, -0.5, 0.5, 1.0], [3.0616171314629196e-17, 0.5, 0.5, 1.0], [-0.15450850129127502, -0.5, 0.4755282700061798, 1.0], [-0.15450850129127502, 0.5, 0.4755282700061798, 1.0], [-0.29389262199401855, -0.5, 0.404508501291275, 1.0], [-0.29389262199401855, 0.5, 0.404508501291275, 1.0], [-0.404508501291275, -0.5, 0.29389262199401855, 1.0], [-0.404508501291275, 0.5, 0.29389262199401855, 1.0], [-0.4755282700061798, -0.5, 0.15450850129127502, 1.0], [-0.4755282700061798, 0.5, 0.15450850129127502, 1.0], [-0.5, -0.5, 6.123234262925839e-17, 1.0], [-0.5, 0.5, 6.123234262925839e-17, 1.0], [-0.4755282700061798, -0.5, -0.15450850129127502, 1.0], [-0.4755282700061798, 0.5, -0.15450850129127502, 1.0], [-0.404508501291275, -0.5, -0.29389262199401855, 1.0], [-0.404508501291275, 0.5, -0.29389262199401855, 1.0], [-0.29389262199401855, -0.5, -0.404508501291275, 1.0], [-0.29389262199401855, 0.5, -0.404508501291275, 1.0], [-0.15450850129127502, -0.5, -0.4755282700061798, 1.0], [-0.15450850129127502, 0.5, -0.4755282700061798, 1.0], [-9.184850732644269e-17, -0.5, -0.5, 1.0], [-9.184850732644269e-17, 0.5, -0.5, 1.0], [0.15450850129127502, -0.5, -0.4755282700061798, 1.0], [0.15450850129127502, 0.5, -0.4755282700061798, 1.0], [0.29389262199401855, -0.5, -0.404508501291275, 1.0], [0.29389262199401855, 0.5, -0.404508501291275, 1.0], [0.404508501291275, -0.5, -0.29389262199401855, 1.0], [0.404508501291275, 0.5, -0.29389262199401855, 1.0], [0.4755282700061798, -0.5, -0.15450850129127502, 1.0], [0.4755282700061798, 0.5, -0.15450850129127502, 1.0], [0.0, 0.5, 0.0, 1.0], [0.5, 0.5, 0.0, 1.0], [0.4755282700061798, 0.5, 0.15450850129127502, 1.0], [0.404508501291275, 0.5, 0.29389262199401855, 1.0], [0.29389262199401855, 0.5, 0.404508501291275, 1.0], [0.15450850129127502, 0.5, 0.4755282700061798, 1.0], [3.0616171314629196e-17, 0.5, 0.5, 1.0], [-0.15450850129127502, 0.5, 0.4755282700061798, 1.0], [-0.29389262199401855, 0.5, 0.404508501291275, 1.0], [-0.404508501291275, 0.5, 0.29389262199401855, 1.0], [-0.4755282700061798, 0.5, 0.15450850129127502, 1.0], [-0.5, 0.5, 6.123234262925839e-17, 1.0], [-0.4755282700061798, 0.5, -0.15450850129127502, 1.0], [-0.404508501291275, 0.5, -0.29389262199401855, 1.0], [-0.29389262199401855, 0.5, -0.404508501291275, 1.0], [-0.15450850129127502, 0.5, -0.4755282700061798, 1.0], [-9.184850732644269e-17, 0.5, -0.5, 1.0], [0.15450850129127502, 0.5, -0.4755282700061798, 1.0], [0.29389262199401855, 0.5, -0.404508501291275, 1.0], [0.404508501291275, 0.5, -0.29389262199401855, 1.0], [0.4755282700061798, 0.5, -0.15450850129127502, 1.0], [0.0, -0.5, 0.0, 1.0], [0.5, -0.5, 0.0, 1.0], [0.4755282700061798, -0.5, 0.15450850129127502, 1.0], [0.404508501291275, -0.5, 0.29389262199401855, 1.0], [0.29389262199401855, -0.5, 0.404508501291275, 1.0], [0.15450850129127502, -0.5, 0.4755282700061798, 1.0], [3.0616171314629196e-17, -0.5, 0.5, 1.0], [-0.15450850129127502, -0.5, 0.4755282700061798, 1.0], [-0.29389262199401855, -0.5, 0.404508501291275, 1.0], [-0.404508501291275, -0.5, 0.29389262199401855, 1.0], [-0.4755282700061798, -0.5, 0.15450850129127502, 1.0], [-0.5, -0.5, 6.123234262925839e-17, 1.0], [-0.4755282700061798, -0.5, -0.15450850129127502, 1.0], [-0.404508501291275, -0.5, -0.29389262199401855, 1.0], [-0.29389262199401855, -0.5, -0.404508501291275, 1.0], [-0.15450850129127502, -0.5, -0.4755282700061798, 1.0], [-9.184850732644269e-17, -0.5, -0.5, 1.0], [0.15450850129127502, -0.5, -0.4755282700061798, 1.0], [0.29389262199401855, -0.5, -0.404508501291275, 1.0], [0.404508501291275, -0.5, -0.29389262199401855, 1.0], [0.4755282700061798, -0.5, -0.15450850129127502, 1.0]], dtype=np.float32)
indices_4 = np.array([0, 1, 3, 0, 3, 2, 2, 3, 5, 2, 5, 4, 4, 5, 7, 4, 7, 6, 6, 7, 9, 6, 9, 8, 8, 9, 11, 8, 11, 10, 10, 11, 13, 10, 13, 12, 12, 13, 15, 12, 15, 14, 14, 15, 17, 14, 17, 16, 16, 17, 19, 16, 19, 18, 18, 19, 21, 18, 21, 20, 20, 21, 23, 20, 23, 22, 22, 23, 25, 22, 25, 24, 24, 25, 27, 24, 27, 26, 26, 27, 29, 26, 29, 28, 28, 29, 31, 28, 31, 30, 30, 31, 33, 30, 33, 32, 32, 33, 35, 32, 35, 34, 34, 35, 37, 34, 37, 36, 36, 37, 39, 36, 39, 38, 38, 39, 1, 38, 1, 0, 40, 42, 41, 40, 43, 42, 40, 44, 43, 40, 45, 44, 40, 46, 45, 40, 47, 46, 40, 48, 47, 40, 49, 48, 40, 50, 49, 40, 51, 50, 40, 52, 51, 40, 53, 52, 40, 54, 53, 40, 55, 54, 40, 56, 55, 40, 57, 56, 40, 58, 57, 40, 59, 58, 40, 60, 59, 40, 41, 60, 61, 62, 63, 61, 63, 64, 61, 64, 65, 61, 65, 66, 61, 66, 67, 61, 67, 68, 61, 68, 69, 61, 69, 70, 61, 70, 71, 61, 71, 72, 61, 72, 73, 61, 73, 74, 61, 74, 75, 61, 75, 76, 61, 76, 77, 61, 77, 78, 61, 78, 79, 61, 79, 80, 61, 80, 81, 61, 81, 62], dtype=np.uint32)
colors_4 = np.array([[1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0]], dtype=np.float32)
normals_4 = np.array([[0.9986093044281006, 0.0, 0.05272136256098747, 0.0], [0.9986093044281006, 0.0, -0.05272136256098747, 0.0], [0.9334420561790466, 0.0, 0.3587282598018646, 0.0], [0.9660256505012512, 0.0, 0.25844618678092957, 0.0], [0.776902973651886, 0.0, 0.6296203136444092, 0.0], [0.8388806581497192, 0.0, 0.5443153381347656, 0.0], [0.5443153381347656, 0.0, 0.8388806581497192, 0.0], [0.6296203136444092, 0.0, 0.776902973651886, 0.0], [0.25844618678092957, 0.0, 0.9660256505012512, 0.0], [0.3587282598018646, 0.0, 0.9334420561790466, 0.0], [-0.05272136256098747, 0.0, 0.9986093044281006, 0.0], [0.05272136256098747, 0.0, 0.9986093044281006, 0.0], [-0.3587282598018646, 0.0, 0.9334420561790466, 0.0], [-0.25844618678092957, 0.0, 0.9660256505012512, 0.0], [-0.6296203136444092, 0.0, 0.776902973651886, 0.0], [-0.5443153381347656, 0.0, 0.8388806581497192, 0.0], [-0.8388806581497192, 0.0, 0.5443153381347656, 0.0], [-0.776902973651886, 0.0, 0.6296203136444092, 0.0], [-0.9660256505012512, 0.0, 0.25844618678092957, 0.0], [-0.9334420561790466, 0.0, 0.3587282598018646, 0.0], [-0.9986093044281006, 0.0, -0.05272136256098747, 0.0], [-0.9986093044281006, 0.0, 0.05272136256098747, 0.0], [-0.9334420561790466, 0.0, -0.3587282598018646, 0.0], [-0.9660256505012512, 0.0, -0.25844618678092957, 0.0], [-0.776902973651886, 0.0, -0.6296203136444092, 0.0], [-0.8388806581497192, 0.0, -0.5443153381347656, 0.0], [-0.5443153381347656, 0.0, -0.8388806581497192, 0.0], [-0.6296203136444092, 0.0, -0.776902973651886, 0.0], [-0.25844618678092957, 0.0, -0.9660256505012512, 0.0], [-0.3587282598018646, 0.0, -0.9334420561790466, 0.0], [0.05272136256098747, 0.0, -0.9986093044281006, 0.0], [-0.05272136256098747, 0.0, -0.9986093044281006, 0.0], [0.3587282598018646, 0.0, -0.9334420561790466, 0.0], [0.25844618678092957, 0.0, -0.9660256505012512, 0.0], [0.6296203136444092, 0.0, -0.776902973651886, 0.0], [0.5443153381347656, 0.0, -0.8388806581497192, 0.0], [0.8388806581497192, 0.0, -0.5443153381347656, 0.0], [0.776902973651886, 0.0, -0.6296203136444092, 0.0], [0.9660256505012512, 0.0, -0.25844618678092957, 0.0], [0.9334420561790466, 0.0, -0.3587282598018646, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, -1.0, 0.0, 0.0], [0.0, -1.0, 0.0, 0.0], [0.0, -1.0, 0.0, 0.0], [0.0, -1.0, 0.0, 0.0], [0.0, -1.0, 0.0, 0.0], [0.0, -1.0, 0.0, 0.0], [0.0, -1.0, 0.0, 0.0], [0.0, -1.0, 0.0, 0.0], [0.0, -1.0, 0.0, 0.0], [0.0, -1.0, 0.0, 0.0], [0.0, -1.0, 0.0, 0.0], [0.0, -1.0, 0.0, 0.0], [0.0, -1.0, 0.0, 0.0], [0.0, -1.0, 0.0, 0.0], [0.0, -1.0, 0.0, 0.0], [0.0, -1.0, 0.0, 0.0], [0.0, -1.0, 0.0, 0.0], [0.0, -1.0, 0.0, 0.0], [0.0, -1.0, 0.0, 0.0], [0.0, -1.0, 0.0, 0.0], [0.0, -1.0, 0.0, 0.0]], dtype=np.float32)


node_4 = scene.world.createEntity(Entity(name="cylinder_1"))
scene.world.addEntityChild(rootEntity, node_4)

trans_4 = scene.world.addComponent(
    node_4,
    BasicTransform(name="cylinder_1_TRS", trs=util.translate(4.5, 0.5, 0.0) @ util.identity())
)

mesh_4 = scene.world.addComponent(node_4, RenderMesh(name="cylinder_1_mesh"))
mesh_4.vertex_attributes.append(vertices_4)
mesh_4.vertex_attributes.append(colors_4)
mesh_4.vertex_attributes.append(normals_4)
mesh_4.vertex_index.append(indices_4)

scene.world.addComponent(node_4, VertexArray())

shader_4 = scene.world.addComponent(
    node_4,
    ShaderGLDecorator(
        Shader(
            vertex_source=Shader.VERT_PHONG_MVP,
            fragment_source=Shader.FRAG_PHONG
        )
    )
)


import imgui
import json
import time
from pathlib import Path

SHARED_DIR = Path('C:\\Users\\yanni\\Documents\\GitHub\\Elements\\Elements\\extensions\\textToScene\\src\\scene_bridge')
SHARED_DIR.mkdir(parents=True, exist_ok=True)

AI_REQUEST_FILE = SHARED_DIR / "ai_request.json"
UI_STATE_FILE = SHARED_DIR / "ui_state.json"
SCENE_STATE_FILE = SHARED_DIR / "scene_state.json"

command_text = ""
status_message = "Ready for input."
show_editor_panel = True
request_counter = 0
current_request_id = None
current_mode = "official"
current_active_script = ""


def read_json_file(path):
    try:
        if not path.exists():
            return None
        with open(str(path), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def write_json_file(path, data):
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with open(str(tmp_path), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    tmp_path.replace(path)


def load_bridge_state():
    global request_counter
    global current_request_id
    global current_mode
    global current_active_script

    req = read_json_file(AI_REQUEST_FILE)
    if isinstance(req, dict):
        try:
            req_id = int(req.get("request_id", 0))
            if req_id > 0:
                request_counter = max(request_counter, req_id)
                current_request_id = req_id
        except Exception:
            pass

    scene_state = read_json_file(SCENE_STATE_FILE)
    if isinstance(scene_state, dict):
        current_mode = str(scene_state.get("mode", "official"))
        current_active_script = str(scene_state.get("active_script", ""))


def poll_backend_state():
    global status_message
    global request_counter
    global current_request_id
    global current_mode
    global current_active_script

    req = read_json_file(AI_REQUEST_FILE)
    ui = read_json_file(UI_STATE_FILE)
    scene_state = read_json_file(SCENE_STATE_FILE)

    if isinstance(scene_state, dict):
        current_mode = str(scene_state.get("mode", "official"))
        current_active_script = str(scene_state.get("active_script", ""))

    if isinstance(req, dict):
        try:
            req_id = int(req.get("request_id", 0))
            if req_id > 0:
                request_counter = max(request_counter, req_id)
                current_request_id = req_id
        except Exception:
            pass

        req_status = req.get("status")

        if req_status == "pending":
            status_message = "Request sent. Waiting for preview."
        elif req_status == "preview_ready":
            status_message = "Preview ready."
        elif req_status == "applied":
            status_message = "Applied."
        elif req_status == "rejected":
            status_message = "Rejected."
        elif req_status == "undone":
            status_message = "Undo restored previous scene."
        elif req_status == "new_scene_created":
            status_message = "New scene created."
        elif req_status == "scene_saved":
            status_message = str(req.get("message", "Scene saved."))
        elif req_status == "save_blocked_preview":
            status_message = "Save blocked. Apply or Reject preview first."
        elif req_status == "stale":
            status_message = "Previous stale request was cleared."
        elif req_status == "error":
            status_message = "Error: " + str(req.get("error", "unknown error"))

    if isinstance(ui, dict) and ui.get("action") == "error":
        status_message = "Controller error: " + str(ui.get("message", "unknown"))


def write_ai_request(prompt_text):
    global request_counter
    global current_request_id

    load_bridge_state()
    request_counter += 1
    current_request_id = request_counter

    data = {
        "request_id": request_counter,
        "status": "pending",
        "prompt": prompt_text,
        "created_at": time.time()
    }

    write_json_file(AI_REQUEST_FILE, data)
    return request_counter


def write_ui_action(action_name):
    data = {
        "action": action_name,
        "created_at": time.time()
    }

    if current_request_id is not None:
        data["request_id"] = current_request_id

    write_json_file(UI_STATE_FILE, data)


def display_active_script():
    if not current_active_script:
        return "(unknown)"

    try:
        return Path(current_active_script).name
    except Exception:
        return current_active_script


def draw_editor_panel():
    global command_text
    global status_message
    global show_editor_panel

    if not show_editor_panel:
        return

    imgui.begin("Scene Editor", True)

    imgui.text("Mode: " + str(current_mode))
    imgui.text("Request ID: " + (str(current_request_id) if current_request_id is not None else "(none)"))
    imgui.text_wrapped("Active script: " + display_active_script())

    imgui.spacing()
    imgui.separator()
    imgui.spacing()

    imgui.text("Command:")
    changed, command_text = imgui.input_text_multiline(
        "##scene_command",
        command_text,
        1024,
        width=420,
        height=100
    )

    imgui.spacing()

    if imgui.button("Send to AI", width=120):
        if command_text.strip():
            try:
                req_id = write_ai_request(command_text)
                status_message = "Request sent. request_id = " + str(req_id)
            except Exception as e:
                status_message = "Failed to send request: " + str(e)
        else:
            status_message = "Please type a command first."

    imgui.same_line()

    if imgui.button("Apply", width=80):
        try:
            write_ui_action("apply")
            status_message = "Apply sent."
        except Exception as e:
            status_message = "Apply failed: " + str(e)

    imgui.same_line()

    if imgui.button("Reject", width=80):
        try:
            write_ui_action("reject")
            status_message = "Reject sent."
        except Exception as e:
            status_message = "Reject failed: " + str(e)

    imgui.same_line()

    if imgui.button("Undo", width=80):
        try:
            write_ui_action("undo")
            status_message = "Undo sent."
        except Exception as e:
            status_message = "Undo failed: " + str(e)

    imgui.spacing()

    if imgui.button("New Scene", width=120):
        try:
            write_ui_action("new_scene")
            status_message = "New scene requested."
        except Exception as e:
            status_message = "New scene failed: " + str(e)

    imgui.same_line()

    if imgui.button("Save", width=80):
        try:
            write_ui_action("save_scene")
            status_message = "Save requested."
        except Exception as e:
            status_message = "Save failed: " + str(e)

    imgui.spacing()
    imgui.separator()
    imgui.text("Status:")
    imgui.text_wrapped(status_message)

    imgui.end()


running = True
load_bridge_state()

scene.init(
    imgui=True,
    windowWidth=winWidth,
    windowHeight=winHeight,
    windowTitle="Generated Scene",
    openGLversion=4,
    customImGUIdecorator=ImGUIecssDecorator2
)

scene.world.traverse_visit(initUpdate, scene.world.root)





eManager = scene.world.eventManager
gWindow = scene.renderWindow
gGUI = scene.gContext

renderGLEventActuator = RenderGLStateSystem()

eManager._subscribers['OnUpdateWireframe'] = gWindow
eManager._actuators['OnUpdateWireframe'] = renderGLEventActuator
eManager._subscribers['OnUpdateCamera'] = gWindow
eManager._actuators['OnUpdateCamera'] = renderGLEventActuator

gWindow._myCamera = view

while running:
    running = scene.render()
    scene.world.traverse_visit(renderUpdate, scene.world.root)
    scene.world.traverse_visit_pre_camera(camUpdate, orthoCam)
    scene.world.traverse_visit(camUpdate, scene.world.root)

    view = gWindow._myCamera

    model_1 = util.identity() @ (util.translate(0.0, 0.5, 0.0) @ util.identity())
    mvp_1 = projMat @ view @ model_1
    shader_1.setUniformVariable(key='modelViewProj', value=mvp_1, mat4=True)
    shader_1.setUniformVariable(key='model', value=model_1, mat4=True)
    shader_1.setUniformVariable(key='ambientColor', value=Lambientcolor, float3=True)
    shader_1.setUniformVariable(key='ambientStr', value=Lambientstr, float1=True)
    shader_1.setUniformVariable(key='viewPos', value=LviewPos, float3=True)
    shader_1.setUniformVariable(key='lightPos', value=activeLightPos, float3=True)
    shader_1.setUniformVariable(key='lightColor', value=activeLightColor, float3=True)
    shader_1.setUniformVariable(key='lightIntensity', value=activeLightIntensity, float1=True)
    shader_1.setUniformVariable(key='shininess', value=Mshininess, float1=True)
    shader_1.setUniformVariable(key='matColor', value=util.vec(0.7, 0.7, 0.7), float3=True)


    model_2 = util.identity() @ (util.translate(1.5, 0.5, 0.0) @ util.identity())
    mvp_2 = projMat @ view @ model_2
    shader_2.setUniformVariable(key='modelViewProj', value=mvp_2, mat4=True)
    shader_2.setUniformVariable(key='model', value=model_2, mat4=True)
    shader_2.setUniformVariable(key='ambientColor', value=Lambientcolor, float3=True)
    shader_2.setUniformVariable(key='ambientStr', value=Lambientstr, float1=True)
    shader_2.setUniformVariable(key='viewPos', value=LviewPos, float3=True)
    shader_2.setUniformVariable(key='lightPos', value=activeLightPos, float3=True)
    shader_2.setUniformVariable(key='lightColor', value=activeLightColor, float3=True)
    shader_2.setUniformVariable(key='lightIntensity', value=activeLightIntensity, float1=True)
    shader_2.setUniformVariable(key='shininess', value=Mshininess, float1=True)
    shader_2.setUniformVariable(key='matColor', value=util.vec(1.0, 1.0, 0.0), float3=True)


    _t_orb_3 = time.time()
    _ang_orb_3 = _t_orb_3 * 0.8
    model_3 = util.translate(1.5 + np.cos(_ang_orb_3) * 3.0, 0.5, 0.0 + np.sin(_ang_orb_3) * 3.0) @ util.scale(1.0, 1.0, 1.0)
    mvp_3 = projMat @ view @ model_3
    shader_3.setUniformVariable(key='modelViewProj', value=mvp_3, mat4=True)
    shader_3.setUniformVariable(key='model', value=model_3, mat4=True)
    shader_3.setUniformVariable(key='ambientColor', value=Lambientcolor, float3=True)
    shader_3.setUniformVariable(key='ambientStr', value=Lambientstr, float1=True)
    shader_3.setUniformVariable(key='viewPos', value=LviewPos, float3=True)
    shader_3.setUniformVariable(key='lightPos', value=activeLightPos, float3=True)
    shader_3.setUniformVariable(key='lightColor', value=activeLightColor, float3=True)
    shader_3.setUniformVariable(key='lightIntensity', value=activeLightIntensity, float1=True)
    shader_3.setUniformVariable(key='shininess', value=Mshininess, float1=True)
    shader_3.setUniformVariable(key='matColor', value=util.vec(1.0, 1.0, 0.0), float3=True)


    _t_orb_4 = time.time()
    _ang_orb_4 = _t_orb_4 * 0.8
    model_4 = util.translate(0.0 + np.cos(_ang_orb_4) * 3.0, 0.0, 0.0 + np.sin(_ang_orb_4) * 3.0) @ util.scale(1.0, 1.0, 1.0)
    mvp_4 = projMat @ view @ model_4
    shader_4.setUniformVariable(key='modelViewProj', value=mvp_4, mat4=True)
    shader_4.setUniformVariable(key='model', value=model_4, mat4=True)
    shader_4.setUniformVariable(key='ambientColor', value=Lambientcolor, float3=True)
    shader_4.setUniformVariable(key='ambientStr', value=Lambientstr, float1=True)
    shader_4.setUniformVariable(key='viewPos', value=LviewPos, float3=True)
    shader_4.setUniformVariable(key='lightPos', value=activeLightPos, float3=True)
    shader_4.setUniformVariable(key='lightColor', value=activeLightColor, float3=True)
    shader_4.setUniformVariable(key='lightIntensity', value=activeLightIntensity, float1=True)
    shader_4.setUniformVariable(key='shininess', value=Mshininess, float1=True)
    shader_4.setUniformVariable(key='matColor', value=util.vec(1.0, 1.0, 0.0), float3=True)
    poll_backend_state()
    draw_editor_panel()
    scene.render_post()

scene.shutdown()
