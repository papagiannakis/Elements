"""
Viewer classes, part of the Elements.pyGLV
    
Elements.pyGLV (Computer Graphics for Deep Learning and Scientific Visualization)
@Copyright 2021-2022 Dr. George Papagiannakis
    
The classes below are all related to the GUI and Display part of the package

Basic design principles are based on the Decorator Design pattern:
	• https://refactoring.guru/design-patterns/decorator
	• https://github.com/faif/python-patterns/blob/master/patterns/structural/decorator.py
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from collections.abc import Iterable, Iterator
from sys import platform

import sdl2
import sdl2.ext
from sdl2.keycode import SDLK_ESCAPE,SDLK_w
from sdl2.video import SDL_WINDOWPOS_CENTERED, SDL_WINDOW_ALLOW_HIGHDPI 

import weakref 
import glfw 
from Elements.pyGLV.GUI.windowEvents import PushEvent, PollEventAndFlush, WindowEvent, EventTypes

import OpenGL.GL as gl
from OpenGL.GL import shaders
import imgui
from imgui.integrations.sdl2 import SDL2Renderer

import Elements.pyECSS.System    
import Elements.pyECSS.math_utilities as util
import Elements.pyECSS.Event
from Elements.pyECSS.System import System  
from Elements.pyECSS.Component import BasicTransform
import numpy as np
from scipy.spatial.transform import Rotation
# from Elements.pyGLV.GL.Scene import Scene
# from Elements.pyGLV.GL.Scene import Scene

import Elements.utils.Shortcuts as Shortcuts 

KEY_MAP = {
    glfw.KEY_DOWN: "ArrowDown",
    glfw.KEY_UP: "ArrowUp",
    glfw.KEY_LEFT: "ArrowLeft",
    glfw.KEY_RIGHT: "ArrowRight",
    glfw.KEY_BACKSPACE: "Backspace",
    glfw.KEY_CAPS_LOCK: "CapsLock",
    glfw.KEY_DELETE: "Delete",
    glfw.KEY_END: "End",
    glfw.KEY_ENTER: "Enter",  # aka return
    glfw.KEY_ESCAPE: "Escape",
    glfw.KEY_F1: "F1",
    glfw.KEY_F2: "F2",
    glfw.KEY_F3: "F3",
    glfw.KEY_F4: "F4",
    glfw.KEY_F5: "F5",
    glfw.KEY_F6: "F6",
    glfw.KEY_F7: "F7",
    glfw.KEY_F8: "F8",
    glfw.KEY_F9: "F9",
    glfw.KEY_F10: "F10",
    glfw.KEY_F11: "F11",
    glfw.KEY_F12: "F12",
    glfw.KEY_HOME: "Home",
    glfw.KEY_INSERT: "Insert",
    glfw.KEY_LEFT_ALT: "Alt",
    glfw.KEY_LEFT_CONTROL: "Control",
    glfw.KEY_LEFT_SHIFT: "Shift",
    glfw.KEY_LEFT_SUPER: "Meta",  # in glfw super means Windows or MacOS-command
    glfw.KEY_NUM_LOCK: "NumLock",
    glfw.KEY_PAGE_DOWN: "PageDown",
    glfw.KEY_PAGE_UP: "Pageup",
    glfw.KEY_PAUSE: "Pause",
    glfw.KEY_PRINT_SCREEN: "PrintScreen",
    glfw.KEY_RIGHT_ALT: "Alt",
    glfw.KEY_RIGHT_CONTROL: "Control",
    glfw.KEY_RIGHT_SHIFT: "Shift",
    glfw.KEY_RIGHT_SUPER: "Meta",
    glfw.KEY_SCROLL_LOCK: "ScrollLock",
    glfw.KEY_TAB: "Tab",
    glfw.KEY_A: "A",
    glfw.KEY_B: "B",
    glfw.KEY_C: "C",
    glfw.KEY_D: "D",
    glfw.KEY_E: "E",
    glfw.KEY_F: "F",
    glfw.KEY_G: "G",
    glfw.KEY_H: "H",
    glfw.KEY_I: "I",
    glfw.KEY_J: "J",
    glfw.KEY_K: "K",
    glfw.KEY_L: "L",
    glfw.KEY_M: "M",
    glfw.KEY_N: "N",
    glfw.KEY_O: "O",
    glfw.KEY_P: "P",
    glfw.KEY_Q: "Q",
    glfw.KEY_R: "R",
    glfw.KEY_S: "S",
    glfw.KEY_T: "T",
    glfw.KEY_U: "U",
    glfw.KEY_V: "V",
    glfw.KEY_W: "W",
    glfw.KEY_X: "X",
    glfw.KEY_Y: "Y",
    glfw.KEY_Z: "Z",
    glfw.KEY_0: "0",
    glfw.KEY_1: "1",
    glfw.KEY_2: "2",
    glfw.KEY_3: "3",
    glfw.KEY_4: "4",
    glfw.KEY_5: "5",
    glfw.KEY_6: "6",
    glfw.KEY_7: "7",
    glfw.KEY_8: "8",
    glfw.KEY_9: "9",
    glfw.KEY_GRAVE_ACCENT: "`",
    glfw.KEY_MINUS: "-",
    glfw.KEY_EQUAL: "=",
    glfw.KEY_LEFT_BRACKET: "[",
    glfw.KEY_RIGHT_BRACKET: "]",
    glfw.KEY_BACKSLASH: "\\",
    glfw.KEY_SEMICOLON: ";",
    glfw.KEY_APOSTROPHE: "'",
    glfw.KEY_COMMA: ",",
    glfw.KEY_PERIOD: ".",
    glfw.KEY_SLASH: "/",
    glfw.KEY_KP_0: "KP_0",
    glfw.KEY_KP_1: "KP_1",
    glfw.KEY_KP_2: "KP_2",
    glfw.KEY_KP_3: "KP_3",
    glfw.KEY_KP_4: "KP_4",
    glfw.KEY_KP_5: "KP_5",
    glfw.KEY_KP_6: "KP_6",
    glfw.KEY_KP_7: "KP_7",
    glfw.KEY_KP_8: "KP_8",
    glfw.KEY_KP_9: "KP_9",
    glfw.KEY_KP_DECIMAL: "KP_Decimal",
    glfw.KEY_KP_DIVIDE: "KP_Divide",
    glfw.KEY_KP_MULTIPLY: "KP_Multiply",
    glfw.KEY_KP_SUBTRACT: "KP_Subtract",
    glfw.KEY_KP_ADD: "KP_Add",
    glfw.KEY_KP_ENTER: "KP_Enter",
    glfw.KEY_KP_EQUAL: "KP_Equal",
}

KEY_MAP_MOD = {
    glfw.KEY_LEFT_SHIFT: "Shift",
    glfw.KEY_RIGHT_SHIFT: "Shift",
    glfw.KEY_LEFT_CONTROL: "Control",
    glfw.KEY_RIGHT_CONTROL: "Control",
    glfw.KEY_LEFT_ALT: "Alt",
    glfw.KEY_RIGHT_ALT: "Alt",
    glfw.KEY_LEFT_SUPER: "Meta",
    glfw.KEY_RIGHT_SUPER: "Meta",
}

button_map = {
    glfw.MOUSE_BUTTON_1: 1,  # == MOUSE_BUTTON_LEFT
    glfw.MOUSE_BUTTON_2: 2,  # == MOUSE_BUTTON_RIGHT
    glfw.MOUSE_BUTTON_3: 3,  # == MOUSE_BUTTON_MIDDLE
    glfw.MOUSE_BUTTON_4: 4,
    glfw.MOUSE_BUTTON_5: 5,
    glfw.MOUSE_BUTTON_6: 6,
    glfw.MOUSE_BUTTON_7: 7,
    glfw.MOUSE_BUTTON_8: 8,
}


def weakbind(method):
    """Replace a bound method with a callable object that stores the `self` using a weakref."""
    ref = weakref.ref(method.__self__)
    class_func = method.__func__
    del method

    def proxy(*args, **kwargs):
        self = ref()
        if self is not None:
            return class_func(self, *args, **kwargs)

    proxy.__name__ = class_func.__name__
    return proxy 



class RenderWindow(ABC):
    """
    The Abstract base class of the Viewer GUI/Display sub-system of pyglGA
    based on the Decorator Pattern, this class is "wrapped" by decorators
    in order to provide extra cpapabilities e.g. SDL2 window, context and ImGUI widgets        
    """          
        
    def __init__(self):
        self._eventManager = None
        self._scene = None
    
    #define properties for EventManager, Scene objects
    @property #name
    def eventManager(self):
        """  Get RenderWindow's eventManager  """
        return self._eventManager
    @eventManager.setter
    def eventManager(self, value):
        self._eventManager = value
        
    @property #name
    def scene(self):
        """  Get RenderWindow's Scene reference  """
        return self._scene
    @scene.setter
    def scene(self, value):
        self._scene = value
        
    @abstractmethod
    def init(self):
        raise NotImplementedError
        
    abstractmethod
    def init_post(self):
        raise NotImplementedError
        
    @abstractmethod
    def display(self):
        raise NotImplementedError
        
    @abstractmethod
    def display_post(self):
        raise NotImplementedError
        
    @abstractmethod
    def shutdown(self):
        raise NotImplementedError
        
    @abstractmethod
    def event_input_process(self, running = True):
        raise NotImplementedError
        
    @abstractmethod
    def accept(self, system: Elements.pyECSS.System, event = None):
        """
        Accepts a class object to operate on the RenderWindow, based on the Visitor pattern.

        :param system: [a System object]
        :type system: [System]
        """
        raise NotImplementedError
        
    @classmethod
    def getClassName(cls):
        return cls.__name__
    
    

