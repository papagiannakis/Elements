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
from OpenGL.GLU import gluUnProject

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
        self.inv_projection = util.inverse(self.projection)
        self.view = View
        self.inv_view = util.inverse(self.view)
        self.is_selected = False
        self.selected_trs = None
        self.selected_mesh = None
        self.selected_comp = "None"
        self.gizmos_comps = set(["Gizmos_X","Gizmos_X_trans","Gizmos_X_mesh",
                                "Gizmos_Y","Gizmos_Y_trans","Gizmos_Y_mesh",
                                "Gizmos_Z","Gizmos_Z_trans","Gizmos_Z_mesh"])

        self.cameraInUse = ""
        self.screen_width = 1.0
        self.screen_height = 1.0
        self.fov = 1.0
        self.aspect_ratio = 1.0
        self.near = 1.0
        self.far = 1.0

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
        
        self.x_min_bb, self.x_max_bb = self.calculate_bounding_box(self.gizmos_x_mesh)
        self.y_min_bb, self.y_max_bb = self.calculate_bounding_box(self.gizmos_y_mesh)
        self.z_min_bb, self.z_max_bb = self.calculate_bounding_box(self.gizmos_z_mesh)

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
        self.inv_view = util.inverse(self.view)

    def set_camera_in_use(self,camera: str):
        if self.cameraInUse=="":
            self.total = self.total - 1
        self.cameraInUse = camera

    def update_projection(self, Proj):
        self.projection = Proj
        self.inv_projection = util.inverse(self.projection)
    
    def update_projection_args(self,window_width,window_height,fov):
        """
        """
        self.screen_width = window_width
        self.screen_height = window_height
        self.fov = fov
        self.aspect_ratio = self.screen_width/self.screen_height

    def calculate_bounding_box(self,mesh: RenderMesh):
        """
        A simple method that calculates a bounding box based on given mesh's vertices

        """
        vertices = mesh.vertex_attributes[0]
        minbb = util.vec(vertices[0][0],vertices[0][0],vertices[0][2])
        maxbb = util.vec(vertices[0][0],vertices[0][0],vertices[0][2])
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

    def raycast(self):
        """
        Raycast from mouse position
        Arguments:
            self: that's me
        Returns:
            None

        Source: http://www.opengl-tutorial.org/miscellaneous/clicking-on-objects/picking-with-custom-ray-obb-function/
        """

        #aspect_ratio = self.screen_width/self.screen_height
        #x = (2 * ( (self.mouse_x.value+0.5)/self.screen_width)-1) * tan(self.fov/2*pi/180) * aspect_ratio
        #y = (1-2*((self.mouse_y.value+0.5)/self.screen_height)) * tan(self.fov/2*pi/180)
        x = 2 * (self.mouse_x.value/self.screen_width - 0.5)
        y = 2 * (self.mouse_y.value/self.screen_height - 0.5)

        ray_start = util.vec(x,y,1.0,1.0) #z is 1 or -1, I don't know which one is right yet
        ray_end = util.vec(x,y,0.0,1.0)

        ray_start_Camera = self.inv_projection @ ray_start
        ray_start_Camera = ray_start_Camera/ray_start_Camera[3]

        ray_start_World = self.inv_view @ ray_start_Camera
        ray_start_World = ray_start_World/ray_start_World[3]

        ray_end_Camera = self.inv_projection @ ray_end
        ray_end_Camera = ray_end_Camera/ray_end_Camera[3]

        ray_end_world = self.inv_view @ ray_end_Camera
        ray_end_world = ray_end_world/ray_end_world[3]

        #rayDirection = util.vec(x,y,1) # -1?
        #rayDirection = util.normalise(rayDirection)
        ray_dir_world = ray_end_world - ray_start_World
        ray_dir_world = util.normalise(ray_dir_world)

        #print("Origin: ",ray_start_World)
        #print("Direction: ",ray_dir_world)

        #Delete these later if not needed
        ray_start_World = util.vec(ray_start_World[0],
                                   ray_start_World[1],
                                   ray_start_World[2])
        ray_dir_world = util.vec(ray_dir_world[0],
                                 ray_dir_world[1],
                                 ray_dir_world[2])

        #trials to check whether the program understands an intersection
        #to be deleted after the gizmos can be intersected correctly
        if self.selected_trs is not None and self.testRayBoundingBoxIntesection(ray_start_World,
                                              ray_dir_world,
                                              self.x_min_bb,
                                              self.x_max_bb,self.gizmos_x_trans.trs):
            print("intersected X")
        if self.selected_trs is not None and self.testRayBoundingBoxIntesection(ray_start_World,
                                              ray_dir_world,
                                              self.y_min_bb,
                                              self.y_max_bb,self.gizmos_y_trans.trs):
            print("intersected Y")
        if self.selected_trs is not None and self.testRayBoundingBoxIntesection(ray_start_World,
                                              ray_dir_world,
                                              self.z_min_bb,
                                              self.z_max_bb,self.gizmos_z_trans.trs):
            print("intersected Z")

        if self.selected_mesh is not None:
            #let's see if the program can understand if the mouse is hoveting over an element's bounding box
            min,max = self.calculate_bounding_box(self.selected_mesh)
            if self.selected_trs is not None and self.testRayBoundingBoxIntesection(ray_start_World,
                                                                                    ray_dir_world,
                                                                                    min,
                                                                                    max,
                                                                                    self.selected_trs.trs):
                print("selected object intersected")

    def testRayBoundingBoxIntesection(self,ray_origin,ray_direction,minbb,maxbb,model):
        """
        A method that tests if a ray starting from the mouse position is intersecting with a given bounding box
        Arguments:
            self: that's me
            ray_origin: the location the ray starts from in world space
            ray_direction: the direction of the ray
            minbb: minimum coordinates of an element's bounding box
            maxbb: maximum coordinates of an element's bounding box
            model: the element's model matrix
        """
        tmin = 0.0
        tmax = 100000.0

        bb_pos_world = util.vec(model[3][0],model[3][1],model[3][2])
        delta = bb_pos_world - ray_origin

        x_axis = util.vec(model[0][0],model[0][1],model[0][2])
        y_axis = util.vec(model[1][0],model[1][1],model[1][2])
        z_axis = util.vec(model[2][0],model[2][1],model[2][2])

        # Test intersection with the 2 planes perpendicular to the bounding box's X axis

        e = np.dot(x_axis,delta)
        f = np.dot(ray_direction,x_axis)

        if abs(f)>0.001 :
            t1 = (e+minbb[0])/f 
            t2 = (e+maxbb[0])/f 

            if t1 > t2 :
                tmp = t1
                t1 = t2
                t2 = tmp
            
            if t2 < tmax:
                tmax = t2
            if t1 > tmin:
                tmin = t1
            
            if tmax < tmin:
                return False
            
        else:
            if -e+minbb[0] > 0.0 or -e+maxbb[0] < 0.0:
                return False
            
        # Test intersection with the 2 planes perpendicular to the bounding box's Y axis

        tmin = 0.0
        tmax = 100000.0

        e = np.dot(y_axis,delta)
        f = np.dot(ray_direction,y_axis)

        if abs(f) > 0.001 :
            t1 = (e+minbb[1])/f 
            t2 = (e+maxbb[1])/f 

            if t1 > t2 :
                tmp = t1
                t1 = t2
                t2 = tmp
            
            if t2 < tmax:
                tmax = t2
            if t1 > tmin:
                tmin = t1
            
            if tmin > tmax:
                return False
            
        else:
            if -e+minbb[1] > 0.0 or -e+maxbb[1] < 0.0:
                return False
            
        # Test intersection with the 2 planes perpendicular to the bounding box's Z axis

        tmin = 0.0
        tmax = 100000.0

        e = np.dot(z_axis,delta)
        f = np.dot(ray_direction,z_axis)

        if abs(f) > 0.001 :
            t1 = (e+minbb[2])/f #intersection with left plane
            t2 = (e+maxbb[2])/f #intersection with right plane

            if t1 > t2 :
                tmp = t1
                t1 = t2
                t2 = tmp
            
            if t2 < tmax:
                tmax = t2
            if t1 > tmin:
                tmin = t1
            
            if tmax < tmin:
                return False
            
        else:
            if -e+minbb[2] > 0.0 or -e+maxbb[2] < 0.0:
                return False
        return True



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

    def scale_selected(self,x=1.0,y=1.0,z=1.0):
        """
        Scale Selected Element
        Arguments:
            self: that's me
            x: Scaling on x-axis
            y: Scaling on y-axis
            z: Scaling on z-axis
        Returns:
            None
        """
        pass
