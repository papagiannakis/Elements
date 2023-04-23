from Elements.pyGLV.GL.Scene import Scene
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform
import Elements.pyECSS.utilities as util
import sdl2 as sdl
from ctypes import c_int, byref

class Gizmos:
    def __init__(self,
                 scene: Scene):
        sdl.ext.init()
        self.scene = scene
        self.selected = -1
        self.selected_pos = -1
        self.first_pos = -1
        self.mouse_x, self.mouse_y = c_int(0), c_int(0)
        self.mouse_state = 0 #LMB not clicked
        self.key_states = sdl.SDL_GetKeyboardState(None)
        self.key_down = False
        self.trs_table = {}
        self.__index_components(scene)

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

    def __index_components(self,
                         scene: Scene):
        """
        Create an indexing for each entity's "BasicTransform" component's position
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
                    break #no need to Iterate any further
    
    def get_keyboard_Event(self):
        """
        When TAB is pressed change selected entity
        Arguments:
            self: that's me
        Returns:
            None
        """
        if self.key_states[sdl.SDL_SCANCODE_TAB] and not self.key_down:
            print('TAB key pressed')
            self.key_down = True
            self.change_target()
            print(self.scene.world.root.getChild(self.selected))
            print(self.scene.world.root.getChild(self.selected).getChild(self.selected_pos).trs)
        elif not self.key_states[sdl.SDL_SCANCODE_TAB] and self.key_down:
            print('TAB key released')
            self.key_down = False