class GLFWWindow(RenderWindow):
    """ The concrete subclass of RenderWindow for the GLFW GUI API

    :param RenderWindow: [description]
    :type RenderWindow: [type]
    """ 
    
    def __init__(self, windowWidth = None, windowHeight = None, windowTitle = None, scene = None, eventManager = None, openGLveriosn = 4): 
        """Constructor GLFWWindow for basic GLFW parameters

        :param windowWidth: [description], defaults to None
        :type windowWidth: [type], optional
        :param windowHeight: [description], defaults to None
        :type windowHeight: [type], optional
        :param windowTitle: [description], defaults to None
        :type windowTitle: [type], optional
        """ 
        
        super().__init__() 
        
        self._running = True 
        
        self._gWindow = None
        self._gContext = None
        self._gVersionLabel = "None" 
        
        self.openGLversion = openGLveriosn 
        
        if windowWidth is None: 
            self._windowWidth = 1024
        else: 
            self._windowWidth = windowWidth 
            
        if windowHeight is None: 
            self._windowHeight = 768
        else: 
            self._windowHeight = windowHeight 
            
        if windowTitle is None: 
            self._windowTile = "GLFW window" 
        else:
            self._windowTile = windowTitle
            
        if eventManager is not None and scene is None:
            # in case we are testing without a Scene and just an EventManager
            self.eventManager = eventManager 
            
        if scene is not None:
            # set the reference of parent RenderWindow to Scene
            # get the reference to EventManager from Scene.ECSSManager
            self._scene = scene
            self.eventManager = scene.world.eventManager
            
        #OpenGL state variables
        self._wireframeMode = False
        self._colorEditor = 0.0, 0.0, 0.0
        self._myCamera = np.identity(4) 
        
    @property
    def gWindow(self):
        return self._gWindow

    @property
    def gContext(self):
        return self._gContext 
    
    def init(self):  
        """
        Initialize a GLFW window, not directly but from GLFWDecorator
        """ 

        print(f'{self.getClassName()}: init()')
        glfw.init()
          
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE) 
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, glfw.TRUE) 
        glfw.window_hint(glfw.DOUBLEBUFFER, glfw.TRUE)
        glfw.window_hint(glfw.SAMPLES, 4)
        
        #depth stencil buffer size
        glfw.window_hint(glfw.DEPTH_BITS, 24)
        glfw.window_hint(glfw.STENCIL_BITS, 8)  
        
        if self.openGLversion == 3:
            print("=" * 24)
            print("Using OpenGL version 3.2")
            print("="*24)
            glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
            glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 2)
        else: 
            print("="*24)
            print("Using OpenGL version 4.1")
            print("="*24)
            glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 4)
            glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 1) 
           
        if platform.startswith("darwin"): 
            # Emulate right-click with Control on macOS
            # glfw.window_hint(glfw.COCOA_CHDIR_RESOURCES, glfw.TRUE)
            # glfw.window_hint(glfw.COCOA_MENUBAR, glfw.FALSE)
            glfw.window_hint(glfw.COCOA_RETINA_FRAMEBUFFER, glfw.FALSE)

        # Disable high DPI mode
        # TODO: refactor inconify for preventing action while minimized
        glfw.window_hint(glfw.AUTO_ICONIFY, glfw.TRUE)  # This is a workaround for high DPI on some systems
        
        self._gWindow = glfw.create_window(
            int(self._windowHeight), 
            int(self._windowWidth),  
            self._windowTile, 
            None, 
            None
        )  
        
        self._key_modifiers = [] 
        self._pointer_buttons = [] 
        self._pointer_pos = 0, 0 
        self._double_click_state = {"clicks": 0}
        glfw.set_window_close_callback(self._gWindow, weakbind(self._on_check_close)) 
        glfw.set_framebuffer_size_callback(self._gWindow, weakbind(self._on_size_change))  
        glfw.set_mouse_button_callback(self._gWindow, weakbind(self._on_mouse_button))
        glfw.set_cursor_pos_callback(self._gWindow, weakbind(self._on_cursor_pos))
        glfw.set_scroll_callback(self._gWindow, weakbind(self._on_scroll))
        glfw.set_key_callback(self._gWindow, weakbind(self._on_key)) 
        
        if self._gWindow is None:
            print("Window could not be created! GLFW Error: ", glfw.get_error())
            exit(1)       
            
        glfw.make_context_current(self._gWindow) 
        self._gContext = glfw.get_current_context() 
        
        if self._gContext is None:
            print("OpenGL Context could not be created! GLFW Error: ", glfw.get_error())
            exit(1)  
            
        glfw.swap_interval(1)
        
        self._gVersionLabel = f'OpenGL {gl.glGetString(gl.GL_VERSION).decode()} GLSL {gl.glGetString(gl.GL_SHADING_LANGUAGE_VERSION).decode()} Renderer {gl.glGetString(gl.GL_RENDERER).decode()}'
        print(self._gVersionLabel)
            
    def init_post(self):
        """
        Post init method for GLFW
        this should be ctypiically alled AFTER all other GL contexts have been created
        """
        pass

    def display(self):
        """
        Main display window method to be called standalone or from within a concrete Decorator
        """
        # GPTODO make background clear color as parameter at class level

        gl.glClearColor(*self._colorEditor, 1.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        gl.glDisable(gl.GL_CULL_FACE)
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glDepthFunc(gl.GL_LESS)
        # gl.glDepthFunc(gl.GL_LEQUAL);

        # gl.glDepthMask(gl.GL_FALSE);

        # gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)

        # setup some extra GL state flags
        if self._wireframeMode:
            gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_LINE)
            #print(f"SDL2Window:display() set wireframemode: {self._wireframeMode}")
        else:
            gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)
            # print(f"SDL2Window:display() set wireframemode: {self._wireframeMode}")

        # print(f'{self.getClassName()}: display()')

    def display_post(self):
        """
        To be called at the end of each drawn frame to swap double buffers
        """ 
        
        glfw.swap_buffers(self._gWindow)
        # print(f'{self.getClassName()}: display_post()')

    def shutdown(self):
        """
        Shutdown and cleanup GLFW operations
        """
        print(f'{self.getClassName()}: shutdown()')
        if (self._gContext and self._gWindow is not None): 
            glfw.destroy_window(self._gWindow)
            glfw.terminate()
    
    def event_input_process(self, running=True):   
        glfw.poll_events()   
        
        events = PollEventAndFlush()
        for event in events:
            print(event.data)
         
        if self._running and running:
            if glfw.get_key(self._gWindow, glfw.KEY_ESCAPE) == glfw.PRESS: 
                self._running = False 

        return self._running

    def _on_check_close(self, *args):
        # Follow the close flow that glfw intended.
        if self._gWindow is not None and glfw.window_should_close(self._gWindow): 
            self._running = False
             
    def _on_size_change(self, *args): 
        # simple buffer and window resizing
        width, height = glfw.get_framebuffer_size(self._gWindow)
        if width > 0 and height > 0: 
            self._windowWidth = width;
            self._windowHeight = height;
            gl.glViewport(0, 0, self._windowWidth, self._windowHeight)
            print(f"Window Resized to {self._windowWidth} X {self._windowHeight}")  
            
            ev = {
                "width": width, 
                "height": height
            } 
           
            event = WindowEvent() 
            event.type = EventTypes.WINDOW_SIZE
            event.data = ev 
            PushEvent(event)
           
    def _on_mouse_button(self, window, but, action, mods):    
        button = button_map.get(but, 0) 
        
        if action == glfw.PRESS:  
            event_type = EventTypes.MOUSE_BUTTON_PRESS
            buttons = set(self._pointer_buttons)
            buttons.add(button) 
            self._pointer_buttons = list(sorted(buttons)) 
        elif action == glfw.RELEASE: 
            event_type = EventTypes.MOUSE_BUTTON_RELEASE
            buttons = set(self._pointer_buttons) 
            buttons.discard(button) 
            self._pointer_buttons = list(sorted(buttons)) 
        else:
            return
            
        ev = {  
            "x": self._pointer_pos[0], 
            "y": self._pointer_pos[1], 
            "button": button, 
            "buttons": list(self._pointer_buttons),
            "modifiers": list(self._key_modifiers)  
        } 
        
        event = WindowEvent()  
        event.type = event_type 
        event.data = ev
        PushEvent(event)
        
    def _on_cursor_pos(self, window, x, y):  
        self._pointer_pos = x, y
        
        ev = {  
            "x": self._pointer_pos[0], 
            "y": self._pointer_pos[1],
            "button": 0, 
            "buttons": list(self._pointer_buttons),
            "modifiers": list(self._key_modifiers)
        } 
      
        event = WindowEvent() 
        event.type = EventTypes.MOUSE_MOTION
        event.data = ev  
        PushEvent(event) 
        
    def _on_scroll(self, window, dx, dy): 
        ev = {  
            "dx": 100.0 * dx, 
            "dy": -100.0 * dy, 
            "x": self._pointer_pos[0], 
            "y": self._pointer_pos[1],
            "buttons": list(self._pointer_buttons),
            "modifiers": list(self._key_modifiers)
        }   
        
        event = WindowEvent() 
        event.type = EventTypes.SCROLL
        event.data = ev
        PushEvent(event) 
    
    #TODO refactor for modes 
    def _on_key(self, window, key, scancode, action, mods): 
        modifier = KEY_MAP_MOD.get(key, None)
        
        if action == glfw.PRESS:
            event_type = EventTypes.KEY_PRESS
            if modifier: 
                modifiers = set(self._key_modifiers) 
                modifiers.add(modifier) 
                self._key_modifiers = list(sorted(modifiers)) 
        elif action == glfw.RELEASE: 
            event_type = EventTypes.KEY_RELEASE
            if modifier: 
                modifiers = set(self._key_modifiers) 
                modifiers.discard(modifier)
                self._key_modifiers = list(sorted(modifiers)) 
        else: 
            return 
        
        if key in KEY_MAP: 
            keyname = KEY_MAP[key] 
        else: 
            try:
                keyname = chr(key) 
            except ValueError:
                return
            if "Shift" not in self._key_modifiers:
                keyname = keyname.lower() 
                
        ev = {  
            "key": keyname, 
            "modifiers": list(self._key_modifiers)
        } 
        
        event = WindowEvent()  
        event.type = event_type
        event.data = ev 
        PushEvent(event)
      
    def accept(self, system: Elements.pyECSS.System, event = None):
        system.apply2GLFWWindow(self, event)
             
             
             
