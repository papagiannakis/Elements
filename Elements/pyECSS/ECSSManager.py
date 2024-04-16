"""
ECSSManager, part of the Elements.pyECSS package

The ECSSManager is a singleton providing factory methods for creating and traversing
all entities, components, systems of a scenegraph in Elements.pyECSS
    
Elements.pyECSS (Entity Component Systems in a Scenegraph) package
@Copyright 2021-2022 Dr. George Papagiannakis

"""

from __future__ import annotations
from abc import ABC, abstractmethod
from collections.abc import Iterable, Iterator
from typing import List, Dict
import pprint
import time

from Elements.pyECSS.Entity import Entity
import Elements.pyECSS.Component
import Elements.pyECSS.System
import Elements.pyECSS.Event 

from Elements.pyGLV.GL.FrameBuffer import FrameBuffer
from Elements.pyECSS.Component import BasicTransform
from Elements.pyGLV.GL.Shader import ShaderGLDecorator
import Elements.pyECSS.math_utilities as util

class ECSSManager():
    """
    Singleton Manager class to provide factory creation methods for
    all Entities, Components, Systems, as an alternative way and hide the scenegraph complexity.

    """
    _instance = None

    def __new__(cls):
        """
        Special singleton class method, returns single instance of ECSSManager

        :return: single class instance
        :rtype: ECSSManagger
        """
        if cls._instance is None:
            print('Creating ECSSManager Singleton Object')
            cls._instance = super(ECSSManager, cls).__new__(cls)
            # add further init here
        return cls._instance

    def __init__(self):
        """
        Construct initial data structures for scenegraph elements
        """
        self._systems: List[Elements.pyECSS.System.System] = []  # list for all systems
        # list with all scenegraph components
        self._components: List[Elements.pyECSS.Component.Component] = []
        self._entities: List[Entity] = []  # list of all scenegraph entities
        # list of all scenegraph camera components
        self._cameras: List[Elements.pyECSS.Component.Component] = []
        # dict with keys entities and values list of components per entity
        self._entities_components = {}
        # the ECSSManager creates one main EventManager for the whole world
        self._eventManager = Elements.pyECSS.Event.EventManager()
        self._root = None
        self._buffer = FrameBuffer()

    # define properties
    @property  # root Entity getter
    def root(self) -> Entity:
        """ Get ECSS's root node """
        return self._root
    
    @root.setter #root settter
    def root(self, value):
        self._root = value
    
    @property # EventManager getter
    def eventManager(self) -> Elements.pyECSS.Event.EventManager:
        """ Get ECSS's EventManager """
        return self._eventManager
    
    @property # Systems getter
    def systems(self) -> List:
        return self._systems
    
    @property # Components getter
    def components(self) -> List:
        return self._components
    
    @property # Entities getter
    def entities(self) -> List:
        return self._entities
    
    @property # Camera Components getter
    def cameras(self) -> List:
        return self._cameras
    
    @property # Components per Entity getter
    def entities_components(self) -> Dict:
        return self._entities_components
    

    def createEntity(self, entity: Entity):
        """
        Creates an Entity in the underlying scenegraph and adds it in the ECSS data structures.

        Checks if the Entity's name is "root" to add it as root of the ECSS

        :param entity: Entity to add in the Scenegraph
        :type entity: Entity
        """
        if isinstance(entity, Entity):
            # add an empty list for components with the new Entity
            self._entities.append(entity)
            self._entities_components[entity] = [None]

            # @@@TODO: refactor so that only first entity is set to root
            # now it is hardcoded with the name root 
            if entity.name.lower() == "root":
                self._root = entity
            
            if self._root is None:
                raise Exception('root node should have the name Root}')

        # if the method was called with an inline constructor e.g. 'createEntity(Entity())',
        return entity
        # we return that created Entity in case it is needed

    def createSystem(self, system: Elements.pyECSS.System.System):
        """
        Creates a System and adds it in the ECSS data structures

        """
        if isinstance(system, Elements.pyECSS.System.System):
            self._systems.append(system)

        return system

    def createIterator(self, entity: Entity, dfs=True):
        """
        Creates and returns a scenegraph traversal node iterator

        :param entity: [description]
        :type entity: Entity
        """
        if isinstance(entity, Entity):
            if dfs:
                return iter(entity)
        else:
            raise RuntimeError

    def addComponent(self, entity: Entity, component: Elements.pyECSS.Component.Component):
        """
        Adds a component to an Entity in a scenegraph and in the ECSS data structures

        Checks if that Component is a Camera, to add it in the list of Cameras

        Checks if that Entity has already such a component of that type and replaces 
        it with the new one

        Checks that indeed only a component is added with this method. 
        If we need to add a child Entity to an Enity, we use addEntityChild()

        :param entity: Parent Entity
        :type entity: Entity
        :param component: The component to be added to this Entity
        :type component: Component
        """
        if isinstance(entity, Entity) and isinstance(component, Elements.pyECSS.Component.Component):
            if isinstance(component, Elements.pyECSS.Component.Camera):
                self._cameras.append(component)
            else:  # add the component in the _components []
                self._components.append(component)

            # loop through all dictionary elements of _entities_components
            for key, value in self._entities_components.items():
                if key is entity:  # find key [entity]
                    # el are Components (but can also be Entities)
                    for index, el in enumerate(value):
                        # check if the value list() of that entity has already that component type
                        # we only add Components here and not Entities
                        if isinstance(el, type(component)) and not isinstance(el, Entity):
                            # if it has it, replace previous component with same type
                            # bur first remove previous from scenegraph and add new one
                            # remove it from scenegraph Entity's children list
                            key.remove(el)
                            # remove previous component from _entities_components list
                            value.remove(el)
                            # remove component from ECSSManager _components list
                            self._components.remove(el)
                            # insert new component at same index
                            value.insert(index, component)
                            # add it in the scenegraph as child of the Entity
                            key.add(component)
                        else:  # otherwise add it in ECSSManager and in Scenegraph
                            key.add(component)
                            # check if there is a list of components and add it there otherwise create one
                            if isinstance(value, list):
                                # check if first element is None
                                if (value[0] == None):
                                    value[0] = component
                                elif component not in value:
                                    value.append(component)
                            else:
                                value = list(component)
                            return component
            return component

    def addEntityChild(self, entity_parent: Entity, entity_child: Entity):
        """
        Adds a child Enity to a parent one and thus establishes a hierarchy 
        in the underlying scenegraph.

        Adds the child Entity also in the ECSS _entities_components dictionary 
        data structure, so that the hierarchy is also visible at ECSSManager level.

        :param entity_parent: [description]
        :type entity_parent: Entity
        :param entity_child: [description]
        :type entity_child: Entity
        """
        if isinstance(entity_parent, Entity) and isinstance(entity_child, Entity):
            # check if there is already a parent-child relationship between the Entities
            if entity_child.getParent() is not entity_parent:
                # if not, create one
                entity_parent.add(entity_child)
            # add entity_child in the _entities_components dictionary
            # loop through all dictionary elements of _entities_components
            

            if entity_parent not in self._entities_components:
                self._entities_components[entity_parent] = [];
            self._entities_components[entity_parent].append(entity_child);

    def update_entity_values(self, entity, winWidth, winHeight, Phong = False,
                             Lambientcolor = None, Lambientstr = None, LviewPos = None,
                             Lposition = None, Lcolor = None, Lintensity = None,
                             Mshininess = None, Mcolor = None):
        from Elements.pyGLV.GL.Scene import Scene
        scene = Scene();
        view = scene.renderWindow._myCamera;

        try:
            iterator = self.createIterator(entity)
        except RuntimeError:
            print("ECSSManager::traverse_visit() Could Not Create Iterator")

        if iterator is not None:
            done_traversing = False
            
            while(not done_traversing):
                try:
                    traversedComp = next(iterator)
                except StopIteration:

                    done_traversing = True
                else:
                    shaderDec = None;
                    trans = None;

                    if isinstance(traversedComp, Entity):
                        for child in traversedComp._children:
                            if isinstance(child, ShaderGLDecorator):
                                shaderDec = child;
                            elif isinstance(child, BasicTransform):
                                trans = child;
                    
                    if shaderDec is not None and trans is not None:
                        projMat = util.perspective(50.0, winWidth/winHeight, 0.01, 100.0)   
                        model = trans.l2world;
                        mvp = projMat @ view @ model;
                        shaderDec.setUniformVariable(key='modelViewProj', value=mvp, mat4=True)

                        if Phong:
                            shaderDec.setUniformVariable(key='model', value=model, mat4=True)
                            shaderDec.setUniformVariable(key='View', value=view, mat4=True)
                            shaderDec.setUniformVariable(key='Proj', value=projMat, mat4=True)
                            shaderDec.setUniformVariable(key='ambientColor',value=Lambientcolor,float3=True)
                            shaderDec.setUniformVariable(key='ambientStr',value=Lambientstr,float1=True)
                            shaderDec.setUniformVariable(key='viewPos',value=LviewPos,float3=True)
                            shaderDec.setUniformVariable(key='lightPos',value=Lposition,float3=True)
                            shaderDec.setUniformVariable(key='lightColor',value=Lcolor,float3=True)
                            shaderDec.setUniformVariable(key='lightIntensity',value=Lintensity,float1=True)
                            shaderDec.setUniformVariable(key='shininess',value=Mshininess,float1=True)
                            #shaderDec4.setUniformVariable(key='matColor',value=Mcolor,float3=True)
                            

    
    def traverse_visit_pre_camera(self, camUpdate: Elements.pyECSS.System, camera: Elements.pyECSS.Component.Camera):
        """
        Specifically run a CameraSystem on a Camera Component attached in a scenecegraph, 
        in order to calculate the MR2C root2camera matrix that is an essential part of the 
        local2camera matrix.
        This visitor has to be accepted after the L2W traversal has completed and has to be part of the
        cameraUpdate  system that will traverse whole scenegraph afterwards
        """
        camera.accept(camUpdate)
    
    
    def traverse_visit(self, system: Elements.pyECSS.System, entity: Entity, dfs=True):
        """
        Traverse whole scenegraph by iterating every Entity/Component and calling 
        a specific System on each different element.   

        :param system: [description]
        :type system: System.System
        :param iterator: [description]
        :type iterator: Iterator
        """
        self._buffer.bindFramebuffer();
        iterator = None
        try:
            if dfs:
                iterator = self.createIterator(entity)
        except RuntimeError:
            print("ECSSManager::traverse_visit() Could Not Create Iterator")

        if isinstance(system, Elements.pyECSS.System.System) and iterator is not None:
            tic1 = time.perf_counter()

            done_traversing = False
            while(not done_traversing):
                try:
                    traversedComp = next(iterator)
                except StopIteration:

                    done_traversing = True
                else:
                    # only if we reached end of Entity's children traversedComp is None
                    if (traversedComp is not None):
                        #print(traversedComp)
                        # accept a visitor System for each Component that can accept it
                        # calls specific concrete Visitor's apply2Component(), which calls specific concrete Component's methods
                        traversedComp.accept(system)

            toc1 = time.perf_counter()

        self._buffer.unbindFramebuffer();


    def print(self):
        """
        pretty print the contents of the ECSS
        """
        print("_entities_components {}".center(100, '-'))
        # pprint.pprint(self._entities_components)
        for en, co in self._entities_components.items():
            print(f"{en.name}")
            for comp in co:
                if comp is not None:
                    print(f"\t :: {comp.name}")

        print("_entities []".center(100, '-'))
        for ent in self._entities:
            print(ent)
        print("_components []".center(100, '-'))
        for com in self._components:
            print(com.name, "<--", com.parent.name)
        print("_systems []".center(100, '-'))
        for sys in self._systems:
            print(sys)
        print("_cameras []".center(100, '-'))
        for cam in self._cameras:
            print(cam)


if __name__ == "__main__":
    # The client code.

    s1 = ECSSManager()
    s2 = ECSSManager()

    if id(s1) == id(s2):
        print("Singleton works, both variables contain the same instance.")
    else:
        print("Singleton failed, variables contain different instances.")
