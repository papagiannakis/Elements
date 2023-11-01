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
import Elements.utils.normals as norm
import imgui
import enum

def generateCircle(axis='X',points=50,color=[1.0,0.0,0.0,1.0]):
    """
    Generates and returns data for a circle, used to create part of the rotation gizmo
    Arguments:
        axis: where the circle is on
        points: number of total points corresponding to the circle
        color: color of the circle
    Returns:
        The vertex, index and color arrays of a circle
    
    """

    _angle = 360.0/(points-2)
    init_indices = np.array([0,3,4,4,3,7,7,6,3,3,6,2,5,6,1,5,2,1,0,4,1,1,4,5],dtype=np.int32)
    curr_indices = np.array(init_indices,copy=True)
    inc = 4

    # x-axis gizmos
    p1 = util.vec(1.0,0.0,-0.02,1.0)
    p2 = util.vec(1.0,0.0,0.02,1.0)
    p3 = util.vec(1.01,0.0,-0.02,1.0)
    p4 = util.vec(1.01,0.0,0.02,1.0)

    if axis=='Y':
        # y-axis gizmos
        p1 = util.vec(1.0,-0.02,0.0,1.0)
        p2 = util.vec(1.0,0.02,0.0,1.0)
        p3 = util.vec(1.01,0.02,0.0,1.0)
        p4 = util.vec(1.01,-0.02,0.0,1.0)
    elif axis=='Z':
        # z-axis gizmo
        p1 = util.vec(-0.02,0.0,1.0,1.0)
        p2 = util.vec(0.02,0.0,1.0,1.0)
        p3 = util.vec(0.02,0.0,1.01,1.0)
        p4 = util.vec(-0.02,0.0,1.01,1.0)
    

    ver = np.array([p1,p2,p3,p4],dtype=np.float32)
    ind = np.array(init_indices,dtype=np.int32)
    col = np.full((4 * points,4),color,dtype=np.float32)

    p = np.array([p1,p2,p3,p4],dtype=np.float32)

    for i in range(1,points):

        if axis=='X':
            p = p @ util.rotate(axis=(0.0,0.0,1.0),angle=_angle)
        elif axis=='Y':
            p = p @ util.rotate(axis=(0.0,1.0,0.0),angle=_angle)
        else:
            p = p @ util.rotate(axis=(1.0,0.0,0.0),angle=_angle)

        if i==points-1:
            ind = np.append(ind,init_indices)
        else:
            curr_indices = curr_indices + inc
            ver = np.concatenate((ver,p),axis=0)
            ind = np.append(ind,curr_indices)

    return ver, ind, col

RX_GIZMOS, rindex_x, rcolor_x = generateCircle(axis='X',color=[1.0,0.0,0.0,1.0])
RY_GIZMOS, rindex_y, rcolor_y = generateCircle(axis='Y',color=[0.0,1.0,0.0,1.0])
RZ_GIZMOS, rindex_z, rcolor_z = generateCircle(axis='Z',color=[0.0,0.0,1.0,1.0])

# Vertex data for the translate gizmos
VERTEX_GIZMOS_X = np.array([[0.1, 0.1, -0.1, 1.0],
                          [0.1, -0.1, -0.1, 1.0],
                          [0.1, 0.1, 0.1, 1.0],
                          [0.1, -0.1, 0.1, 1.0],
                          [1.4, -0.1, -0.1, 1.0],
                          [1.4, 0.1, -0.1, 1.0],
                          [1.4, -0.1, 0.1, 1.0],
                          [1.4, 0.1, 0.1, 1.0],],dtype=np.float32)
    
VERTEX_GIZMOS_Y = np.array([[0.1, 0.1, -0.1, 1.0],
                          [-0.1, 0.1, -0.1, 1.0],
                          [0.1, 0.1, 0.1, 1.0],
                          [-0.1, 0.1, 0.1, 1.0],
                          [-0.1, 1.4, -0.1, 1.0],
                          [0.1, 1.4, -0.1, 1.0],
                          [-0.1, 1.4, 0.1, 1.0],
                          [0.1, 1.4, 0.1, 1.0],],dtype=np.float32)
    
VERTEX_GIZMOS_Z = np.array([[-0.1, 0.1, 0.1, 1.0],
                          [-0.1, -0.1, 0.1, 1.0],
                          [0.1, 0.1, 0.1, 1.0],
                          [0.1, -0.1, 0.1, 1.0],
                          [-0.1, -0.1, 1.4, 1.0],
                          [-0.1, 0.1, 1.4, 1.0],
                          [0.1, -0.1, 1.4, 1.0],
                          [0.1, 0.1, 1.4, 1.0],],dtype=np.float32)
    
VERTEX_GIZMOS_X = VERTEX_GIZMOS_X @ util.scale(0.7,0.3,0.3)
VERTEX_GIZMOS_Y = VERTEX_GIZMOS_Y @ util.scale(0.3,0.7,0.3)
VERTEX_GIZMOS_Z = VERTEX_GIZMOS_Z @ util.scale(0.3,0.3,0.7)

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

#translate cubes indices
ARROW_INDEX2 = np.array((0,1,3, 2,0,3, 
                            5,4,0, 1,0,4,
                            7,2,6, 6,2,3,
                            4,5,7, 4,7,6,
                            7,5,2, 5,0,2,
                            4,3,1, 4,6,3), np.int32)


# SCALE VERTICES, INDICES, COLORS, NORMALS

# cubes indices for the scale cube at the end of the scale gizmo
ARROW_INDEX = np.array((0,1,3, 2,0,3, 
                            5,4,0, 1,0,4,
                            7,2,6, 6,2,3,
                            4,5,7, 4,7,6,
                            7,5,2, 5,0,2,
                            4,3,1, 4,6,3), np.int32)