# class SDL2Window(RenderWindow):
#     """ The concrete subclass of RenderWindow for the SDL2 GUI API 

#     :param RenderWindow: [description]
#     :type RenderWindow: [type]
#     """
    
#     def __init__(self, windowWidth = None, windowHeight = None, windowTitle = None, scene = None, eventManager = None, openGLversion = 4):
#         """Constructor SDL2Window for basic SDL2 parameters

#         :param windowWidth: [description], defaults to None
#         :type windowWidth: [type], optional
#         :param windowHeight: [description], defaults to None
#         :type windowHeight: [type], optional
#         :param windowTitle: [description], defaults to None
#         :type windowTitle: [type], optional
#         """
#         super().__init__()
                
#         self._gWindow = None
#         self._gContext = None
#         self._gVersionLabel = "None"

#         self.openGLversion = openGLversion
        
#         if windowWidth is None:
#             self._windowWidth = 1024
#         else:
#             self._windowWidth = windowWidth
        
#         if windowHeight is None:
#             self._windowHeight = 768
#         else:
#             self._windowHeight = windowHeight

#         if windowTitle is None:
#             self._windowTitle = "SDL2Window"
#         else:
#             self._windowTitle = windowTitle
                
#         if eventManager is not None and scene is None:
#             # in case we are testing without a Scene and just an EventManager
#             self.eventManager = eventManager
                
