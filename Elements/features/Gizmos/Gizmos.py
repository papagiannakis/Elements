from Elements.pyGLV.GL.Scene import Scene
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform
import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Component import BasicTransform, RenderMesh
from Elements.pyGLV.GL.VertexArray import VertexArray
import sdl2 as sdl
from Elements.pyGLV.GL.Shader import Shader, ShaderGLDecorator
from ctypes import c_int, byref
from OpenGL.GL import GL_LINES
from math import sqrt, pow
import numpy as np
import imgui
import enum

class Mode(enum.Enum):
    TRANSLATE="Translate"
    ROTATE="Rotate"
    SCALE="Scale"

def generateCircle(axis='X',points=50,color=[1.0,0.0,0.0,1.0]):
    """
    Generates and returns data for a circle
    Arguments:
        axis: where the circle is on
        points: number of total points corresponding to the circle
        color: color of the circle
    Returns:
        The vertex, index and color arrays of a circle
    
    """
    _angle = 360.0/points

    ver = np.empty([points,4],dtype=np.float32)
    ind = np.empty(points,dtype=np.int32)
    col = np.full((points,4),color,dtype=np.float32)

    p = util.vec(1.0,0.0,0.0,1.0) # x-axis
    if axis=='Z':
        p = util.vec(0.0,0.0,1.0,1.0) # z-axis

    for i in range(points):
        p2 = p @ util.rotate(axis=(0.0,0.0,1.0),angle=i*_angle)
        if axis=='Y':
            p2 = p @ util.rotate(axis=(0.0,1.0,0.0),angle=i*_angle)
        if axis=='Z':
            p2 = p @ util.rotate(axis=(1.0,0.0,0.0),angle=i*_angle)

        ver[i] = p2
        ind = np.append(ind,i)
        if i==points-1:
            ind[i] = 0
        else:
            ind[i] = i+1
    return ver, ind, col

