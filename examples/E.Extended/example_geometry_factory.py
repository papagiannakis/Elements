"""
A minimal ECS scene -- camera, one point light, a few stacked primitives -- built the same way as
Normals_USDimporter_BSP/example_cow.py's neighbors but sourcing its shapes from
Elements.extensions.Shapes.geometry_factory instead of the older
Elements.extensions.BasicShapes.BasicShapes module: geometry_factory is the actively maintained
one (it's what showcase/scene_helpers.py and textToScene's code generator both build on), and
unlike BasicShapes it returns plain (vertices, indices, colors, normals) arrays rather than
ready-made ECS entities, so this example wires each shape's Entity/BasicTransform/RenderMesh/
Shader/VertexArray itself via spawn_shape() below.
"""

import numpy as np
import OpenGL.GL as gl

import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, RenderMesh
from Elements.pyECSS.System import TransformSystem, CameraSystem
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GL.SimpleCamera import SimpleCamera
from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray
from Elements.pyGLV.GUI.Viewer import RenderGLStateSystem
from Elements.pyGLV.GUI.ImguiDecorator import ImGUIecssDecorator
from Elements.extensions.Shapes import geometry_factory
from Elements.definitions import SHADER_DIR

from Elements.utils.Shortcuts import displayGUI_text
example_description = \
"This example demonstrates Elements.extensions.Shapes.geometry_factory, the \n\
actively maintained replacement for the older BasicShapes module. Unlike \n\
BasicShapes, it returns plain (vertices, indices, colors, normals) arrays, so \n\
this script wires each shape's own Entity/Transform/Shader/VertexArray by hand. \n\
A torus, cylinder, cube and sphere are stacked and Phong-lit by a point light, \n\
in the same layout as example_basic_shapes.py. \n\
You may move the camera using the mouse or the GUI. Hit ESC OR Close the window to quit."


def spawn_shape(scene, parent, name, shape_type, params, position, scale=1.0):
    """One geometry_factory shape as a Phong-lit ECS entity under `parent`. Returns
    (entity, transform, shader) so the caller can drive the shader's per-frame uniforms."""
    vertices, indices, colors, normals = geometry_factory.build_render_mesh(shape_type, params)

    entity = scene.world.createEntity(Entity(name=name))
    scene.world.addEntityChild(parent, entity)
    trans = scene.world.addComponent(
        entity, BasicTransform(name=f"{name}_trans", trs=util.translate(*position) @ util.scale(scale))
    )
    mesh = scene.world.addComponent(entity, RenderMesh(name=f"{name}_mesh"))
    mesh.vertex_attributes.extend([vertices, colors, normals])
    mesh.vertex_index.append(indices)
    shaderDec = scene.world.addComponent(
        entity, ShaderGLDecorator(Shader(vertex_import_file=SHADER_DIR / "Phong.vert", fragment_import_file=SHADER_DIR / "Phong.frag"))
    )
    scene.world.addComponent(entity, VertexArray())
    return entity, trans, shaderDec


def spawn_light_marker(scene, parent, position):
    """A small unlit cube marking the point light's position -- geometry_factory's cube standing
    in for BasicShapes.PointLight's own hand-rolled one."""
    vertices, indices, colors, normals = geometry_factory.build_render_mesh("cube", {"color": [1.0, 1.0, 1.0]})
    entity = scene.world.createEntity(Entity(name="PointLight"))
    scene.world.addEntityChild(parent, entity)
    trans = scene.world.addComponent(
        entity, BasicTransform(name="PointLight_trans", trs=util.translate(*position) @ util.scale(0.2))
    )
    mesh = scene.world.addComponent(entity, RenderMesh(name="PointLight_mesh"))
    mesh.vertex_attributes.extend([vertices, colors, normals])
    mesh.vertex_index.append(indices)
    shaderDec = scene.world.addComponent(
        entity, ShaderGLDecorator(Shader(vertex_import_file=SHADER_DIR / "ColorMVP.vert", fragment_import_file=SHADER_DIR / "Color.frag"))
    )
    scene.world.addComponent(entity, VertexArray())
    return entity, trans, shaderDec


