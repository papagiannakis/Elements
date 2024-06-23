import time

class TimeStepManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TimeStepManager, cls).__new__(cls)
            cls._instance.init()
        return cls._instance 
    
    def __init__(self) -> None: 
        None

    def init(self):
        self.last_time = time.time()
        self.time_step = 0.0

    def update(self):
        current_time = time.time()
        self.time_step = current_time - self.last_time
        self.last_time = current_time 

        return self.time_step