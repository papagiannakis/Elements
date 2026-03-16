def generate_scene(ir):
    if "window" not in ir:
        raise ValueError("IR must contain a 'window' key")  
    if "objects" not in ir:
        raise ValueError("IR must contain an 'objects' key")
    window = ir["window"]
    objects = ir["objects"]
    if "width" not in window or "height" not in window:
        raise ValueError("Window must contain 'width' and 'height' keys")
    code = f"create_window({window['width']}, {window['height']})\n"
    for obj in objects:
        if "type" not in obj or "name" not in obj:
            raise ValueError("Each object must contain 'type' and 'name' keys")
        obj_type = obj["type"]
        name = obj["name"]
        position = obj.get("position", [0, 0, 0])
        scale = obj.get("scale", [1, 1, 1])
        color = obj.get("color", [1, 1, 1])
        if obj["type"] == "cube":
            code += f"""
        node = scene.world.createEntity(Entity(name="{obj['name']}"))
            scene.world.addEntityChild(rootEntity, node)
            trans = scene.world.addComponent(
                node,
                BasicTransform(name="TRS", trs=util.translate{tuple(obj["position"])})
            )
            scene.world.addComponent(
                node,
                BoxCollider(name="BoxCollider", halfExtents=util.vec3({tuple(obj["scale"])}))
            )
            scene.world.addComponent(
                node,
                MeshRenderer(name="MeshRenderer", mesh=util.mesh("cube"), material=util.material(color={tuple(obj["color"])}))
            )

            """

#function for vec3
def vec3_to_util_vec3 (vec):
    if len(vec) != 3:
        raise ValueError("Vector must have 3 components")
    return f"util.vec3({vec[0]}, {vec[1]}, {vec[2]})"

#function for translation
def make_translate(position):
    return f"util.translate({vec3_to_util_vec3(position)})" 

#function for scaling
def make_scale(scale):
    if isinstance(scale, (int, float)):
        return f"util.scale({float(scale)})"
    sx,sy,sz = scale # for uniform scale all numbers must be equal
    if sx==sy==sz:
        return f"util.scale({float(sx)})"
    return "util.identity()"

