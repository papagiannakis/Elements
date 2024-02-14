"""
Unit tests
Employing the unittest standard python test framework
https://docs.python.org/3/library/unittest.html
    
Elements.pyGLV (Computer Graphics for Deep Learning and Scientific Visualization)
@Copyright 2021-2022 Dr. George Papagiannakis
"""



import unittest
import time
import numpy as np

from Elements.pyGLV.GUI.Viewer import SDL2Window
from Elements.pyGLV.GUI.ImguiDecorator import ImGUIDecorator, ImGUIecssDecorator

class TestSDL2Window(unittest.TestCase):
    
    def setUp(self):
        """[summary]
        """
        self.gWindow = SDL2Window(windowTitle="Sample SDL WINDOW: Hit ESC OR Close the window to quit")
        self.gGUI = ImGUIDecorator(self.gWindow)
    
    #@unittest.skip("test_initSDL2Decorator or test_initSDL2Decorator, skipping the test")
    def test_initSDL2Decorator(self):
        """
        Running the basic RenderWindow with the concrete basic Compoment of the decorator
        patter, that is the SDL2Window, without any decorator on top
        """
        print("TestSDL2Window:test_initSDL2Decorator START".center(100, '-'))
        
        self.gWindow.init()
        
        
        running = True
        # MAIN RENDERING LOOP
        while running:
            self.gWindow.display()
            running = self.gWindow.event_input_process()
            self.gWindow.display_post()
        self.gWindow.shutdown()
        
        self.assertIsNotNone(self.gWindow)
        self.assertIsInstance(self.gWindow, SDL2Window)
        
        print("TestSDL2Window:test_initSDL2Decorator START".center(100, '-'))
        
    #@unittest.skip("test_initSDL2Decorator or test_initSDL2Decorator, skipping the test")    
    def test_initImGUIDecorator(self):
        """
        Running the basic RenderWindow (SDL2Window) with an ImGUIDecorator on top
        """
        print("TestSDL2Window:test_initImGUIDecorator START".center(100, '-'))
        
        self.gGUI.init() #calls ImGUIDecorator::init()-->SDL2Window::init()
        
        running = True
        # MAIN RENDERING LOOP
        while running:
            self.gGUI.display()
            running = self.gGUI.event_input_process()
            self.gGUI.display_post()
        self.gGUI.shutdown()
        
        self.assertIsNotNone(self.gWindow)
        self.assertIsNotNone(self.gGUI)
        self.assertIsInstance(self.gWindow, SDL2Window)
        self.assertIsInstance(self.gGUI, ImGUIDecorator)
        
        print("TestSDL2Window:test_initImGUIDecorator START".center(100, '-'))

if __name__ == "__main__":
    unittest.main(argv=[''], verbosity=3, exit=False)