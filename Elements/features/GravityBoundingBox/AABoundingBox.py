"""
Axis Alinged bounding box class
    
@author Nikos Iliakis csd4375
"""
import numpy as np
from Elements.pyECSS.Component import Component
from GravityCollisonSystem import GravityCollisionSystem

"""Axis Aligned bounding boxes Class"""
class AABoundingBox(Component):
    def __init__(self, name=None, type=None, id=None, vertices=None, objectCollisionList=None, density=0.001, hasGravity=True):
        super().__init__(name, type, id)
        
        mins = [np.min(vertices[:, 0]), np.min(vertices[:, 1]), np.min(vertices[:, 2])]
        maxs = [np.max(vertices[:, 0]), np.max(vertices[:, 1]), np.max(vertices[:, 2])]
        
        self._vertices = [
            [mins[0], mins[1], mins[2], 1],
            [mins[0], mins[1], maxs[2], 1],
            [mins[0], maxs[1], mins[2], 1],
            [mins[0], maxs[1], maxs[2], 1],
            [maxs[0], mins[1], mins[2], 1],
            [maxs[0], mins[1], maxs[2], 1],
            [maxs[0], maxs[1], mins[2], 1],
            [maxs[0], maxs[1], maxs[2], 1],
        ]
            
        self._trans_max_points = mins
        self._trans_min_points = maxs
        
        self._objectCollisionList = objectCollisionList
        self._density = density
        self._hasGravity = hasGravity
        self._isColliding = False

    @property
    def vertices(self):
        return self._vertices
    
    @vertices.setter
    def vertices(self, vertices):
        self._vertices = vertices
    
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
    def objectCollisionList(self):
        return self._objectCollisionList
    
    @objectCollisionList.setter
    def objectCollisionList(self, objectCollisionList):
        self._objectCollisionList = objectCollisionList
        
    @property
    def isColliding(self):
        return self._isColliding
    
    @isColliding.setter
    def isColliding(self, isColliding):
        self._isColliding = isColliding
    
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
    
    def accept(self, system: GravityCollisionSystem, event = None):
        """
        Accepts a class object to operate on the Component, based on the Visitor pattern.

        :param system: [a System object]
        :type system: [System]
        """
        
        # We need this to check if the current system in accept is the GravityCollisionSystem
        # Because if it isnt it wont have apply2BoundingBox function and it will throw an error
        if hasattr(system, 'apply2BoundingBox'):
            system.apply2BoundingBox(self)   # Call the method if it exists
            
    