COLOR_FRAG = """
    #version 410

    in vec4 color;
    out vec4 outputColor;

    void main()
    {
        outputColor = color;
        //outputColor = vec4(0.1, 0.1, 0.1, 1);
    }
"""

COLOR_VERT_MVP = """

    #version 410

    layout (location=0) in vec4 vPosition;
    layout (location=1) in vec4 vColor;

    out     vec4 color;
    uniform mat4 modelViewProj;
    uniform vec4 extColor;

    void main()
    {

        gl_Position = modelViewProj * vPosition;
        color = extColor;
    }
"""

VERT_PHONG_MVP = """
    #version 410

    layout (location=0) in vec4 vPosition;
    layout (location=1) in vec4 vColor;
    layout (location=2) in vec4 vNormal;

    out     vec4 pos;
    out     vec4 color;
    out     vec3 normal;

    uniform mat4 modelViewProj;
    uniform mat4 model;

    void main()
    {
        gl_Position = modelViewProj * vPosition;
        pos = model * vPosition;
        color = vColor;
        normal = mat3(transpose(inverse(model))) * vNormal.xyz;
    }
"""

FRAG_PHONG = """
    #version 410

    in vec4 pos;
    in vec4 color;
    in vec3 normal;

    out vec4 outputColor;

    // Phong products
    uniform vec3 ambientColor;
    uniform float ambientStr;

    // Lighting 
    uniform vec3 viewPos;
    uniform vec3 lightPos;
    uniform vec3 lightColor;
    uniform float lightIntensity;

    // Material
    uniform float shininess;
    uniform vec3 matColor;

    void main()
    {
        vec3 norm = normalize(normal);
        vec3 lightDir = normalize(lightPos - pos.xyz);
        vec3 viewDir = normalize(viewPos - pos.xyz);
        vec3 reflectDir = reflect(-lightDir, norm);


        // Ambient
        vec3 ambientProduct = ambientStr * ambientColor;
        // Diffuse
        float diffuseStr = max(dot(norm, lightDir), 0.0);
        vec3 diffuseProduct = diffuseStr * lightColor;
        // Specular
        float specularStr = pow(max(dot(viewDir, reflectDir), 0.0), 32);
        vec3 specularProduct = shininess * specularStr * color.xyz;

        vec3 result = (ambientProduct + (diffuseProduct + specularProduct) * lightIntensity) * matColor;
        outputColor = vec4(result, 1);
    }
"""


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





class IndexedConverter():

    # Assumes triangulated buffers. Produces indexed results that support
    # normals as well.
    def Convert(self, vertices, colors, indices, produceNormals=True):

        iVertices = []
        iColors = []
        iNormals = []
        iIndices = []
        for i in range(0, len(indices), 3):
            iVertices.append(vertices[indices[i]])
            iVertices.append(vertices[indices[i + 1]])
            iVertices.append(vertices[indices[i + 2]])
            iColors.append(colors[indices[i]])
            iColors.append(colors[indices[i + 1]])
            iColors.append(colors[indices[i + 2]])

            iIndices.append(i)
            iIndices.append(i + 1)
            iIndices.append(i + 2)

        if produceNormals:
            for i in range(0, len(indices), 3):
                iNormals.append(
                    util.calculateNormals(vertices[indices[i]], vertices[indices[i + 1]], vertices[indices[i + 2]]))
                iNormals.append(
                    util.calculateNormals(vertices[indices[i]], vertices[indices[i + 1]], vertices[indices[i + 2]]))
                iNormals.append(
                    util.calculateNormals(vertices[indices[i]], vertices[indices[i + 1]], vertices[indices[i + 2]]))

        iVertices = np.array(iVertices, dtype=np.float32)
        iColors = np.array(iColors, dtype=np.float32)
        iIndices = np.array(iIndices, dtype=np.uint32)

        iNormals = np.array(iNormals, dtype=np.float32)

        return iVertices, iColors, iIndices, iNormals

