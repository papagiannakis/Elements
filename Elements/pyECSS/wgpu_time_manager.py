import time

class TimeStepManager: 
    """
    Singleton class that manages time steps for the ECS framework.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TimeStepManager, cls).__new__(cls)
            cls._instance.init()
        return cls._instance 
    
    def __init__(self) -> None: 
        None

    def init(self):
        """
        Initialize the time tracking variables.
        """ 

        self.last_time = time.time()
        self.time_step = 0.0

    def update(self): 
        """
        Update the time step based on the current time.
        
        :return: The time step since the last update.
        """ 
        
        current_time = time.time()
        self.time_step = current_time - self.last_time
        self.last_time = current_time 

        return self.time_step