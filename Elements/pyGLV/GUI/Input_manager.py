from __future__ import annotations

class InputManager():
    """
    Singleton Scene that assembles ECSSManager and Viewer classes together for Scene authoring
    in pyglGA. It also brings together the new extensions to pyglGA: Shader, VertexArray and 
    RenderMeshDecorators
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
        self.canvas_monitor_instance = instance

    def is_key_pressed(self, key): 
        if self.canvas_monitor_instance: 
            return self.canvas_monitor_instance.IsKeyPressed(key)  
        else: 
            return None 

    def is_button_pressed(self, button): 
        if self.canvas_monitor_instance: 
            return self.canvas_monitor_instance.IsButtonPressed(button)  
        else: 
            return None
    
    def get_mouse_pos(self):  
        if self.canvas_monitor_instance:
            return self.canvas_monitor_instance.GetMousePos() 
        else: 
            return None
