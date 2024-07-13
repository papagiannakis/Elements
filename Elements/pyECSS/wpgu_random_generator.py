import numpy as np 

class RandomGenerator(): 
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            print('Creating RandomGenerator manager')
            cls._instance = super(RandomGenerator, cls).__new__(cls)  

            cls.max_index = 163840
            cls.range = np.random.random(cls.max_index) 
            cls.index = 0

        return cls._instance
    
    def __init__(self):
        None;  

    def get_random(self):
        if self.index == self.max_index:
            self.index = 0
        
        num = self.range[self.index]   
        self.index += 1
        return num