# regarding the lines coordinates of the scale gizmo
XS_LINE = np.array([[0.0,0.0,0.0,1.0], [1.0,0.0,0.0,1.0]],dtype=np.float32)    
YS_LINE = np.array([[0.0,0.0,0.0,1.0], [0.0,1.0,0.0,1.0]],dtype=np.float32)
ZS_LINE = np.array([[0.0,0.0,0.0,1.0], [0.0,0.0,1.0,1.0]],dtype=np.float32)
    
# regarding the lines colors of the scale gizmo
XS_LINE_COLOR = np.array([ [1.0, 0.0, 0.0, 1.0], [1.0, 0.0, 0.0, 1.0] ], dtype=np.float32)
YS_LINE_COLOR = np.array([ [0.0, 1.0, 0.0, 1.0], [0.0, 1.0, 0.0, 1.0] ], dtype=np.float32)
ZS_LINE_COLOR = np.array([ [0.0, 0.0, 1.0, 1.0], [0.0, 0.0, 1.0, 1.0] ], dtype=np.float32)

# regarding the lines indices of the scale gizmo
LINE_INDEX = np.array((0,1),dtype=np.int32)

# regarding the cube coordinates of the scale gizmo
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

# generates the scale gizmo's cube's colors, indices and normals
XS_GIZMOS, INDEX_XS, COLOR_XS, NORMALS_XS = norm.generateFlatNormalsMesh(XS_GIZMOS,ARROW_INDEX,COLOR_X)
YS_GIZMOS, INDEX_YS, COLOR_YS, NORMALS_YS = norm.generateFlatNormalsMesh(YS_GIZMOS,ARROW_INDEX,COLOR_Y)
ZS_GIZMOS, INDEX_ZS, COLOR_ZS, NORMALS_ZS = norm.generateFlatNormalsMesh(ZS_GIZMOS,ARROW_INDEX,COLOR_Z)
    


class Mode(enum.Enum):
    # Enum class for the gizmos' modes
    TRANSLATE="Translate"
    ROTATE="Rotate"
    SCALE="Scale"
    DISAPPEAR="Disappear"

class entity_transformations:
    """
    This class is used for storing each entity's unique transformations seperately
    """
    def __init__(self) -> None:
        self.translation = util.identity()
        self.rotation = util.identity()
        self.scaling=util.vec(1.0,1.0,1.0)

