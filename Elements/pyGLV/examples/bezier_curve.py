#### BEZIER 3D ####

import numpy as np
import bezier
import imgui

import Elements.pyECSS.utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, RenderMesh

from Elements.pyGLV.GL.Shader import Shader, ShaderGLDecorator
from Elements.pyGLV.GL.VertexArray import VertexArray

from OpenGL.GL import GL_LINES, GL_POINTS, glPointSize

test_bezier_control_nodes = [[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]]

input_bezier_control_nodes = [[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]]
input_render_detail = 100

class Bezier_Curve():
    def __init__(self, bezier_entity, scene, rootEntity, all_shaders, initUpdate) -> None:

        self.bezier_entity = bezier_entity
        self.scene = scene
        self.rootEntity = rootEntity
        self.all_shaders = all_shaders
        self.initUpdate = initUpdate


    def render_gui_and_curve(self):
        global input_render_detail
        global global_bezier
        global_bezier = self.bezier_entity

        global input_bezier_control_nodes
        imgui.begin("Print Bezier Curve")

        imgui.text("Control nodes X, Y, Z")
        for i, control_node in enumerate(input_bezier_control_nodes):
            changed, input_bezier_control_nodes[i] = imgui.input_float3(f"Control Node {i + 1}", *control_node)

        button_remove_node_pressed = imgui.button("Remove Node")
        imgui.same_line()
        button_add_node_pressed = imgui.button("Add Node")
        if (button_remove_node_pressed):
            input_bezier_control_nodes.pop()
        if (button_add_node_pressed):
            input_bezier_control_nodes.append([0.0, 0.0, 0.0])

        button_bezier_pressed = imgui.button("Print Bezier")

        changed, input_render_detail = imgui.input_int('Detailed', input_render_detail)
        if imgui.is_item_hovered():
            imgui.set_tooltip("Make sure the detail is between 4 to 100")

        if (button_bezier_pressed):
            input_bezier_control_nodes = [list(tuple) for tuple in input_bezier_control_nodes]
            self.render_curve(input_bezier_control_nodes, input_render_detail)

        imgui.end()

    def render_curve(self, bezier_control_nodes, render_detail):
        vertexBezier, colorBezier, indexBezier = generate_bezier_data(bezier_control_nodes,
                                                                      render_detail, 0, 1)

        ## ADD / UPDATE BEZIER ##

        removeEntityChilds(global_bezier)

        self.scene.world.addEntityChild(self.rootEntity, global_bezier)
        bezier_trans = self.scene.world.addComponent(global_bezier,
                                                     BasicTransform(name="bezier_trans", trs=util.identity()))
        bezier_mesh = self.scene.world.addComponent(global_bezier, RenderMesh(name="bezier_mesh"))
        bezier_mesh.vertex_attributes.append(vertexBezier)
        bezier_mesh.vertex_attributes.append(colorBezier)
        bezier_mesh.vertex_index.append(indexBezier)
        bezier_vArray = self.scene.world.addComponent(global_bezier,
                                                      VertexArray(primitive=GL_LINES))  # note the primitive change

        bezier_shader = self.scene.world.addComponent(global_bezier, ShaderGLDecorator(
            Shader(vertex_source=Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))
        self.all_shaders.append(bezier_shader)

        ## VISUALIZE BEZIER CONTROL NODES ##

        vertexControlNodes = xyz_to_vertecies(bezier_control_nodes)
        colorControlNodes = np.array([[0.5, 0.5, 1.0, 1.0]] * len(vertexControlNodes), dtype=np.float32)
        indexControlNodes = np.array(range(len(vertexControlNodes)), np.uint32)

        control_nodes = self.scene.world.createEntity(Entity(name="control_nodes"))
        self.scene.world.addEntityChild(self.rootEntity, control_nodes)
        control_nodes_trans = self.scene.world.addComponent(control_nodes,
                                                            BasicTransform(name="control_nodes_trans",
                                                                           trs=util.identity()))
        control_nodes_mesh = self.scene.world.addComponent(control_nodes, RenderMesh(name="control_nodes_mesh"))
        control_nodes_mesh.vertex_attributes.append(vertexControlNodes)
        control_nodes_mesh.vertex_attributes.append(colorControlNodes)
        control_nodes_mesh.vertex_index.append(indexControlNodes)
        glPointSize(5)
        control_nodes_vArray = self.scene.world.addComponent(control_nodes, VertexArray(primitive=GL_POINTS))

        # TODO
        # GL POINT SIZE ASK DOMINIK!

        control_nodes_shader = self.scene.world.addComponent(control_nodes, ShaderGLDecorator(
            Shader(vertex_source=Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))
        self.all_shaders.append(control_nodes_shader)

        self.scene.world.traverse_visit(self.initUpdate, self.scene.world.root)

def vertecies_to_line_vertecies(coordinates):
    vertecies = []
    vertecies.append(coordinates[0])
    for coord in coordinates[1:-1]:
        vertecies.extend([coord, coord])
    vertecies.append(coordinates[-1])
    return vertecies

def separate_coordinates(coordinates):
    x_coordinates = [coord[0] for coord in coordinates]
    y_coordinates = [coord[1] for coord in coordinates]
    z_coordinates = [coord[2] for coord in coordinates]
    return [x_coordinates, y_coordinates, z_coordinates]

def combine_coordinates(coordinates):
    return [[coord[0], coord[1], coord[2]] for coord in zip(coordinates[0], coordinates[1], coordinates[2])]

def xyz_to_vertecies(coords):
    return [coord + [1.0] for coord in coords]


def generate_bezier_data(bezier_nodes, num_points, start_x, end_x):
    bezier_curve = bezier.Curve.from_nodes(separate_coordinates(bezier_nodes))
    print("created bezier curve:", bezier_curve)

    x_values = np.linspace(start_x, end_x, num_points)
    bezier_points = bezier_curve.evaluate_multi(x_values)
    print("bezier_points", bezier_points)

    xyz_values = combine_coordinates(bezier_points)

    vertexBezier = np.array(vertecies_to_line_vertecies(xyz_to_vertecies(xyz_values)), dtype=np.float32)
    print("vertexBezier", vertexBezier)

    colorBezier = np.array([[0.5, 0.0, 1.0, 1.0]] * len(vertexBezier), dtype=np.float32)

    indexBezier = np.array(range(len(vertexBezier)), np.uint32)

    return vertexBezier, colorBezier, indexBezier


def removeEntityChilds(entity: Entity):
    while entity.getChild(1) != None:
        entity.remove(entity.getChild(1))
