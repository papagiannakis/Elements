"""
Viewer classes, part of the Elements.pyGLV
    
Elements.pyGLV (Computer Graphics for Deep Learning and Scientific Visualization)
@Copyright 2021-2022 Dr. George Papagiannakis
    
The classes below are all related to the GUI and Display part of the package

Basic design principles are based on the Decorator Design pattern:
	• https://refactoring.guru/design-patterns/decorator
	• https://github.com/faif/python-patterns/blob/master/patterns/structural/decorator.py
"""

from __future__         import annotations
from abc                import ABC, abstractmethod
from typing             import List, Dict, Any
from collections.abc    import Iterable, Iterator
from sys import platform

import sdl2
import sdl2.ext
from sdl2.keycode import SDLK_ESCAPE
from sdl2.video import SDL_WINDOWPOS_CENTERED, SDL_WINDOW_ALLOW_HIGHDPI
import OpenGL.GL as gl
from OpenGL.GL import shaders
import imgui
from imgui.integrations.sdl2 import SDL2Renderer

import Elements.pyECSS.System  
import Elements.pyECSS.utilities as util
import Elements.pyECSS.Event
from Elements.pyECSS.System import System 
from Elements.pyECSS.Component import BasicTransform
import numpy as np


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
        """ Get RenderWindow's eventManager """
        return self._eventManager
    @eventManager.setter
    def eventManager(self, value):
        self._eventManager = value
        
    @property #name
    def scene(self):
        """ Get RenderWindow's Scene reference """
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