class Gizmos:

    def __init__(self,rootEntity: Entity):
        sdl.ext.init()
        self.scene = Scene() # Scene object
        self.selected = 0 # Selected entity
        self.total = 0 # Total number of entities on the scene
        self.mouse_x, self.mouse_y = c_int(0), c_int(0) # Mouse coordinates
        self.key_states = sdl.SDL_GetKeyboardState(None) # Keyboard state
        self.tab_down = False # Tab key state
        self.lmb_down = False # Left mouse button state
        self.projection = np.array([4,4],dtype=np.float32) # Projection matrix
        self.view = np.array([4,4],dtype=np.float32) # View matrix

        self.is_selected = False # Is an entity selected
        self.selected_trans = None # Transform component of the selected entity
        self.selected_mesh = None # Mesh component of the selected entity
        self.selected_comp = "None" # Component of the selected entity
        self.mode = Mode.DISAPPEAR # Current mode of the gizmos
        
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
        
        self.seperate_transformations = {} # Dictionary for storing each entity's unique transformations seperately
        self.initial_transformations = {} # Dictionary for storing each entity's initial transformations seperately
        self.entity_dict = {} # Dictionary for storing each entity's name and id seperately

        self.cameraInUse = "" # Camera in use - in order to ignore it
        self.screen_width = 1024.0
        self.screen_height = 768.0
        self.picked = False # Is an entity picked
        self.selected_gizmo = '' # Selected gizmo, X, Y or Z
        self.previous_distance = 0.0 # Previous distance between the mouse and the gizmo
        self.rotation_distance = 0.0 # Distance between the mouse and the gizmo for rotation
        self.previous_x = 0.0 # Previous x coordinate of the mouse
        self.previous_y = 0.0 # Previous y coordinate of the mouse
        self.previous_z = 0.0 # Previous z coordinate of the mouse

        self.rotation = util.identity() # Rotation matrix for rotation mode - stores the previous rotation until you release the mouse button
        self.rotation_modifier = 45 # Rotation modifier for rotation mode: greater value = faster rotation

        #Light parameters for scale cubes
        self.Lambientcolor = util.vec(1.0, 1.0, 1.0)
        self.Lambientstr = 0.3
        self.LviewPos = util.vec(2.5, 2.8, 5.0)
        self.Lcolor = util.vec(1.0,1.0,1.0)
        self.Lintensity = 0.9
        #Material parameters for scale cubes
        self.Mshininess = 0.4 
        self.Mcolor = util.vec(0.8, 0.0, 0.8)

        ########## Translate components
        self.gizmos_x = self.scene.world.createEntity(Entity(name="Gizmos_X"))
        self.scene.world.addEntityChild(rootEntity, self.gizmos_x)
        self.gizmos_x_trans = self.scene.world.addComponent(self.gizmos_x, BasicTransform(name="Gizmos_X_trans", trs=util.identity()))
        self.gizmos_x_mesh = self.scene.world.addComponent(self.gizmos_x, RenderMesh(name="Gizmos_X_mesh"))
        self.gizmos_x_mesh.vertex_attributes.append(VERTEX_GIZMOS_X)
        self.gizmos_x_mesh.vertex_attributes.append(COLOR_X)
        self.gizmos_x_mesh.vertex_index.append(ARROW_INDEX2)
        self.gizmos_x_vArray = self.scene.world.addComponent(self.gizmos_x, VertexArray())
        self.gizmos_x_shader = self.scene.world.addComponent(self.gizmos_x, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))

        self.gizmos_y = self.scene.world.createEntity(Entity(name="Gizmos_Y"))
        self.scene.world.addEntityChild(rootEntity, self.gizmos_y)
        self.gizmos_y_trans = self.scene.world.addComponent(self.gizmos_y, BasicTransform(name="Gizmos_Y_trans", trs=util.identity()))
        self.gizmos_y_mesh = self.scene.world.addComponent(self.gizmos_y, RenderMesh(name="Gizmos_Y_mesh"))
        self.gizmos_y_mesh.vertex_attributes.append(VERTEX_GIZMOS_Y)
        self.gizmos_y_mesh.vertex_attributes.append(COLOR_Y)
        self.gizmos_y_mesh.vertex_index.append(ARROW_INDEX2)
        self.gizmos_y_vArray = self.scene.world.addComponent(self.gizmos_y, VertexArray())
        self.gizmos_y_shader = self.scene.world.addComponent(self.gizmos_y, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))

        self.gizmos_z = self.scene.world.createEntity(Entity(name="Gizmos_Z"))
        self.scene.world.addEntityChild(rootEntity, self.gizmos_z)
        self.gizmos_z_trans = self.scene.world.addComponent(self.gizmos_z, BasicTransform(name="Gizmos_Z_trans", trs=util.identity()))
        self.gizmos_z_mesh = self.scene.world.addComponent(self.gizmos_z, RenderMesh(name="Gizmos_Z_mesh"))
        self.gizmos_z_mesh.vertex_attributes.append(VERTEX_GIZMOS_Z)
        self.gizmos_z_mesh.vertex_attributes.append(COLOR_Z)
        self.gizmos_z_mesh.vertex_index.append(ARROW_INDEX2)
        self.gizmos_z_vArray = self.scene.world.addComponent(self.gizmos_z, VertexArray())
        self.gizmos_z_shader = self.scene.world.addComponent(self.gizmos_z, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))
        ##############

        ############## Scale components
        self.gizmos_x_S_line = self.scene.world.createEntity(Entity(name="Gizmos_x_S_line"))
        self.scene.world.addEntityChild(rootEntity, self.gizmos_x_S_line)
        self.gizmos_x_S_line_trans = self.scene.world.addComponent(self.gizmos_x_S_line, BasicTransform(name="Gizmos_x_S_line_trans", trs=util.identity()))
        self.gizmos_x_S_line_mesh = self.scene.world.addComponent(self.gizmos_x_S_line, RenderMesh(name="Gizmos_x_S_line_mesh"))
        self.gizmos_x_S_line_mesh.vertex_attributes.append(XS_LINE)
        self.gizmos_x_S_line_mesh.vertex_attributes.append(XS_LINE_COLOR)
        self.gizmos_x_S_line_mesh.vertex_index.append(LINE_INDEX)
        self.gizmos_x_S_line_vArray = self.scene.world.addComponent(self.gizmos_x_S_line, VertexArray(primitive=GL_LINES))
        self.gizmos_x_S_line_shader = self.scene.world.addComponent(self.gizmos_x_S_line, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))

        self.gizmos_y_S_line = self.scene.world.createEntity(Entity(name="Gizmos_y_S_line"))
        self.scene.world.addEntityChild(rootEntity, self.gizmos_y_S_line)
        self.gizmos_y_S_line_trans = self.scene.world.addComponent(self.gizmos_y_S_line, BasicTransform(name="Gizmos_y_S_line_trans", trs=util.identity()))
        self.gizmos_y_S_line_mesh = self.scene.world.addComponent(self.gizmos_y_S_line, RenderMesh(name="Gizmos_y_S_line_mesh"))
        self.gizmos_y_S_line_mesh.vertex_attributes.append(YS_LINE)
        self.gizmos_y_S_line_mesh.vertex_attributes.append(YS_LINE_COLOR)
        self.gizmos_y_S_line_mesh.vertex_index.append(LINE_INDEX)
        self.gizmos_y_S_line_vArray = self.scene.world.addComponent(self.gizmos_y_S_line, VertexArray(primitive=GL_LINES))
        self.gizmos_y_S_line_shader = self.scene.world.addComponent(self.gizmos_y_S_line, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))
        
        self.gizmos_z_S_line = self.scene.world.createEntity(Entity(name="Gizmos_z_S_line"))
        self.scene.world.addEntityChild(rootEntity, self.gizmos_z_S_line)
        self.gizmos_z_S_line_trans = self.scene.world.addComponent(self.gizmos_z_S_line, BasicTransform(name="Gizmos_z_S_line_trans", trs=util.identity()))
        self.gizmos_z_S_line_mesh = self.scene.world.addComponent(self.gizmos_z_S_line, RenderMesh(name="Gizmos_z_S_line_mesh"))
        self.gizmos_z_S_line_mesh.vertex_attributes.append(ZS_LINE)
        self.gizmos_z_S_line_mesh.vertex_attributes.append(ZS_LINE_COLOR)
        self.gizmos_z_S_line_mesh.vertex_index.append(LINE_INDEX)
        self.gizmos_z_S_line_vArray = self.scene.world.addComponent(self.gizmos_z_S_line, VertexArray(primitive=GL_LINES))
        self.gizmos_z_S_line_shader = self.scene.world.addComponent(self.gizmos_z_S_line, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))
        
        self.gizmos_x_S_cube = self.scene.world.createEntity(Entity(name="Gizmos_x_S_cube"))
        self.scene.world.addEntityChild(rootEntity, self.gizmos_x_S_cube)
        self.gizmos_x_S_cube_trans = self.scene.world.addComponent(self.gizmos_x_S_cube, BasicTransform(name="Gizmos_x_S_cube_trans", trs=util.identity()))
        self.gizmos_x_S_cube_mesh = self.scene.world.addComponent(self.gizmos_x_S_cube, RenderMesh(name="Gizmos_x_S_cube_mesh"))
        self.gizmos_x_S_cube_mesh.vertex_attributes.append(XS_GIZMOS)
        self.gizmos_x_S_cube_mesh.vertex_attributes.append(COLOR_XS)
        self.gizmos_x_S_cube_mesh.vertex_attributes.append(NORMALS_XS)
        self.gizmos_x_S_cube_mesh.vertex_index.append(INDEX_XS)
        self.gizmos_x_S_cube_vArray = self.scene.world.addComponent(self.gizmos_x_S_cube, VertexArray())
        self.gizmos_x_S_cube_shader = self.scene.world.addComponent(self.gizmos_x_S_cube, ShaderGLDecorator(Shader(vertex_source = Shader.VERT_PHONG_MVP, fragment_source=Shader.FRAG_PHONG)))

        self.gizmos_y_S_cube = self.scene.world.createEntity(Entity(name="Gizmos_y_S_cube"))
        self.scene.world.addEntityChild(rootEntity, self.gizmos_y_S_cube)
        self.gizmos_y_S_cube_trans = self.scene.world.addComponent(self.gizmos_y_S_cube, BasicTransform(name="Gizmos_y_S_cube_trans", trs=util.identity()))
        self.gizmos_y_S_cube_mesh = self.scene.world.addComponent(self.gizmos_y_S_cube, RenderMesh(name="Gizmos_y_S_cube_mesh"))
        self.gizmos_y_S_cube_mesh.vertex_attributes.append(YS_GIZMOS)
        self.gizmos_y_S_cube_mesh.vertex_attributes.append(COLOR_YS)
        self.gizmos_y_S_cube_mesh.vertex_attributes.append(NORMALS_YS)
        self.gizmos_y_S_cube_mesh.vertex_index.append(INDEX_YS)
        self.gizmos_y_S_cube_vArray = self.scene.world.addComponent(self.gizmos_y_S_cube, VertexArray())
        self.gizmos_y_S_cube_shader = self.scene.world.addComponent(self.gizmos_y_S_cube, ShaderGLDecorator(Shader(vertex_source = Shader.VERT_PHONG_MVP, fragment_source=Shader.FRAG_PHONG)))

        self.gizmos_z_S_cube = self.scene.world.createEntity(Entity(name="Gizmos_z_S_cube"))
        self.scene.world.addEntityChild(rootEntity, self.gizmos_z_S_cube)
        self.gizmos_z_S_cube_trans = self.scene.world.addComponent(self.gizmos_z_S_cube, BasicTransform(name="Gizmos_z_S_cube_trans", trs=util.identity()))
        self.gizmos_z_S_cube_mesh = self.scene.world.addComponent(self.gizmos_z_S_cube, RenderMesh(name="Gizmos_z_S_cube_mesh"))
        self.gizmos_z_S_cube_mesh.vertex_attributes.append(ZS_GIZMOS)
        self.gizmos_z_S_cube_mesh.vertex_attributes.append(COLOR_ZS)
        self.gizmos_z_S_cube_mesh.vertex_attributes.append(NORMALS_ZS)
        self.gizmos_z_S_cube_mesh.vertex_index.append(INDEX_ZS)
        self.gizmos_z_S_cube_vArray = self.scene.world.addComponent(self.gizmos_z_S_cube, VertexArray())
        self.gizmos_z_S_cube_shader = self.scene.world.addComponent(self.gizmos_z_S_cube, ShaderGLDecorator(Shader(vertex_source = Shader.VERT_PHONG_MVP, fragment_source=Shader.FRAG_PHONG)))
        ##############

        ############## Rotation Gizmos components
        self.gizmos_x_R = self.scene.world.createEntity(Entity(name="Gizmos_x_R"))
        self.scene.world.addEntityChild(rootEntity, self.gizmos_x_R)
        self.gizmos_x_R_trans = self.scene.world.addComponent(self.gizmos_x_R, BasicTransform(name="Gizmos_x_R_trans", trs=util.identity()))
        self.gizmos_x_R_mesh = self.scene.world.addComponent(self.gizmos_x_R, RenderMesh(name="Gizmos_x_R_mesh"))
        self.gizmos_x_R_mesh.vertex_attributes.append(RX_GIZMOS)
        self.gizmos_x_R_mesh.vertex_attributes.append(rcolor_x)
        self.gizmos_x_R_mesh.vertex_index.append(rindex_x)
        self.gizmos_x_R_vArray = self.scene.world.addComponent(self.gizmos_x_R, VertexArray())
        self.gizmos_x_R_shader = self.scene.world.addComponent(self.gizmos_x_R, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))

        self.gizmos_y_R = self.scene.world.createEntity(Entity(name="Gizmos_y_R"))
        self.scene.world.addEntityChild(rootEntity, self.gizmos_y_R)
        self.gizmos_y_R_trans = self.scene.world.addComponent(self.gizmos_y_R, BasicTransform(name="Gizmos_y_R_trans", trs=util.identity()))
        self.gizmos_y_R_mesh = self.scene.world.addComponent(self.gizmos_y_R, RenderMesh(name="Gizmos_y_R_mesh"))
        self.gizmos_y_R_mesh.vertex_attributes.append(RY_GIZMOS)
        self.gizmos_y_R_mesh.vertex_attributes.append(rcolor_y)
        self.gizmos_y_R_mesh.vertex_index.append(rindex_y)
        self.gizmos_y_R_vArray = self.scene.world.addComponent(self.gizmos_y_R, VertexArray())
        self.gizmos_y_R_shader = self.scene.world.addComponent(self.gizmos_y_R, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))

        self.gizmos_z_R = self.scene.world.createEntity(Entity(name="Gizmos_z_R"))
        self.scene.world.addEntityChild(rootEntity, self.gizmos_z_R)
        self.gizmos_z_R_trans = self.scene.world.addComponent(self.gizmos_z_R, BasicTransform(name="Gizmos_z_R_trans", trs=util.identity()))
        self.gizmos_z_R_mesh = self.scene.world.addComponent(self.gizmos_z_R, RenderMesh(name="Gizmos_z_R_mesh"))
        self.gizmos_z_R_mesh.vertex_attributes.append(RZ_GIZMOS)
        self.gizmos_z_R_mesh.vertex_attributes.append(rcolor_z)
        self.gizmos_z_R_mesh.vertex_index.append(rindex_z)
        self.gizmos_z_R_vArray = self.scene.world.addComponent(self.gizmos_z_R, VertexArray())
        self.gizmos_z_R_shader = self.scene.world.addComponent(self.gizmos_z_R, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))

        #Translation gizmos bounding boxes
        self.x_min_bb, self.x_max_bb = self.calculate_bounding_box(self.gizmos_x_mesh.vertex_attributes[0])
        self.y_min_bb, self.y_max_bb = self.calculate_bounding_box(self.gizmos_y_mesh.vertex_attributes[0])
        self.z_min_bb, self.z_max_bb = self.calculate_bounding_box(self.gizmos_z_mesh.vertex_attributes[0])

        #scaling gizmos bounding boxes
        self.xs_min_bb, self.xs_max_bb = self.calculate_bounding_box(self.gizmos_x_S_cube_mesh.vertex_attributes[0])
        self.ys_min_bb, self.ys_max_bb = self.calculate_bounding_box(self.gizmos_y_S_cube_mesh.vertex_attributes[0])
        self.zs_min_bb, self.zs_max_bb = self.calculate_bounding_box(self.gizmos_z_S_cube_mesh.vertex_attributes[0])

        #Rotation Gizmos Bounding Boxes
        self.xrot_min_bb, self.xrot_max_bb = self.calculate_bounding_box(self.gizmos_x_R_mesh.vertex_attributes[0])
        self.yrot_min_bb, self.yrot_max_bb = self.calculate_bounding_box(self.gizmos_y_R_mesh.vertex_attributes[0])
        self.zrot_min_bb, self.zrot_max_bb = self.calculate_bounding_box(self.gizmos_z_R_mesh.vertex_attributes[0])

        self.count_components() # Count Basic transform components in the scene, besides the Gizmos

    @property
    def isSelected(self):
        return self.is_selected
    
    def __remove_rotation__(self,model):
        """
        Creates and returns a copy of a given TRS model matrix after removing its rotation
        Arguments:
            self: self
            model: a TRS matrix
        Returns:
            The TRS matrix without rotation and scaling
        """
        M = np.array(model,copy=True)
        for i in range(3):
            for j in range(3):
                if i==j:
                    M[i][j] = 1.0
                else:
                    M[i][j] = 0.0
        return M

    def reset_to_None(self):
        """
        Resets Gizmos to initial state if someone tries to unsuccessfully pick something
        Arguments:
            self: self
        Returns:
            None
        """
        prev = self.mode
        self.mode = Mode.DISAPPEAR
        self.__update_positions()
        self.mode = prev
        self.is_selected = False
        self.selected_trans = None
        self.selected_mesh = None
        self.selected_comp = "None"

    def reset_to_default(self):
        """
        Resets selected Entity's transformations to inital state (when clicking 0)
        Arguments:
            self: self
        Returns:
            None
        """
        self.selected_trans.trs = self.initial_transformations[self.selected_comp]
        self.seperate_transformations[self.selected_comp] = entity_transformations()

        self.__update_gizmos_trans()
        self.__update_gizmos()

    def change_target(self):
        """
        Change selected entity (when clicking TAB)
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

            #Have to check because there is always some component that is NoneType
            if component is not None:
                parentname = component.parent.name
                #next BasicTransform component that is not one of the gizmos components and is not child of the camera in use
                if component.getClassName()=="BasicTransform" and component.name not in self.gizmos_comps and parentname!=self.cameraInUse and parentname.find("ground")==-1 and parentname.find("BoundingBox")==-1 and parentname.find("Skybox")==-1:
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
        if component is not None:
            self.showSelectedBB(component.parent.getChildByType("AABoundingBox"))

    def update_ray_start(self):
        """
        Update mouse position and mouse state. Additionally Raycast (or try to pick an Entity)
        Arguments:
            self: self
        Returns:
            None
        """
        mouse_state = sdl.mouse.SDL_GetMouseState(byref(self.mouse_x), byref(self.mouse_y)) # Mouse state = 1 if Left Mouse Button is pressed or 0 if not
        #Raycast only when LMB is pressed
        if mouse_state==1:
            if self.key_states[sdl.SDL_SCANCODE_LALT] and self.selected_trans is not None:
                self.raycast()
            else:
                self.raycastForSelection()
        else:
            self.lmb_down = False
            self.selected_gizmo = ''
            self.picked = False
            self.rotation = util.identity() # the gizmos are reset to their initial state
            if self.is_selected:
                self.__update_gizmos_trans() # update gizmos' positions matrices
                self.__update_positions() # update gizmos' positions shaders
        
    def count_components(self):
        """
        Count transform components in the scene
        Arguments:
            self: self
        Returns:
            None
        """
        for component in self.scene.world.root:
            if component is not None and component.getClassName()=="BasicTransform" and component.name not in self.gizmos_comps and component.parent.name.find("ground")==-1 and component.parent.name.find("BoundingBox")==-1 and component.parent.name.find("Skybox")==-1:
                entity_name = component.parent.name
                self.seperate_transformations[entity_name] = entity_transformations()
                self.initial_transformations[entity_name] = component.trs
                self.entity_dict[entity_name] = component.parent

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
        if self.key_states[sdl.SDL_SCANCODE_TAB] and not self.tab_down:
            self.tab_down = True
            self.change_target()
            if self.total>0:
                self.is_selected = True
                self.__update_gizmos_trans()
                self.__update_gizmos()
        elif not self.key_states[sdl.SDL_SCANCODE_TAB] and self.tab_down:
            self.tab_down = False

        if self.key_states[sdl.SDL_SCANCODE_0]:
            self.reset_to_default()

        if self.key_states[sdl.SDL_SCANCODE_T]:
            self.mode = Mode.TRANSLATE
            self.__update_gizmos()
        if self.key_states[sdl.SDL_SCANCODE_R]:
            self.mode = Mode.ROTATE
            self.__update_gizmos()
        if self.key_states[sdl.SDL_SCANCODE_S]:
            self.mode = Mode.SCALE
            self.__update_gizmos()
        if self.key_states[sdl.SDL_SCANCODE_D]:
            self.mode = Mode.DISAPPEAR
            self.reset_to_None()
    
    def __update_gizmos(self):
        """
        Update Gizmos uniform variables 
        Arguments:
            self: self
        Returns:
            None
        """
        if self.is_selected:
            self.__update_lights() 
            self.__update_positions()
    
    def __update_lights(self):
        """
        Update Lighting of Scaling Gizmos
        Arguments:
            self: self
        REturns:
            None
        """
        model_XS_cube = self.gizmos_x_S_cube_trans.trs
        model_YS_cube = self.gizmos_y_S_cube_trans.trs
        model_ZS_cube = self.gizmos_z_S_cube_trans.trs
        
        Lposition = util.vec(model_XS_cube[0,3],model_XS_cube[1,3]+0.5,model_XS_cube[2,3]+0.5)
            
        self.gizmos_x_S_cube_shader.setUniformVariable(key='model',value=model_XS_cube,mat4=True)
        self.gizmos_x_S_cube_shader.setUniformVariable(key='ambientColor',value=self.Lambientcolor,float3=True)
        self.gizmos_x_S_cube_shader.setUniformVariable(key='ambientStr',value=self.Lambientstr,float1=True)
        self.gizmos_x_S_cube_shader.setUniformVariable(key='viewPos',value=self.LviewPos,float3=True)
        self.gizmos_x_S_cube_shader.setUniformVariable(key='lightPos',value=Lposition,float3=True)
        self.gizmos_x_S_cube_shader.setUniformVariable(key='lightColor',value=self.Lcolor,float3=True)
        self.gizmos_x_S_cube_shader.setUniformVariable(key='lightIntensity',value=self.Lintensity,float1=True)
        self.gizmos_x_S_cube_shader.setUniformVariable(key='shininess',value=self.Mshininess,float1=True)
        self.gizmos_x_S_cube_shader.setUniformVariable(key='matColor',value=self.Mcolor,float3=True)
            
        Lposition = util.vec(model_YS_cube[0,3],model_YS_cube[1,3]+0.5,model_YS_cube[2,3]+0.5)
            
        self.gizmos_y_S_cube_shader.setUniformVariable(key='model',value=model_YS_cube,mat4=True)
        self.gizmos_y_S_cube_shader.setUniformVariable(key='ambientColor',value=self.Lambientcolor,float3=True)
        self.gizmos_y_S_cube_shader.setUniformVariable(key='ambientStr',value=self.Lambientstr,float1=True)
        self.gizmos_y_S_cube_shader.setUniformVariable(key='viewPos',value=self.LviewPos,float3=True)
        self.gizmos_y_S_cube_shader.setUniformVariable(key='lightPos',value=Lposition,float3=True)
        self.gizmos_y_S_cube_shader.setUniformVariable(key='lightColor',value=self.Lcolor,float3=True)
        self.gizmos_y_S_cube_shader.setUniformVariable(key='lightIntensity',value=self.Lintensity,float1=True)
        self.gizmos_y_S_cube_shader.setUniformVariable(key='shininess',value=self.Mshininess,float1=True)
        self.gizmos_y_S_cube_shader.setUniformVariable(key='matColor',value=self.Mcolor,float3=True)
            
        Lposition = util.vec(model_ZS_cube[0,3],model_ZS_cube[1,3]+0.5,model_ZS_cube[2,3]+0.5)

        self.gizmos_z_S_cube_shader.setUniformVariable(key='model',value=model_ZS_cube,mat4=True)
        self.gizmos_z_S_cube_shader.setUniformVariable(key='ambientColor',value=self.Lambientcolor,float3=True)
        self.gizmos_z_S_cube_shader.setUniformVariable(key='ambientStr',value=self.Lambientstr,float1=True)
        self.gizmos_z_S_cube_shader.setUniformVariable(key='viewPos',value=self.LviewPos,float3=True)
        self.gizmos_z_S_cube_shader.setUniformVariable(key='lightPos',value=Lposition,float3=True)
        self.gizmos_z_S_cube_shader.setUniformVariable(key='lightColor',value=self.Lcolor,float3=True)
        self.gizmos_z_S_cube_shader.setUniformVariable(key='lightIntensity',value=self.Lintensity,float1=True)
        self.gizmos_z_S_cube_shader.setUniformVariable(key='shininess',value=self.Mshininess,float1=True)
        self.gizmos_z_S_cube_shader.setUniformVariable(key='matColor',value=self.Mcolor,float3=True)

    def __update_positions(self):
        """
        Update model matrices of all Gizmo components and update their shaders
        Arguments:
            self: self
        Returns:
            None
        """
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

        # if rotate is not used, then the gizmos are not visible
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
        Update window's projection and calculate its inverse, if needed
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
        Update window's View and calculate its inverse, if needed
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
        Used to help raycasting
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

        for i in  range(len(vertices)):
            vertices[i] = vertices[i]/vertices[i][3]

        minbb = util.vec(vertices[0][0],vertices[0][1],vertices[0][2],1.0)
        maxbb = util.vec(vertices[0][0],vertices[0][1],vertices[0][2],1.0)
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
            a ray's starting position and direction in world space

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

    def showSelectedBB(self, compBB):
        for comp in self.scene.world.root:
            if comp is not None and comp.getClassName()=="RenderMesh" and comp.name == "mesh_BoundingBox":
                comp.parent.getChildByType("BasicTransform").trs = compBB.parent.getChildByType("BasicTransform").l2world @ compBB.scaleMatrix 
                return
            
    def raycastForSelection(self):
        """
        Raycast from mouse position to an object in the scenegraph to select it
        Arguments:
            self: self
        Returns:
            None
        """
        ray_origin, ray_direction = self.calculate_ray()
        obj_intersects, obj_in_point = False, util.vec(0.0)

        count=0
        for component in self.scene.world.root:
            if component is not None and component.getClassName()=="BasicTransform" and component.name not in self.gizmos_comps and component.parent.name.find("ground")==-1 and component.parent.name.find("BoundingBox")==-1 and component.parent.name.find("Skybox")==-1:
                count = count + 1
                bb = component.parent.getChildByType("AABoundingBox")
                if (bb is not None):
                    model = component 
                    mmin = bb._trans_min_points #@ model.trs
                    mmax = bb._trans_max_points #@ model.trs
                    obj_intersects, obj_in_point = self.testRayBoundingBoxIntesection(ray_origin,
                                                ray_direction,
                                                mmin,
                                                mmax,
                                                model.trs)    
                    if (obj_intersects):
                        self.selected = count-2
                        self.change_target()
                        if self.total>0:
                            self.is_selected = True
                            self.__update_gizmos_trans()
                            self.__update_gizmos()
                        return

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
            model_x = self.gizmos_x_trans.trs
            model_y = self.gizmos_y_trans.trs
            model_z = self.gizmos_z_trans.trs

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
        elif self.mode==Mode.ROTATE:
            model_x = self.gizmos_x_R_trans.trs
            model_y = self.gizmos_y_R_trans.trs
            model_z = self.gizmos_z_R_trans.trs

            mesh_x = self.gizmos_x_R_mesh
            mesh_y = self.gizmos_y_R_mesh
            mesh_z = self.gizmos_z_R_mesh

            previous_distance = self.previous_distance

            #divide the Gizmos' meshes in smaller bounding boxes and test each one of them during the first iteration
            if self.selected_gizmo=='': # could be X, Y or Z

                # evaluate the distance from the ray origin to the gizmo's mesh for both X, Y and Z and determine which one is the closest
                # therefore, which one the user meant to pick
                x_intersects, x_in_point = self.testRayCircleIntersection(ray_origin,
                                                    ray_direction,
                                                    mesh_x,
                                                    model_x)
                if x_intersects:
                    x_distance = self.previous_distance
                else:
                    x_distance = 1000000.0
            
                y_intersects, y_in_point = self.testRayCircleIntersection(ray_origin,
                                                    ray_direction,
                                                    mesh_y,
                                                    model_y)
                if y_intersects:
                    y_distance = self.previous_distance
                else:
                    y_distance = 1000000.0
            
                z_intersects, z_in_point = self.testRayCircleIntersection(ray_origin,
                                                    ray_direction,
                                                    mesh_z,
                                                    model_z)
                if z_intersects:
                    z_distance = self.previous_distance
                else:
                    z_distance = 1000000.0


            # we are here, AFTER clicking and WHILE holding the mouse button
            elif self.selected_gizmo=='X':
                x_intersects, x_in_point = self.testRayBoundingBoxIntesection(ray_origin,ray_direction,
                                                                              self.xrot_min_bb,
                                                                              self.xrot_max_bb,
                                                                              model_x)

                if x_intersects:
                    x_distance = self.previous_distance
                    y_distance = 1000000.0
                    z_distance = 1000000.0
                else:
                    x_distance = 1000000.0

            elif self.selected_gizmo=='Y':
                y_intersects, y_in_point = self.testRayBoundingBoxIntesection(ray_origin,ray_direction,
                                                                              self.yrot_min_bb,
                                                                              self.yrot_max_bb,
                                                                              model_y)
                if y_intersects:
                    y_distance = self.previous_distance
                    x_distance = 1000000.0
                    z_distance = 1000000.0
                else:
                    y_distance = 1000000.0

            elif self.selected_gizmo=='Z':
                z_intersects, z_in_point = self.testRayBoundingBoxIntesection(ray_origin,ray_direction,
                                                                              self.zrot_min_bb,
                                                                              self.zrot_max_bb,
                                                                              model_z)
                if z_intersects:
                    z_distance = self.previous_distance
                    x_distance = 1000000.0
                    y_distance = 1000000.0
                else:
                    z_distance = 1000000.0

            

            #When the ray intersects with more than one gizmo apply rotation to the one closest to the ray origin
            if x_intersects and (x_distance > y_distance or x_distance > z_distance):
                x_intersects = False
            if y_intersects and (y_distance > x_distance or y_distance > z_distance):
                y_intersects = False
            if z_intersects and (z_distance > x_distance or z_distance > y_distance):
                z_intersects = False
            
            if self.selected_gizmo=='X':
                self.rotation_distance = previous_distance - x_distance
            if self.selected_gizmo=='Y':
                self.rotation_distance = previous_distance - y_distance
            if self.selected_gizmo=='Z':
                self.rotation_distance = previous_distance - z_distance

        if self.selected_gizmo=='X' or (self.selected_gizmo=='' and x_intersects):
            self.selected_gizmo = 'X'
            self.__transform_selected_entity(x_in_point)
        elif self.selected_gizmo=='Y' or (self.selected_gizmo==''  and y_intersects):
            self.selected_gizmo = 'Y'
            self.__transform_selected_entity(y_in_point)
        elif self.selected_gizmo=='Z' or (self.selected_gizmo==''and z_intersects):
            self.selected_gizmo = 'Z'
            self.__transform_selected_entity(z_in_point)
        
        if self.selected_trans is not None:
            self.showSelectedBB(self.selected_trans.parent.getChildByType("AABoundingBox"))

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
            elif self.selected_gizmo=='Z':
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
                    #if(diffZ==0.0):
                    #    diffZ = 0.01
                    self.previous_z = inter_point[2]
            self.__scale_selected(x=diffX,y=diffY,z=diffZ)
        elif self.mode==Mode.ROTATE:
            if self.selected_gizmo=='X':
                if self.picked==False:
                    self.picked = True
                    self.previous_x = inter_point[0]
                else:
                    diff = self.rotation_modifier * (self.previous_x - inter_point[0])/2
                    self.previous_x = inter_point[0]
                    self.__rotate_selected(_angle = diff, _axis = (0.0,0.0,1.0))
            elif self.selected_gizmo=='Y':
                if self.picked==False:
                    self.picked = True
                    self.previous_y = inter_point[0]
                else:
                    diff = -self.rotation_modifier * (self.previous_y - inter_point[0])/2
                    self.previous_y = inter_point[0]
                    self.__rotate_selected(_angle = diff, _axis = (0.0,1.0,0.0))
            elif self.selected_gizmo=='Z':
                if self.picked==False:
                    self.picked = True
                    self.previous_z = inter_point[2]
                else:
                    diff = -self.rotation_modifier * (self.previous_z - inter_point[2])
                    self.previous_z = inter_point[2]
                    self.__rotate_selected(_angle = diff, _axis = (1.0,0.0,0.0))
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
            Sets seld.previous_distance to the distance between the ray's origin and the intersection point
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
            
        #This is needed when the mouse is not hovering on a bounding box but the user is still holding the LMB
        self.previous_distance = tmin

        return True, self.intersection_point(tmin,ray_origin,ray_direction)
    
    def testRayCircleIntersection(self, ray_origin, ray_direction, mesh: RenderMesh, model):
        """
        Tests if a Ray intersects with a Rotation Gizmo
        Arguments:
            self: self
            ray_origin: Ray Starting Point
            ray_direction: Ray's Direction
            mesh: the mesh of a Rotation Gizmo
            model: a model matrix
        Returns:
            True if there is an intersection, False otherwise. Additionally returns the Intersection point
        """
        vertices = np.array(mesh.vertex_attributes[0],copy=True)
        indices = np.array(mesh.vertex_index[0],copy=True)

        for i in range(0,len(indices)-48,24):
            #for every 24 indices i have to find those that correspond to 8 unique vertices
            #from those unique vertices I will calculate a bounding box
            s = set()
            for j in range(i,i+23):
                s.add(indices[j])
            sub = np.empty(shape=[0,4])

            for index in s:
                sub = np.append(sub,vertices[index])
            
            sub = np.reshape(sub,(8,4))
            
            minbb, maxbb = self.calculate_bounding_box(sub)

            intersects, point = self.testRayBoundingBoxIntesection(ray_origin,ray_direction,minbb,maxbb,model)
            if intersects:
                return intersects, point
        
        return False, self.intersection_point(self.previous_distance,ray_origin,ray_direction)

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
        self.selected_trans.trs = util.translate(x,y,z) @ self.selected_trans.trs
        self.__update_gizmos_trans()
 
    def __rotate_selected(self,_angle=0.0,_axis=(1.0,0.0,0.0)):
        """
        Rotate Selected Element around a given axis on local space
        Arguments:
            self: self
            _angle: Rotation Angle
            _axis: axis to rotate
        Returns:
            None
        """
        selected = self.seperate_transformations[self.selected_comp]
        translation = self.__remove_rotation__(self.selected_trans.trs)

        #self.selected_trans.trs = self.selected_trans.trs @ util.rotate(angle=_angle,axis=_axis)
        self.selected_trans.trs = translation @ util.rotate(angle=_angle,axis=_axis) @ util.inverse(translation) @ self.selected_trans.trs
        selected.rotation = selected.rotation @ util.rotate(angle=_angle,axis=_axis)

        self.rotation = self.rotation @ util.rotate(angle=_angle,axis=_axis)
        
        self.__update_gizmos_trans()

    def __scale_selected(self,x=1.0,y=1.0,z=1.0):
        """
        Scale Selected Element on local space
        Arguments:
            self: self
            x: Scaling on x-axis
            y: Scaling on y-axis
            z: Scaling on z-axis
        Returns:
            None
        """
        selected = self.seperate_transformations[self.selected_comp]

        self.selected_trans.trs = self.selected_trans.trs @ util.scale(x,y,z)
        #self.seperate_transformations[self.selected_comp].scaling += util.vec(x-1.0,y-1.0,z-1.0)
        selected.scaling *= util.vec(x,y,z)
        self.__update_gizmos_trans()

    def __update_gizmos_trans(self):
        """
        
        """
        scaling = self.seperate_transformations[self.selected_comp].scaling
        #rotation = self.seperate_transformations[self.selected_comp].rotation

        #selected Entity's local-2-world without rotation or scaling
        #Used for Translation and Scaling Gizmos
        no_rotation = self.__remove_rotation__(self.selected_trans.l2world)

        self.gizmos_x_trans.trs = no_rotation
        self.gizmos_y_trans.trs = no_rotation
        self.gizmos_z_trans.trs = no_rotation

        self.gizmos_x_S_line_trans.trs = no_rotation @ util.scale(scaling[0],1.0,1.0)
        self.gizmos_y_S_line_trans.trs = no_rotation @ util.scale(1.0,scaling[1],1.0)
        self.gizmos_z_S_line_trans.trs = no_rotation @ util.scale(1.0,1.0,scaling[2])

        #translate the Scaling cubes based on Selected Entity's current scaling
        x_t = util.translate(x=scaling[0]-1.0)
        y_t = util.translate(y=scaling[1]-1.0)
        z_t = util.translate(z=scaling[2]-1.0)

        self.gizmos_x_S_cube_trans.trs = no_rotation @ x_t
        self.gizmos_y_S_cube_trans.trs = no_rotation @ y_t
        self.gizmos_z_S_cube_trans.trs = no_rotation @ z_t

        r_gizmos = no_rotation @ self.rotation
        self.gizmos_x_R_trans.trs = r_gizmos
        self.gizmos_y_R_trans.trs = r_gizmos
        self.gizmos_z_R_trans.trs = r_gizmos