def emit_cube_geometry(var_suffix: str) -> str:
    return f"""
vertexCube_{var_suffix} = np.array([
    [-0.5, -0.5, 0.5, 1.0],
    [-0.5, 0.5, 0.5, 1.0],
    [0.5, 0.5, 0.5, 1.0],
    [0.5, -0.5, 0.5, 1.0],
    [-0.5, -0.5, -0.5, 1.0],
    [-0.5, 0.5, -0.5, 1.0],
    [0.5, 0.5, -0.5, 1.0],
    [0.5, -0.5, -0.5, 1.0]
], dtype=np.float32)

colorCube_{var_suffix} = nm.array([colorCube_{var_suffix} = np.array([
    [0.0, 0.0, 0.0, 1.0],
    [1.0, 0.0, 0.0, 1.0],
    [1.0, 1.0, 0.0, 1.0],
    [0.0, 1.0, 0.0, 1.0],
    [0.0, 0.0, 1.0, 1.0],
    [1.0, 0.0, 1.0, 1.0],
    [1.0, 1.0, 1.0, 1.0],
    [0.0, 1.0, 1.0, 1.0]
], dtype=np.float32)

indexCube_{var_suffix} = np.array((
    1,0,3, 1,3,2,
    2,3,7, 2,7,6,
    3,0,4, 3,4,7,
    6,5,1, 6,1,2,
    4,5,6, 4,6,7,
    5,4,0, 5,0,1
), np.uint32)

vertices_{var_suffix}, indices_{var_suffix}, colors_{var_suffix}, normals_{var_suffix} = norm.generateSmoothNormalsMesh(
    vertexCube_{var_suffix},
    indexCube_{var_suffix},
    colorCube_{var_suffix}
)
"""
def emit_cube_object(obj: dict, idx: int) -> tuple[str, str]:
    name = obj.get("name", f"cube{idx}")
    position = obj.get("position", [0.0, 0.5, 0.0])
    scale = obj.get("scale", [1.0, 1.0, 1.0])
    color = obj.get("color", [0.8, 0.0, 0.8])

    suffix = f"{idx}"
    entity_var = f"node_{suffix}"
    trans_var = f"trans_{suffix}"
    mesh_var = f"mesh_{suffix}"
    shader_var = f"shader_{suffix}"

    trs_expr = f"{make_scale(scale)} @ {make_translate(position)}"
    mat_color_expr = vec3_to_util_vec(color)

    object_code = f"""
# ===== Cube: {name} =====
{emit_cube_geometry(suffix)}

{entity_var} = scene.world.createEntity(Entity(name="{name}"))
scene.world.addEntityChild(rootEntity, {entity_var})

{trans_var} = scene.world.addComponent(
    {entity_var},
    BasicTransform(name="{name}_TRS", trs={trs_expr})
)

{mesh_var} = scene.world.addComponent({entity_var}, RenderMesh(name="{name}_mesh"))
{mesh_var}.vertex_attributes.append(vertices_{suffix})
{mesh_var}.vertex_attributes.append(colors_{suffix})
{mesh_var}.vertex_attributes.append(normals_{suffix})
{mesh_var}.vertex_index.append(indices_{suffix})

scene.world.addComponent({entity_var}, VertexArray())

{shader_var} = scene.world.addComponent(
    {entity_var},
    ShaderGLDecorator(
        Shader(
            vertex_source=Shader.VERT_PHONG_MVP,
            fragment_source=Shader.FRAG_PHONG
        )
    )
)
"""

    uniform_code = f"""
    mvp_{suffix} = projMat @ view @ {trans_var}.trs
    {shader_var}.setUniformVariable(key='modelViewProj', value=mvp_{suffix}, mat4=True)
    {shader_var}.setUniformVariable(key='model', value={trans_var}.trs, mat4=True)
    {shader_var}.setUniformVariable(key='ambientColor', value=Lambientcolor, float3=True)
    {shader_var}.setUniformVariable(key='ambientStr', value=Lambientstr, float1=True)
    {shader_var}.setUniformVariable(key='viewPos', value=LviewPos, float3=True)
    {shader_var}.setUniformVariable(key='lightPos', value=Lposition, float3=True)
    {shader_var}.setUniformVariable(key='lightColor', value=Lcolor, float3=True)
    {shader_var}.setUniformVariable(key='lightIntensity', value=Lintensity, float1=True)
    {shader_var}.setUniformVariable(key='shininess', value=Mshininess, float1=True)
    {shader_var}.setUniformVariable(key='matColor', value={mat_color_expr}, float3=True)
"""

    return object_code, uniform_code

#function to create the header and the imports

def built_header(window: dict)->str:
    width = window.get("width", 1200)
    height =window.get("height", 800)
    title = window.get("title", "generated scene")

    return f'''import numpy as np
import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, Camera, RenderMesh
from Elements.pyECSS.System import TransformSystem, CameraSystem
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GUI.Viewer import RenderGLStateSystem
from Elements.pyGLV.GUI.ImguiDecorator import ImGUIecssDecorator2
from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray

import OpenGL.GL as gl
import Elements.utils.normals as norm

example_description = "Generated scene from natural language"

# Light
Lposition = util.vec(2.0, 5.5, 2.0)
Lambientcolor = util.vec(1.0, 1.0, 1.0)
Lambientstr = 0.3
LviewPos = util.vec(2.5, 2.8, 5.0)
Lcolor = util.vec(1.0, 1.0, 1.0)
Lintensity = 0.8

# Material
Mshininess = 0.4

winWidth = {width}
winHeight = {height}

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
'''

def build_ending(title: str, uniform_block: str)->str:
    return f'''
running = True
scene.init(
    imgui=True,
    windowWidth=winWidth,
    windowHeight=winHeight,
    windowTitle="{title}",
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
{uniform_block}
    scene.render_post()

scene.shutdown()
'''