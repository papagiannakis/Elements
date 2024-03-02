""" Entity classes, part of the Elements.pyECSS package
    
Elements.pyECSS (Entity Component Systems in a Scenegraph) package
@Copyright 2021-2022 Dr. George Papagiannakis
    
The Entity realted classes are the based aggregation of Components in Elements.pyECSS, 
based on the Composite design pattern

"""

from __future__ import annotations
from abc import ABC, abstractmethod
from collections.abc import Iterable, Iterator
from typing import Any, List
import uuid

from Elements.pyECSS.Component import Component, ComponentIterator
from Elements.pyECSS.System import System



class EntityDfsIterator(Iterator, ComponentIterator):
    """
    This is a depth-first-iterator for Hierarchical Entities (Iterables) and their Components, 
    based on the Iterator design pattern

    :param Iterator: [description]
    :type Iterator: [type]

    Here is the explanation for the code above:
        1. This is a depth-first-iterator for Hierarchical Entities (Iterables) and their Components, 
    based on the Iterator design pattern
        2. We have a stack to keep track of the iterators that we have to go through.
        3. We push the Entity's iterator on the stack, that is the iterator that iterates through the Entity's children.
        4. We get the iterator from the top of the stack, and try to get the next child.
        5. If we get a StopIteration exception, then we have reached the end of the iterator, and we pop it off the stack.
        6. If we get a node, then we check if it is an Entity, and if it is, we push the Entity's iterator on the stack, and return the node.
        7. If we get a node and it is not an Entity, then we return the node.
    """
            
    # List stack to push/pop iterators
            
    def __init__(self, entity: Entity) ->None:
        self._entity = entity #entity this iterator can access the children of
        
        # access underlying Entity List iterator
        self._entityIterator = iter(self._entity._children)
        self._stack: List[Iterator] = []
        
        # store top level Entity List iterator in stack
        self._stack.append(self._entityIterator)
                    
    def __next__(self):
        """
        The __next__() iterator method should return the next Entity in the graph, using a DFS algorithm.
        This is a "pythonic" iterator, based on standard python List iterators
        """
        if (len(self._stack) == 0): 
            raise StopIteration
        else:
            stackIter = self._stack[-1] # peak last stack element
            try:
                node = next(stackIter) # advance stack iterator to retrieve first child node in it
            except StopIteration:
                    self._stack.pop() # remove top iterator as it has been exhausted
                    return None
            else:
                if isinstance(node, Entity):
                    self._stack.append(iter(node._children)) # push the new Entity's iterator on top of the stack to be parsed next() iteration
                    return node #node is an Entity
                else: 
                    return node #node is Component
            
class Entity(Component):
    """
    The main EntityI concrete class of glGA ECS 
    This is the typical equivalent of a Group node in traditional scenegraphs or GameObject in Unity Engine
    It can contain several other Entity objects as children. 
    It is an actual data aggregator container of Components. All the actuall operations and logic is performed by 
    Systems and not the Components or Entity itself.
    """

    def __init__(self, name=None, type=None, id=None) -> None:
        """
        PEP 256 
        note this is how we declare the type of variables in Phython 3.6 and later.
        e.g. x: int=1 or x: List[int] = [1] 
        """
        super().__init__(name, type, id)
        
        self._children: List[Component]=[]
        self._parent = None
        
    
    def print(self):
        """
        Print out contents of Entity for Debug purposes only
        """
        #print out name, type, id of this Entity and its components
        
        print(f" _______________________________________________________________ ")
        #create a local iterator of Entity's children
        debugIterator = iter(self._children)
        #call print() on all children (Concrete Components or Entities) while there are more children to traverse
        done_traversing = False
        while not done_traversing:
            try:
                comp = next(debugIterator)
            except StopIteration:
                done_traversing = True
            else:
                print(comp) #calls the component's __str__()
                comp.print() # recursive call of this method to traverse hierarchy
    

    def add(self, object: Component) ->None:
        self._children.append(object)
        object._parent = self

    def remove(self, object: Component) ->None:
        self._children.remove(object)
        object._parent = None
        
    def getChild(self, index) ->Component:
        if index < len(self._children):
            return self._children[index]
        else:
            return None
    
    def getChildByType(self, type) ->Component:
        for node in self._children:
            if node.type == type:
                return node
        return None
    
    def getParent(self) ->Component:
            return self._parent
    
    def getNumberOfChildren(self) -> int:
        return len(self._children)
    
    
    def isEntity(self) -> bool:
        return True
    
    def update(self, **kwargs) ->bool:
        return True
    
    def transform(self)->bool:
        """ Sample transform() only for subclassing here and debug purposes """
        return False
        ""
    
    def accept(self, system: System):
        """
        Accepts a class object to operate on the Component, based on the Visitor pattern.

        :param system: [a System object]
        :type system: [System]
        """
        system.update()
    
    def init(self):
        """
        abstract method to be subclassed for extra initialisation
        """
        pass
    
    def __iter__(self) -> EntityDfsIterator: 
        """
        The __iter__() method normaly returns the iterator object itself, by default
        we return the depth-first-search iterator
        """
        return EntityDfsIterator(self)
    
    def __str__(self):
        if (self._parent is not None): #in case this is not the root node
            return f"\n{self.getClassName()} \nname: {self._name}, \ntype: {self._type}, \nid: {self._id}, \nparent: {self._parent._name}"
        else:
            return f"\n{self.getClassName()} \nname: {self._name}, \ntype: {self._type}, \nid: {self._id}, \nparent: None (root node)"

        
    
    
    