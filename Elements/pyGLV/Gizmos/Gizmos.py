from Elements.pyGLV.GL.Scene import Scene
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform
import Elements.pyECSS.utilities as util
from Elements.pyECSS.Component import BasicTransform, RenderMesh
from Elements.pyGLV.GL.VertexArray import VertexArray
import sdl2 as sdl
from OpenGL.GL import GL_LINES, GL_POINT
from Elements.pyGLV.GL.Shader import Shader, ShaderGLDecorator
from ctypes import c_int, byref
import numpy as np
import imgui
import enum

class Mode(enum.Enum):
    TRANSLATE="Translate"
    ROTATE="Rotate"
    SCALE="Scale"


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
    
    __model_x = util.rotate(angle=90,axis=(0.0,0.0,1.0))
    __model_y = util.identity()
    __model_z = util.rotate(angle=-90,axis=(1.0,0.0,0.0))
    
    VERTEX_GIZMOS_X = VERTEX_GIZMOS_X @ util.scale(0.7,0.7,0.7)
    VERTEX_GIZMOS_Y = VERTEX_GIZMOS_Y @ util.scale(0.7,0.7,0.7)
    VERTEX_GIZMOS_Z = VERTEX_GIZMOS_Z @ util.scale(0.7,0.7,0.7)

    #VERTEX_GIZMOS_X = VERTEX_GIZMOS @ __model_x
    #VERTEX_GIZMOS_Y = VERTEX_GIZMOS #@ __model_y
    #VERTEX_GIZMOS_Z = VERTEX_GIZMOS #@ __model_z

    #for i in range(len(VERTEX_GIZMOS_X)): #same length
    #    VERTEX_GIZMOS_X[i] = VERTEX_GIZMOS_X[i]/VERTEX_GIZMOS_X[i][3]
    #    VERTEX_GIZMOS_Y[i] = VERTEX_GIZMOS_Y[i]/VERTEX_GIZMOS_Y[i][3]
    #    VERTEX_GIZMOS_Z[i] = VERTEX_GIZMOS_Z[i]/VERTEX_GIZMOS_Z[i][3]

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
        if(Projection is not None):
            self.inv_projection = util.inverse(Projection)
        if(View is not None):
            self.inv_view = util.inverse(View)
        self.is_selected = False
        self.selected_trs = None
        self.selected_mesh = None
        self.selected_comp = "None"
        self.mode = Mode.TRANSLATE
        self.gizmos_comps = set(["Gizmos_X","Gizmos_X_trans","Gizmos_X_mesh",
                                "Gizmos_Y","Gizmos_Y_trans","Gizmos_Y_mesh",
                                "Gizmos_Z","Gizmos_Z_trans","Gizmos_Z_mesh",
                                "ray","ray_trans","ray_mesh"])

        self.cameraInUse = ""
        self.screen_width = 1024.0
        self.screen_height = 768.0

        self.picked = False
        self.LMB_pressed = True
        self.selected_gizmo = ''
        self.previous_x = 0.0
        self.previous_y = 0.0
        self.previous_z = 0.0

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
        
        self.x_min_bb, self.x_max_bb = self.calculate_bounding_box(self.gizmos_x_mesh)
        self.y_min_bb, self.y_max_bb = self.calculate_bounding_box(self.gizmos_y_mesh)
        self.z_min_bb, self.z_max_bb = self.calculate_bounding_box(self.gizmos_z_mesh)

        self.count_components()

    def reset_to_None(self):
        """
        Resets to initial state
        Arguments:
            self: self
        Returns:
            None
        """
        self.is_selected = False
        self.selected_trs = None
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
                        self.selected_trs = component
                        self.selected_comp = self.selected_trs.parent.name
                        children = component.parent.getNumberOfChildren()
                        self.selected_mesh = None
                        for i in range(children):
                            child = component.parent.getChild(i)
                            if child is not None and child.getClassName()=="RenderMesh":
                                self.selected_mesh = child
                                break
                        break

    def update_mouse_position(self):
        """
        Update mouse position, mouse state and Raycast
        Arguments:
            self: self
        Returns:
            None
        """
        self.mouse_state = sdl.mouse.SDL_GetMouseState(byref(self.mouse_x), byref(self.mouse_y))
        #Raycast only when LMB is pressed
        #if Last time LMB was pressed raycast didn't intersect, then do not raycast until LMB is released

        #if self.mouse_state==1 and self.LMB_pressed and self.selected_trs is not None:
            #self.raycast()
        if self.key_states[sdl.SDL_SCANCODE_B] and self.LMB_pressed and self.selected_trs is not None:
            self.raycast()
        else:
            self.picked = False
            self.LMB_pressed = True
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

    def get_keyboard_Event(self):
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
                

                self.gizmos_x_trans.l2world = self.selected_trs.l2world
                self.gizmos_y_trans.l2world = self.selected_trs.l2world
                self.gizmos_z_trans.l2world = self.selected_trs.l2world
                #self.gizmos_x_trans.l2world = self.selected_trs.trs
                #self.gizmos_y_trans.l2world = self.selected_trs.trs
                #self.gizmos_z_trans.l2world = self.selected_trs.trs

        elif not self.key_states[sdl.SDL_SCANCODE_TAB] and self.key_down:
            self.key_down = False

        if self.key_states[sdl.SDL_SCANCODE_T]:
            self.mode = Mode.TRANSLATE
        if self.key_states[sdl.SDL_SCANCODE_R]:
            self.mode = Mode.ROTATE
        if self.key_states[sdl.SDL_SCANCODE_S]:
            self.mode = Mode.SCALE
    
    def update_gizmos(self):
        """
        Update Gizmos uniform variables
        Arguments:
            self: self
        Returns:
            None
        """
        if self.is_selected:
            #model_x = self.selected_trs.trs @ self.model_x
            #model_y = self.selected_trs.trs @ self.model_y
            #model_z = self.selected_trs.trs @ self.model_z

            model_x = self.gizmos_x_trans.l2world
            model_y = self.gizmos_y_trans.l2world
            model_z = self.gizmos_z_trans.l2world
            
            mvp_x = self.projection @ self.view @ model_x
            mvp_y = self.projection @ self.view @ model_y
            mvp_z = self.projection @ self.view @ model_z
            self.gizmos_x_shader.setUniformVariable(key='modelViewProj', value=mvp_x, mat4=True)
            self.gizmos_y_shader.setUniformVariable(key='modelViewProj', value=mvp_y, mat4=True)
            self.gizmos_z_shader.setUniformVariable(key='modelViewProj', value=mvp_z, mat4=True)

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

    def calculate_bounding_box(self,mesh: RenderMesh):
        """
        A simple method that calculates an axis aligned bounding box using a given mesh's vertices
        Arguments:
            self: self
            mesh: A RenderMesh component
        Returns
            minbb: minimum bounding box coordinates
            maxbb: maximum bounding box coordinates
        """
        vertices = mesh.vertex_attributes[0]

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
    
    def calculate_bounding_boxV2(self,mesh: RenderMesh,Model):
        """
        A simple method that calculates an axis aligned bounding box using a given mesh's vertices
        Arguments:
            self: self
            vertices: the vertices of a mesh
            Model: Model Matrix of a component
        Returns
            minbb: minimum bounding box coordinates
            maxbb: maximum bounding box coordinates
        """
        vertices = mesh.vertex_attributes[0] @ Model
        for i in range(len(vertices)):
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

    def calculate_bounding_boxV3(self,minbb,maxbb,Model):
        """
        A simple method that calculates an axis aligned bounding box using a given mesh's vertices
        Arguments:
            self: self
            ver: the vertices of a mesh
            Model: Model Matrix of a component
        Returns
            minbb: minimum bounding box coordinates
            maxbb: maximum bounding box coordinates
        """
        vertices = np.array([[minbb[0],minbb[1],minbb[2],1.0],
                             [minbb[0],minbb[1],maxbb[2],1.0],
                             [maxbb[0],minbb[1],minbb[2],1.0],
                             [maxbb[0],minbb[1],maxbb[2],1.0],
                             [minbb[0],maxbb[1],minbb[2],1.0],
                             [maxbb[0],maxbb[1],minbb[2],1.0],
                             [minbb[0],maxbb[1],maxbb[2],1.0],
                             [maxbb[0],maxbb[1],maxbb[2],1.0]],dtype=np.float32)
        
        vertices = vertices @ Model
        
        
        for i in range(len(vertices)):
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

    def raycast(self):
        """
        Raycast from mouse position
        Arguments:
            self: self
        Returns:
            None

        Source: http://www.opengl-tutorial.org/miscellaneous/clicking-on-objects/picking-with-custom-ray-obb-function/
        """

        #mouse position in normalized device coordinates

        x = 2.0 * (self.mouse_x.value/self.screen_width - 0.5)
        y = -2.0 * (self.mouse_y.value/self.screen_height - 0.5)
        
        #x = 2.0 * (self.mouse_x.value/self.screen_width - 0.5)
        #y = 2.0 * (self.mouse_y.value/self.screen_height - 0.5)
        
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
        
        ray_origin = util.vec(ray_start_World[0],ray_start_World[1],ray_start_World[2])
        ray_direction = util.normalise(ray_dir_world)

        model_x = self.gizmos_x_trans.l2world
        model_y = self.gizmos_y_trans.l2world
        model_z = self.gizmos_z_trans.l2world

        if self.selected_trs is not None:

            if self.selected_gizmo=='X' or (self.selected_gizmo=='' and self.testRayBoundingBoxIntesection(ray_origin,
                                                ray_direction,
                                                self.x_min_bb,
                                                self.x_max_bb,
                                                model_x)):
                print("intersected X Gizmo")
                self.selected_gizmo = 'X'
            elif self.selected_gizmo=='Y' or (self.selected_gizmo==''  and self.testRayBoundingBoxIntesection(ray_origin,
                                                ray_direction,
                                                self.y_min_bb,
                                                self.y_max_bb,
                                                model_y)):
                print("intersected Y Gizmo")
                self.selected_gizmo = 'Y'
            elif self.selected_gizmo=='Z' or (self.selected_gizmo==''and self.testRayBoundingBoxIntesection(ray_origin,
                                                ray_direction,
                                                self.z_min_bb,
                                                self.z_max_bb,
                                                model_z)):
                print("intersected Z Gizmo")
                self.selected_gizmo = 'Z'

                """
                model = model_z
                bb_pos_world = util.vec(model[3][0],model[3][1],model[3][2])
                z_axis = util.vec(model[2][0],model[2][1],model[2][2])
                min,max = self.calculate_tmin_tmax(ray_origin,
                                                ray_direction,
                                                self.z_min_bb, #self.z_min_bb
                                                self.z_max_bb, #self.z_max_bb
                                                z_axis,bb_pos_world)
                
                if self.picked==False:
                    self.picked=True
                    self.previous_z = min #min or max
                else:

                    diff = min - self.previous_z #min or max
                    #diff =  max - self.previous_z #min or max
                    self.previous_z = min #min or max

                    #TODO: use correct Transformation
                    self.translate_selected(z=diff)
                    self.update_gizmos()
                """
                    
            else:
                self.LMB_pressed = False

    def calculate_tmin_tmax(self,ray_origin,ray_direction,minbb,maxbb,axis,bb_position):
        """
        Calculate a ray's intersection points with the bounding box
        Used for computing the difference from a starting point
        Arguments:
            self: self
            ray_origin: ray's starting point
            ray_direction: ray's direction
            minbb: minimum bounding box coordinates
            maxbb maximum bounding box coordinates
            axis: local to world  model matrix
            bb_position: bounding box position
        Returns:
            tmin: near intersection
            tmax: far intersection 
        """
        tmin = 0.0
        tmax = 100000.0

        delta = bb_position - ray_origin

        e = np.dot(axis,delta)
        f = np.dot(ray_direction,axis)

        t1 = (e+minbb[0])/f 
        t2 = (e+maxbb[0])/f 

        if t1 > t2 :
            t1, t2 = t2, t1
            
        if t2 < tmax:
            tmax = t2
        if t1 > tmin:
            tmin = t1

        return tmin,tmax

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
            True if there is an intersection, False otherwise
            
        Source: http://www.opengl-tutorial.org/miscellaneous/clicking-on-objects/picking-with-custom-ray-obb-function/
        """
        tmin = 0.0
        tmax = 100000.0

        ################
        #bb_pos_world = util.vec(model[3][0],model[3][1],model[3][2])
        #delta = bb_pos_world - ray_origin

        #x_axis = util.vec(model[0][0],model[0][1],model[0][2])
        #y_axis = util.vec(model[1][0],model[1][1],model[1][2])
        #z_axis = util.vec(model[2][0],model[2][1],model[2][2])
        ############################

        ray_origin2 = util.vec(ray_origin[0],ray_origin[1],ray_origin[2],0.0)
        ray_direction2 = util.vec(ray_direction[0],ray_direction[1],ray_direction[2],0.0)

        bb_pos_world = util.vec(model[3][0],model[3][1],model[3][2],model[3][3])
        delta = bb_pos_world - ray_origin2

        x_axis = util.vec(model[0][0],model[0][1],model[0][2],model[0][3])
        y_axis = util.vec(model[1][0],model[1][1],model[1][2],model[1][3])
        z_axis = util.vec(model[2][0],model[2][1],model[2][2],model[2][3])

        # Test intersection with the 2 planes perpendicular to the bounding box's X axis

        #e = np.dot(x_axis,delta)
        #f = np.dot(ray_direction,x_axis)
        e = np.dot(x_axis,delta)
        f = np.dot(ray_direction2,x_axis)

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
                return False
            
        else:
            if minbb[0] > e or maxbb[0] < e:
                return False
            
        # Test intersection with the 2 planes perpendicular to the bounding box's Y axis

        #e = np.dot(y_axis,delta)
        #f = np.dot(ray_direction,y_axis)
        e = np.dot(y_axis,delta)
        f = np.dot(ray_direction2,y_axis)

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
                return False
            
        else:
            if minbb[1] > e or maxbb[1] < e:
                return False
            
        # Test intersection with the 2 planes perpendicular to the bounding box's Z axis

        #e = np.dot(z_axis,delta)
        #f = np.dot(ray_direction,z_axis)
        e = np.dot(z_axis,delta)
        f = np.dot(ray_direction2,z_axis)

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
                return False
            
        else:
            if minbb[2] > e or maxbb[2] < e:
                return False
        return True

    def translate_selected(self,x=0.0,y=0.0,z=0.0):
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
        self.selected_trs.l2world = self.selected_trs.l2world @ util.translate(x,y,z) #.l2world was trs
        self.gizmos_x_trans.l2world = self.selected_trs.l2world
        self.gizmos_y_trans.l2world = self.selected_trs.l2world
        self.gizmos_z_trans.l2world = self.selected_trs.l2world
    
    def rotate_selected(self,angle=0.0,axis=(1.0,0.0,0.0)):
        """
        Rotate Selected Element
        Arguments:
            self: self
            angle: Rotation Angle
            axis: axis to rotate
        Returns:
            None
        """
        pass

    def scale_selected(self,x=1.0,y=1.0,z=1.0):
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
        self.selected_trs.trs = self.selected_trs.trs @ util.scale(x,y,z)
