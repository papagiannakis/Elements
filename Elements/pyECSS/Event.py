""" Event classes, part of the Elements.pyECSS package
    
Elements.pyECSS (Entity Component Systems in a Scenegraph) package
@Copyright 2021-2022 Dr. George Papagiannakis
    
The Event related classes are the mechanism for Event management in Elements.pyECSS
based on the Mediator and Observer design patterns.

"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from dataclasses import dataclass




@dataclass
class Event:
    """A simple dataclass that encapsulates an Event
    """
    name: str
    id: Any
    value: Any


class EventPublisher(ABC):
    """
    Interface class for all EventManagers that act as Publishers/Subjects (based on the Observer design pattern)
    or as Mediators (based on the Mediator design pattern) 
    """
    
    @abstractmethod
    def notify(self, sender: Any, event: Event):
        """the main mediator pattern type notification

        :param sender: [the object sending the event]
        :type sender: Component or RenderWindow
        :param event: [the Event name, id and value]
        :type event: Event
        :raises NotImplementedError: [description]
        """
        raise NotImplementedError
    

class EventManager(EventPublisher):
    """
    Main Mediator (Subject/Publisher) class that contains list of Observers/Subscribers (Components) that is being 
    subscribed (notified) from and delegates to Systems to act upon these events invoked from these Components.
    """
    
    def __init__(self):
        self._publishers: Dict[str,Any] = {}
        self._subscribers: Dict[str,Any] = {}
        self._actuators: Dict[str,Any] = {}
        self._events: Dict[str,Event] = {}
    
    def notify(self, sender: Any, event: Event):
        if event is not None:
            # print(f'\n{EventManager.getClassName()}: notify() reacts from {sender} with {event}\n')
        
            # hardcode it for now, in a refactored version search if there is a match in the dictionaries
            # i.e. no need to hardcode this in the future:
            # just add event name and appropriate subscribers, publishers, actuators
            # and run matchmaking here between event names and subscribers-actuators
            # all needed data are passed from the Event.value
            # and the appopriate actuator (System) will know what to do
            # if event.name == "OnUpdateBackground":
            #     print(f'\n{event.name}: will be actuated from the appropriate system\n')
            # elif event.name == "OnUpdateWireframe":
            #     print(f'\n{event.name}: will be actuated from the appropriate system\n')

            # elif event.name == "OnUpdateCamera":
            #     print(f'\n{event.name}: will be actuated from the appropriate system - OnUpdateCamera\n')


            if event.name in self._subscribers:
                subscriber  = self._subscribers[event.name] 
                # print(f'\n{EventManager.getClassName()}: notify() subscriber: {subscriber} for {event}\n')
                if event.name in self._actuators:
                    systemActuator = self._actuators[event.name]
                    # print(f'\n{EventManager.getClassName()}: notify() actuator: {systemActuator} for {event}\n')
                    subscriber.accept(systemActuator, event)
        
        # print("EventManager:notify() ended")
       
        
    '''
    @TODO NEED REFACTORING these methods once API is stable
    # value should be a List
    # any new subscriber to same key::Event of the Dict should be appended on the value:: List
    #
    def subscribe(self, component: Any):
        self._subscribers.append(component)
        
    def unsubscribe(self, component: Any):
        self._subscribers.remove(component)
    '''
    def subscribe(self, component: Any):
        pass
    
    def unsubscribe(self, component: Any):
        pass
    
    def publish(self, component: Any):
        pass
    
    def unpublish(self, component: Any):
        pass
    
    def actuate(self, system: Any):
        pass
    
    def unactuate(self, system: Any):
        pass
    
    @classmethod
    def getClassName(cls):
        return cls.__name__    
    
    def print(self):
        """ debug output
        """
        print("\n_publishers dict\n".center(100, '-'))
        for key, value in self._publishers.items():
            print(f"\n{key} with value: {value} and value type: {type(value)} and contents:")
            if isinstance(value, List):
                for el in value:
                    print(el)
        
        print("\n_subscribers dict\n".center(100, '-'))
        for key, value in self._subscribers.items():
            print(f"\n{key} with value: {value} and value type: {type(value)} and contents:")
            if isinstance(value, List):
                for el in value:
                    print(el)
        
        print("\n_actuators dict\n".center(100, '-'))
        for key, value in self._actuators.items():
            print(f"\n{key} with value: {value} and value type: {type(value)} and contents:")
            if isinstance(value, List):
                for el in value:
                    print(el)
        
        print("\n_events dict\n".center(100, '-'))
        for key, value in self._events.items():
            print(f"\n{key} with value: {value} and value type: {type(value)} and contents:")
            if isinstance(value, List):
                for el in value:
                    print(el)