class Gizmos:

    VERTEX_GIZMOS_X = np.array([[0.1, 0.1, -0.1, 1.0],
                          [0.1, -0.1, -0.1, 1.0],
                          [0.1, 0.1, 0.1, 1.0],
                          [0.1, -0.1, 0.1, 1.0],
                          [1.4, -0.1, -0.1, 1.0],
                          [1.4, 0.1, -0.1, 1.0],
                          [1.4, -0.1, 0.1, 1.0],
                          [1.4, 0.1, 0.1, 1.0],],dtype=np.float32)
    
    VERTEX_GIZMOS_Y = np.array([[-0.1, 0.1, -0.1, 1.0],
                          [0.1, 0.1, -0.1, 1.0],
                          [-0.1, 0.1, 0.1, 1.0],
                          [0.1, 0.1, 0.1, 1.0],
                          [-0.1, 1.4, -0.1, 1.0],
                          [0.1, 1.4, -0.1, 1.0],
                          [-0.1, 1.4, 0.1, 1.0],
                          [0.1, 1.4, 0.1, 1.0],],dtype=np.float32)
    
    VERTEX_GIZMOS_Z = np.array([[0.1, 0.1, 0.1, 1.0],
                          [0.1, -0.1, 0.1, 1.0],
                          [-0.1, 0.1, 0.1, 1.0],
                          [-0.1, -0.1, 0.1, 1.0],
                          [0.1, 0.1, 1.4, 1.0],
                          [0.1, -0.1, 1.4, 1.0],
                          [-0.1, 0.1, 1.4, 1.0],
                          [-0.1, -0.1, 1.4, 1.0],],dtype=np.float32)
    
    VERTEX_GIZMOS_X = VERTEX_GIZMOS_X @ util.scale(0.7,0.7,0.7)
    VERTEX_GIZMOS_Y = VERTEX_GIZMOS_Y @ util.scale(0.7,0.7,0.7)
    VERTEX_GIZMOS_Z = VERTEX_GIZMOS_Z @ util.scale(0.7,0.7,0.7)

    COLOR_X = np.array([
    [1.0, 0.0, 0.0, 1.0],
    [1.0, 0.0, 0.0, 1.0],
    [1.0, 0.0, 0.0, 1.0],
    [1.0, 0.0, 0.0, 1.0],
    [1.0, 0.0, 0.0, 1.0],
    [1.0, 0.0, 0.0, 1.0],
    [1.0, 0.0, 0.0, 1.0],
    [1.0, 0.0, 0.0, 1.0]
    ], dtype=np.float32)

    COLOR_Y = np.array([
    [0.0, 1.0, 0.0, 1.0],
    [0.0, 1.0, 0.0, 1.0],
    [0.0, 1.0, 0.0, 1.0],
    [0.0, 1.0, 0.0, 1.0],
    [0.0, 1.0, 0.0, 1.0],
    [0.0, 1.0, 0.0, 1.0],
    [0.0, 1.0, 0.0, 1.0],
    [0.0, 1.0, 0.0, 1.0]
    ], dtype=np.float32)

    COLOR_Z = np.array([
    [0.0, 0.0, 1.0, 1.0],
    [0.0, 0.0, 1.0, 1.0],
    [0.0, 0.0, 1.0, 1.0],
    [0.0, 0.0, 1.0, 1.0],
    [0.0, 0.0, 1.0, 1.0],
    [0.0, 0.0, 1.0, 1.0],
    [0.0, 0.0, 1.0, 1.0],
    [0.0, 0.0, 1.0, 1.0]
    ], dtype=np.float32)

    ARROW_INDEX = np.array((0,1,3, 2,0,3, 
                            0,4,5, 0,5,1,
                            2,6,0, 6,4,0,
                            3,6,2, 3,7,6,
                            1,5,7, 1,7,3,
                            7,4,6, 7,5,4), np.int32)
    
    XS_LINE = np.array([[0.0,0.0,0.0,1.0],
                        [1.0,0.0,0.0,1.0]],dtype=np.float32)
    
    YS_LINE = np.array([[0.0,0.0,0.0,1.0],
                        [0.0,1.0,0.0,1.0]],dtype=np.float32)
    
    ZS_LINE = np.array([[0.0,0.0,0.0,1.0],
                        [0.0,0.0,1.0,1.0]],dtype=np.float32)
    
    XS_LINE_COLOR = np.array([
    [1.0, 0.0, 0.0, 1.0],
    [1.0, 0.0, 0.0, 1.0]
    ], dtype=np.float32)

    YS_LINE_COLOR = np.array([
    [0.0, 1.0, 0.0, 1.0],
    [0.0, 1.0, 0.0, 1.0]
    ], dtype=np.float32)

    ZS_LINE_COLOR = np.array([
    [0.0, 0.0, 1.0, 1.0],
    [0.0, 0.0, 1.0, 1.0]
    ], dtype=np.float32)

    LINE_INDEX = np.array((0,1),dtype=np.int32)

    XS_GIZMOS = np.array([[1.0, 0.1, -0.1, 1.0],
                          [1.0, -0.1, -0.1, 1.0],
                          [1.0, 0.1, 0.1, 1.0],
                          [1.0, -0.1, 0.1, 1.0],
                          [1.2, -0.1, -0.1, 1.0],
                          [1.2, 0.1, -0.1, 1.0],
                          [1.2, -0.1, 0.1, 1.0],
                          [1.2, 0.1, 0.1, 1.0]],dtype=np.float32)
    
    YS_GIZMOS = np.array([[0.1, 1.0, -0.1, 1.0],
                          [-0.1, 1.0, -0.1, 1.0],
                          [0.1, 1.0, 0.1, 1.0],
                          [-0.1, 1.0, 0.1, 1.0],
                          [-0.1, 1.2, -0.1, 1.0],
                          [0.1, 1.2, -0.1, 1.0],
                          [-0.1, 1.2, 0.1, 1.0],
                          [0.1, 1.2, 0.1, 1.0]],dtype=np.float32)
    
    ZS_GIZMOS = np.array([[-0.1, 0.1, 1.0, 1.0],
                          [-0.1, -0.1, 1.0, 1.0],
                          [0.1, 0.1, 1.0, 1.0],
                          [0.1, -0.1, 1.0, 1.0],
                          [-0.1, -0.1, 1.2, 1.0],
                          [-0.1, 0.1, 1.2, 1.0],
                          [0.1, -0.1, 1.2, 1.0],
                          [0.1, 0.1, 1.2, 1.0]],dtype=np.float32)
    
    RX_GIZMOS, rindex_x, rcolor_x = generateCircle(axis='X',points=50,color=[1.0,0.0,0.0,1.0])
    RY_GIZMOS, rindex_y, rcolor_y = generateCircle(axis='Y',points=50,color=[0.0,1.0,0.0,1.0])
    RZ_GIZMOS, rindex_z, rcolor_z = generateCircle(axis='Z',points=50,color=[0.0,0.0,1.0,1.0])


    def __init__(self,rootEntity: Entity,Projection=None, View=None):
        sdl.ext.init()
        self.scene = Scene()
        self.selected = 0
        self.total = 0
        self.mouse_x, self.mouse_y = c_int(0), c_int(0)
        self.mouse_state = 0 #LMB not clicked
        self.key_states = sdl.SDL_GetKeyboardState(None)
        self.key_down = False
        self.projection = Projection
        self.view = View
        if Projection is not None:
            self.inv_projection = util.inverse(Projection)
        if View is not None:
            self.inv_view = util.inverse(View)
        self.is_selected = False
        self.selected_trans = None
        self.selected_mesh = None
        self.selected_comp = "None"
        self.mode = Mode.TRANSLATE
        #a set of node names that are ignored in change_target
        self.gizmos_comps = set(["Gizmos_X","Gizmos_X_trans","Gizmos_X_mesh",
                                "Gizmos_Y","Gizmos_Y_trans","Gizmos_Y_mesh",
                                "Gizmos_Z","Gizmos_Z_trans","Gizmos_Z_mesh",
                                "Gizmos_x_S_line","Gizmos_x_S_line_trans","Gizmos_x_S_line_mesh",
                                "Gizmos_y_S_line","Gizmos_y_S_line_trans","Gizmos_y_S_line_mesh",
                                "Gizmos_z_S_line","Gizmos_z_S_line_trans","Gizmos_z_S_line_mesh",
                                "Gizmos_x_S_cube","Gizmos_x_S_cube_trans","Gizmos_x_S_cube_mesh",
                                "Gizmos_y_S_cube","Gizmos_y_S_cube_trans","Gizmos_y_S_cube_mesh",
                                "Gizmos_z_S_cube","Gizmos_z_S_cube_trans","Gizmos_z_S_cube_mesh",
                                "Gizmos_x_R","Gizmos_x_R_trans","Gizmos_x_R_mesh",
                                "Gizmos_y_R","Gizmos_y_R_trans","Gizmos_y_R_mesh",
                                "Gizmos_z_R","Gizmos_z_R_trans","Gizmos_z_R_mesh"])

        self.cameraInUse = ""
        self.screen_width = 1024.0
        self.screen_height = 768.0
        self.picked = False
        self.selected_gizmo = ''
        self.previous_distance = 0.0
        self.previous_x = 0.0
        self.previous_y = 0.0
        self.previous_z = 0.0

        ########## Translate components
        self.gizmos_x = self.scene.world.createEntity(Entity(name="Gizmos_X"))
        self.scene.world.addEntityChild(rootEntity, self.gizmos_x)
        self.gizmos_x_trans = self.scene.world.addComponent(self.gizmos_x, BasicTransform(name="Gizmos_X_trans", trs=util.identity()))
        self.gizmos_x_mesh = self.scene.world.addComponent(self.gizmos_x, RenderMesh(name="Gizmos_X_mesh"))
        self.gizmos_x_mesh.vertex_attributes.append(Gizmos.VERTEX_GIZMOS_X)
        self.gizmos_x_mesh.vertex_attributes.append(Gizmos.COLOR_X)
        self.gizmos_x_mesh.vertex_index.append(Gizmos.ARROW_INDEX)
        self.gizmos_x_vArray = self.scene.world.addComponent(self.gizmos_x, VertexArray())
        self.gizmos_x_shader = self.scene.world.addComponent(self.gizmos_x, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))

        self.gizmos_y = self.scene.world.createEntity(Entity(name="Gizmos_Y"))
        self.scene.world.addEntityChild(rootEntity, self.gizmos_y)
        self.gizmos_y_trans = self.scene.world.addComponent(self.gizmos_y, BasicTransform(name="Gizmos_Y_trans", trs=util.identity()))
        self.gizmos_y_mesh = self.scene.world.addComponent(self.gizmos_y, RenderMesh(name="Gizmos_Y_mesh"))
        self.gizmos_y_mesh.vertex_attributes.append(Gizmos.VERTEX_GIZMOS_Y) 
        self.gizmos_y_mesh.vertex_attributes.append(Gizmos.COLOR_Y)
        self.gizmos_y_mesh.vertex_index.append(Gizmos.ARROW_INDEX)
        self.gizmos_y_vArray = self.scene.world.addComponent(self.gizmos_y, VertexArray())
        self.gizmos_y_shader = self.scene.world.addComponent(self.gizmos_y, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))

        self.gizmos_z = self.scene.world.createEntity(Entity(name="Gizmos_Z"))
        self.scene.world.addEntityChild(rootEntity, self.gizmos_z)
        self.gizmos_z_trans = self.scene.world.addComponent(self.gizmos_z, BasicTransform(name="Gizmos_Z_trans", trs=util.identity()))
        self.gizmos_z_mesh = self.scene.world.addComponent(self.gizmos_z, RenderMesh(name="Gizmos_Z_mesh"))
        self.gizmos_z_mesh.vertex_attributes.append(Gizmos.VERTEX_GIZMOS_Z)
        self.gizmos_z_mesh.vertex_attributes.append(Gizmos.COLOR_Z)
        self.gizmos_z_mesh.vertex_index.append(Gizmos.ARROW_INDEX)
        self.gizmos_z_vArray = self.scene.world.addComponent(self.gizmos_z, VertexArray())
        self.gizmos_z_shader = self.scene.world.addComponent(self.gizmos_z, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))
        ##############

        ############## Scale components
        self.gizmos_x_S_line = self.scene.world.createEntity(Entity(name="Gizmos_x_S_line"))
        self.scene.world.addEntityChild(rootEntity, self.gizmos_x_S_line)
        self.gizmos_x_S_line_trans = self.scene.world.addComponent(self.gizmos_x_S_line, BasicTransform(name="Gizmos_x_S_line_trans", trs=util.identity()))
        self.gizmos_x_S_line_mesh = self.scene.world.addComponent(self.gizmos_x_S_line, RenderMesh(name="Gizmos_x_S_line_mesh"))
        self.gizmos_x_S_line_mesh.vertex_attributes.append(Gizmos.XS_LINE)
        self.gizmos_x_S_line_mesh.vertex_attributes.append(Gizmos.XS_LINE_COLOR)
        self.gizmos_x_S_line_mesh.vertex_index.append(Gizmos.LINE_INDEX)
        self.gizmos_x_S_line_vArray = self.scene.world.addComponent(self.gizmos_x_S_line, VertexArray(primitive=GL_LINES))
        self.gizmos_x_S_line_shader = self.scene.world.addComponent(self.gizmos_x_S_line, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))

        self.gizmos_y_S_line = self.scene.world.createEntity(Entity(name="Gizmos_y_S_line"))
        self.scene.world.addEntityChild(rootEntity, self.gizmos_y_S_line)
        self.gizmos_y_S_line_trans = self.scene.world.addComponent(self.gizmos_y_S_line, BasicTransform(name="Gizmos_y_S_line_trans", trs=util.identity()))
        self.gizmos_y_S_line_mesh = self.scene.world.addComponent(self.gizmos_y_S_line, RenderMesh(name="Gizmos_y_S_line_mesh"))
        self.gizmos_y_S_line_mesh.vertex_attributes.append(Gizmos.YS_LINE)
        self.gizmos_y_S_line_mesh.vertex_attributes.append(Gizmos.YS_LINE_COLOR)
        self.gizmos_y_S_line_mesh.vertex_index.append(Gizmos.LINE_INDEX)
        self.gizmos_y_S_line_vArray = self.scene.world.addComponent(self.gizmos_y_S_line, VertexArray(primitive=GL_LINES))
        self.gizmos_y_S_line_shader = self.scene.world.addComponent(self.gizmos_y_S_line, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))
        
        self.gizmos_z_S_line = self.scene.world.createEntity(Entity(name="Gizmos_z_S_line"))
        self.scene.world.addEntityChild(rootEntity, self.gizmos_z_S_line)
        self.gizmos_z_S_line_trans = self.scene.world.addComponent(self.gizmos_z_S_line, BasicTransform(name="Gizmos_z_S_line_trans", trs=util.identity()))
        self.gizmos_z_S_line_mesh = self.scene.world.addComponent(self.gizmos_z_S_line, RenderMesh(name="Gizmos_z_S_line_mesh"))
        self.gizmos_z_S_line_mesh.vertex_attributes.append(Gizmos.ZS_LINE)
        self.gizmos_z_S_line_mesh.vertex_attributes.append(Gizmos.ZS_LINE_COLOR)
        self.gizmos_z_S_line_mesh.vertex_index.append(Gizmos.LINE_INDEX)
        self.gizmos_z_S_line_vArray = self.scene.world.addComponent(self.gizmos_z_S_line, VertexArray(primitive=GL_LINES))
        self.gizmos_z_S_line_shader = self.scene.world.addComponent(self.gizmos_z_S_line, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))
        
        self.gizmos_x_S_cube = self.scene.world.createEntity(Entity(name="Gizmos_x_S_cube"))
        self.scene.world.addEntityChild(rootEntity, self.gizmos_x_S_cube)
        self.gizmos_x_S_cube_trans = self.scene.world.addComponent(self.gizmos_x_S_cube, BasicTransform(name="Gizmos_x_S_cube_trans", trs=util.identity()))
        self.gizmos_x_S_cube_mesh = self.scene.world.addComponent(self.gizmos_x_S_cube, RenderMesh(name="Gizmos_x_S_cube_mesh"))
        self.gizmos_x_S_cube_mesh.vertex_attributes.append(Gizmos.XS_GIZMOS)
        self.gizmos_x_S_cube_mesh.vertex_attributes.append(Gizmos.COLOR_X)
        self.gizmos_x_S_cube_mesh.vertex_index.append(Gizmos.ARROW_INDEX)
        self.gizmos_x_S_cube_vArray = self.scene.world.addComponent(self.gizmos_x_S_cube, VertexArray())
        self.gizmos_x_S_cube_shader = self.scene.world.addComponent(self.gizmos_x_S_cube, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))

        self.gizmos_y_S_cube = self.scene.world.createEntity(Entity(name="Gizmos_y_S_cube"))
        self.scene.world.addEntityChild(rootEntity, self.gizmos_y_S_cube)
        self.gizmos_y_S_cube_trans = self.scene.world.addComponent(self.gizmos_y_S_cube, BasicTransform(name="Gizmos_y_S_cube_trans", trs=util.identity()))
        self.gizmos_y_S_cube_mesh = self.scene.world.addComponent(self.gizmos_y_S_cube, RenderMesh(name="Gizmos_y_S_cube_mesh"))
        self.gizmos_y_S_cube_mesh.vertex_attributes.append(Gizmos.YS_GIZMOS)
        self.gizmos_y_S_cube_mesh.vertex_attributes.append(Gizmos.COLOR_Y)
        self.gizmos_y_S_cube_mesh.vertex_index.append(Gizmos.ARROW_INDEX)
        self.gizmos_y_S_cube_vArray = self.scene.world.addComponent(self.gizmos_y_S_cube, VertexArray())
        self.gizmos_y_S_cube_shader = self.scene.world.addComponent(self.gizmos_y_S_cube, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))

        self.gizmos_z_S_cube = self.scene.world.createEntity(Entity(name="Gizmos_z_S_cube"))
        self.scene.world.addEntityChild(rootEntity, self.gizmos_z_S_cube)
        self.gizmos_z_S_cube_trans = self.scene.world.addComponent(self.gizmos_z_S_cube, BasicTransform(name="Gizmos_z_S_cube_trans", trs=util.identity()))
        self.gizmos_z_S_cube_mesh = self.scene.world.addComponent(self.gizmos_z_S_cube, RenderMesh(name="Gizmos_z_S_cube_mesh"))
        self.gizmos_z_S_cube_mesh.vertex_attributes.append(Gizmos.ZS_GIZMOS)
        self.gizmos_z_S_cube_mesh.vertex_attributes.append(Gizmos.COLOR_Z)
        self.gizmos_z_S_cube_mesh.vertex_index.append(Gizmos.ARROW_INDEX)
        self.gizmos_z_S_cube_vArray = self.scene.world.addComponent(self.gizmos_z_S_cube, VertexArray())
        self.gizmos_z_S_cube_shader = self.scene.world.addComponent(self.gizmos_z_S_cube, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))
        ##############

        ############## Rotation Gizmos components
        self.gizmos_x_R = self.scene.world.createEntity(Entity(name="Gizmos_x_R"))
        self.scene.world.addEntityChild(rootEntity, self.gizmos_x_R)
        self.gizmos_x_R_trans = self.scene.world.addComponent(self.gizmos_x_R, BasicTransform(name="Gizmos_x_R_trans", trs=util.identity()))
        self.gizmos_x_R_mesh = self.scene.world.addComponent(self.gizmos_x_R, RenderMesh(name="Gizmos_x_R_mesh"))
        self.gizmos_x_R_mesh.vertex_attributes.append(Gizmos.RX_GIZMOS)
        self.gizmos_x_R_mesh.vertex_attributes.append(Gizmos.rcolor_x)
        self.gizmos_x_R_mesh.vertex_index.append(Gizmos.rindex_x)
        self.gizmos_x_R_vArray = self.scene.world.addComponent(self.gizmos_x_R, VertexArray(primitive=GL_LINES))
        self.gizmos_x_R_shader = self.scene.world.addComponent(self.gizmos_x_R, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))

        self.gizmos_y_R = self.scene.world.createEntity(Entity(name="Gizmos_y_R"))
        self.scene.world.addEntityChild(rootEntity, self.gizmos_y_R)
        self.gizmos_y_R_trans = self.scene.world.addComponent(self.gizmos_y_R, BasicTransform(name="Gizmos_y_R_trans", trs=util.identity()))
        self.gizmos_y_R_mesh = self.scene.world.addComponent(self.gizmos_y_R, RenderMesh(name="Gizmos_y_R_mesh"))
        self.gizmos_y_R_mesh.vertex_attributes.append(Gizmos.RY_GIZMOS)
        self.gizmos_y_R_mesh.vertex_attributes.append(Gizmos.rcolor_y)
        self.gizmos_y_R_mesh.vertex_index.append(Gizmos.rindex_y)
        self.gizmos_y_R_vArray = self.scene.world.addComponent(self.gizmos_y_R, VertexArray(primitive=GL_LINES))
        self.gizmos_y_R_shader = self.scene.world.addComponent(self.gizmos_y_R, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))

        self.gizmos_z_R = self.scene.world.createEntity(Entity(name="Gizmos_z_R"))
        self.scene.world.addEntityChild(rootEntity, self.gizmos_z_R)
        self.gizmos_z_R_trans = self.scene.world.addComponent(self.gizmos_z_R, BasicTransform(name="Gizmos_z_R_trans", trs=util.identity()))
        self.gizmos_z_R_mesh = self.scene.world.addComponent(self.gizmos_z_R, RenderMesh(name="Gizmos_z_R_mesh"))
        self.gizmos_z_R_mesh.vertex_attributes.append(Gizmos.RZ_GIZMOS)
        self.gizmos_z_R_mesh.vertex_attributes.append(Gizmos.rcolor_z)
        self.gizmos_z_R_mesh.vertex_index.append(Gizmos.rindex_z)
        self.gizmos_z_R_vArray = self.scene.world.addComponent(self.gizmos_z_R, VertexArray(primitive=GL_LINES))
        self.gizmos_z_R_shader = self.scene.world.addComponent(self.gizmos_z_R, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))

        #Translation gizmos bounding boxes
        self.x_min_bb, self.x_max_bb = self.calculate_bounding_box(self.gizmos_x_mesh.vertex_attributes[0])
        self.y_min_bb, self.y_max_bb = self.calculate_bounding_box(self.gizmos_y_mesh.vertex_attributes[0])
        self.z_min_bb, self.z_max_bb = self.calculate_bounding_box(self.gizmos_z_mesh.vertex_attributes[0])

        #scaling gizmos bounding boxes
        self.xs_min_bb, self.xs_max_bb = self.calculate_bounding_box(self.gizmos_x_S_cube_mesh.vertex_attributes[0])
        self.ys_min_bb, self.ys_max_bb = self.calculate_bounding_box(self.gizmos_y_S_cube_mesh.vertex_attributes[0])
        self.zs_min_bb, self.zs_max_bb = self.calculate_bounding_box(self.gizmos_z_S_cube_mesh.vertex_attributes[0])

        self.count_components()

    def __remove_scaling(self,model):
        """
        Creates and returns a copy of a given model matrix with (1.0,1.0,1.0) scaling
        Arguments:
            self: self
            model: a matrix
        Returns:
            The model matrix with (1.0,1.0,1.0) scaling
        """
        M = np.array(model,copy=True)
        for i in range(len(M)-1):
            M[i][i] = 1
        return M

    def reset_to_None(self):
        """
        Resets to initial state
        Arguments:
            self: self
        Returns:
            None
        """
        self.is_selected = False
        self.selected_trans = None
        self.selected_mesh = None
        self.selected_comp = "None"
        #TODO: reset uniform variables too

    def change_target(self):
        """
        Change selected entity
        Arguments:
            self: self
        Returns:
            None
        """
        self.selected = self.selected+1
        count = self.selected
        if(count>self.total):
            count = 1
            self.selected = 1

        for component in self.scene.world.root:

            #Have to check because there is always some component that has Nonetype
            if component is not None:
                parentname = component.parent.name
                #next BasicTransform component that is not one of the gizmos components and is now the camera's in use component
                if component.getClassName()=="BasicTransform" and component.name not in self.gizmos_comps and parentname!=self.cameraInUse:
                    count = count-1
                    if(count==0):
                        self.selected_trans = component
                        self.selected_comp = self.selected_trans.parent.name
                        children = component.parent.getNumberOfChildren()
                        self.selected_mesh = None
                        for i in range(children):
                            child = component.parent.getChild(i)
                            if child is not None and child.getClassName()=="RenderMesh":
                                self.selected_mesh = child
                                break
                        break

    def update_ray_init_position(self):
        """
        Update mouse position, mouse state and Raycast
        Arguments:
            self: self
        Returns:
            None
        """
        self.mouse_state = sdl.mouse.SDL_GetMouseState(byref(self.mouse_x), byref(self.mouse_y))
        #Raycast only when LMB is pressed
        if self.mouse_state==1 and self.key_states[sdl.SDL_SCANCODE_LALT] and self.selected_trans is not None:
            self.raycast()
        else:
            self.picked = False
            self.selected_gizmo=''
        
    def count_components(self):
        """
        Count transform components in the scene
        Arguments:
            self: self
        Returns:
            None
        """
        for component in self.scene.world.root:
            if component is not None and component.getClassName()=="BasicTransform" and component.name not in self.gizmos_comps:
                self.total = self.total + 1

    def get_Event(self):
        """
        When TAB is pressed change selected entity
        Additionally:
            T: change to translate mode
            R: change to rotate mode
            S: change to scale mode
        Arguments:
            self: self
        Returns:
            None
        """
        if self.key_states[sdl.SDL_SCANCODE_TAB] and not self.key_down:
            self.key_down = True
            self.change_target()
            if self.total>0:
                self.is_selected = True
                
                self.gizmos_x_trans.trs = self.__remove_scaling(self.selected_trans.trs)
                self.gizmos_y_trans.trs = self.__remove_scaling(self.selected_trans.trs)
                self.gizmos_z_trans.trs = self.__remove_scaling(self.selected_trans.trs)

                self.gizmos_x_S_line_trans.trs = self.selected_trans.trs
                self.gizmos_y_S_line_trans.trs = self.selected_trans.trs
                self.gizmos_z_S_line_trans.trs = self.selected_trans.trs

                x_t = util.translate(x=self.selected_trans.trs[0][0]-1.0)
                y_t = util.translate(y=self.selected_trans.trs[1][1]-1.0)
                z_t = util.translate(z=self.selected_trans.trs[2][2]-1.0)

                self.gizmos_x_S_cube_trans.trs = self.__remove_scaling(self.selected_trans.trs) @ x_t
                self.gizmos_y_S_cube_trans.trs = self.__remove_scaling(self.selected_trans.trs) @ y_t
                self.gizmos_z_S_cube_trans.trs = self.__remove_scaling(self.selected_trans.trs) @ z_t

                self.gizmos_x_R_trans.trs = self.__remove_scaling(self.selected_trans.trs)
                self.gizmos_y_R_trans.trs = self.__remove_scaling(self.selected_trans.trs)
                self.gizmos_z_R_trans.trs = self.__remove_scaling(self.selected_trans.trs)

                self.__update_gizmos()

        elif not self.key_states[sdl.SDL_SCANCODE_TAB] and self.key_down:
            self.key_down = False

        if self.key_states[sdl.SDL_SCANCODE_T]:
            self.mode = Mode.TRANSLATE
            self.__update_gizmos()
        if self.key_states[sdl.SDL_SCANCODE_R]:
            self.mode = Mode.ROTATE
            self.__update_gizmos()
        if self.key_states[sdl.SDL_SCANCODE_S]:
            self.mode = Mode.SCALE
            self.__update_gizmos()
    
    def __update_gizmos(self):
        """
        Update Gizmos uniform variables
        Arguments:
            self: self
        Returns:
            None
        """
        if self.is_selected:
            vp = self.projection @ self.view

            #### Translate components
            model_x = self.gizmos_x_trans.trs
            model_y = self.gizmos_y_trans.trs
            model_z = self.gizmos_z_trans.trs
            mvp_x = 0.0
            mvp_y = 0.0
            mvp_z = 0.0
            if self.mode==Mode.TRANSLATE:
                mvp_x = vp @ model_x
                mvp_y = vp @ model_y
                mvp_z = vp @ model_z

            self.gizmos_x_shader.setUniformVariable(key='modelViewProj', value=mvp_x, mat4=True)
            self.gizmos_y_shader.setUniformVariable(key='modelViewProj', value=mvp_y, mat4=True)
            self.gizmos_z_shader.setUniformVariable(key='modelViewProj', value=mvp_z, mat4=True)

            #### Scale components
            model_XS_line = self.gizmos_x_S_line_trans.trs
            model_YS_line = self.gizmos_y_S_line_trans.trs
            model_ZS_line = self.gizmos_z_S_line_trans.trs

            model_XS_cube = self.gizmos_x_S_cube_trans.trs
            model_YS_cube = self.gizmos_y_S_cube_trans.trs
            model_ZS_cube = self.gizmos_z_S_cube_trans.trs

            mvp_xs_line = 0.0
            mvp_ys_line = 0.0
            mvp_zs_line = 0.0
            mvp_xs_cube = 0.0
            mvp_ys_cube = 0.0
            mvp_zs_cube = 0.0
            if self.mode==Mode.SCALE:
                mvp_xs_line = vp @ model_XS_line
                mvp_ys_line = vp @ model_YS_line
                mvp_zs_line = vp @ model_ZS_line

                mvp_xs_cube = vp @ model_XS_cube
                mvp_ys_cube = vp @ model_YS_cube
                mvp_zs_cube = vp @ model_ZS_cube

            #Scale lines
            self.gizmos_x_S_line_shader.setUniformVariable(key='modelViewProj', value=mvp_xs_line, mat4=True)
            self.gizmos_y_S_line_shader.setUniformVariable(key='modelViewProj', value=mvp_ys_line, mat4=True)
            self.gizmos_z_S_line_shader.setUniformVariable(key='modelViewProj', value=mvp_zs_line, mat4=True)

            #Scale cubes
            self.gizmos_x_S_cube_shader.setUniformVariable(key='modelViewProj', value=mvp_xs_cube, mat4=True)
            self.gizmos_y_S_cube_shader.setUniformVariable(key='modelViewProj', value=mvp_ys_cube, mat4=True)
            self.gizmos_z_S_cube_shader.setUniformVariable(key='modelViewProj', value=mvp_zs_cube, mat4=True)

            model_rx = self.gizmos_x_R_trans.trs
            model_ry = self.gizmos_y_R_trans.trs
            model_rz = self.gizmos_z_R_trans.trs

            mvp_rx = 0.0
            mvp_ry = 0.0
            mvp_rz = 0.0
            if self.mode==Mode.ROTATE:
                mvp_rx = vp @ model_rx
                mvp_ry = vp @ model_ry
                mvp_rz = vp @ model_rz

            self.gizmos_x_R_shader.setUniformVariable(key='modelViewProj', value=mvp_rx, mat4=True)
            self.gizmos_y_R_shader.setUniformVariable(key='modelViewProj', value=mvp_ry, mat4=True)
            self.gizmos_z_R_shader.setUniformVariable(key='modelViewProj', value=mvp_rz, mat4=True)

    def update_imgui(self):
        """
        Update selected Entity and Transformation information on the imgui
        Arguments:
            self: self
        Returns
            None
        """
        imgui.set_next_window_size(200.0,100.0)
        imgui.begin("Selected Entity")
        imgui.text_ansi(self.selected_comp)
        imgui.text_ansi("Mode: "+self.mode.value)
        imgui.end()

    def update_projection(self, Proj):
        """
        Update window's projection and calculate its inverse if needed
        Arguments:
            self: self
            Proj: Projection matrix
        Returns:
            None
        """
        if self.selected is not None and not np.array_equiv(self.projection,Proj):
            self.projection = Proj
            self.inv_projection = util.inverse(self.projection)
            self.__update_gizmos()

    def update_view(self, View):
        """
        Update window's View and calculate its inverse if needed
        Arguments:
            self: self
            View: View matrix
            Returns:
                None
        """
        if self.selected is not None and not np.array_equiv(self.view,View):
            self.view = View
            self.inv_view = util.inverse(self.view)
            self.__update_gizmos()

    def set_camera_in_use(self,camera: str):
        """
        Set the name of the camera that is currently used
        Arguments:
            self: self
            camera: name of the camera Entity
        Returns:
            None
        """
        if self.cameraInUse=="":
            self.total = self.total - 1
        self.cameraInUse = camera
    
    def update_screen_dimensions(self,window_width,window_height):
        """
        update saved window width  height and field of view
        Arguments:
            self: self
            window_width: window's current width
            window_height: window's current height
            fov: field of view
        Returns:
            None
        """
        self.screen_width = window_width
        self.screen_height = window_height

    def calculate_bounding_box(self,mesh_vertices):
        """
        A simple method that calculates an axis aligned bounding box using a given mesh's vertices
        Arguments:
            self: self
            mesh: A RenderMesh component
        Returns
            minbb: minimum bounding box coordinates
            maxbb: maximum bounding box coordinates
        """
        vertices = mesh_vertices

        #hmm, is this needed?
        for i in  range(len(vertices)):
            vertices[i] = vertices[i]/vertices[i][3]

        minbb = util.vec(vertices[0][0],vertices[0][0],vertices[0][2],1.0)
        maxbb = util.vec(vertices[0][0],vertices[0][0],vertices[0][2],1.0)
        for i in range(1,len(vertices)):
            #min coordinates
            if vertices[i][0]<minbb[0]:
                minbb[0] = vertices[i][0]
            if vertices[i][1]<minbb[1]:
                minbb[1] = vertices[i][1]
            if vertices[i][2]<minbb[2]:
                minbb[2] = vertices[i][2]
                
            #max coordinates
            if vertices[i][0] > maxbb[0]:
                maxbb[0] = vertices[i][0]
            if vertices[i][1] > maxbb[1]:
                maxbb[1] = vertices[i][1]
            if vertices[i][2] > maxbb[2]:
                maxbb[2] = vertices[i][2]
        return minbb, maxbb

    def calculate_ray(self):
        """
        Calculate and Return a Ray that starts from mouse position
        Arguments:
            self: self
        Returns:
            a ray's starting position and direction

        Source: http://www.opengl-tutorial.org/miscellaneous/clicking-on-objects/picking-with-custom-ray-obb-function/
        """

        #mouse position in normalized device coordinates
        x = 2.0 * (self.mouse_x.value/self.screen_width - 0.5)
        y = -2.0 * (self.mouse_y.value/self.screen_height - 0.5)
        
        #ray start and ray end in normalized devive coordinates
        ray_start = util.vec(x,y,-1.0,1.0)
        ray_end = util.vec(x,y,0.0,1.0)

        # normalized device to Camera space
        ray_start_Camera = self.inv_projection @ ray_start
        ray_start_Camera = ray_start_Camera/ray_start_Camera[3]
        # Camera space to world space
        ray_start_World = self.inv_view @ ray_start_Camera
        ray_start_World = ray_start_World/ray_start_World[3]

        #normalized device to Camera space
        ray_end_Camera = self.inv_projection @ ray_end
        ray_end_Camera = ray_end_Camera/ray_end_Camera[3]

        # Camera space to World space
        ray_end_world = self.inv_view @ ray_end_Camera
        ray_end_world = ray_end_world/ray_end_world[3]

        #calculate and normalize the ray's direction
        ray_dir_world = util.vec(ray_end_world[0] - ray_start_World[0],
                                 ray_end_world[1] - ray_start_World[1],
                                 ray_end_world[2] - ray_start_World[2])
        ray_dir_world = util.normalise(ray_dir_world)
        
        ray_origin = util.vec(ray_start_World[0],ray_start_World[1],ray_start_World[2],0.0)
        ray_direction = util.vec(ray_dir_world[0],ray_dir_world[1],ray_dir_world[2],0.0)

        return ray_origin, ray_direction

    def raycast(self):
        """
        Raycast from mouse position
        Arguments:
            self: self
        Returns:
            None

        Source: http://www.opengl-tutorial.org/miscellaneous/clicking-on-objects/picking-with-custom-ray-obb-function/
        """

        ray_origin, ray_direction = self.calculate_ray()

        x_intersects, x_in_point = False, util.vec(0.0)
        y_intersects, y_in_point = False, util.vec(0.0)
        z_intersects, z_in_point = False, util.vec(0.0)

        if self.mode==Mode.TRANSLATE:
            model_x = self.__remove_scaling(self.gizmos_x_trans.trs)
            model_y = self.__remove_scaling(self.gizmos_y_trans.trs)
            model_z = self.__remove_scaling(self.gizmos_z_trans.trs)

            x_intersects, x_in_point = self.testRayBoundingBoxIntesection(ray_origin,
                                                ray_direction,
                                                self.x_min_bb,
                                                self.x_max_bb,
                                                model_x)
        
            y_intersects, y_in_point = self.testRayBoundingBoxIntesection(ray_origin,
                                                ray_direction,
                                                self.y_min_bb,
                                                self.y_max_bb,
                                                model_y)
        
            z_intersects, z_in_point = self.testRayBoundingBoxIntesection(ray_origin,
                                                ray_direction,
                                                self.z_min_bb,
                                                self.z_max_bb,
                                                model_z)
        elif self.mode==Mode.SCALE:
            model_x = self.gizmos_x_S_cube_trans.trs
            model_y = self.gizmos_y_S_cube_trans.trs
            model_z = self.gizmos_z_S_cube_trans.trs

            x_intersects, x_in_point = self.testRayBoundingBoxIntesection(ray_origin,
                                                ray_direction,
                                                self.xs_min_bb,
                                                self.xs_max_bb,
                                                model_x)
        
            y_intersects, y_in_point = self.testRayBoundingBoxIntesection(ray_origin,
                                                ray_direction,
                                                self.ys_min_bb,
                                                self.ys_max_bb,
                                                model_y)
        
            z_intersects, z_in_point = self.testRayBoundingBoxIntesection(ray_origin,
                                                ray_direction,
                                                self.zs_min_bb,
                                                self.zs_max_bb,
                                                model_z)

        if self.selected_gizmo=='X' or (self.selected_gizmo=='' and x_intersects):
            self.selected_gizmo = 'X'
            self.__transform_selected_entity(x_in_point)
        elif self.selected_gizmo=='Y' or (self.selected_gizmo==''  and y_intersects):
            self.selected_gizmo = 'Y'
            self.__transform_selected_entity(y_in_point)
        elif self.selected_gizmo=='Z' or (self.selected_gizmo==''and z_intersects):
            self.selected_gizmo = 'Z'
            self.__transform_selected_entity(z_in_point)

    def __transform_selected_entity(self,inter_point):
        """
        When a gizmo is selected Transform selected Entity based on the selected mode and selected axis
        Arguments:
            self: self
            inter_point: Intersection point on bounding box
        Returns:
            None
        """
        if self.mode==Mode.TRANSLATE:
            if self.selected_gizmo=='X':
                if self.picked==False:
                    self.picked = True
                    self.previous_x = inter_point[0]
                else:
                    diff = inter_point[0] - self.previous_x
                    self.previous_x = inter_point[0]
                    self.__translate_selected(x=diff)
            elif self.selected_gizmo=='Y':
                if self.picked==False:
                    self.picked = True
                    self.previous_y = inter_point[1]
                else:
                    diff = inter_point[1] - self.previous_y
                    self.previous_y = inter_point[1]
                    self.__translate_selected(y=diff)
            if self.selected_gizmo=='Z':
                if self.picked==False:
                    self.picked = True
                    self.previous_z = inter_point[2]
                else:
                    diff = inter_point[2] - self.previous_z
                    self.previous_z = inter_point[2]
                    self.__translate_selected(z=diff)
        elif self.mode==Mode.SCALE:
            diffX = 1.0
            diffY = 1.0
            diffZ = 1.0
            if self.selected_gizmo=='X':
                if self.picked==False:
                    self.picked = True
                    self.previous_x = inter_point[0]
                else:
                    diffX = np.abs(inter_point[0]/self.previous_x) # 10*sigmoid (0, +inf)
                    if(diffX==0.0):
                        diffX = 0.01
                    self.previous_x = inter_point[0]
            elif self.selected_gizmo=='Y':
                if self.picked==False:
                    self.picked = True
                    self.previous_y = inter_point[1]
                else:
                    diffY = np.abs(inter_point[1]/self.previous_y)
                    if(diffY==0.0):
                        diffY = 0.01
                    self.previous_y = inter_point[1]
            elif self.selected_gizmo=='Z':
                if self.picked==False:
                    self.picked = True
                    self.previous_z = inter_point[2]
                else:
                    diffZ = np.abs(inter_point[2]/self.previous_z)
                    if(diffZ==0.0):
                        diffZ = 0.01
                    self.previous_z = inter_point[2]
            self.__scale_selected(x=diffX,y=diffY,z=diffZ)
        self.__update_gizmos()

    def testRayBoundingBoxIntesection(self,ray_origin,ray_direction,minbb,maxbb,model):
        """
        A method that tests if a ray starting from the mouse position is intersecting with a given bounding box
        Arguments:
            self: self
            ray_origin: the location the ray starts from in world space
            ray_direction: the direction of the ray
            minbb: minimum coordinates of an element's bounding box
            maxbb: maximum coordinates of an element's bounding box
            model: the element's model matrix
        Returns:
            True if there is an intersection, False otherwise. Additionally it returns the intersection point on the bounding box
            
        Source: http://www.opengl-tutorial.org/miscellaneous/clicking-on-objects/picking-with-custom-ray-obb-function/
        """
        tmin = 0.0
        tmax = 100000.0

        bb_pos_world = util.vec(model[3][0],model[3][1],model[3][2],model[3][3])
        delta = bb_pos_world - ray_origin

        x_axis = util.vec(model[0][0],model[0][1],model[0][2],model[0][3])
        y_axis = util.vec(model[1][0],model[1][1],model[1][2],model[1][3])
        z_axis = util.vec(model[2][0],model[2][1],model[2][2],model[2][3])

        # Test intersection with the 2 planes perpendicular to the bounding box's X axis

        e = np.dot(x_axis,delta)
        f = np.dot(ray_direction,x_axis)

        if np.abs(f)>0.001 : 
            t1 = (e+minbb[0])/f
            t2 = (e+maxbb[0])/f

            if t1 > t2 :
                t1, t2 = t2, t1
            
            if t2 < tmax:
                tmax = t2
            if t1 > tmin:
                tmin = t1
            
            if tmax < tmin:
                return False, self.intersection_point(self.previous_distance,ray_origin,ray_direction)
        else:
            if minbb[0] > e or maxbb[0] < e:
                return False, self.intersection_point(self.previous_distance,ray_origin,ray_direction)
            
        # Test intersection with the 2 planes perpendicular to the bounding box's Y axis

        e = np.dot(y_axis,delta)
        f = np.dot(ray_direction,y_axis)

        if np.abs(f) > 0.001 :
            t1 = (e+minbb[1])/f
            t2 = (e+maxbb[1])/f 

            if t1 > t2 :
                t1, t2 = t2, t1
            
            if t2 < tmax:
                tmax = t2
            if t1 > tmin:
                tmin = t1
            
            if tmin > tmax:
                return False, self.intersection_point(self.previous_distance,ray_origin,ray_direction)
        else:
            if minbb[1] > e or maxbb[1] < e:
                return False, self.intersection_point(self.previous_distance,ray_origin,ray_direction)
            
        # Test intersection with the 2 planes perpendicular to the bounding box's Z axis

        e = np.dot(z_axis,delta)
        f = np.dot(ray_direction,z_axis)

        if np.abs(f) > 0.001 :
            t1 = (e+minbb[2])/f
            t2 = (e+maxbb[2])/f

            if t1 > t2 :
                t1, t2 = t2, t1
            
            if t2 < tmax:
                tmax = t2
            if t1 > tmin:
                tmin = t1
            
            if tmin > tmax:
                return False, self.intersection_point(self.previous_distance,ray_origin,ray_direction)   
        else:
            if minbb[2] > e or maxbb[2] < e:
                return False, self.intersection_point(self.previous_distance,ray_origin,ray_direction)
            
        #let's check this out
        self.previous_distance = tmin
        ##

        return True, self.intersection_point(tmin,ray_origin,ray_direction)
    
    def testRayCircleIntersection(self,ray_origin,mesh):
        """
        Tests if a Ray intersects with a Rotation Gizmo
        Arguments:
            self: self
            ray_origin: Ray Starting Point
            ray_direction: Ray's Direction
            mesh: the mesh of a Rotation Gizmo
        Returns:
            True if there is an intersection, False otherwise. Additionally returns the Intersection point
        """
        pass
    
    def intersection_point(self,distance,ray_origin,ray_direction):
        """
        Calculates an intersection point given the following Arguments
        Arguments:
            self: self
            distance: minimum intersection distance
            ray_origin: ray starting point
            ray_direction: ray direction
        Returns:
            The intersection point on a bounding box
        """
        bottom = sqrt(pow(ray_direction[0],2)+pow(ray_direction[1],2)+pow(ray_direction[2],2))
        x = ray_origin[0]+(ray_direction[0]*distance)/bottom
        y = ray_origin[1]+(ray_direction[1]*distance)/bottom
        z = ray_origin[2]+(ray_direction[2]*distance)/bottom
        return util.vec(x,y,z)

    def __translate_selected(self,x=0.0,y=0.0,z=0.0):
        """
        Translate Selected Element
        Arguments:
            self: self
            x: x value
            y: y value
            z: z value
        Returns:
            None
        """
        self.selected_trans.trs = self.selected_trans.trs @ util.translate(x,y,z)
        self.gizmos_x_trans.trs = self.__remove_scaling(self.selected_trans.trs)
        self.gizmos_y_trans.trs = self.__remove_scaling(self.selected_trans.trs)
        self.gizmos_z_trans.trs = self.__remove_scaling(self.selected_trans.trs)

        self.gizmos_x_S_line_trans.trs = self.selected_trans.trs
        self.gizmos_y_S_line_trans.trs = self.selected_trans.trs
        self.gizmos_z_S_line_trans.trs = self.selected_trans.trs

        x_t = util.translate(x=self.selected_trans.trs[0][0]-1.0)
        y_t = util.translate(y=self.selected_trans.trs[1][1]-1.0)
        z_t = util.translate(z=self.selected_trans.trs[2][2]-1.0)

        self.gizmos_x_S_cube_trans.trs = self.__remove_scaling(self.selected_trans.trs) @ x_t
        self.gizmos_y_S_cube_trans.trs = self.__remove_scaling(self.selected_trans.trs) @ y_t
        self.gizmos_z_S_cube_trans.trs = self.__remove_scaling(self.selected_trans.trs) @ z_t

        self.gizmos_x_R_trans.trs = self.__remove_scaling(self.selected_trans.trs)
        self.gizmos_y_R_trans.trs = self.__remove_scaling(self.selected_trans.trs)
        self.gizmos_z_R_trans.trs = self.__remove_scaling(self.selected_trans.trs)

        
    
    def __rotate_selected(self,_angle=0.0,_axis=(1.0,0.0,0.0)):
        """
        Rotate Selected Element
        Arguments:
            self: self
            _angle: Rotation Angle
            _axis: axis to rotate
        Returns:
            None
        """
        self.selected_trans.trs = self.selected_trans.trs @ util.rotate(angle=_angle,axis=_axis)
        self.gizmos_x_trans.trs = self.selected_trans.trs #remove scaling too
        self.gizmos_y_trans.trs = self.selected_trans.trs
        self.gizmos_z_trans.trs = self.selected_trans.trs

    def __scale_selected(self,x=1.0,y=1.0,z=1.0):
        """
        Scale Selected Element
        Arguments:
            self: self
            x: Scaling on x-axis
            y: Scaling on y-axis
            z: Scaling on z-axis
        Returns:
            None
        """
        self.selected_trans.trs = self.selected_trans.trs @ util.scale(x,y,z)
        self.gizmos_x_trans.trs = self.__remove_scaling(self.selected_trans.trs)
        self.gizmos_y_trans.trs = self.__remove_scaling(self.selected_trans.trs)
        self.gizmos_z_trans.trs = self.__remove_scaling(self.selected_trans.trs)

        self.gizmos_x_S_line_trans.trs = self.selected_trans.trs
        self.gizmos_y_S_line_trans.trs = self.selected_trans.trs
        self.gizmos_z_S_line_trans.trs = self.selected_trans.trs

        x_t = util.translate(x=self.selected_trans.trs[0][0]-1.0)
        y_t = util.translate(y=self.selected_trans.trs[1][1]-1.0)
        z_t = util.translate(z=self.selected_trans.trs[2][2]-1.0)

        self.gizmos_x_S_cube_trans.trs = self.__remove_scaling(self.selected_trans.trs) @ x_t
        self.gizmos_y_S_cube_trans.trs = self.__remove_scaling(self.selected_trans.trs) @ y_t
        self.gizmos_z_S_cube_trans.trs = self.__remove_scaling(self.selected_trans.trs) @ z_t

        self.gizmos_x_R_trans.trs = self.__remove_scaling(self.selected_trans.trs)
        self.gizmos_y_R_trans.trs = self.__remove_scaling(self.selected_trans.trs)
        self.gizmos_z_R_trans.trs = self.__remove_scaling(self.selected_trans.trs)