class GameObjectEntity_Point(Entity):
    def __init__(self, name=None, type=None, id=None, primitiveID=gl.GL_LINES) -> None:
        super().__init__(name, type, id)

        # Gameobject basic properties
        self._color = [1, 0.5, 0.2, 1.0]  # this will be used as a uniform var
        # Create basic components of a primitive object
        self.trans = BasicTransform(name="trans", trs=util.identity())
        self.mesh = RenderMesh(name="mesh")
        # self.shaderDec      = ShaderGLDecorator(Shader(vertex_source=Shader.VERT_PHONG_MVP, fragment_source=Shader.FRAG_PHONG))
        self.shaderDec = ShaderGLDecorator(Shader(vertex_source=COLOR_VERT_MVP, fragment_source=COLOR_FRAG))
        self.vArray = VertexArray(primitive=primitiveID)
        # Add components to entity
        scene = Scene()
        scene.world.createEntity(self)
        scene.world.addComponent(self, self.trans)
        scene.world.addComponent(self, self.mesh)
        scene.world.addComponent(self, self.shaderDec)
        scene.world.addComponent(self, self.vArray)

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, colorArray):
        self._color = colorArray

    def drawSelfGui(self, imgui):
        changed, value = imgui.color_edit3("Color", self.color[0], self.color[1], self.color[2])
        self.color = [value[0], value[1], value[2], 1.0]

    def SetVertexAttributes(self, vertex, color, index, normals=None):
        self.mesh.vertex_attributes.append(vertex)
        self.mesh.vertex_attributes.append(color)
        self.mesh.vertex_index.append(index)
        if normals is not None:
            self.mesh.vertex_attributes.append(normals)


class GameObjectEntity(Entity):

    def __init__(self, name=None, type=None, id=None, primitiveID=gl.GL_LINES) -> None:
        super().__init__(name, type, id)

        # Gameobject basic properties
        self._color = [1, 0.5, 0.2, 1.0]  # this will be used as a uniform var
        # Create basic components of a primitive object
        self.trans = BasicTransform(name="trans", trs=util.identity())
        self.mesh = RenderMesh(name="mesh")
        self.shaderDec = ShaderGLDecorator(Shader(vertex_source=VERT_PHONG_MVP, fragment_source=FRAG_PHONG))
        # self.shaderDec      = ShaderGLDecorator(Shader(vertex_source= Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG))
        self.vArray = VertexArray(primitive=primitiveID)
        # Add components to entity
        scene = Scene()
        scene.world.createEntity(self)
        scene.world.addComponent(self, self.trans)
        scene.world.addComponent(self, self.mesh)
        scene.world.addComponent(self, self.shaderDec)
        scene.world.addComponent(self, self.vArray)

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, colorArray):
        self._color = colorArray

    def drawSelfGui(self, imgui):
        changed, value = imgui.color_edit3("Color", self.color[0], self.color[1], self.color[2])
        self.color = [value[0], value[1], value[2], 1.0]

    def SetVertexAttributes(self, vertex, color, index, normals=None):
        self.mesh.vertex_attributes.append(vertex)
        self.mesh.vertex_attributes.append(color)
        self.mesh.vertex_index.append(index)
        if normals is not None:
            self.mesh.vertex_attributes.append(normals)


def LineSpawn(linename="Line", p1=[0, 0, 0, 1], p2=[0.4, 0.4, 0, 1], r=0.7, g=0.7, b=0.7):
    line = GameObjectEntity(linename, primitiveID=gl.GL_LINES)
    vertices = [
        p1, p2
    ]
    colors = [
        [r, g, b, 1.0],
        [r, g, b, 1.0]
    ]

    indices = np.array(
        (
            0, 1, 3
        ),
        dtype=np.uint32
    )

    line.SetVertexAttributes(vertices, colors, indices, None)

    return line


def PointSpawn(pointname="Point", p1=[0, 0, 0, 1], r=0., g=1., b=1.):
    point = GameObjectEntity_Point(pointname, primitiveID=gl.GL_POINTS)
    vertices = [
        p1
    ]
    colors = [

        [r, g, b, 1.0]
    ]
    indices = np.array(
        (
            0
        ),
        dtype=np.uint32
    )

    # vertices, colors, indices, normals = IndexedConverter().Convert(vertices, colors, indices, produceNormals=True)
    point.SetVertexAttributes(vertices, colors, indices, None)

    return point









scene = Scene()
rootEntity = scene.world.createEntity(Entity(name="RooT"))
entityCam1 = scene.world.createEntity(Entity(name="entityCam1"))
scene.world.addEntityChild(rootEntity, entityCam1)
trans1 = scene.world.addComponent(entityCam1, BasicTransform(name="trans1", trs=util.identity()))

axes = scene.world.createEntity(Entity(name="axes"))
scene.world.addEntityChild(rootEntity, axes)
axes_trans = scene.world.addComponent(axes, BasicTransform(name="axes_trans", trs=util.identity()))
axes_mesh = scene.world.addComponent(axes, RenderMesh(name="axes_mesh"))

SuperFunction2D = scene.world.createEntity(Entity("SuperFunction"))
scene.world.addEntityChild(rootEntity, SuperFunction2D)
trans8 = BasicTransform(name="trans8", trs=util.identity())
scene.world.addComponent(SuperFunction2D, trans8)

