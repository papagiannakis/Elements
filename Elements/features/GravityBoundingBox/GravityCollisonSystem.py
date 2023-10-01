"""
A Gravity Collision System that applies the force of gravity on entities, 
that have a RenderMesh a GravityCollisionSystem and a Transform
    
@author Nikos Iliakis csd4375
"""

import Elements
import Elements.pyECSS.math_utilities as util
import numpy as np
from Elements.pyECSS.System import System

'''
Conventions:
We assume objects can collide with only the floor not each other
We assume the moment an object collides with the floor its gravity is not applied anymore
'''
class GravityCollisionSystem(System):
    def __init__(self, name=None, type=None, id=None):
        super().__init__(name, type, id)
    
    def update(self):
        """
        method to be subclassed for  behavioral or logic computation 
        when visits Components of an EntityNode. 
        
        """
        pass
    
    '''aabb_comp: Elements.pyECSS.Component.AABoundingBox'''
    def apply2BoundingBox(self, aabb_comp: Elements.pyECSS.Component):
        
        # Checking if the aa bound box is not of the floors and if its not colliding with anything
        if(aabb_comp.hasGravity and aabb_comp.isColliding == False):
            self.apply_force_of_gravity(aabb_comp, 9.8)
        
        # Updating translated bounding_box_points
        basicTrans = self.getBasicTransformComp(aabb_comp.parent)
        if(basicTrans != None):
            trs_vertices = []
            for i in range(0, len(aabb_comp.vertices)):
                trs_vertices.append(list(basicTrans.trs @ aabb_comp.vertices[i]))
            
            # Calculate the maximum and minimum values for each component (x, y, z)
            max_x = max(vertex[0] for vertex in trs_vertices)
            max_y = max(vertex[1] for vertex in trs_vertices)
            max_z = max(vertex[2] for vertex in trs_vertices)

            min_x = min(vertex[0] for vertex in trs_vertices)
            min_y = min(vertex[1] for vertex in trs_vertices)
            min_z = min(vertex[2] for vertex in trs_vertices)

            # Set the transformed maximum and minimum points
            aabb_comp.trans_max_points = [max_x, max_y, max_z]
            aabb_comp.trans_min_points = [min_x, min_y, min_z]

            
        isItAlreadyColliding = aabb_comp.isColliding
        
        # Check if aa bound box is colliding with floor if so then set collision bool to true else false
        if(aabb_comp.objectCollisionList != None):
            aabb_comp.isColliding = self.check_list_for_collision(aabb_comp=aabb_comp)
        
        if(isItAlreadyColliding == False and aabb_comp.isColliding == True):
            aabb_comp.objectCollisionList.append(aabb_comp)            
    
    def check_list_for_collision(self, aabb_comp: Elements.pyECSS.Component):
        for col_object in aabb_comp.objectCollisionList:
            collision_bool = self.collision_with_other_aabb(aabb_comp=aabb_comp, other_aabb_comp=col_object)
            if(collision_bool == True): return True
        
        return False
    
    def collision_with_other_aabb(self, aabb_comp: Elements.pyECSS.Component, other_aabb_comp: Elements.pyECSS.Component):
        # Check if this AABB intersects with another AABB 
        return all(
            aabb_comp.trans_min_points[i] <= other_aabb_comp.trans_max_points[i]
            and aabb_comp.trans_max_points[i] >= other_aabb_comp.trans_min_points[i]
            for i in range(3)
        )
    
    def calculate_volume_mass_of_object(self, aabb_comp: Elements.pyECSS.Component):
        aabb_comp.volume = self.volume(aabb_comp)
        aabb_comp.mass = aabb_comp.density * aabb_comp.volume
        
    def apply_force_of_gravity(self, aabb_comp: Elements.pyECSS.Component, gravityAcceleration):
        self.calculate_volume_mass_of_object(aabb_comp)
        self.getBasicTransformComp(aabb_comp.parent).trs = util.translate(0, -aabb_comp.mass * gravityAcceleration, 0) @ self.getBasicTransformComp(aabb_comp.parent).trs
                
        
    def volume(self, bb_comp: Elements.pyECSS.Component):
        # Calculate the volume of the AABB
        width = bb_comp.trans_max_points[0] - bb_comp.trans_min_points[0]
        height = bb_comp.trans_max_points[1] - bb_comp.trans_min_points[1]
        depth = bb_comp.trans_max_points[2] - bb_comp.trans_min_points[2]
        return 1
    
    def getBasicTransformComp(self, parent):
        for i in range(0, parent.getNumberOfChildren()):
            childComp = parent.getChild(i)
            if(childComp.getClassName() == "BasicTransform"):
                return childComp
            
        return None