#         if scene is not None:
#             # set the reference of parent RenderWindow to Scene
#             # get the reference to EventManager from Scene.ECSSManager
#             self._scene = scene
#             self.eventManager = scene.world.eventManager
            
#         #OpenGL state variables
#         self._wireframeMode = False
#         self._colorEditor = 0.0, 0.0, 0.0
#         self._myCamera = np.identity(4)
                          
#     @property
#     def gWindow(self):
#         return self._gWindow

#     @property
#     def gContext(self):
#         return self._gContext

#     def init(self):
#         """
#         Initialise an SDL2 RenderWindow, not directly but via the SDL2Decorator
#         """
#         print(f'{self.getClassName()}: init()')
        
#         #SDL_Init for the window initialization
#         sdl_not_initialised = sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO | sdl2.SDL_INIT_TIMER)
#         if sdl_not_initialised !=0:
#             print("SDL2 could not be initialised! SDL Error: ", sdl2.SDL_GetError())
#             exit(1)
        
#         #setting OpenGL attributes for the GL state
#         sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_CONTEXT_FLAGS,
#                                  sdl2.SDL_GL_CONTEXT_FORWARD_COMPATIBLE_FLAG
#                                  )
#         sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_CONTEXT_PROFILE_MASK,
#                                  sdl2.SDL_GL_CONTEXT_PROFILE_CORE
#                                  )
#         sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_DOUBLEBUFFER, 1)
                
#         sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_ACCELERATED_VISUAL, 1)

#         sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_DEPTH_SIZE, 24)
#         sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_STENCIL_SIZE, 8)      
#         sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_MULTISAMPLEBUFFERS, 1)

#         if self.openGLversion == 3:
#             print("=" * 24)
#             print("Using OpenGL version 3.2")
#             print("="*24)
#             sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_CONTEXT_MAJOR_VERSION, 3)
#             sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_CONTEXT_MINOR_VERSION, 2)    
#         else: 
#             print("="*24)
#             print("Using OpenGL version 4.1")
#             print("="*24)
#             sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_CONTEXT_MAJOR_VERSION, 4)
#             sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_CONTEXT_MINOR_VERSION, 1)

                     
#         # SDL_GL_MULTISAMPLESAMPLES does not work on VMs and some Linux systems, 
#         # therefore we depracate it for now
    
#         # if platform == "linux" or platform == "linux2":
#         #     pass
#         # else:
#         #     sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_MULTISAMPLESAMPLES, 16)        

#         sdl2.SDL_SetHint(sdl2.SDL_HINT_MAC_CTRL_CLICK_EMULATE_RIGHT_CLICK, b"1")
#         sdl2.SDL_SetHint(sdl2.SDL_HINT_VIDEO_HIGHDPI_DISABLED, b"1")
        
#         #creating the SDL2 window
#         self._gWindow = sdl2.SDL_CreateWindow(self._windowTitle.encode(), 
#                                               sdl2.SDL_WINDOWPOS_CENTERED,
#                                               sdl2.SDL_WINDOWPOS_CENTERED,
#                                               self._windowWidth,
#                                               self._windowHeight,
#                                             #   sdl2.SDL_WINDOW_ALLOW_HIGHDPI)
#                                               sdl2.SDL_WINDOW_OPENGL | sdl2.SDL_WINDOW_RESIZABLE | sdl2.SDL_WINDOW_SHOWN )
        
#         if self._gWindow is None:
#             print("Window could not be created! SDL Error: ", sdl2.SDL_GetError())
#             exit(1)
            
#         #create the OpenGL context for rendering into the SDL2Window that was constructed just before
#         self._gContext = sdl2.SDL_GL_CreateContext(self._gWindow)
#         if self._gContext is None:
#             print("OpenGL Context could not be created! SDL Error: ", sdl2.SDL_GetError())
#             exit(1)
#         sdl2.SDL_GL_MakeCurrent(self._gWindow, self._gContext)
#         if sdl2.SDL_GL_SetSwapInterval(1) < 0:
#             print("Warning: Unable to set VSync! SDL Error: ", sdl2.SDL_GetError())
#             # exit(1)
#         #obtain the GL versioning system info
#         self._gVersionLabel = f'OpenGL {gl.glGetString(gl.GL_VERSION).decode()} GLSL {gl.glGetString(gl.GL_SHADING_LANGUAGE_VERSION).decode()} Renderer {gl.glGetString(gl.GL_RENDERER).decode()}'
#         print(self._gVersionLabel)

#     def init_post(self):
#         """
#         Post init method for SDL2
#         this should be ctypiically alled AFTER all other GL contexts have been created
#         """
#         pass

#     def display(self):
#         """
#         Main display window method to be called standalone or from within a concrete Decorator
#         """
#         # GPTODO make background clear color as parameter at class level

#         gl.glClearColor(*self._colorEditor, 1.0)
#         gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
#         gl.glDisable(gl.GL_CULL_FACE)
#         gl.glEnable(gl.GL_DEPTH_TEST)
#         gl.glDepthFunc(gl.GL_LESS)
#         # gl.glDepthFunc(gl.GL_LEQUAL);

#         # gl.glDepthMask(gl.GL_FALSE);

#         # gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)