class SDL2Window(RenderWindow):
    """ The concrete subclass of RenderWindow for the SDL2 GUI API 

    :param RenderWindow: [description]
    :type RenderWindow: [type]
    """
    
    def __init__(self, windowWidth = None, windowHeight = None, windowTitle = None, scene = None, eventManager = None, openGLversion = 4):
        """Constructor SDL2Window for basic SDL2 parameters

        :param windowWidth: [description], defaults to None
        :type windowWidth: [type], optional
        :param windowHeight: [description], defaults to None
        :type windowHeight: [type], optional
        :param windowTitle: [description], defaults to None
        :type windowTitle: [type], optional
        """
        super().__init__()
        
        self._gWindow = None
        self._gContext = None
        self._gVersionLabel = "None"

        self.openGLversion = openGLversion
        
        if windowWidth is None:
            self._windowWidth = 1024
        else:
            self._windowWidth = windowWidth
        
        if windowHeight is None:
            self._windowHeight = 768
        else:
            self._windowHeight = windowHeight
            
        if windowTitle is None:
            self._windowTitle = "SDL2Window"
        else:
            self._windowTitle = windowTitle
        
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
        Initialise an SDL2 RenderWindow, not directly but via the SDL2Decorator
        """
        print(f'{self.getClassName()}: init()')
        
        #SDL_Init for the window initialization
        sdl_not_initialised = sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO | sdl2.SDL_INIT_TIMER)
        if sdl_not_initialised !=0:
            print("SDL2 could not be initialised! SDL Error: ", sdl2.SDL_GetError())
            exit(1)
        
        #setting OpenGL attributes for the GL state
        sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_CONTEXT_FLAGS,
                                 sdl2.SDL_GL_CONTEXT_FORWARD_COMPATIBLE_FLAG
                                 )
        sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_CONTEXT_PROFILE_MASK,
                                 sdl2.SDL_GL_CONTEXT_PROFILE_CORE
                                 )
        sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_DOUBLEBUFFER, 1)
        
        sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_ACCELERATED_VISUAL, 1)
        

        sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_DEPTH_SIZE, 24)
        sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_STENCIL_SIZE, 8)   
        sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_MULTISAMPLEBUFFERS, 1)

        
        if self.openGLversion==3:
            print("="*24)
            print("Using OpenGL version 3.2")
            print("="*24)
            sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_CONTEXT_MAJOR_VERSION, 3)
            sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_CONTEXT_MINOR_VERSION, 2)    
        else: 
            print("="*24)
            print("Using OpenGL version 4.1")
            print("="*24)
            sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_CONTEXT_MAJOR_VERSION, 4)
            sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_CONTEXT_MINOR_VERSION, 1)

                     
            
        # Linux doesn't like SDL_GL_MULTISAMPLESAMPLES
        if platform == "linux" or platform == "linux2":
            pass
        else:
            sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_MULTISAMPLESAMPLES, 16)        
        
        sdl2.SDL_SetHint(sdl2.SDL_HINT_MAC_CTRL_CLICK_EMULATE_RIGHT_CLICK, b"1")
        sdl2.SDL_SetHint(sdl2.SDL_HINT_VIDEO_HIGHDPI_DISABLED, b"1")
        
        #creating the SDL2 window
        self._gWindow = sdl2.SDL_CreateWindow(self._windowTitle.encode(), 
                                              sdl2.SDL_WINDOWPOS_CENTERED,
                                              sdl2.SDL_WINDOWPOS_CENTERED,
                                              self._windowWidth,
                                              self._windowHeight,
                                            #   sdl2.SDL_WINDOW_ALLOW_HIGHDPI)
                                              sdl2.SDL_WINDOW_OPENGL,
                                              sdl2.SDL_WINDOW_RESIZABLE)
        if self._gWindow is None:
            print("Window could not be created! SDL Error: ", sdl2.SDL_GetError())
            exit(1)
            
        #create the OpenGL context for rendering into the SDL2Window that was constructed just before
        self._gContext = sdl2.SDL_GL_CreateContext(self._gWindow)
        if self._gContext is None:
            print("OpenGL Context could not be created! SDL Error: ", sdl2.SDL_GetError())
            exit(1)
        sdl2.SDL_GL_MakeCurrent(self._gWindow, self._gContext)
        if sdl2.SDL_GL_SetSwapInterval(1) < 0:
            print("Warning: Unable to set VSync! SDL Error: ", sdl2.SDL_GetError())
            # exit(1)
        #obtain the GL versioning system info
        self._gVersionLabel = f'OpenGL {gl.glGetString(gl.GL_VERSION).decode()} GLSL {gl.glGetString(gl.GL_SHADING_LANGUAGE_VERSION).decode()} Renderer {gl.glGetString(gl.GL_RENDERER).decode()}'
        print(self._gVersionLabel)
    
    
    def init_post(self):
        """
        Post init method for SDL2
        this should be ctypiically alled AFTER all other GL contexts have been created
        """
        pass
    
    
    def display(self):
        """
        Main display window method to be called standalone or from within a concrete Decorator
        """
        #GPTODO make background clear color as parameter at class level

            
        gl.glClearColor(*self._colorEditor, 1.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        gl.glDisable(gl.GL_CULL_FACE)
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glDepthFunc(gl.GL_LESS)
        # gl.glDepthFunc(gl.GL_LEQUAL);
        
        
        
        # gl.glDepthMask(gl.GL_FALSE);  
    
    
        #gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)
        
        #setup some extra GL state flags
        if self._wireframeMode:
            gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_LINE)
            #print(f"SDL2Window:display() set wireframemode: {self._wireframeMode}")
        else:
            gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)
            #print(f"SDL2Window:display() set wireframemode: {self._wireframeMode}")
            
        #print(f'{self.getClassName()}: display()')
    
    
    def display_post(self):
        """
        To be called at the end of each drawn frame to swap double buffers
        """
        sdl2.SDL_GL_SwapWindow(self._gWindow)
        #print(f'{self.getClassName()}: display_post()')       
    
    
    def shutdown(self):
        """
        Shutdown and cleanup SDL2 operations
        """
        print(f'{self.getClassName()}: shutdown()')
        if (self._gContext and self._gWindow is not None):
            sdl2.SDL_GL_DeleteContext(self._gContext)
            sdl2.SDL_DestroyWindow(self._gWindow)
            sdl2.SDL_Quit()   


    def event_input_process(self):
    #def event_input_process(self, running = True):
        """
        process SDL2 basic events and input
        """
        running = True
        events = sdl2.ext.get_events()
        for event in events:
            if event.type == sdl2.SDL_KEYDOWN:
                if event.key.keysym.sym == sdl2.SDLK_ESCAPE:
                    running = False
            if event.type == sdl2.SDL_QUIT:
                running = False
        return running
    
    def accept(self, system: Elements.pyECSS.System, event = None):
        system.apply2SDLWindow(self, event)


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
        
        
    def event_input_process(self):
        """
        extra decorator method to handle input events
        :param running: [description], defaults to True
        :type running: bool, optional
        """
        return self._wrapeeWindow.event_input_process()
    
    
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
                    
class ImGUIDecorator(RenderDecorator):
    """
    ImGUI decorator

    :param RenderDecorator: [description]
    :type RenderDecorator: [type]
    """
    def __init__(self, wrapee: RenderWindow, imguiContext = None):
        super().__init__(wrapee)
        if imguiContext is None:
            self._imguiContext = imgui.create_context()
        else:
            self._imguiContext = imguiContext
        self._imguiRenderer = None
        #setup a simple Event: change to wireframe mode via the GUI
        self._updateWireframe = None
        self._updateCamera = None
        # extra UI elements
        self._wireframeMode = False
        self._changed = False 
        self._checkbox = False 
        self._colorEditor = wrapee._colorEditor
        self._eye = (2.5, 2.5, 2.5)
        self._target = (0.0, 0.0, 0.0) 
        self._up = (0.0, 1.0, 0.0)
       
    def init(self):
        """
        Calls Decoratee init() and also sets up events
        """
        self.wrapeeWindow.init()
        if self._imguiContext is None:
            print("Window could not be created! ImGUI Error: ")
            exit(1)
        else:
            # print("Yay! ImGUI context created successfully")
            pass
        
        # GPTODO here is the issue: SDL2Decorator takes an SDLWindow as wrappee wheras
        # ImGUIDEcorator takes and SDL2Decorator and decorates it!
        if isinstance(self.wrapeeWindow, SDL2Window):   
            self._imguiRenderer = SDL2Renderer(self.wrapeeWindow._gWindow)
            
        #
        # Setting up events that this class is publishing (if the EventManager is present in the decorated wrappee)
        #
        self._updateWireframe = Elements.pyECSS.Event.Event(name="OnUpdateWireframe", id=201, value=None)
        if self._wrapeeWindow.eventManager is not None:
            self._wrapeeWindow.eventManager._events[self._updateWireframe.name] = self._updateWireframe
            self._wrapeeWindow.eventManager._publishers[self._updateWireframe.name] = self
        
        
        self._updateCamera = Elements.pyECSS.Event.Event(name="OnUpdateCamera", id=300, value=None)
        if self._wrapeeWindow.eventManager is not None:
            self._wrapeeWindow.eventManager._events[self._updateCamera.name] = self._updateCamera
            self._wrapeeWindow.eventManager._publishers[self._updateCamera.name] = self
        
        # print(f'{self.getClassName()}: init()')
        
        
    def display(self):
        """
        ImGUI decorator display: calls wrapee (RenderWindow::display) as well as extra ImGUI widgets
        """
        self.wrapeeWindow.display()
        gl.glClearColor(*self._colorEditor, 1.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        #render the ImGUI widgets
        self.extra()
        #draw scenegraph tree widget
        self.scenegraphVisualiser()
        #print(f'{self.getClassName()}: display()')
        
        
        
        
    def display_post(self):
        # this is important to draw the ImGUI in full mode and not wireframe!
        gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)
        
        # render imgui (after 3D scene and just before the SDL double buffer swap window)
        imgui.render()
        self._imguiRenderer.render(imgui.get_draw_data())


        # call the SDL window window swapping in the end of the scene as final render action
        self.wrapeeWindow.display_post()
        
        
    def extra(self):
        """sample ImGUI widgets to be rendered on a RenderWindow
        """
        imgui.set_next_window_size(300.0, 200.0)
        
        #start new ImGUI frame context
        imgui.new_frame()
        #demo ImGUI window with all widgets
        # imgui.show_test_window()
        #new custom imgui window
        imgui.begin("Elements ImGUI window", True)
        #labels inside the window
        imgui.text("PyImgui + PySDL2 integration successful!")
        imgui.text(self._wrapeeWindow._gVersionLabel)
        
        # populate window with extra UI elements
        imgui.separator()
        imgui.new_line()
        #
        # wireframe Event updates the GL state
        self._changed, self._checkbox = imgui.checkbox("Wireframe", self._wireframeMode)
        if self._changed:
            if self._checkbox is True:
                self._wireframeMode = True
                self._updateWireframe.value = self._wireframeMode
                if self._wrapeeWindow.eventManager is not None:
                    self.wrapeeWindow.eventManager.notify(self, self._updateWireframe) 
                print(f"wireframe: {self._wireframeMode}")
            if self._checkbox is False:
                self._wireframeMode = False
                self._updateWireframe.value = self._wireframeMode
                if self._wrapeeWindow.eventManager is not None:
                    self.wrapeeWindow.eventManager.notify(self, self._updateWireframe) 
                print(f"wireframe: {self._wireframeMode}")
        #
        # simple slider for color
        self._changed, self._colorEditor = imgui.color_edit3("Color edit", *self._colorEditor)
        if self._changed:
            print(f"_colorEditor: {self._colorEditor}")
        imgui.separator()
        #
        # START
        # simple slider for eye - IMPORTANT PART HERE
        self._changed, self._eye = imgui.drag_float3( "Eye", *self._eye, change_speed = 0.01, min_value=-10, max_value=10,format="%.3f")
        if self._changed:
            self._updateCamera.value = util.lookat(util.vec(self._eye), util.vec(self._target), util.vec(self._up))
            print ("NEW CAMERA VALUE", self._updateCamera.value)
            if self._wrapeeWindow.eventManager is not None:
                    self.wrapeeWindow.eventManager.notify(self, self._updateCamera)
            print(f"_eye: {self._eye}")
        imgui.separator()
        #
        # simple slider for target
        self._changed, self._target = imgui.drag_float3( "Target", *self._target, change_speed = 0.01, min_value=-10, max_value=10,format="%.3f")
        if self._changed:
            self._updateCamera.value = util.lookat(util.vec(self._eye), util.vec(self._target), util.vec(self._up))
            print ("NEW CAMERA VALUE", self._updateCamera.value)
            if self._wrapeeWindow.eventManager is not None:
                self.wrapeeWindow.eventManager.notify(self, self._updateCamera)
            print(f"_target: {self._target}")
        imgui.separator()
        # simple slider for up
        self._changed, self._up = imgui.drag_float3( "Up", *self._up, change_speed = 0.01 ,min_value=-5, max_value=5,format="%.3f")
        if self._changed:
            self._updateCamera.value = util.lookat(util.vec(self._eye), util.vec(self._target), util.vec(self._up))
            print ("NEW CAMERA VALUE", self._updateCamera.value)
            if self._wrapeeWindow.eventManager is not None:
                self.wrapeeWindow.eventManager.notify(self, self._updateCamera)
            print(f"_up: {self._up}")
        imgui.separator()
        # END
        # simple FPS counter
        strFrameRate = str(("Application average: ", imgui.get_io().framerate, " FPS"))
        imgui.text(strFrameRate)
        #end imgui frame context
        imgui.end()
        
        #print(f'{self.getClassName()}: extra()')
    
    def scenegraphVisualiser(self):
        """display the ECSS in an ImGUI tree node structure
        Typically this is a custom widget to be extended in an ImGUIDecorator subclass 
        """
        pass
        
        
    def accept(self, system: Elements.pyECSS.System, event = None):
        system.apply2ImGUIDecorator(self, event)

class ImGUIecssDecorator(ImGUIDecorator):
    """custom ImGUI decorator for this example

    :param ImGUIDecorator: [description]
    :type ImGUIDecorator: [type]
    """
    def __init__(self, wrapee: RenderWindow, imguiContext = None):
        super().__init__(wrapee, imguiContext)
        self.selected = None; # Selected should be a component

        # TRS Variables 
        self.translation = {};
        self.translation["x"] = 0; self.translation["y"] = 0; self.translation["z"] = 0; 

        self.rotation = {};
        self.rotation["x"] = 0; self.rotation["y"] = 0; self.rotation["z"] = 0; 

        self.scale = {};
        self.scale["x"] = 0; self.scale["y"] = 0; self.scale["z"] = 0; 

        self.color = [255, 50, 50];
        self._mouse_x = 0
        self._mouse_y = 0
        self.lctrl = False
        
        self.traverseCamera()

    def scenegraphVisualiser(self):
        """display the ECSS in an ImGUI tree node structure
        Typically this is a custom widget to be extended in an ImGUIDecorator subclass 
        """
        sceneRoot = self.wrapeeWindow.scene.world.root.name
        if sceneRoot is None:
            sceneRoot = "ECSS Root Entity"
        
        twoColumn = False

        if twoColumn:
            # 2 Column Version
            imgui.begin("ECSS graph")
            imgui.columns(2,"Properties")
            if imgui.tree_node(sceneRoot, imgui.TREE_NODE_OPEN_ON_ARROW):
                self.drawNode(self.wrapeeWindow.scene.world.root)
                imgui.tree_pop()
            imgui.next_column()
            imgui.text("Properties")
            imgui.separator()
        else:
            imgui.begin("ECSS graph")
            imgui.columns(1,"Properties")
            # below is a recursive call to build-up the whole scenegraph as ImGUI tree
            # if imgui.tree_node(sceneRoot, imgui.TREE_NODE_OPEN_ON_ARROW):
                # self.drawNode(self.wrapeeWindow.scene.world.root)
                # imgui.tree_pop()
            # imgui.next_column()
            imgui.text("Properties")
            imgui.separator()


        # smallerTRSgui = True
        #TRS sample
        # if(isinstance(self.selected, BasicTransform)):

        if imgui.tree_node("Translation", imgui.TREE_NODE_OPEN_ON_ARROW):
            # changed, value = imgui.slider_float("X", self.translation["x"], -3, 3, "%.01f", 1);
            # self.translation["x"] = value;
            # changed, value = imgui.slider_float("Y", self.translation["y"], -3, 3, "%.01f", 1);
            # self.translation["y"] = value;
            # changed, value = imgui.slider_float("Z", self.translation["z"], -3, 3, "%.01f", 1);
            # self.translation["z"] = value;
            changed, value = imgui.drag_float3("X,Y,Z",self.translation["x"],self.translation["y"],self.translation["z"], 0.01, -30, 30, "%.001f", 1);
            self.translation["x"],self.translation["y"],self.translation["z"] = value[0],value[1], value[2]
            imgui.tree_pop();
        if imgui.tree_node("Rotation", imgui.TREE_NODE_OPEN_ON_ARROW):
            # changed, value = imgui.slider_float("X", self.rotation["x"], -90, 90, "%.1f", 1);
            # self.rotation["x"] = value;
            # changed, value = imgui.slider_float("Y", self.rotation["y"], -90, 90, "%.1f", 1);
            # self.rotation["y"] = value;
            # changed, value = imgui.slider_float("Z", self.rotation["z"], -90, 90, "%.1f", 1);
            # self.rotation["z"] = value;
            changed, value = imgui.drag_float3("X,Y,Z",self.rotation["x"],self.rotation["y"],self.rotation["z"], 1, -180, 180, "%.1f", 1);
            self.rotation["x"],self.rotation["y"],self.rotation["z"] = value[0],value[1], value[2]
            imgui.tree_pop();
        if imgui.tree_node("Scale", imgui.TREE_NODE_OPEN_ON_ARROW):
            # changed, value = imgui.slider_float("X", self.scale["x"], 0, 3, "%.01f", 1);
            # self.scale["x"] = value;
            # changed, value = imgui.slider_float("Y", self.scale["y"], 0, 3, "%.01f", 1);
            # self.scale["y"] = value;
            # changed, value = imgui.slider_float("Z", self.scale["z"], 0, 3, "%.01f", 1);
            # self.scale["z"] = value;
            changed, value = imgui.drag_float3("X,Y,Z",self.scale["x"],self.scale["y"],self.scale["z"], 0.01, 0, 4, "%.01f", 1);
            self.scale["x"],self.scale["y"],self.scale["z"] = value[0],value[1], value[2]
            imgui.tree_pop();

        
        if twoColumn:
            pass
        else:
            imgui.separator()
            if imgui.tree_node(sceneRoot, imgui.TREE_NODE_OPEN_ON_ARROW):
                self.drawNode(self.wrapeeWindow.scene.world.root)
                imgui.tree_pop()

        imgui.end()
        
    def drawNode(self, component):
        #create a local iterator of Entity's children
        if component._children is not None:
            debugIterator = iter(component._children)
            #call print() on all children (Concrete Components or Entities) while there are more children to traverse
            done_traversing = False
            while not done_traversing:
                try:
                    comp = next(debugIterator)
                    imgui.indent(10)
                except StopIteration:
                    done_traversing = True
                else:
                    # using ## creates unique labels, without showing anything after ##
                    # see: https://github.com/ocornut/imgui/blob/master/docs/FAQ.md#q-how-can-i-have-multiple-widgets-with-the-same-label
                    if imgui.tree_node(comp.name + "##" + str(comp.id), imgui.TREE_NODE_OPEN_ON_ARROW):
                        imgui.text(comp.name)
                        _, selected = imgui.selectable(comp.__str__(), True)
                        if selected:

                            if comp != self.selected: # First time selecting it. Set trs values to GUI;
                                self.selected = comp;
                                if isinstance(comp, BasicTransform):
                                    [x, y, z] = comp.translation;
                                    self.translation["x"] = x;
                                    self.translation["y"] = y;
                                    self.translation["z"] = z;
                                    [x, y, z] = comp.scale;
                                    self.scale["x"] = x;
                                    self.scale["y"] = y;
                                    self.scale["z"] = z;
                                    [x, y, z] = comp.rotationEulerAngles;
                                    self.rotation["x"] = x;
                                    self.rotation["y"] = y;
                                    self.rotation["z"] = z;
                                # elif isinstance(comp, GameObjectEntity):
                                    # self.color = comp.color.copy();
                            else:                       # Set GUI values to trs;
                                if isinstance(comp, BasicTransform):
                                    transMat = util.translate(self.translation["x"], self.translation["y"], self.translation["z"]);
                                    rotMatX = util.rotate((1, 0, 0), self.rotation["x"])
                                    rotMatY = util.rotate((0, 1, 0), self.rotation["y"])
                                    rotMatZ = util.rotate((0, 0, 1), self.rotation["z"])
                                    scaleMat = util.scale(self.scale["x"], self.scale["y"], self.scale["z"])

                                    comp.trs = util.identity() @ transMat @ rotMatX @ rotMatY @ rotMatZ @ scaleMat;
                                    # comp.trs = scaleMat @ rotMatZ @ rotMatY @ rotMatX @ transMat;
                                elif hasattr(comp, "drawSelfGui"):
                                    comp.drawSelfGui(imgui);

                        imgui.tree_pop()
                    
                    self.drawNode(comp) # recursive call of this method to traverse hierarchy
                    imgui.unindent(10) # Corrent placement of unindent

    
    def traverseCamera(self):
        self.cam = None
        found = False
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
                    if comp.name == "Simple Camera":
                        self.cam = comp
                        found = True
                        
    def updateCamera(self):                   
        transMat = util.translate(self.translation["x"], self.translation["y"], self.translation["z"])
        rotMatX = util.rotate((1, 0, 0), self.rotation["x"])
        rotMatY = util.rotate((0, 1, 0), self.rotation["y"])
        rotMatZ = util.rotate((0, 0, 1), self.rotation["z"])
        scaleMat = util.scale(self.scale["x"], self.scale["y"], self.scale["z"])
        combinedMat = transMat @ rotMatX @ rotMatY @ rotMatZ @ scaleMat
        if self.cam != None:
            self.cam.trans1.trs = self.cam.trans1.trs @ combinedMat
        # else:
        #     eyeMat = combinedMat @ np.transpose(np.matrix([self._eye[0], self._eye[1], self._eye[2], 1])) 

        #     temp = list(self._eye)
        #     temp[0] = eyeMat[0,0] 
        #     temp[1] = eyeMat[1,0] 
        #     temp[2] = eyeMat[2,0]
        #     #self._eye = tuple(temp)

        #     targetMat = transMat @ np.transpose(np.matrix([self._eye[0], self._eye[1], self._eye[2], 1]))  
            
        #     temp = list(self._target)
        #     temp[0] = targetMat[0,0] 
        #     temp[1] = targetMat[1,0] 
        #     temp[2] = targetMat[2,0]
        #     self._target = tuple(temp)

        #     self._updateCamera.value = util.lookat(util.vec(self._eye), util.vec(self._target), util.vec(self._up))
        #     if self._wrapeeWindow.eventManager is not None:
        #         self.wrapeeWindow.eventManager.notify(self, self._updateCamera)
        
    def cameraRotate(self, offset_x, offset_y, offset_z):
        """Called when mouse buttons are pressed and the mouse is dragged.
        
            event: sdl2.events.SDL_Event, 
            x: horiz coord relative to window, y: vert coord relative to window,
            dx: relative horizontal motion, dy: relative vertical motion
            button: RIGHT - MIDDLE - LEFT
        """

        print("camera rotate ")
        print(offset_x, offset_y, offset_z)
  
        self.translation["x"] = 0.0
        self.translation["y"] = 0.0
        self.translation["z"] = 0.0
        self.rotation["x"] = offset_x
        self.rotation["y"] = offset_y
        self.rotation["z"] = offset_z
        self.scale["x"]= 1.0
        self.scale["y"]= 1.0
        self.scale["z"]= 1.0
        self.updateCamera()   


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

    def cameraMove(self, offset_x, offset_y, offset_z):
        """Called when the mouse wheel is scrolled.

            event: sdl2.events.SDL_Event, 
            offset_x: horizontal scroll, positive - negative 
            offset_y (int): vertical scroll, positive - negative 
        """
        print("mouse move ")
        print(offset_x, offset_y, offset_z)

        self.translation["x"] = offset_x 
        self.translation["y"] = offset_y
        self.translation["z"] = offset_z
        self.rotation["x"] = 0.0
        self.rotation["y"] = 0.0
        self.rotation["z"] = 0.0
        self.scale["x"]= 1.0
        self.scale["y"]= 1.0
        self.scale["z"]= 1.0
        self.updateCamera()
 
    def event_input_process(self):
        """
        process SDL2 basic events and input
        """
        #width = self.wrapeeWindow.scene._renderWindow.windowWidth
        running = True
        events = sdl2.ext.get_events()
        for event in events:
            
            #height = self.wrapeeWindow.scene._gWindow._windowHeight
            #width = self._gWindow._windowWidth
            #on mouse motion on_mouse_drag
            if event.type == sdl2.SDL_MOUSEWHEEL:
                keystatus = sdl2.SDL_GetKeyboardState(None)

                if keystatus[sdl2.SDL_SCANCODE_LSHIFT]:
                    offset_x = event.wheel.x/1024*60
                    offset_y = event.wheel.y/1024*60
                    offset_z = 0.0
                    self.cameraMove(offset_x, offset_y, offset_z)
                elif keystatus[sdl2.SDL_SCANCODE_LCTRL] or self.lctrl:
                    offset_x = 0.0
                    offset_y = 0.0
                    offset_z = -event.wheel.y/1024*60
                    self.cameraMove(offset_x, offset_y, offset_z)
                else:
                    offset_x = -event.wheel.y/1024*360*5
                    offset_y = event.wheel.x/1024*360*5
                    offset_z = 0.0
                    self.cameraRotate(offset_x, offset_y, offset_z)
                
                # x = event.motion.x
                # y = event.motion.y
                # buttons = event.motion.state
                # if buttons & sdl2.SDL_BUTTON_LMASK and 
                #     dx = (x - self._mouse_x)/1024*60
                #     dy = (y - self._mouse_y)/1024*60
                #     button = "LEFT"
                #     self.on_mouse_drag(event, self._mouse_x, self._mouse_y, dx, dy, button)
                # elif buttons & sdl2.SDL_BUTTON_MMASK:
                #     button = "MIDDLE"
                #     self.on_mouse_drag(event, self._mouse_x, self._mouse_y, dx, dy, button)
                # elif buttons & sdl2.SDL_BUTTON_RMASK:
                #     dx = (x - self._mouse_x)/1024*360
                #     dy = (y - self._mouse_y)/1024*360
                #     button = "RIGHT"
                #     self.on_mouse_drag(event, self._mouse_x, self._mouse_y, dx, dy, button)
                # else:
                #     #dx = (x - self._mouse_x)
                #     #dx = (y - self._mouse_y)
                #     #self.on_mouse_motion(event, self._mouse_x, self._mouse_y, dx, dy,)
                #     pass
                # self._mouse_x = x
                # self._mouse_y = y
                continue

            if event.type == sdl2.SDL_MOUSEBUTTONUP:
                pass

            # on_mouse_press
            if event.type == sdl2.SDL_MOUSEBUTTONDOWN:
                # x = event.button.x
                # y = event.button.y
                # self._mouse_x = x
                # self._mouse_y = y
                
                # button_n = event.button.button
                # if button_n == sdl2.SDL_BUTTON_LEFT:
                #     button = "LEFT"
                # elif button_n == sdl2.SDL_BUTTON_RIGHT:
                #     button = "RIGHT"
                # elif button_n == sdl2.SDL_BUTTON_MIDDLE:
                #     button = "MIDDLE"

                # double = bool(event.button.clicks - 1)
                # self.on_mouse_press(event, x, y, button, double)
                continue

            #keyboard events
            if event.type == sdl2.SDL_KEYDOWN:
                if event.key.keysym.sym == sdl2.SDLK_UP or event.key.keysym.sym == sdl2.SDLK_w :
                    pass
                if event.key.keysym.sym == sdl2.SDLK_DOWN or event.key.keysym.sym == sdl2.SDLK_s :
                    pass
                if event.key.keysym.sym == sdl2.SDLK_LEFT or event.key.keysym.sym == sdl2.SDLK_a :
                    pass
                if event.key.keysym.sym == sdl2.SDLK_RIGHT or event.key.keysym.sym == sdl2.SDLK_d :
                    pass
                if event.key.keysym.sym == sdl2.SDLK_LCTRL:
                    self.lctrl=True
                if event.key.keysym.sym == sdl2.SDLK_ESCAPE:
                    running = False

            if event.type == sdl2.SDL_KEYUP and event.key.keysym.sym == sdl2.SDLK_LCTRL:
                self.lctrl = False

            if event.type == sdl2.SDL_QUIT:
                running = False
            #imgui event
            self._imguiRenderer.process_event(event)
            
        #imgui input
        self._imguiRenderer.process_inputs()
        
        return running
        

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
            
    
    def apply2SDLWindow(self, sdlWindow, event = None):
        """method for  behavioral or logic computation 
        when visits Components. 
        
        In this case update GL State from SDLWindow

        :param sdlWindow: [description]
        :type sdlWindow: [type]
        :param event: [description], defaults to None
        :type event: [type], optional
        """
        if event.name == "OnUpdateWireframe":
            # print(f"RenderGLStateSystem():apply2SDLWindow() actuator system for: {event}")
            sdlWindow._wireframeMode = event.value

        if event.name == "OnUpdateCamera":
            # print(f"OnUpdateCamera: RenderGLStateSystem():apply2SDLWindow() actuator system for: {event}")
            sdlWindow._myCamera = event.value
        
        


if __name__ == "__main__":
    # # The client code.
    gWindow = SDL2Window(openGLversion=3) # uses openGL version 3.2 instead of the default 4.1
    gWindow.init()
    gWindow.init_post()
    running = True
    # MAIN RENDERING LOOP
    while running:
        gWindow.display()
        running = gWindow.event_input_process()
        gWindow.display_post()
    gWindow.shutdown()