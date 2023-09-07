"""
System classes, part of the Elements.pyECSS package
    
Elements.pyECSS (Entity Component Systems in a Scenegraph) package
@Copyright 2021-2022 Dr. George Papagiannakis
    
The System class is the logic-specific processor of different Components in Elements.pyECSS,
based on the Visitor design pattern

"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List

import Elements.pyECSS.Component
import Elements.pyECSS.math_utilities as util
import uuid  

class System(ABC):
    """
    Main abstract class of the System part of our ECS
    
    Typically involves all logic involving operations such as: 
    Transform, Physics, Animation (simulation), Camera (cull), Rendering (draw) 
    traversals and logic operationls on Components and Entities
   
    :param ABC: [description]
    :type ABC: [type]
    """
    
    def __init__(self, name=None, type=None, id=None, priority=0):
        if (name is None):
            self._name = self.getClassName()
        else:
            self._name = name
        
        if (type is None):
            self._type = self.getClassName()
        else:
            self._type = type
        
        if id is None:
            self._id = uuid.uuid1().int #assign unique ID on Component
        else:
            self._id = id
        self._priority = priority
    
    #define properties for id, name, type, priority
     
    @property #name
    def name(self) -> str:
        """ Get Systems's name """
        return self._name
    @name.setter
    def name(self, value):
        self._name = value
        
    @property #type
    def type(self) -> str:
        """ Get Systems's type """
        return self._type
    @type.setter
    def type(self, value):
        self._type = value
        
    @property #id
    def id(self) -> str:
        """ Get Systems's id """
        return self._id
    @id.setter
    def id(self, value):
        self._id = value
        
    @property #priority
    def priority(self) -> str:
        """ Get Systems's priority """
        return self._priority
    @priority.setter
    def priority(self, value):
        self._priority = value
    
    @classmethod
    def getClassName(cls):
        return cls.__name__
    
    def update(self):
        """
        method to be subclassed for  behavioral or logic computation 
        when visits Components of an EntityNode. 
        
        """
        pass
    
    def init(self):
        """
        method to be subclassed for  behavioral or logic computation 
        when visits Components of an EntityNode. 
        
        """
        pass
    
    def apply(self, Entity, event = None):
        """
        method to be subclassed for  behavioral or logic computation 
        when visits Entities. 
        
        """
        pass
    
    #MYCHANGE
    def test(self, comp: Elements.pyECSS.Component):
        pass
    
    #MYCHANGE
    def apply2BoundingBox(self, aabb_comp: Elements.pyECSS.Component.AABoundingBox, event = None):
        """
        method to be subclassed for  behavioral or logic computation 
        when visits Components. 
        """
        
        pass
    
    #MYCHANGE
    def applyBB2RenderMesh(self, renderMesh: Elements.pyECSS.Component.RenderMesh, event = None):
        """
        method to be subclassed for  behavioral or logic computation 
        when visits Components. 
        
        """
        pass
        
    def apply2RenderMesh(self, renderMesh: Elements.pyECSS.Component.RenderMesh, event = None):
        """
        method to be subclassed for  behavioral or logic computation 
        when visits Components. 
        
        """
        pass
    
    
    def apply2BasicTransform(self, basicTransform: Elements.pyECSS.Component.BasicTransform, event = None):
        """
        method to be subclassed for  behavioral or logic computation 
        when visits Components. 
        
        """
        pass
    
    def apply2GATransform(self, basicTransform: Elements.pyECSS.GA.GA_Component.GATransform , event = None):
        """
        method to be subclassed for  behavioral or logic computation 
        when visits Components. 
        """
        pass

    def applyCamera2BasicTransform(self, basicTransform: Elements.pyECSS.Component.BasicTransform, event = None):
        """
        method to be subclassed for  behavioral or logic computation 
        when visits Components. 
        
        """
        pass
    
    def apply2Camera(self, basicTransform: Elements.pyECSS.Component.Camera, event = None):
        """
        method to be subclassed for  behavioral or logic computation 
        when visits Components. 
        
        """
        pass
    
    def apply2VertexArray(self, vertexArray, event = None):
        pass
    
    def apply2Shader(self, shader, event = None):
        pass
    
    def apply2ShaderGLDecorator(self, shaderGLDecorator, event = None):
        pass
    
    def apply2RenderWindow(self, renderWindow, event = None):
        pass
    
    def apply2SDLWindow(self, sdlWindow, event = None):
        pass
    
    def apply2RenderDecorator(self, renderDecorator, event = None):
        pass 
    
    def apply2ImGUIDecorator(self, imGUIDecorator, event = None):
        pass 
    
