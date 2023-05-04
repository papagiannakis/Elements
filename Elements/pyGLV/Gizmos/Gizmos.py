from Elements.pyGLV.GL.Scene import Scene
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform
import Elements.pyECSS.utilities as util
from Elements.pyECSS.Component import BasicTransform, RenderMesh, Component
from Elements.pyGLV.GL.VertexArray import VertexArray
import sdl2 as sdl
from Elements.pyGLV.GL.Shader import Shader, ShaderGLDecorator
from ctypes import c_int, byref
import OpenGL.GL as gl
import numpy as np
from math import tan, pi
import imgui

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
        self.is_selected = False
        self.selected_trs = None
        self.selected_mesh = None
        self.selected_comp = "None"
        self.gizmos_comps = set(["Gizmos_X","Gizmos_X_trans","Gizmos_X_mesh",
                                "Gizmos_Y","Gizmos_Y_trans","Gizmos_Y_mesh",
                                "Gizmos_Z","Gizmos_Z_trans","Gizmos_Z_mesh"])

        self.cameraInUse = ""
        self.fov = 0.0
        self.aspect_ratio = 0.0
        self.near = 0.0
        self.far = 0.0

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
        
        self.count_components()        

    def change_target(self):
        """
        Change selected entity
        Arguments:
            self: that's me
        Returns:
            None
        """
        self.selected = self.selected+1
        count = self.selected
        if(count>self.total):
            count = 1
            self.selected = 1

        for component in self.scene.world.root:
            if component is not None:
                parentname = component.parent.name
                if component.getClassName()=="BasicTransform" and component.name not in self.gizmos_comps and parentname!=self.cameraInUse:
                    count = count-1
                    if(count==0):
                        self.selected_trs = component
                        self.selected_comp = self.selected_trs.parent.name
                        children = self.selected_trs.getNumberOfChildren()

                        for i in range(children):
                            child = self.selected_trs.getChild(i)
                            if child.getClassName()=="RenderMesh":
                                self.selected_mesh = child
                                print(child)
                                break
                        break

    def update_mouse_position(self):
        """
        Update mouse position and state
        Arguments:
            self: that's me
        Returns:
            None
        """
        self.mouse_state = sdl.mouse.SDL_GetMouseState(byref(self.mouse_x), byref(self.mouse_y))
        self.raycast()
        #print("Mouse Position: (",self.mouse_x.value,",",self.mouse_y.value,")")
        #print("Left Mouse Button state: ",self.mouse_state)

    def count_components(self):
        """
        Count transform components in the scene
        Arguments:
            self: that's me
        Returns:
            None
        """
        for component in self.scene.world.root:
            if component is not None and component.getClassName()=="BasicTransform" and component.name not in self.gizmos_comps:
                self.total = self.total + 1

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
            if self.total>0:
                self.is_selected = True
                self.gizmos_x_trans.trs = self.selected_trs.trs
                self.gizmos_y_trans.trs = self.selected_trs.trs
                self.gizmos_z_trans.trs = self.selected_trs.trs
        elif not self.key_states[sdl.SDL_SCANCODE_TAB] and self.key_down:
            #print('TAB key released')
            self.key_down = False
        #if self.key_states[sdl.SDL_SCANCODE_A] and self.selected_trs is not None:
        #    print("Translating selected")
        #    self.translate_selected(x=0.1)
    
    def update_gizmos(self):
        """
        Update Gizmos uniform variables
        Arguments:
            self: that's me
        Returns:
            None
        """
        if self.is_selected:
            model_x = self.gizmos_x_trans.trs
            model_y = self.gizmos_y_trans.trs
            model_z = self.gizmos_z_trans.trs
            mvp_x = self.projection @ self.view @ model_x
            mvp_y = self.projection @ self.view @ model_y
            mvp_z = self.projection @ self.view @ model_z
            self.gizmos_x_shader.setUniformVariable(key='modelViewProj', value=mvp_x, mat4=True)
            self.gizmos_y_shader.setUniformVariable(key='modelViewProj', value=mvp_y, mat4=True)
            self.gizmos_z_shader.setUniformVariable(key='modelViewProj', value=mvp_z, mat4=True)

    def update_imgui(self):
        imgui.set_next_window_size(200.0,100.0)
        imgui.begin("Selected Entity")
        imgui.text_ansi(self.selected_comp)
        imgui.end()

    def update_view(self, View):
        self.view = View

    def set_camera_in_use(self,camera: str):
        self.cameraInUse = camera
        self.total = self.total - 1

    def update_projection(self, Proj):
        self.projection = Proj
    
    def raycast(self):
        """
        Raycast from mouse position
        Arguments:
            self: that's me
        Returns:
            None
        """
        imagewidth = 1024.0 #modifications
        imageheight = 768.0 #modifications
        fov = 50.0 #modifications
        aspectratio = imagewidth/imageheight #modifications
        x = (2 * ( (self.mouse_x.value+0.5)/imagewidth)-1) * tan(fov/2*pi/180) * aspectratio
        y = (1-2*((self.mouse_y.value+0.5)/imageheight)) * tan(fov/2*pi/180)
        rayDirection = util.vec(x,y,1) # -1?
        rayDirection = util.normalise(rayDirection)
        #print(rayDirection)
    
    def translate_selected(self,x=0.0,y=0.0,z=0.0):
        """
        Translate Selected Element
        Arguments:
            self: that's me
            x: x value
            y: y value
            z: z value
        Returns:
            None
        """
        self.selected_trs.trs = self.selected_trs.trs @ util.translate(x,y,z)
        #selected = self.scene.world.root.getChild(self.selected).getChild(self.selected_pos)
        #selected.trs = selected.trs @ util.translate(x,y,z)
        #selected_trs = self.scene.world.root.getChild(self.selected).getChild(self.selected_pos).trs
        #self.scene.world.root.getChild(self.selected).getChild(self.selected_pos).trs = selected_trs @ util.translate(x,y,z)
    
    def rotate_selected(self,angle=0.0,axis=(1.0,0.0,0.0)):
        """
        Rotate Selected Element
        Arguments:
            self: that's me
            angle: Rotation Angle
            axis: axis to rotate
        Returns:
            None
        """
        pass
        #selected_trs = self.scene.world.root.getChild(self.selected).getChild(self.selected_pos).trs
