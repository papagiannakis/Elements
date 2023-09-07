import Elements
import numpy as np
from Elements.pyECSS.Component import Component
from Elements.pyECSS.System import System

class AABoundingBox(Component):
    '''Axis Aligned bounding boxes'''
    def __init__(self, name=None, type=None, id=None, min_points=None, max_points=None, floor=None, density=0.01, hasGravity=True):
        """Just testing"""
        super().__init__(name, type, id)
        
        self._max_points = max_points
        self._min_points = min_points
        self._trans_max_points = max_points
        self._trans_min_points = min_points
        self._floor = floor
        self._density = density
        self._hasGravity = hasGravity
        self._collision = False

    @property
    def max_points(self):
        return self._max_points
    
    @max_points.setter
    def max_points(self, max_points):
        self._max_points = max_points

    @property
    def min_points(self):
        return self._min_points
    
    @min_points.setter
    def min_points(self, min_points):
        self._min_points = min_points
    
    @property
    def trans_max_points(self):
        return self._trans_max_points
    
    @trans_max_points.setter
    def trans_max_points(self, trans_max_points):
        self._trans_max_points = trans_max_points

    @property
    def trans_min_points(self):
        return self._trans_min_points
    
    @trans_min_points.setter
    def trans_min_points(self, trans_min_points):
        self._trans_min_points = trans_min_points
        
    @property
    def floor(self):
        return self._floor
    
    @floor.setter
    def floor(self, floor):
        self._floor = floor
        
    @property
    def collision(self):
        return self._collision
    
    @collision.setter
    def collision(self, collision):
        self._collision = collision
    
    @property
    def mass(self):
        return self._mass
    
    @mass.setter
    def mass(self, mass):
        self._mass = mass 
        
    @property
    def volume(self):
        return self._volume
    
    @volume.setter
    def volume(self, volume):
        self._volume = volume 
        
    @property
    def density(self):
        return self._density
    
    @density.setter
    def density(self, density):
        self._density = density 
    
    @property
    def hasGravity(self):
        return self._hasGravity
    
    @hasGravity.setter
    def hasGravity(self, hasGravity):
        self._hasGravity = hasGravity 
        
        
    def init(self):
        pass
    
    def update(self, **kwargs):
        "Debug Only"
        pass
    
    def accept(self, system: System, event = None):
        """
        Accepts a class object to operate on the Component, based on the Visitor pattern.

        :param system: [a System object]
        :type system: [System]
        """
        system.apply2BoundingBox(self)
        
    