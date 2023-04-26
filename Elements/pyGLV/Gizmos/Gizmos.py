from Elements.pyGLV.GL.Scene import Scene
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform
import Elements.pyECSS.utilities as util
from Elements.pyECSS.Component import BasicTransform, RenderMesh
from Elements.pyGLV.GL.VertexArray import VertexArray
import sdl2 as sdl
from Elements.pyGLV.GL.Shader import Shader, ShaderGLDecorator
from ctypes import c_int, byref
import OpenGL.GL as gl
import numpy as np

class Gizmos:
    GIZMOS_X=np.array([
    [0.0, 0.0, 0.0, 1.0],
    [1.5, 0.0, 0.0, 1.0]
    ], dtype=np.float32)

    GIZMOS_Y=np.array([
    [0.0, 0.0, 0.0, 1.0],
    [0.0, 1.5, 0.0, 1.0]
    ]  ,dtype=np.float32)

    GIZMOS_Z=np.array([
    [0.0, 0.0, 0.0, 1.0],
    [0.0, 0.0, 1.5, 1.0]
    ], dtype=np.float32)

    COLOR_X = np.array([
    [1.0, 0.0, 0.0, 1.0],
    [1.0, 0.0, 0.0, 1.0]
    ], dtype=np.float32)

    COLOR_Y = np.array([
    [0.0, 1.0, 0.0, 1.0],
    [0.0, 1.0, 0.0, 1.0]
    ], dtype=np.float32)

    COLOR_Z = np.array([
    [0.0, 0.0, 1.0, 1.0],
    [0.0, 0.0, 1.0, 1.0]
    ], dtype=np.float32)

    GIZMOS_INDEX = np.array((0,1), np.uint32)

    def __init__(self,rootEntity: Entity,Projection, View):
        sdl.ext.init()
        self.scene = Scene()
        self.selected = -1
        self.selected_pos = -1
        self.mouse_x, self.mouse_y = c_int(0), c_int(0)
        self.mouse_state = 0 #LMB not clicked
        self.key_states = sdl.SDL_GetKeyboardState(None)
        self.key_down = False
        self.trs_table = {}
        self.projection = Projection
        self.view = View
        self.is_selected = False

        self.gizmos_x = self.scene.world.createEntity(Entity(name="Gizmos_X"))
        self.scene.world.addEntityChild(rootEntity, self.gizmos_x)
        self.gizmos_x_trans = self.scene.world.addComponent(self.gizmos_x, BasicTransform(name="Gizmos_X_trans", trs=util.identity()))
        self.gizmos_x_mesh = self.scene.world.addComponent(self.gizmos_x, RenderMesh(name="Gizmos_X_mesh"))
        self.gizmos_x_mesh.vertex_attributes.append(Gizmos.GIZMOS_X) 
        self.gizmos_x_mesh.vertex_attributes.append(Gizmos.COLOR_X)
        self.gizmos_x_mesh.vertex_index.append(Gizmos.GIZMOS_INDEX)
        self.gizmos_x_vArray = self.scene.world.addComponent(self.gizmos_x, VertexArray(primitive=gl.GL_LINES))
        self.gizmos_x_shader = self.scene.world.addComponent(self.gizmos_x, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))

        self.gizmos_y = self.scene.world.createEntity(Entity(name="Gizmos_Y"))
        self.scene.world.addEntityChild(rootEntity, self.gizmos_y)
        self.gizmos_y_trans = self.scene.world.addComponent(self.gizmos_y, BasicTransform(name="Gizmos_Y_trans", trs=util.identity()))
        self.gizmos_y_mesh = self.scene.world.addComponent(self.gizmos_y, RenderMesh(name="Gizmos_Y_mesh"))
        self.gizmos_y_mesh.vertex_attributes.append(Gizmos.GIZMOS_Y) 
        self.gizmos_y_mesh.vertex_attributes.append(Gizmos.COLOR_Y)
        self.gizmos_y_mesh.vertex_index.append(Gizmos.GIZMOS_INDEX)
        self.gizmos_y_vArray = self.scene.world.addComponent(self.gizmos_y, VertexArray(primitive=gl.GL_LINES))
        self.gizmos_y_shader = self.scene.world.addComponent(self.gizmos_y, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))

        self.gizmos_z = self.scene.world.createEntity(Entity(name="Gizmos_Z"))
        self.scene.world.addEntityChild(rootEntity, self.gizmos_z)
        self.gizmos_z_trans = self.scene.world.addComponent(self.gizmos_z, BasicTransform(name="Gizmos_Z_trans", trs=util.identity()))
        self.gizmos_z_mesh = self.scene.world.addComponent(self.gizmos_z, RenderMesh(name="Gizmos_Z_mesh"))
        self.gizmos_z_mesh.vertex_attributes.append(Gizmos.GIZMOS_Z) 
        self.gizmos_z_mesh.vertex_attributes.append(Gizmos.COLOR_Z)
        self.gizmos_z_mesh.vertex_index.append(Gizmos.GIZMOS_INDEX)
        self.gizmos_z_vArray = self.scene.world.addComponent(self.gizmos_z, VertexArray(primitive=gl.GL_LINES))
        self.gizmos_z_shader = self.scene.world.addComponent(self.gizmos_z, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))

        self.index_components(self.scene)

    def change_target(self):
        """
        Change selected entity
        Arguments:
            self: that's me
        Returns:
            None
        """
        entities = self.scene.world.root.getNumberOfChildren()

        if self.selected<0 or self.selected==entities-1:
            self.selected = 0
        else:
            self.selected +=1
        self.selected_pos = self.trs_table[self.selected]

    def update_mouse_position(self):
        """
        Update mouse position and state
        Arguments:
            self: that's me
        Returns:
            None
        """
        self.mouse_state = sdl.mouse.SDL_GetMouseState(byref(self.mouse_x), byref(self.mouse_y))
        #print("Mouse Position: (",self.mouse_x.value,",",self.mouse_y.value,")")
        #print("Left Mouse Button state: ",self.mouse_state)

    def index_components(self,
                         scene: Scene):
        """
        Create an indexing for each entity's "BasicTransform" and "RenderMesh" components' position
        Arguments:
            self: that's me
            scene: Scene component that stores all entities
        Returns:
            None
        """
        entities = scene.world.root.getNumberOfChildren()
        for i in range(entities):
            entity = scene.world.root.getChild(i)
            children = entity.getNumberOfChildren()
            for j in range(children):
                comp = entity.getChild(j)
                if comp is not None and comp.getClassName()=="BasicTransform":
                    self.trs_table[i] = j
                    break
    
    def get_keyboard_Event(self):
        """
        When TAB is pressed change selected entity
        Arguments:
            self: that's me
        Returns:
            None
        """
        if self.key_states[sdl.SDL_SCANCODE_TAB] and not self.key_down:
            #print('TAB key pressed')
            self.key_down = True
            self.change_target()
            self.is_selected = True
            print(self.scene.world.root.getChild(self.selected))
            print(self.scene.world.root.getChild(self.selected).getChild(self.selected_pos).trs)
            self.gizmos_x_trans.trs = self.scene.world.root.getChild(self.selected).getChild(self.selected_pos).trs
            self.gizmos_y_trans.trs = self.scene.world.root.getChild(self.selected).getChild(self.selected_pos).trs
            self.gizmos_z_trans.trs = self.scene.world.root.getChild(self.selected).getChild(self.selected_pos).trs
            self.update_gizmos()
        elif not self.key_states[sdl.SDL_SCANCODE_TAB] and self.key_down:
            #print('TAB key released')
            self.key_down = False
    
    def update_gizmos(self):
        """
        Update Gizmos uniform variables
        Arguments:
            self: that's me
        Returns:
            None
        """
        if self.is_selected:
            #model = self.scene.world.root.getChild(self.selected).getChild(self.selected_pos).trs
            model = self.gizmos_x_trans.trs #hmm
            mvp = self.projection @ self.view @ model
            self.gizmos_x_shader.setUniformVariable(key='modelViewProj', value=mvp, mat4=True)
            self.gizmos_y_shader.setUniformVariable(key='modelViewProj', value=mvp, mat4=True)
            self.gizmos_z_shader.setUniformVariable(key='modelViewProj', value=mvp, mat4=True)

    def update_view(self, View):
        self.view = View

    def update_projection(self, Proj):
        self.projection = Proj