#         # setup some extra GL state flags
#         if self._wireframeMode:
#             gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_LINE)
#             #print(f"SDL2Window:display() set wireframemode: {self._wireframeMode}")
#         else:
#             gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)
#             # print(f"SDL2Window:display() set wireframemode: {self._wireframeMode}")

#         # print(f'{self.getClassName()}: display()')

#     def display_post(self):
#         """
#         To be called at the end of each drawn frame to swap double buffers
#         """
#         sdl2.SDL_GL_SwapWindow(self._gWindow)
#         # print(f'{self.getClassName()}: display_post()')

#     def shutdown(self):
#         """
#         Shutdown and cleanup SDL2 operations
#         """
#         print(f'{self.getClassName()}: shutdown()')
#         if (self._gContext and self._gWindow is not None):
#             sdl2.SDL_GL_DeleteContext(self._gContext)
#             sdl2.SDL_DestroyWindow(self._gWindow)
#             sdl2.SDL_Quit()      

#     def event_input_process(self, running=True):
#         """
#         process SDL2 basic events and input
#         """
#         events = sdl2.ext.get_events()
#         for event in events:
#             if event.type == sdl2.SDL_KEYDOWN:
#                 if event.key.keysym.sym == sdl2.SDLK_ESCAPE:
#                     running = False
#             if event.type == sdl2.SDL_QUIT:
#                 running = False
#             if  event.type == sdl2.SDL_WINDOWEVENT:
#                 window = self.gWindow
#                 if event.window.event == sdl2.SDL_WINDOWEVENT_RESIZED:
#                     print("Window Resized to ", event.window.data1, " X " , event.window.data2)
#                     # new width and height: event.window.data1 and event.window.data2
#                     window._windowWidth = event.window.data1
#                     window._windowHeight = event.window.data2
#                     gl.glViewport(0, 0, event.window.data1, event.window.data2)
#         return running
    
#     def accept(self, system: Elements.pyECSS.System, event = None):
#         system.apply2SDLWindow(self, event)


