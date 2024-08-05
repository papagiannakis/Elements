"""
Running the basic RenderWindow (SDL2Window) with an ImGUIDecorator on top
"""
from Elements.pyGLV.GUI.Viewer import GLFWWindow
from Elements.pyGLV.GUI.ImguiDecorator import ImGUIecssDecorator

from Elements.utils.Shortcuts import displayGUI_text
example_description = "This is a simple empty scene with ImGUI enabled. Feel free to add your own widgets!" 

    
gWindow = GLFWWindow()
gGUI = ImGUIecssDecorator(gWindow)

gGUI.init() #calls ImGUIDecorator::init()-->SDL2Window::init()



running = True
while running:
  gGUI.display()
  displayGUI_text(example_description)
  running = gGUI.event_input_process()
  gGUI.display_post()
gGUI.shutdown()
