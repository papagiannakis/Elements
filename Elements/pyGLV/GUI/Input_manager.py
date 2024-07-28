from __future__ import annotations

class InputManager():
    """
    Singleton class to manage input from the user. Provides methods to check key and button states
    and to get the mouse position.
    """

    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            print('Creating Scene Singleton Object')
            cls._instance = super(InputManager, cls).__new__(cls)  

            cls.canvas_monitor_instance = None

        return cls._instance 
    
    def __init__(self):
        None;  

    def set_monitor(self, instance): 
        """
        Set the canvas monitor instance that provides input state information.

        :param instance: The canvas monitor instance.
        """

        self.canvas_monitor_instance = instance

    def is_key_pressed(self, key): 
        """
        Check if a key is pressed.

        :param key: The key to check.
        :return: True if the key is pressed, False otherwise, or None if the monitor is not set.
        """

        if self.canvas_monitor_instance: 
            return self.canvas_monitor_instance.IsKeyPressed(key)  
        else: 
            return None 

    def is_button_pressed(self, button): 
        """
        Check if a mouse button is pressed.

        :param button: The mouse button to check.
        :return: True if the button is pressed, False otherwise, or None if the monitor is not set.
        """

        if self.canvas_monitor_instance: 
            return self.canvas_monitor_instance.IsButtonPressed(button)  
        else: 
            return None
    
    def get_mouse_pos(self):  
        """
        Get the current mouse position.

        :return: Tuple of (x, y) coordinates of the mouse position, or None if the monitor is not set.
        """

        if self.canvas_monitor_instance:
            return self.canvas_monitor_instance.GetMousePos() 
        else: 
            return None