class RenderDecorator(RenderWindow):
    """
    Main Decorator class that wraps a RenderWindow so that all other Decorator classes can dynamically be
    adding layered functionality on top of the wrapee (RenderWindow) e.g. ImGUI widgets etc.

    :param RenderWindow: [description]
    :type RenderWindow: [type]
    """
    def __init__(self, wrapee: RenderWindow):
        super().__init__()
        
        self._wrapeeWindow = wrapee
    
        self._eye = (2.5, 2.5, 2.5)
        self._target = (0.0, 0.0, 0.0) 
        self._up = (0.0, 1.0, 0.0)

        # TRS Variables 
        self.translation = {};
        self.translation["x"] = 0; self.translation["y"] = 0; self.translation["z"] = 0; 

        self.rotation = {};
        self.rotation["x"] = 0; self.rotation["y"] = 0; self.rotation["z"] = 0; 

        self.scale = {};
        self.scale["x"] = 0; self.scale["y"] = 0; self.scale["z"] = 0; 

        #this is not used anywhere
        self.color = [255, 50, 50];

        self.lctrl = False
        
        self.traverseCamera() 


    @property
    def wrapeeWindow(self):
        return self._wrapeeWindow
    
    
    def init(self):
        """
        [summary]
        """
        self._wrapeeWindow.init()
        print(f'RenderDecorator: init()')
        
        
    def display(self):
        """
        Main decorator display method
        """
        self._wrapeeWindow.display()
        
        
    def shutdown(self):
        """
        [summary]
        """
        self._wrapeeWindow.shutdown()
        print(f'RenderDecorator: shutdown()')   

    def traverseCamera(self):
        self.cam = None
        found = False
        if self.wrapeeWindow.scene is not None:
            rootComp = self.wrapeeWindow.scene.world.root
            if rootComp._children is not None:
                Iterator = iter(rootComp._children)
                done_traversing = False
                while not found and not done_traversing:
                    try:
                        comp = next(Iterator)
                    except StopIteration:
                        done_traversing = True
                    else:
                        if "camera" in comp.name.lower(): # just put the "Camera" string in the Entity that holds the camera
                            self.cam = comp
                            found = True
                        
    def createViewMatrix(self, eye, lookAt, upVector):
        self._eye = tuple(eye)
        self._target = tuple(lookAt)
        #self._up = tuple(upVector)
        #directionVector = util.normalise(lookAt - eye) 
        #rightVector = util.normalise(np.cross(directionVector, upVector))
        #upVector = util.normalise(np.cross(rightVector, directionVector))
        self._updateCamera.value = util.lookat(eye, lookAt, upVector)
    
    def updateCamera(self, moveX, moveY, moveZ, rotateX, rotateY):  
        if self.cam != None:
            #for examples 7-11 and pyJANVRED implementations
            cameraspeed = 5
            #scaleMat = util.scale(self.scale["x"], self.scale["y"], self.scale["z"])
            #combinedMat = scaleMat
            if rotateX:# or rotateY: 
                #rotMatX = util.rotate((1, 0, 0), -self.rotation["y"] * cameraspeed)
                rotMatY = util.rotate((0, 1, 0), self.rotation["x"] * cameraspeed)
                #rotMatZ = util.rotate((0, 0, 1), self.rotation["z"] * cameraspeed)
                #combinedMat = rotMatX @ rotMatY @ rotMatZ @ combinedMat 
                #combinedMat = rotMatY #@ combinedMat 
                self.cam.trans1.trs = rotMatY @ self.cam.trans1.trs
            elif rotateY: 
                rotMatX = util.rotate((1, 0, 0), -self.rotation["y"] * cameraspeed)
                #combinedMat = rotMatX #@ combinedMat 
                self.cam.trans1.trs = self.cam.trans1.trs @ rotMatX
            if moveX or moveY or moveZ:
                transMat = util.translate(self.translation["x"], self.translation["y"], -self.translation["z"])
                #combinedMat = transMat #@ combinedMat
                self.cam.trans1.trs =  self.cam.trans1.trs @ transMat
        else:
            #for examples 4-5-6-8-9-10 implementations
            cameraspeed = 0.2
            teye = np.array(self._eye)
            ttarget = np.array(self._target)
            tup = np.array(self._up)

            forwardDir = util.normalise(ttarget - teye)
            rightDir = util.normalise(np.cross(forwardDir, tup))
   
            if rotateX:
                rotMatY = util.rotate(tup, self.rotation["x"] * cameraspeed*15)
                transMatY = util.translate(ttarget) @ rotMatY @ util.translate(-ttarget)
                teye = transMatY @ np.append(teye, [1])
                teye = teye[:-1] / teye[-1]
            elif rotateY:
                rotMatX = util.rotate(rightDir, -self.rotation["y"] * cameraspeed*15)
                transMatX = util.translate(ttarget) @ rotMatX @ util.translate(-ttarget)
                teye = transMatX @ np.append(teye, [1])
                teye = teye[:-1] / teye[-1]
            elif moveX or moveY:
                panX = -cameraspeed * self.translation["x"] * rightDir
                panY = -self.translation["y"] * cameraspeed * tup
                teye += panX + panY
                ttarget += panX + panY
            elif moveZ:
                zoom =  np.sign(self.translation["z"]) * cameraspeed * forwardDir
                teye += zoom
                ttarget += zoom
            self.createViewMatrix(teye, ttarget, tup)
            
            if self._wrapeeWindow.eventManager is not None:
                self.wrapeeWindow.eventManager.notify(self, self._updateCamera)
        
 
    def on_mouse_motion(self, event, x, y, dx, dy):
        """Called when the mouse is moved.

            event: sdl2.events.SDL_Event, 
            x: horiz coord relative to window, y: vert coord relative to window,
            dx: relative horizontal motion, dy: relative vertical motion
        """
        pass

    def on_mouse_press(self, event, x, y, button, dclick):
        """Called when mouse buttons are pressed.

            event: sdl2.events.SDL_Event, 
            x: horiz coord relative to window, y: vert coord relative to window,
            dx: relative horizontal motion, dy: relative vertical motion
            button: RIGHT - MIDDLE - LEFT
            dclick: True - False if button was double click
        """
        pass

    def resetAll(self):
        self.translation["x"] = 0.0
        self.translation["y"] = 0.0
        self.translation["z"] = 0.0
        self.rotation["x"] = 0.0
        self.rotation["y"] = 0.0
        self.rotation["z"] = 0.0
        self.scale["x"]= 1.0
        self.scale["y"]= 1.0
        self.scale["z"]= 1.0 
        
    def cameraHandling(self, x, y, height, width):
        keystatus = sdl2.SDL_GetKeyboardState(None)
        self.resetAll()

        if keystatus[sdl2.SDL_SCANCODE_LSHIFT]:
            if abs(x) > abs(y):
                self.translation["x"] = x/width*60 #np.sign(event.wheel.x)
                self.updateCamera(True, False, False, False, False)
            else:
                self.translation["y"] =  y/height*60 #np.sign(event.wheel.y)
                self.updateCamera(False, True, False, False, False)
        elif keystatus[sdl2.SDL_SCANCODE_LCTRL] or self.lctrl:
            self.translation["z"] =  y/height*60 #-np.sign(event.wheel.y) 
            self.updateCamera(False, False, True, False, False)
        else:
            if abs(x) > abs(y):
                self.rotation["x"] = np.sign(x) #event.wheel.x/height*180
                self.updateCamera(False, False,False, True, False)
            else:
                self.rotation["y"] = np.sign(y) #event.wheel.y/width*180
                self.updateCamera(False, False,False, False, True)

    def event_input_process(self):
        """
        process GLSL basic events and input
        """  
        glfw.make_context_current(self.wrapeeWindow._gWindow) 
        
        glfw.poll_events() 
        
        events = PollEventAndFlush()
        running = True
        width = self.wrapeeWindow._windowWidth
        height = self.wrapeeWindow._windowHeight 
        
        shortcut_HotKey = KEY_MAP.get(glfw.KEY_LEFT_ALT) 
        
        for event in events:
            print("event: ", event.data)
            if event.type == EventTypes.SCROLL:
                x = event.data["dx"]
                y = event.data["dy"]
                self.cameraHandling(x,y,height,width)
            
            elif event.type == EventTypes.MOUSE_MOTION:
                buttons = event.data["buttons"] 
                if 2 in buttons:
                    x = -event.data["x"]
                    y = event.data["y"]
                    self.cameraHandling(x, y, height, width)
                     
            elif event.type == EventTypes.KEY_PRESS:
                ##################  toggle the wireframe using the alt+F buttons  #############################
                if event.data["key"] == KEY_MAP.get(glfw.KEY_F) and shortcut_HotKey in event.data["modifiers"]:
                    self.toggle_Wireframe() 
                
                ########## shortcuts for selected node from the tree ###########
                if hasattr(self._wrapeeWindow._scene, "_gContext") and self._wrapeeWindow._scene._gContext.__class__.__name__ == "ImGUIecssDecorator" and self.selected:
                    # we must first check if the ImGUIecssDecorator is active otherwise we will get an error on click
                    ################# - translate on x axis when node is selected using W+alt ###########################
                    if (event.data["key"] == KEY_MAP.get(glfw.KEY_W) and shortcut_HotKey in event.data["modifiers"]):
                        self.translation["x"] -= 0.1
                    ################# + translate on x axis when node is selected using W ###########################
                    if (event.data["key"] == KEY_MAP.get(glfw.KEY_W)):
                        self.translation["x"] += 0.1 
                        
                    # ################# - translate on y axis when node is selected using E+alt ###########################
                    if (event.data["key"] == KEY_MAP.get(glfw.KEY_E) and shortcut_HotKey in event.data["modifiers"]): 
                        self.translation["y"] -= 0.1
                    ################# + translate on y axis when node is selected using E ###########################
                    elif(event.data["key"] == KEY_MAP.get(glfw.KEY_E)):
                        self.translation["y"] += 0.1
                    
                    # ################# - translate on z axis when node is selected using R+alt ###########################
                    if (event.data["key"] == KEY_MAP.get(glfw.KEY_R) and shortcut_HotKey in event.data["modifiers"]):
                        self.translation["z"] -= 0.1
                    # ################# + translate on z axis when node is selected using R ########################### 
                    elif(event.data["key"] == KEY_MAP.get(glfw.KEY_R)):
                        self.translation["z"] += 0.1
                    

                    # ################# - rotate on x axis when node is selected using T+alt ########################### 
                    if (event.data["key"] == KEY_MAP.get(glfw.KEY_T) and shortcut_HotKey in event.data["modifiers"]):
                        self.rotation["x"] -= 0.1
                    # ################# + rotate on x axis when node is selected using T ########################### 
                    elif (event.data["key"] == KEY_MAP.get(glfw.KEY_T)):
                        self.rotation["x"] += 0.1
                    
                    # ################# - rotate on y axis when node is selected using Y+alt ###########################
                    if (event.data["key"] == KEY_MAP.get(glfw.KEY_Y) and shortcut_HotKey in event.data["modifiers"]):
                        self.rotation["y"] -= 0.1
                    # ################# + rotate on y axis when node is selected using Y ###########################
                    elif(event.data["key"] == KEY_MAP.get(glfw.KEY_Y)):
                        self.rotation["y"] += 0.1 
                    
                    # ################# - rotate on z axis when node is selected using U+alt ###########################
                    if (event.data["key"] == KEY_MAP.get(glfw.KEY_U) and shortcut_HotKey in event.data["modifiers"]):
                        self.rotation["z"] -= 0.1
                    # ################# + rotate on z axis when node is selected using U ###########################
                    elif(event.data["key"] == KEY_MAP.get(glfw.KEY_U)):
                        self.rotation["z"] += 0.1
                    
                    ################# scale down on x axis when node is selected using I+alt ###########################
                    if (event.data["key"] == KEY_MAP.get(glfw.KEY_I) and shortcut_HotKey in event.data["modifiers"]):
                        self.scale["x"] -= 0.1
                    ################# scale up on x axis when node is selected using I ###########################
                    elif(event.data["key"] == KEY_MAP.get(glfw.KEY_I)):
                        self.scale["x"] += 0.1
                    
                    ################# scale down on y axis when node is selected using O+alt ########################### 
                    if (event.data["key"] == KEY_MAP.get(glfw.KEY_O) and shortcut_HotKey in event.data["modifiers"]):
                        self.scale["y"] -= 0.1
                    ################# scale up on y axis when node is selected using O ###########################
                    elif(event.data["key"] == KEY_MAP.get(glfw.KEY_O)):
                        self.scale["y"] += 0.1 
                    
                    ################# scale down on z axis when node is selected using P+alt ########################### 
                    # if(event.key.keysym.sym == sdl2.SDLK_p  and (sdl2.SDL_GetModState() & shortcut_HotKey)): 
                    if (event.data["key"] == KEY_MAP.get(glfw.KEY_P) and shortcut_HotKey in event.data["modifiers"]):
                        self.scale["z"] -= 0.1
                    ################# scale up on z axis when node is selected using P ###########################
                    elif(event.data["key"] == KEY_MAP.get(glfw.KEY_P)):
                        self.scale["z"] += 0.1

                if event.data["key"] == KEY_MAP.get(glfw.KEY_ESCAPE):
                    running = False
            elif event.type == EventTypes.KEY_RELEASE and event.data["key"] == KEY_MAP.get(glfw.KEY_LEFT_CONTROL):
                self.lctrl = False

                
            elif  event.type == EventTypes.WINDOW_SIZE:
                window = self.wrapeeWindow
                window._windowWidth = event.data["width"]
                window._windowHeight = event.data["height"]
                # new width and height: event.window.data1 and event.window.data2
                gl.glViewport(0, 0, event.data["width"], event.data["height"]) 
                    
        if running:
            if glfw.get_key(self.wrapeeWindow._gWindow, glfw.KEY_ESCAPE) == glfw.PRESS: 
                running = False 
                
            #imgui event 
            # self._imguiRenderer.process_event()
        # #imgui input
        self._imguiRenderer.process_inputs()
                    
        return running #self._wrapeeWindow.event_input_process() & running   
    
    # def event_input_process(self):
    #     """
    #     extra decorator method to handle input events
    #     :param running: [description], defaults to True
    #     :type running: bool, optional
    #     """
    #     return self._wrapeeWindow.event_input_process()
    
    # def event_input_process_sdl2(self):
    #     """
    #     process SDL2 basic events and input
    #     """
    #     running = True
    #     events = sdl2.ext.get_events()
    #     width = self.wrapeeWindow._windowWidth
    #     height = self.wrapeeWindow._windowHeight

    #     ### set up a hot key to easily switch between common keys like shift,ctrl etc
    #     ### default at left alt
    #     alt_Key = sdl2.KMOD_ALT
    #     leftShift_Key = sdl2.KMOD_LSHIFT
    #     rightShift_Key = sdl2.KMOD_RSHIFT
    #     ctrl_Key = sdl2.KMOD_CTRL

    #     shortcut_HotKey = alt_Key
        
    #     for event in events:
    #         if event.type == sdl2.SDL_MOUSEWHEEL:
    #             x = event.wheel.x
    #             y = event.wheel.y
    #             self.cameraHandling(x,y,height,width)

    #         # on_mouse_press
    #         elif event.type == sdl2.SDL_MOUSEMOTION:
    #             buttons = event.motion.state
    #             if buttons & sdl2.SDL_BUTTON_RMASK:
    #                 x = -event.motion.xrel  
    #                 y = event.motion.yrel 
    #                 self.cameraHandling(x, y, height, width)               
            
    #         #keyboard events
    #         elif event.type == sdl2.SDL_KEYDOWN:
    #             ##################  toggle the wireframe using the alt+F buttons  #############################
    #             if (event.key.keysym.sym == sdl2.SDLK_f and (sdl2.SDL_GetModState() & shortcut_HotKey)):
    #                 self.toggle_Wireframe()
                
    #             ########## shortcuts for selected node from the tree ###########
    #             if hasattr(self._wrapeeWindow._scene, "_gContext") and self._wrapeeWindow._scene._gContext.__class__.__name__ == "ImGUIecssDecorator" and self.selected:
    #                 # we must first check if the ImGUIecssDecorator is active otherwise we will get an error on click
    #                 ################# - translate on x axis when node is selected using W+alt ###########################
    #                 if(event.key.keysym.sym == sdl2.SDLK_w and (sdl2.SDL_GetModState() & shortcut_HotKey)):
    #                     self.translation["x"] -= 0.1
    #                 ################# + translate on x axis when node is selected using W ###########################
    #                 elif(event.key.keysym.sym == sdl2.SDLK_w):
    #                     self.translation["x"] += 0.1
                    
    #                 # ################# - translate on y axis when node is selected using E+alt ###########################
    #                 if(event.key.keysym.sym == sdl2.SDLK_e and (sdl2.SDL_GetModState() & shortcut_HotKey)):
    #                     self.translation["y"] -= 0.1
    #                 ################# + translate on y axis when node is selected using E ###########################
    #                 elif(event.key.keysym.sym == sdl2.SDLK_e):
    #                     self.translation["y"] += 0.1 
                    
    #                 # ################# - translate on z axis when node is selected using R+alt ###########################
    #                 if(event.key.keysym.sym == sdl2.SDLK_r and (sdl2.SDL_GetModState() & shortcut_HotKey)):
    #                     self.translation["z"] -= 0.1
    #                 # ################# + translate on z axis when node is selected using R ###########################
    #                 elif(event.key.keysym.sym == sdl2.SDLK_r):
    #                     self.translation["z"] += 0.1
                    

    #                 # ################# - rotate on x axis when node is selected using T+alt ###########################
    #                 if(event.key.keysym.sym == sdl2.SDLK_t and (sdl2.SDL_GetModState() & shortcut_HotKey)):
    #                     self.rotation["x"] -= 0.1
    #                 # ################# + rotate on x axis when node is selected using T ###########################
    #                 elif(event.key.keysym.sym == sdl2.SDLK_t):
    #                     self.rotation["x"] += 0.1
                    
    #                 # ################# - rotate on y axis when node is selected using Y+alt ###########################
    #                 if(event.key.keysym.sym == sdl2.SDLK_y and (sdl2.SDL_GetModState() & shortcut_HotKey)):
    #                     self.rotation["y"] -= 0.1
    #                 # ################# + rotate on y axis when node is selected using Y ###########################
    #                 elif(event.key.keysym.sym == sdl2.SDLK_y):
    #                     self.rotation["y"] += 0.1 
                    
    #                 # ################# - rotate on z axis when node is selected using U+alt ###########################
    #                 if(event.key.keysym.sym == sdl2.SDLK_u and (sdl2.SDL_GetModState() & shortcut_HotKey)):
    #                     self.rotation["z"] -= 0.1
    #                 # ################# + rotate on z axis when node is selected using U ###########################
    #                 elif(event.key.keysym.sym == sdl2.SDLK_u):
    #                     self.rotation["z"] += 0.1
                    
    #                 ################# scale down on x axis when node is selected using I+alt ###########################
    #                 if(event.key.keysym.sym == sdl2.SDLK_i  and (sdl2.SDL_GetModState() & shortcut_HotKey)):
    #                     self.scale["x"] -= 0.1
    #                 ################# scale up on x axis when node is selected using I ###########################
    #                 elif(event.key.keysym.sym == sdl2.SDLK_i ):
    #                     self.scale["x"] += 0.1
                    
    #                 ################# scale down on y axis when node is selected using O+alt ###########################
    #                 if(event.key.keysym.sym == sdl2.SDLK_o  and (sdl2.SDL_GetModState() & shortcut_HotKey)):
    #                     self.scale["y"] -= 0.1
    #                 ################# scale up on y axis when node is selected using O ###########################
    #                 elif(event.key.keysym.sym == sdl2.SDLK_o ):
    #                     self.scale["y"] += 0.1 
                    
    #                 ################# scale down on z axis when node is selected using P+alt ###########################
    #                 if(event.key.keysym.sym == sdl2.SDLK_p  and (sdl2.SDL_GetModState() & shortcut_HotKey)):
    #                     self.scale["z"] -= 0.1
    #                 ################# scale up on z axis when node is selected using P ###########################
    #                 elif(event.key.keysym.sym == sdl2.SDLK_p ):
    #                     self.scale["z"] += 0.1

    #             if event.key.keysym.sym == sdl2.SDLK_ESCAPE:
    #                 running = False
    #         elif event.type == sdl2.SDL_KEYUP and event.key.keysym.sym == sdl2.SDLK_LCTRL:
    #             self.lctrl = False

            
                
    #         elif event.type == sdl2.SDL_QUIT:
    #             running = False
                
    #         elif  event.type == sdl2.SDL_WINDOWEVENT:
    #             window = self.wrapeeWindow
    #             if event.window.event == sdl2.SDL_WINDOWEVENT_RESIZED:
    #                 print("Window Resized to ", event.window.data1, " X " , event.window.data2)
    #                 window._windowWidth = event.window.data1
    #                 window._windowHeight = event.window.data2
    #                 # new width and height: event.window.data1 and event.window.data2
    #                 gl.glViewport(0, 0, event.window.data1, event.window.data2)
            
    #         #imgui event
    #         self._imguiRenderer.process_event(event)
    #     #imgui input
    #     self._imguiRenderer.process_inputs()
    #     return running #self._wrapeeWindow.event_input_process() & running 
    
    def display_post(self):
        """
        Post diplay method after all other display calls have been issued
        """
        self._wrapeeWindow.display_post()
    
    
    def init_post(self):
        """
        Post init method
        this should be ctypiically alled AFTER all other GL contexts have been created, e.g. ImGUI context
        """
        self._wrapeeWindow.init_post()
        
    def accept(self, system: Elements.pyECSS.System, event = None):
        pass
                    
        

