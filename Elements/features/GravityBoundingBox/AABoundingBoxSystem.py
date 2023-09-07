import Elements
import numpy as np
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyECSS.System import System
from AABoundingBox import AABoundingBox
from floor import create_max_points_list #SHOULD CHANGE THIS MAYBE POSSIBLE IDIOT PROGRAMMING HERE
from floor import create_min_points_list #SHOULD CHANGE THIS MAYBE POSSIBLE IDIOT PROGRAMMING HERE

'''
In order to add bb we assume we must have basic transform and rendermesh
'''

class AABoundingBoxSystem(System):
    def __init__(self, name=None, type=None, id=None):
        super().__init__(name, type, id)
        floor_bb = None
    
    def update(self):
        """
        method to be subclassed for  behavioral or logic computation 
        when visits Components of an EntityNode. 
        
        """
        pass
    
    #THIS IS SUPER DUPER ILLEGAL
    @property
    def floor_bb(self):
        return self._floor_bb
    
    @floor_bb.setter
    def max_points(self, floor_bb):
        self._floor_bb = floor_bb
        
    def applyBB2RenderMesh(self, renderMesh: Elements.pyECSS.Component.RenderMesh):
        parent = renderMesh.parent
        basicTrans = self.getBasicTransformComp(parent)
        if(basicTrans != None):
            scene = Scene()
            vertices = renderMesh.vertex_attributes[0]
            scene.world.addComponent(parent, AABoundingBox(name="AABoundingBox",
                                                    min_points=create_min_points_list(vertices), 
                                                    max_points=create_max_points_list(vertices),
                                                    floor= self._floor_bb))
                                                    
        renderMesh.AddedBB = True

    def getBasicTransformComp(self, parent):
        for i in range(0, parent.getNumberOfChildren()):
            childComp = parent.getChild(i)
            if(childComp.getClassName() == "BasicTransform"):
                return childComp
            
        return None