SuperFunction3D = scene.world.createEntity(Entity("SuperFunction"))
scene.world.addEntityChild(rootEntity, SuperFunction3D)
trans12 = BasicTransform(name="trans12", trs=util.identity())
scene.world.addComponent(SuperFunction3D, trans12)

spotPoints = scene.world.createEntity(Entity("spotPoints"))
scene.world.addEntityChild(rootEntity, spotPoints)
trans21 = BasicTransform(name="trans21", trs=util.identity())
scene.world.addComponent(spotPoints, trans21)

axes = scene.world.createEntity(Entity(name="axes"))
scene.world.addEntityChild(rootEntity, axes)
axes_trans = scene.world.addComponent(axes, BasicTransform(name="axes_trans", trs=util.identity()))
axes_mesh = scene.world.addComponent(axes, RenderMesh(name="axes_mesh"))

# Systems
transUpdate = scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
camUpdate = scene.world.createSystem(CameraSystem("camUpdate", "CameraUpdate", "200"))
renderUpdate = scene.world.createSystem(RenderGLShaderSystem())
initUpdate = scene.world.createSystem(InitGLShaderSystem())

spotPointschild=0
SpotPointsColor = 0., 1., 1., 1

PointSize = 5
LightPositionValues= 0.4,8.,0.5

triangle_shader_wrapper = []

def boundries(xmin=-1, xmax =1, ymin=-1,ymax=1,zmin=-1,zmax=1):


    global spotPointschild
    removeEntityChilds(spotPoints)
    spotPointschild=0
    xminR = round(xmin)
    xmaxR = round(xmax)
    yminR = round(ymin)
    ymaxR = round(ymax)
    zminR = round(zmin)
    zmaxR = round(zmax)
    passingx = xminR
    passingy = yminR
    passingz = zminR
    while(passingy <= ymaxR):
        passingx = xminR
        while(passingx <= xmaxR):
            passingz = zminR
            while(passingz <= zmaxR):
                spotPointschild += 1
                DynamicVariable = "spotPoints" + str(spotPointschild)
                point1 = passingx,passingy,passingz,1
                vars()[DynamicVariable]: GameObjectEntity_Point = PointSpawn(DynamicVariable,point1,0,1,1)
                scene.world.addEntityChild(spotPoints, vars()[DynamicVariable])
                passingz += 0.5
            passingx += 0.5
        passingy += 0.5
    scene.world.traverse_visit(initUpdate, scene.world.root)

FuncValues = 0., 1., 0., 1.
f_x = 'x**2+x*4'
f_x_y = 'x**2+y**2'
superfuncchild2D = 0
superfuncchild3D = 0
funcDetail = 10