class RenderGLStateSystem(System):
    """
    System that operates on a RenderDecorator (ImGUIDecorator) and affect GL State

    """
    
    def __init__(self, name=None, type=None, id=None):
        super().__init__(name, type, id)
        
    def update(self):
        """
        method to be subclassed for  behavioral or logic computation 

        """
        pass
    
    
    def apply2ImGUIDecorator(self, imGUIDecorator, event = None):
        """
        method for  behavioral or logic computation 
        when visits Components. 
        
        In this case update GL State from ImGUIDecorator
        
        """
        pass
    
    def apply2GLFWWindow(self, GLFWwindow, event=None):
        """method for  behavioral or logic computation
        when visits Components.

        In this case update GL State from GLFWwindow 

        :param sdlWindow: [description]
        :type sdlWindow: [type]
        :param event: [description], defaults to None
        :type event: [type], optional
        """
        if event.name == "OnUpdateWireframe":
            # print(f"RenderGLStateSystem():apply2SDLWindow() actuator system for: {event}")
            GLFWWindow._wireframeMode = event.value

        if event.name == "OnUpdateCamera":
            # print(f"OnUpdateCamera: RenderGLStateSystem():apply2SDLWindow() actuator system for: {event}")
            GLFWWindow._myCamera = event.value

    # def apply2SDLWindow(self, sdlWindow, event=None):
    #     """method for  behavioral or logic computation
    #     when visits Components.

    #     In this case update GL State from SDLWindow

    #     :param sdlWindow: [description]
    #     :type sdlWindow: [type]
    #     :param event: [description], defaults to None
    #     :type event: [type], optional
    #     """
    #     if event.name == "OnUpdateWireframe":
    #         # print(f"RenderGLStateSystem():apply2SDLWindow() actuator system for: {event}")
    #         sdlWindow._wireframeMode = event.value

    #     if event.name == "OnUpdateCamera":
    #         # print(f"OnUpdateCamera: RenderGLStateSystem():apply2SDLWindow() actuator system for: {event}")
    #         sdlWindow._myCamera = event.value


if __name__ == "__main__":
    # The client code.        
    # gWindow = SDL2Window(openGLversion=3)    
    # # uses openGL version 3.2 instead of the default 4.1        
    # gWindow.init()        
    # gWindow.init_post()        
    # running = True        
    # # MAIN RENDERING LOOP        
    # while running:              
    #     gWindow.display()              
    #     running = gWindow.event_input_process(running)              
    #     gWindow.display_post()            
    # gWindow.shutdown() 
    
    gWindow = GLFWWindow(windowHeight=1200, windowWidth=800, openGLveriosn=3) 
    gWindow.init()
    gWindow.init_post() 
    running = True        
    # MAIN RENDERING LOOP        
    while gWindow.event_input_process(running): 
        gWindow.display()                
        gWindow.display_post()            
    