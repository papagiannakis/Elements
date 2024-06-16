"""
Scene classes
    
Singleton class to assemble Elements.pyECSS::ECSSManager and Elements.pyGLV::Viewer objects

"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Dict

from Elements.pyECSS.ECSSManager import ECSSManager
from Elements.pyGLV.GUI.Viewer import GLFWWindow
from Elements.pyGLV.GUI.ImguiDecorator import ImGUIecssDecorator, ImGUIDecorator

class Scene():
    """
    Singleton Scene that assembles ECSSManager and Viewer classes together for Scene authoring
    in pyglGA. It also brings together the new extensions to pyglGA: Shader, VertexArray and 
    RenderMeshDecorators
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Scene, cls).__new__(cls)
            cls._renderWindow = None
            cls._gContext = None
            cls._world = ECSSManager() #which also instantiates an EventManager
            # add further init here
        return cls._instance
    
    
    def __init__(self):
        None;
    
    @property
    def renderWindow(self):
        return self._renderWindow
    
    @property
    def gContext(self):
        return self._gContext
    
    @property
    def world(self):
        return self._world
    
    
    def init(self, glfw = True, imgui = False, windowWidth = None, windowHeight = None, windowTitle = None, 
            customImGUIdecorator = None, openGLversion = 4):
        """call the init() of all systems attached to this Scene based on the Visitor pattern
        """
        #init Viewer GUI subsystem with just SDL2 window or also an ImGUI decorators
        if glfw == True:
            #create a basic SDL2 RenderWindow with a reference to the Scene and thus ECSSManager and EventManager
            # self._renderWindow = SDL2Window(windowWidth, windowHeight, windowTitle, self, openGLversion = openGLversion)
            # self._gContext = self._renderWindow 
            self._renderWindow = GLFWWindow(windowHeight=windowHeight, windowWidth=windowWidth, windowTitle=windowTitle, scene=self, openGLveriosn=openGLversion)
            self._gContext = self._renderWindow
        
        if imgui == True and customImGUIdecorator == None:
            gGUI = ImGUIDecorator(self._renderWindow)
            self._gContext = gGUI
        elif imgui == True and customImGUIdecorator is not None:
            gGUI = customImGUIdecorator(self._renderWindow)
            self._gContext = gGUI
    
        
        self._gContext.init()
        self._gContext.init_post()
    
    
    def update(self):
        """call the update() of all systems attached to this Scene based on the Visitor pattern
        """
        pass
    
    
    def processInput(self):
        """process the user input per frame based on Strategy and Decorator patterns
        """
        pass
    
        
    def render(self):
        """call the render() of all systems attached to this Scene based on the Visitor pattern
        """
        still_runnning = self._gContext.event_input_process()
        self._gContext.display()
        
        return still_runnning
    
    def render_post(self):
        self._gContext.display_post()
    
    def run(self):
        """main loop Scene method based on the "gameloop" game programming pattern
        """
        pass
    
    
    def shutdown(self):
        """main shutdown Scene method based on the "gameloop" game programming pattern
        """
        self._gContext.shutdown()


if __name__ == "__main__":
    # The client singleton code.

    s1 = Scene()
    s2 = Scene()

    if id(s1) == id(s2):
        print("Singleton works, both Scenes contain the same instance.")
    else:
        print("Singleton failed, Scenes contain different instances.")
        