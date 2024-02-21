"""
Running the basic RenderWindow with the concrete basic Compoment of the decorator
patter, that is the SDL2Window, without any decorator on top
"""

from Elements.pyGLV.GUI.Viewer import GLFWWindow

gWindow = GLFWWindow(windowTitle="A simple empty SDL WINDOW. Hit ESC OR Close the window to quit!")
gWindow.init()



running = True
# MAIN RENDERING LOOP

while running:
    gWindow.display()
    running = gWindow.event_input_process()
    gWindow.display_post()
gWindow.shutdown()
