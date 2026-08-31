"""
Scene classes
    
Singleton class to assemble Elements.pyECSS::ECSSManager and Elements.pyGLV::Viewer objects

"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Dict

from Elements.pyECSS.ECSSManager import ECSSManager


class Scene():
    """
    Singleton Scene that assembles ECSSManager and Viewer classes together for Scene authoring
    in pyglGA. It also brings together the new extensions to pyglGA: Shader, VertexArray and 
    RenderMeshDecorators
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            print('Creating Scene Singleton Object')
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
    
    
    def init(self, sdl2 = True, imgui = False, windowWidth = None, windowHeight = None, windowTitle = None,
            customImGUIdecorator = None, openGLversion = 4, windowClass = None, imgui_bundle = True):
        """call the init() of all systems attached to this Scene based on the Visitor pattern

        ``imgui_bundle`` is enabled by default when available. Pass ``False`` to force classic
        pyimgui. The existing ImGui decorator and already-imported example GUI functions use the
        docking-capable bundle context without requiring example-specific changes.
        """
        bundle_backend = None
        if imgui and imgui_bundle:
            from Elements.pyGLV.GUI.ImguiBundle import create_imgui_bundle_backend, ImguiBundleBackend

            backend_name = getattr(windowClass, "BACKEND_NAME", "SDL2")
            if ImguiBundleBackend.native_libraries_ready(backend_name):
                ImguiBundleBackend.prepare_native_libraries(backend_name)
                bundle_backend = create_imgui_bundle_backend(backend_name)
            else:
                print("imgui_bundle native libraries were already loaded; falling back to classic pyimgui")

        #init Viewer GUI subsystem with just a RenderWindow or also an ImGUI decorator. `sdl2`
        #only gates whether a window is created at all (kept for backward compatibility); which
        #RenderWindow subclass is used is controlled by `windowClass` (e.g.
        #Elements.pyGLV.GUI.Windows.GLFWWindow), defaulting to SDL2Window as before.
        if sdl2 == True:
            from Elements.pyGLV.GUI.Windows import SDL2Window

            WindowCls = windowClass if windowClass is not None else SDL2Window
            #create a basic RenderWindow with a reference to the Scene and thus ECSSManager and EventManager
            self._renderWindow = WindowCls(windowWidth, windowHeight, windowTitle, self, openGLversion = openGLversion)
            self._gContext = self._renderWindow
        
        from Elements.pyGLV.GUI.ImguiDecorator import (
            ImGUIecssDecorator,
            ImGUIDecorator,
            configure_imgui_backend,
        )
        configure_imgui_backend(bundle_backend)

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
