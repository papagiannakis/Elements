import Elements
import Elements.pyECSS.math_utilities as util
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
        # Check if aa bound box is colliding with floor if so then set collision bool to true else false
        if(aabb_comp.floor != None):
            aabb_comp.collision = self.collision_with_other_aabb(aabb_comp=aabb_comp, other_aabb_comp=aabb_comp.floor)
        
        # Checking if the aa bound box is not of the floors and if its not colliding with anything
        if(aabb_comp.hasGravity and aabb_comp.collision == False):
            self.apply_force_of_gravity(aabb_comp, 9.8)
        
        # Updating translated bounding_box_points
        basicTrans = self.getBasicTransformComp(aabb_comp.parent)
        if(basicTrans != None):
            aabb_comp.trans_max_points = basicTrans.l2world @ aabb_comp.max_points
            aabb_comp.trans_min_points = basicTrans.l2world @ aabb_comp.min_points
            self.trans_max_min_check(aabb_comp)
    
    def collision_with_other_aabb(self, aabb_comp: Elements.pyECSS.Component, other_aabb_comp: Elements.pyECSS.Component):
        # Check if this AABB intersects with another AABB
        return all(
            aabb_comp.trans_min_points[i] <= other_aabb_comp.max_points[i]
            and aabb_comp.trans_max_points[i] >= other_aabb_comp.min_points[i]
            for i in range(3)
        )
    
    def contains_point(self, bb_comp: Elements.pyECSS.Component, point):
        # Check if a point is inside the AABB
        return all(bb_comp.trans_min_points[i] <= point[i] <= bb_comp.trans_max_points[i] for i in range(3))
    
    def calculate_volume_mass_of_object(self, aabb_comp: Elements.pyECSS.Component):
        aabb_comp.volume = self.volume(aabb_comp)
        aabb_comp.mass = aabb_comp.density * aabb_comp.volume
        
    def apply_force_of_gravity(self, aabb_comp: Elements.pyECSS.Component, gravityAcceleration):
        self.calculate_volume_mass_of_object(aabb_comp)
        self.getBasicTransformComp(aabb_comp.parent).trs = util.translate(0, -aabb_comp.mass * gravityAcceleration, 0) @ self.getBasicTransformComp(aabb_comp.parent).trs
    
    def trans_max_min_check(self, aabb_comp: Elements.pyECSS.Component):
        #In case of rotation max and min coordinates may need to be swapped
        for i in range(3):
            if(aabb_comp.trans_max_points[i] < aabb_comp.trans_min_points[i]):
                temp = aabb_comp.trans_max_points[i]
                aabb_comp.trans_max_points[i] = aabb_comp.trans_min_points[i]
                aabb_comp.trans_min_points[i] = temp
                
        
    def volume(self, bb_comp: Elements.pyECSS.Component):
        # Calculate the volume of the AABB
        width = bb_comp.trans_max_points[0] - bb_comp.trans_min_points[0]
        height = bb_comp.trans_max_points[1] - bb_comp.trans_min_points[1]
        depth = bb_comp.trans_max_points[2] - bb_comp.trans_min_points[2]
        return width * height * depth
    
    def getBasicTransformComp(self, parent):
        for i in range(0, parent.getNumberOfChildren()):
            childComp = parent.getChild(i)
            if(childComp.getClassName() == "BasicTransform"):
                return childComp
            
        return None