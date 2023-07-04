import numpy as np

import Elements.pyECSS.utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, RenderMesh
from Elements.pyECSS.System import TransformSystem, CameraSystem
from Elements.pyGLV.GL.Scene import Scene

from Elements.pyGLV.GUI.Viewer import RenderGLStateSystem

from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray
from OpenGL.GL import GL_LINES

import OpenGL.GL as gl
import imgui

plot_boundaries = 1, -1, 1, -1 #max X, min X, max Y, min Y
f_x = 'x**2+x*4'
f_x_y = 'x**2+y**2'
func_detail = 100

class FunctionPlotting:
    def __init__(self, function2d_entity, function3d_entity, scene, root_entity, shader_2d, shader_3d,  init_update) -> None:

        self.function2d_entity = function2d_entity
        self.function3d_entity = function3d_entity
        self.scene = scene
        self.rootEntity = root_entity
        self.shader_2d = shader_2d
        self.shader_3d = shader_3d
        self.initUpdate = init_update

    def render_gui_and_plots(self):
        global plot_boundaries
        global f_x_y
        global f_x
        global func_detail

        imgui.begin("Plot 2D and 3D Function")

        changed, f_x = imgui.input_text('2D Function F(x)', f_x, 256)

        button_print_2D_pressed = imgui.button("Print f(x)")

        changed, f_x_y = imgui.input_text('3D Function F(x,y)', f_x_y, 256)

        button_print_3D_pressed = imgui.button("Print f(x,y)")

        imgui.text("Give plot range: max X, min X, max Y, min Y")
        changed, plot_boundaries = imgui.input_float4('', *plot_boundaries)
        # imgui.same_line()
        imgui.text("max X: %.1f, min X: %.1f, max Y: %.1f, min Y: %.1f" % (plot_boundaries[0], plot_boundaries[1], plot_boundaries[2], plot_boundaries[3]))
        changed, func_detail = imgui.input_int('Detailed', func_detail)
        if imgui.is_item_hovered():
            imgui.set_tooltip("Make sure the detail is between 4 to 100")


        if (func_detail > 100):
            func_detail = 100
        elif (func_detail < 4):
            func_detail = 4
        if button_print_2D_pressed:
            self.render_2d_plot(plot_boundaries, func_detail, f_x)
        if button_print_3D_pressed:
            self.render_3d_plot(plot_boundaries, func_detail, f_x_y)
        imgui.end()

    def render_2d_plot(self, plot_boundaries, func_detail, f_x):
        plotting2d_vertices, plotting2d_colors, plotting2d_indices = generate_plot2d_data(plot_boundaries, func_detail, f_x)

        ## ADD / UPDATE PLOT 2D ##

        remove_entity_children(self.function2d_entity)

        plotting2d_trans = self.scene.world.addComponent(self.function2d_entity,
                                                     BasicTransform(name="plotting2d_trans", trs=util.identity()))
        plotting2d_mesh = self.scene.world.addComponent(self.function2d_entity, RenderMesh(name="plotting2d_mesh"))
        plotting2d_mesh.vertex_attributes.append(plotting2d_vertices)
        plotting2d_mesh.vertex_attributes.append(plotting2d_colors)
        plotting2d_mesh.vertex_index.append(plotting2d_indices)
        plotting2d_vArray = self.scene.world.addComponent(self.function2d_entity,
                                                      VertexArray(primitive=GL_LINES))  # note the primitive change

        plotting2d_shader = self.scene.world.addComponent(self.function2d_entity, ShaderGLDecorator(
            Shader(vertex_source=Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))
        self.shader_2d.append(plotting2d_shader)

        self.scene.world.traverse_visit(self.initUpdate, self.scene.world.root)

    def render_3d_plot(self, plot_boundaries, func_detail, f_x_y):
        removeEntityChilds(SuperFunction3D)
        superfuncchild3D = 0

        x = np.linspace(FuncValues[0], FuncValues[1], func_detail)
        z = np.linspace(FuncValues[2], FuncValues[3], func_detail)
        yValues = []
        for xiterate in x:
            for ziterate in z:
                yValues.append(eval_f_x_y(xiterate, ziterate))

        maximumy = np.max(yValues)  # NEEDED to print the color based on y axis
        minimumy = np.min(yValues)  # NEEDED to print the color based on y axis
        if (maximumy == 0):
            maximumy = 1

        triangles_vertices = []

        q = 0
        r = 0.34
        g = 0.15
        b = 0.
        while (q < len(z) - 1):
            q += 1
            l = 0
            while (l < len(x) - 1):
                currY = eval_f_x_y(x[l], z[q])
                r = 0.34 + ((currY - minimumy) / (maximumy + abs(minimumy))) * 0.6
                g = 0.15 + ((currY - minimumy) / (maximumy + abs(minimumy))) * 0.6
                b = ((currY - minimumy) / (maximumy + abs(minimumy))) * 0.6

                l += 1
                # first triangle
                superfuncchild3D += 1
                DynamicVariable = "Function" + str(superfuncchild3D)
                point1 = x[l - 1], eval_f_x_y(x[l - 1], z[q - 1]), z[q - 1], 1
                point2 = x[l], eval_f_x_y(x[l], z[q - 1]), z[q - 1], 1
                point3 = x[l], eval_f_x_y(x[l], z[q]), z[q], 1
                # vars()[DynamicVariable]: GameObjectEntity = TriangleSpawn(DynamicVariable, point1, point2, point3, r, g,
                #                                                           b)
                # scene.world.addEntityChild(SuperFunction3D, vars()[DynamicVariable])
                triangles_vertices.append(point1)
                triangles_vertices.append(point2)
                triangles_vertices.append(point3)


                # second triangle
                superfuncchild3D += 1
                DynamicVariable = "Function" + str(superfuncchild3D)
                point1 = x[l - 1], eval_f_x_y(x[l - 1], z[q - 1]), z[q - 1], 1
                point2 = x[l], eval_f_x_y(x[l], z[q]), z[q], 1
                point3 = x[l - 1], eval_f_x_y(x[l - 1], z[q]), z[q], 1
                # vars()[DynamicVariable]: GameObjectEntity = TriangleSpawn(DynamicVariable, point1, point2, point3, r, g,
                #                                                           b)
                # scene.world.addEntityChild(SuperFunction3D, vars()[DynamicVariable])
                triangles_vertices.append(point1)
                triangles_vertices.append(point2)
                triangles_vertices.append(point3)


        triangles_indices = range(len(triangles_vertices))
        triangles_colors = np.array([[1.0, 1.0, 1.0, 1.0]] * len(triangles_vertices), dtype=np.float32)

        triangles_normals = []
        #create array of normals with size of vertices
        sumNormals = np.array([(0.,0.,0.)] * len(triangles_vertices))
        sumCounter = np.array([(0)] * len(triangles_vertices))
        for i in range(0, len(triangles_indices), 3):
            #calculate normal for each triangle
            normal = np.cross(np.subtract(triangles_vertices[triangles_indices[i+1]], triangles_vertices[triangles_indices[i]])[:-1], np.subtract(triangles_vertices[triangles_indices[i+2]], triangles_vertices[triangles_indices[i]])[:-1])
            #normalize normal
            normal = normal / np.linalg.norm(normal)
            #add normal to each vertex of the triangle
            sumNormals[triangles_indices[i]] += normal
            sumNormals[triangles_indices[i + 1]] += normal
            sumNormals[triangles_indices[i + 2]] += normal
            #increase counter for each vertex of the triangle
            sumCounter[triangles_indices[i]] += 1
            sumCounter[triangles_indices[i + 1]] += 1
            sumCounter[triangles_indices[i + 2]] += 1
        #iterrate through all triangles and set normals to average normal
        for i in range(len(sumNormals)):
            new_normal = sumNormals[i]/sumCounter[i]
            new_normal = new_normal / np.linalg.norm(new_normal)
            triangles_normals.append(new_normal)


        triangles_trans = scene.world.addComponent(SuperFunction3D,
                                                    BasicTransform(name="triangles_trans", trs=util.identity()))
        triangles_mesh = scene.world.addComponent(SuperFunction3D, RenderMesh(name="triangles_mesh"))
        triangles_mesh.vertex_attributes.append(triangles_vertices)
        triangles_mesh.vertex_attributes.append(triangles_colors)
        triangles_mesh.vertex_attributes.append(triangles_normals)
        triangles_mesh.vertex_index.append(triangles_indices)
        triangles_vArray = scene.world.addComponent(SuperFunction3D,
                                                    VertexArray()) 

        triangles_shader = scene.world.addComponent(SuperFunction3D, ShaderGLDecorator(
            Shader(vertex_source=Shader.VERT_PHONG_MVP, fragment_source=Shader.FRAG_PHONG)))
        triangle_shader_wrapper.append(triangles_shader)

        scene.world.traverse_visit(initUpdate, scene.world.root)

def generate_plot2d_data(plot_boundaries, func_detail, f_x):
    x = np.linspace(plot_boundaries[0], plot_boundaries[1], func_detail)
    y = eval_f_x(f_x, x)
    
    plotting_vertices = np.empty((0, 4), np.float32)
    for i in range(0, len(x)-2):
        point1 = [x[i], y[i], 0.0, 1.0]
        point2 = [x[i+1], y[i+1], 0.0, 1.0]
        plotting_vertices = np.append(plotting_vertices, [point1, point2], axis=0)

    plotting_colors = np.array([[0.5, 0.0, 1.0, 1.0]] * len(plotting_vertices), dtype=np.float32)

    plotting_indices = np.array(range(len(plotting_vertices)), np.uint32)

    print("plotting_vertices", plotting_vertices)

    return plotting_vertices, plotting_colors, plotting_indices

def remove_entity_children(entity: Entity):
    while entity.getChild(1) is not None:
        entity.remove(entity.getChild(1))

def eval_f_x_y(function, x,y):
    d= {}
    d['x'] = x
    d['y'] = y
    z = eval(function,d)
    return z

def eval_f_x(function, x):
    d= {}
    d['x'] = x
    y = eval(function,d)
    return y