class SystemDecorator(System):
    """Basic System Decorator, based on the Decorator design pattern

    :param sys: [System to be decorated]
    :type sys: [System]
    """
    
    def __init__(self, sys, name=None, type=None, id=None, priority=0):
        super().__init__(name, type, id, priority)
        self._system = sys
    
    @property
    def system(self):
        return self._system
    
    def init(self):
        self._system.init()
    
    def update(self, **kwargs):
        self._system.update(**kwargs)
    

    
class TransformSystem(System):
    """
    System that operates on BasicTransform Components and calculates Local2World matrices
    that are needed in a Scenegraph DAG hierarchy

    Here is the explanation for Transform System class:
    
    1. I have a BasicTransform component that has a TRS matrix and a l2worldTRS matrix
    2. For each BasicTransform component, I calculate the l2worldTRS matrix of that component based on the hierarchy of its parent nodes
    3. Then I update the l2worldTRS matrix of that BasicTransform component
    4. The l2worldTRS matrix of a component is calculated in the following way:
        a. if the component is the root node, then the l2worldTRS matrix is the TRS matrix of that component
        b. if the component is not the root node, then the l2worldTRS matrix is calculated by multiplying the TRS matrix of that component with the l2worldTRS matrix of its parent node
    
    :param System: [description]
    :type System: [type]
    :return: [description]
    :rtype: [type]
    """
    
    def __init__(self, name=None, type=None, id=None, cameraComponent=None):
        super().__init__(name, type, id)
        self._camera = cameraComponent #if Scene has a cameraComponent, specify also l2Camera
        
    
    def update(self):
        """
        method to be subclassed for  behavioral or logic computation 
        when visits Components of an EntityNode. 
        
        """
        pass
    
    def getLocal2World(self, leafComp: Elements.pyECSS.Component, topComp=None):
        """Calculate the l2world BasicTransform matrix

        :param leafComp: [description]
        :type leafComp: Component
        :param topComp: [description], defaults to None
        :type topComp: [type], optional
        :return: the local2world matrix of the visited BasicTransform
        :rtype: numpy.array
        """
        
        # get parent Entity this BasicTransform Component belongs to
        componentEntity = leafComp.parent
        topAccessedEntity = componentEntity


        l2worldTRS = util.identity(); # # correct one   
        
        while(componentEntity is not topComp):
            # get that parent's TRS by type
            parentBasicTrans = componentEntity.getChildByType("BasicTransform")
            if(parentBasicTrans is not None and parentBasicTrans):
                l2worldTRS = parentBasicTrans.trs @ l2worldTRS

            topAccessedEntity = componentEntity
            componentEntity = componentEntity.parent
        else: #parent is now the root node, so check if it has a Transform component
            parentBasicTrans = topAccessedEntity.getChildByType("BasicTransform")
            if(parentBasicTrans is not None):
                # l2world = multiply current with parent's TRS 
                l2worldTRS = l2worldTRS @ parentBasicTrans.trs
                
        return l2worldTRS
    def apply2BasicTransform(self, basicTransform: Elements.pyECSS.Component.BasicTransform):
        """
        method to be subclassed for  behavioral or logic computation 
        when visits Components. 
        
        In this case calculate the l2w BasicTransform component matrix
        
        """

        #check if the visitor visits a node that it should not
        if (isinstance(basicTransform,Elements.pyECSS.Component.BasicTransform)) == False:
            return #in Python due to duck typing we need to check this!

        

        l2worldTRS = self.getLocal2World(basicTransform)
        #update l2world of basicTransform
        basicTransform.update(l2world=l2worldTRS) 