def main():
    # Material -- shared by every shape below, as in example_basic_shapes.py
    shininess = 0.4
    mat_color = util.vec(0.6, 0.6, 0.6)
    ambient_color = (1.0, 1.0, 1.0)
    ambient_strength = 0.1
    light_color = np.array((1.0, 1.0, 1.0))
    light_intensity = 1.0

    scene = Scene()

    transUpdate = scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
    camUpdate = scene.world.createSystem(CameraSystem("camUpdate", "CameraUpdate", "200"))
    renderUpdate = scene.world.createSystem(RenderGLShaderSystem())
    initUpdate = scene.world.createSystem(InitGLShaderSystem())

    rootEntity = scene.world.createEntity(Entity(name="Root"))

    mainCamera = SimpleCamera("Simple Camera")
    mainCamera.trans2.trs = util.translate(0, 0, 8)
    mainCamera.trans1.trs = util.rotate((1, 0, 0), -45)

    _, lightTrans, lightShaderDec = spawn_light_marker(scene, rootEntity, position=(0.8, 1.0, 1.0))

    home = scene.world.createEntity(Entity(name="Home"))
    scene.world.addEntityChild(rootEntity, home)
    scene.world.addComponent(home, BasicTransform(name="Home_trans", trs=util.identity()))

    # Same stacked layout as example_basic_shapes.py's torus/cylinder/cube/sphere.
    grey = [0.6, 0.6, 0.6]
    shapes = [
        spawn_shape(scene, home, "Torus", "torus", {"color": grey}, position=(0, 0, 0), scale=0.5),
        spawn_shape(scene, home, "Cylinder", "cylinder", {"color": grey}, position=(0, 1.5, 0), scale=0.5),
        spawn_shape(scene, home, "Cube", "cube", {"color": grey}, position=(0, 3, 0), scale=0.5),
        spawn_shape(scene, home, "Sphere", "sphere", {"color": grey}, position=(0, -1.5, 0), scale=0.5),
    ]

    running = True
    scene.init(
        imgui=True, windowWidth=1024, windowHeight=800,
        windowTitle="Elements: Geometry Factory Example", customImGUIdecorator=ImGUIecssDecorator,
    )

    # Pre-pass GLInit traversal (needs the GL context scene.init() just created).
    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
    gl.glDisable(gl.GL_CULL_FACE)
    gl.glEnable(gl.GL_DEPTH_TEST)
    gl.glDepthFunc(gl.GL_LESS)
    scene.world.traverse_visit(initUpdate, scene.world.root)

    gWindow = scene.renderWindow
    eManager = scene.world.eventManager
    renderGLEventActuator = RenderGLStateSystem()
    eManager._subscribers["OnUpdateWireframe"] = gWindow
    eManager._actuators["OnUpdateWireframe"] = renderGLEventActuator
    eManager._subscribers["OnUpdateCamera"] = gWindow
    eManager._actuators["OnUpdateCamera"] = renderGLEventActuator

    while running:
        scene.world.traverse_visit(transUpdate, scene.world.root)
        scene.world.traverse_visit_pre_camera(camUpdate, mainCamera.camera)
        scene.world.traverse_visit(camUpdate, scene.world.root)
        view_pos = mainCamera.trans2.l2world[:3, 3].tolist()
        light_pos = lightTrans.l2world[:3, 3].tolist()

        lightShaderDec.setUniformVariable(key="modelViewProj", value=lightTrans.l2cam, mat4=True)

        for _entity, trans, shaderDec in shapes:
            shaderDec.setUniformVariable(key="modelViewProj", value=trans.l2cam, mat4=True)
            shaderDec.setUniformVariable(key="model", value=trans.l2world, mat4=True)
            shaderDec.setUniformVariable(key="ambientColor", value=ambient_color, float3=True)
            shaderDec.setUniformVariable(key="ambientStr", value=ambient_strength, float1=True)
            shaderDec.setUniformVariable(key="viewPos", value=view_pos, float3=True)
            shaderDec.setUniformVariable(key="lightPos", value=light_pos, float3=True)
            shaderDec.setUniformVariable(key="lightColor", value=light_color, float3=True)
            shaderDec.setUniformVariable(key="lightIntensity", value=light_intensity, float1=True)
            shaderDec.setUniformVariable(key="shininess", value=shininess, float1=True)
            shaderDec.setUniformVariable(key="matColor", value=mat_color, float3=True)

        running = scene.render()
        displayGUI_text(example_description)
        scene.world.traverse_visit(renderUpdate, scene.world.root)
        scene.render_post()

    scene.shutdown()


if __name__ == "__main__":
    main()