def Func_GUI():
    global FuncValues
    global f_x_y
    global f_x

    global superfuncchild2D
    global superfuncchild3D
    global funcDetail
    global platforms
    imgui.begin("Give Function X,Y Values")

    # implementation for a,b,c,d points for X,Y functions
    changed, f_x = imgui.input_text(':F(x)', f_x, 256)

    Func_Button2D = imgui.button("Print f(x)")

    changed, f_x_y = imgui.input_text(':F(x,y)', f_x_y, 256)

    Func_Button3D = imgui.button("Print f(x,y)")

    imgui.text("Give a to b values for X and c to d for Y")
    changed, FuncValues = imgui.input_float4('', *FuncValues)
    # imgui.same_line()
    imgui.text("a: %.1f, b: %.1f, c: %.1f, d: %.1f" % (FuncValues[0], FuncValues[1], FuncValues[2], FuncValues[3]))
    changed, funcDetail = imgui.input_int('Detailed', funcDetail)
    if imgui.is_item_hovered():
        imgui.set_tooltip("Make sure the detail is between 4 to 100")


    if (funcDetail > 100):
        funcDetail = 100
    elif (funcDetail < 4):
        funcDetail = 4
    if (Func_Button2D):
        removeEntityChilds(SuperFunction2D)
        superfuncchild2D = 0
        x = np.linspace(FuncValues[0], FuncValues[1], funcDetail)
        y = f_X(x)
        l = 0
        while (l < len(x) - 1):
            superfuncchild2D += 1
            l += 1
            DynamicVariable = "SuperFunction" + str(superfuncchild2D)
            point1 = x[l], y[l], 0, 1
            point2 = x[l - 1], y[l - 1], 0, 1
            vars()[DynamicVariable]: GameObjectEntity = LineSpawn(DynamicVariable, point2, point1, r=1, g=1, b=1)
            scene.world.addEntityChild(SuperFunction2D, vars()[DynamicVariable])

        scene.world.traverse_visit(initUpdate, scene.world.root)
    if (Func_Button3D):
        removeEntityChilds(SuperFunction3D)
        superfuncchild3D = 0

        x = np.linspace(FuncValues[0], FuncValues[1], funcDetail)
        z = np.linspace(FuncValues[2], FuncValues[3], funcDetail)
        yValues = []
        for xiterate in x:
            for ziterate in z:
                yValues.append(f_Z(xiterate, ziterate))

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
                currY = f_Z(x[l], z[q])
                r = 0.34 + ((currY - minimumy) / (maximumy + abs(minimumy))) * 0.6
                g = 0.15 + ((currY - minimumy) / (maximumy + abs(minimumy))) * 0.6
                b = ((currY - minimumy) / (maximumy + abs(minimumy))) * 0.6

                l += 1
                # first triangle
                superfuncchild3D += 1
                DynamicVariable = "Function" + str(superfuncchild3D)
                point1 = x[l - 1], f_Z(x[l - 1], z[q - 1]), z[q - 1], 1
                point2 = x[l], f_Z(x[l], z[q - 1]), z[q - 1], 1
                point3 = x[l], f_Z(x[l], z[q]), z[q], 1
                # vars()[DynamicVariable]: GameObjectEntity = TriangleSpawn(DynamicVariable, point1, point2, point3, r, g,
                #                                                           b)
                # scene.world.addEntityChild(SuperFunction3D, vars()[DynamicVariable])
                triangles_vertices.append(point1)
                triangles_vertices.append(point2)
                triangles_vertices.append(point3)


                # second triangle
                superfuncchild3D += 1
                DynamicVariable = "Function" + str(superfuncchild3D)
                point1 = x[l - 1], f_Z(x[l - 1], z[q - 1]), z[q - 1], 1
                point2 = x[l], f_Z(x[l], z[q]), z[q], 1
                point3 = x[l - 1], f_Z(x[l - 1], z[q]), z[q], 1
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
        boundries(FuncValues[0], FuncValues[1], minimumy, maximumy, FuncValues[2], FuncValues[3])
    imgui.end()

def removeEntityChilds(entity: Entity):
    while entity.getChild(1) != None:
        entity.remove(entity.getChild(1))


def f_Z (x,y):
    import numpy as np
    global f_x_y
    d= {}
    d['x'] = x
    d['y'] = y
    z = eval(f_x_y,d)
    return z

def f_X (x):
    global f_x
    d= {}
    d['x'] = x
    y = eval(f_x,d)
    return y

