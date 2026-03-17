import os
from pathlib import Path
from typing import Optional
from geometry_factory import create_geometry
import builtins
print("IS BUILTIN OPEN:", builtins.open is open)
print("OPEN OBJECT:", open)

def generate_scene(ir: dict) -> str:
    if not isinstance(ir, dict):
        raise TypeError("IR must be a dictionary")
    # 1. Validate IR
    if "window" not in ir:
        raise ValueError("IR must contain a 'window' key")
    if "objects" not in ir:
        raise ValueError("IR must contain an 'objects' key")

    window = ir["window"]
    objects = ir["objects"]
    title = window.get("title", "generated scene")

    # 2. Start with header
    script_parts: list[str] = []
    script_parts.append(built_header(window))

    # 3. Emit objects + collect uniform code
    uniform_blocks: list[str] = []

    for idx, obj in enumerate(objects):
        if "type" not in obj:
            raise ValueError("Each object must contain a 'type' key")

        obj_type = obj["type"]

        if obj_type == "cube":
            object_code, uniform_code = emit_cube_object(obj, idx)
            script_parts.append(object_code)
            uniform_blocks.append(uniform_code)
        else:
            # For now, ignore or raise for unsupported types
            raise ValueError(f"Unsupported object type: {obj_type}")

    # 4. Combine uniform blocks into one block
    uniform_block_str = "\n".join(uniform_blocks)

    # 5. Add ending (render loop)
    script_parts.append(build_ending(title, uniform_block_str))

    # 6. Join everything into a single script string
    full_script = "\n".join(script_parts)
    return full_script


#function for vec3
def vec3_to_util_vec (vec):
    if len(vec) != 3:
        raise ValueError("Vector must have 3 components")
    return f"util.vec({vec[0]}, {vec[1]}, {vec[2]})"

#function for translation
def make_translate(position):
    x, y, z = position
    return f"util.translate({float(x)}, {float(y)}, {float(z)})" 

#function for scaling
def make_scale(scale):
    if isinstance(scale, (int, float)):
        return f"util.scale({float(scale)})"
    sx,sy,sz = scale # for uniform scale all numbers must be equal
    if sx==sy==sz:
        return f"util.scale({float(sx)})"
    return "util.scale(1.0)" # default to no scale if non-uniform scaling

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

colorCube_{var_suffix} = np.array([
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
def emit_cube_object(obj: dict, idx: int) ->tuple[str, str]:
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

def save_script(script: str, output_path: str = None):
    if output_path is None:
        # Save to Desktop ALWAYS works
        desktop = Path.home() / "Desktop" / "scene_out.py"
        output_file = desktop
    else:
        output_file = Path(output_path)

    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(script)

    print("Saved script to:", output_file)
