from __future__ import annotations

import uuid

class Entity: 
    """
    Represents an entity in the ECS framework with a unique identifier. 
    """ 
    
    def __init__(self): 
        self.id = uuid.uuid4()