def main(imguiFlag=False):
    # Colored Axes
    vertexAxes = np.array([
        [0.0, 0.0, 0.0, 1.0],
        [1.0, 0.0, 0.0, 1.0],
        [0.0, 0.0, 0.0, 1.0],
        [0.0, 1.0, 0.0, 1.0],
        [0.0, 0.0, 0.0, 1.0],
        [0.0, 0.0, 1.0, 1.0]
    ], dtype=np.float32)
    colorAxes = np.array([
        [1.0, 0.0, 0.0, 1.0],
        [1.0, 0.0, 0.0, 1.0],
        [0.0, 1.0, 0.0, 1.0],
        [0.0, 1.0, 0.0, 1.0],
        [0.0, 0.0, 1.0, 1.0],
        [0.0, 0.0, 1.0, 1.0]
    ], dtype=np.float32)

    # index arrays for above vertex Arrays
    # index = np.array((0,1,2), np.uint32) #simple triangle
    indexAxes = np.array((0, 1, 2, 3, 4, 5), np.uint32)  # 3 simple colored Axes as R,G,B lines

    # Systems
    transUpdate = scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
    camUpdate = scene.world.createSystem(CameraSystem("camUpdate", "CameraUpdate", "200"))
    renderUpdate = scene.world.createSystem(RenderGLShaderSystem())
    initUpdate = scene.world.createSystem(InitGLShaderSystem())



    ## ADD AXES ##

    axes = scene.world.createEntity(Entity(name="axes"))
    scene.world.addEntityChild(rootEntity, axes)
    axes_trans = scene.world.addComponent(axes, BasicTransform(name="axes_trans", trs=util.identity()))
    axes_mesh = scene.world.addComponent(axes, RenderMesh(name="axes_mesh"))
    axes_mesh.vertex_attributes.append(vertexAxes)
    axes_mesh.vertex_attributes.append(colorAxes)
    axes_mesh.vertex_index.append(indexAxes)
    axes_vArray = scene.world.addComponent(axes, VertexArray(primitive=GL_LINES))

    # OR
    axes_shader = scene.world.addComponent(axes, ShaderGLDecorator(
        Shader(vertex_source=Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))

    running = True
    # MAIN RENDERING LOOP
    scene.init(imgui=True, windowWidth=1024, windowHeight=768,
               windowTitle="pyglGA test_renderAxesTerrainEVENT")  # , customImGUIdecorator = ImGUIecssDecorator
    imGUIecss = scene.gContext

    # pre-pass scenegraph to initialise all GL context dependent geometry, shader classes
    # needs an active GL context

    #vArrayAxes.primitive = gl.GL_LINES
    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
    gl.glDisable(gl.GL_CULL_FACE)

    # gl.glDepthMask(gl.GL_FALSE)
    gl.glEnable(gl.GL_DEPTH_TEST)
    gl.glDepthFunc(gl.GL_LESS)
    ################### EVENT MANAGER ###################
    scene.world.traverse_visit(initUpdate, scene.world.root)

    eManager = scene.world.eventManager
    gWindow = scene.renderWindow
    gGUI = scene.gContext

    renderGLEventActuator = RenderGLStateSystem()

    eManager._subscribers['OnUpdateWireframe'] = gWindow
    eManager._actuators['OnUpdateWireframe'] = renderGLEventActuator
    eManager._subscribers['OnUpdateCamera'] = gWindow
    eManager._actuators['OnUpdateCamera'] = renderGLEventActuator

    eye = util.vec(1.2, 4.34, 6.1)
    target = util.vec(0.0, 0.0, 0.0)
    up = util.vec(0.0, 1.0, 0.0)
    view = util.lookat(eye, target, up)

    projMat = util.perspective(50.0, 1.0, 1.0, 20.0)  ## Setting the camera as perspective

    gWindow._myCamera = view  # otherwise, an imgui slider must be moved to properly update

    model_terrain_axes = util.translate(0.0, 0.0, 0.0)

    global superfuncchild2D

    global superfuncchild3D

    def function_plotting_display_nodes(function_entity, child_count, mvp_point):
        for i in range(1, child_count+1):
            curr_child = function_entity.getChild(i)
            curr_child.shaderDec.setUniformVariable(key='modelViewProj', value=mvp_point @ curr_child.trans.l2cam, mat4=True)
            shader_set_uniform_variable(curr_child.shaderDec, curr_child.trans.l2cam)

    def shader_set_uniform_variable(shader, projMatrix):
        Lambientcolor = util.vec(1.0, 1.0, 5.0)  # uniform ambient color
        Lambientstr = 0.1  # uniform ambientStr
        LviewPos = util.vec(2.5, 2.8, 5.0)  # uniform viewpos
        Lcolor = util.vec(1.0, 1.0, 1.0)
        Lintensity = 0.5
        # Material
        Mshininess = 0.0
        Mcolor = util.vec(0.7, 0.35, 0.0)
        
        shader.setUniformVariable(key='model', value=projMatrix, mat4=True)
        shader.setUniformVariable(key='ambientColor', value=Lambientcolor, float3=True)
        shader.setUniformVariable(key='ambientStr', value=Lambientstr, float1=True)
        shader.setUniformVariable(key='viewPos', value=LviewPos, float3=True)
        shader.setUniformVariable(key='lightPos', value=Lposition, float3=True)
        shader.setUniformVariable(key='lightColor', value=Lcolor, float3=True)
        shader.setUniformVariable(key='lightIntensity', value=Lintensity, float1=True)
        shader.setUniformVariable(key='shininess', value=Mshininess, float1=True)
        shader.setUniformVariable(key='matColor', value=Mcolor, float3=True)


    while running:
        Lposition = util.vec(LightPositionValues)  # uniform lightpos

        running = scene.render(running)
        scene.world.traverse_visit(renderUpdate, scene.world.root)
        view = gWindow._myCamera  # updates view via the imgui
        mvp_point = projMat @ view
        mvp_terrain_axes = projMat @ view @ model_terrain_axes
        Func_GUI()
        axes_shader.setUniformVariable(key='modelViewProj', value=mvp_terrain_axes, mat4=True)

        function_plotting_display_nodes(SuperFunction2D, superfuncchild2D, mvp_point)
        for shader in triangle_shader_wrapper:
            shader.setUniformVariable(key='modelViewProj', value=mvp_terrain_axes, mat4=True)
            shader_set_uniform_variable(shader, mvp_terrain_axes)

        scene.render_post()

    scene.shutdown()


if __name__ == "__main__":
    main(imguiFlag=True)