class CameraSystem(System):
    """
    System that operates on both BasicTransform Components as well as Camera Components
    For the BasicTransform ones, it calculates the Local2camera matrix. For the Camera Component
    it calculates the Root2camera matrix, which is a necessary component for the Local2camera,
    hence it needs to be calculated first: Ml2c = Mr2c * Ml2w * V
    Like that we can be having many camera and re-calculating all Ml2c transformations accordingly
    
    :param System: [description]
    :type System: [type]
    :return: [description]
    :rtype: [type]
    """
    
    def __init__(self, name=None, type=None, id=None, cameraComponent=None):
        super().__init__(name, type, id)
        self._camera = cameraComponent #if Scene has a cameraComponent, specify also l2Camera
    
    def update(self):
        """
        method to be subclassed for  behavioral or logic computation 
        when visits Components of an EntityNode. 
        
        """
        pass
        
    def getRoot2Camera(self, camComp: Elements.pyECSS.Component, topComp=None):
        """Calculate the root to camera matrix
        
        Root2Camera is to get all parent BasicTransforms till root node (as usual)
        then get their inverse, since Mr2c = Inv(Ti)*Inv(Ti+1)*Proj = Inv(Ti+1*Ti)*Proj
        since we run first the System on a camera node, it is enough to get its Entity'w BasicTrasform
        and from there just retrieve its l2world camera, which was calculated before from the scenegraph 
        l2world traversal (always first system that one to run)

        :param leafComp: [description]
        :type leafComp: Component
        :param topComp: [description], defaults to None
        :type topComp: [type], optional
        :return: [description]
        :rtype: [type]
        """
        r2c = util.identity()
        componentEntity = camComp.parent
        parentBasicTrans = componentEntity.getChildByType("BasicTransform")
        if(parentBasicTrans is not None):
            parentl2world = parentBasicTrans.l2world
            inv_parentl2world = util.inverse(parentl2world)
            r2c = inv_parentl2world;
        
        return r2c
        
    #then this
    def applyCamera2BasicTransform(self, basicTransform: Elements.pyECSS.Component.BasicTransform):
        """
        method to be subclassed for  behavioral or logic computation 
        when visits Components. 
        
        In this case calculate the l2w BasicTransform component matrix

        """
        if (isinstance(basicTransform,Elements.pyECSS.Component.BasicTransform)) == False:
            return #in Python due to duck typing we need to check this!
        # print(self.getClassName(), ": apply(BasicTransform) called from CameraSystem - Calc: Local2Cam")
        
        #l2world of basicTransform has been calculated by the TransformSystem before this System
        l2w = basicTransform.l2world;
        r2c = self._camera.root2cam;
        proj = self._camera.projMat;

        l2c = proj @ r2c @ l2w; # Not sure 100% sure why it didnt play for me before
        basicTransform.update(l2cam=l2c) ;
        
    #first this     
    def apply2Camera(self, cam: Elements.pyECSS.Component.Camera):
        """
        method to be subclassed for  behavioral or logic computation 
        when visits Camera Components. 
        
        In this case ths sole purpose is to calculate the 
        the r2c (root to camera) matrix
        
        """
        if (isinstance(cam,Elements.pyECSS.Component.Camera)) == False:
            return #in Python due to duck typing we need to verify this!
        # print(self.getClassName(), ": apply2Camera called from CameraSystem - Calc: Root2Cam")
        
        # getRoot2Cam returns the one component of the Local2Cam = Local2World * Root2Cam
        r2cam = self.getRoot2Camera(cam)
        #update root2cam of Camera
        cam.update(root2cam=r2cam)
        #save camera component if not specified on constructor
        self._camera = cam 



class RenderSystem(System):
    """
    A basic, empty forward rendering sample system.
    Basically this needs to be redefined in each rendering context: OpenGL, RayTracing etc. 
    """
    pass
               
