from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from collections.abc import Iterable, Iterator
from sys import platform 
from enum import Enum 

WindowEventBuss = []  

class EventTypes(Enum):
    KEY_PRESS = 1
    KEY_RELEASE = 2
    KEY_REPEAT = 3
    MOUSE_BUTTON_PRESS = 4
    MOUSE_BUTTON_RELEASE = 5
    MOUSE_MOTION = 6
    CURSOR_POS = 7
    SCROLL = 8
    WINDOW_SIZE = 9
    WINDOW_CLOSE = 10
    WINDOW_REFRESH = 11
    WINDOW_FOCUS = 12
    FRAMEBUFFER_SIZE = 13
    STICK = 14
    POINTER_ENTER = 15
    POINTER_LEAVE = 16
    FOCUS = 17
    

class WindowEvent:
    """
    Simple event wrapper for the window events provided from the window API
    """ 
    
    type: EventTypes
    data: Any    

def PushEvent(event:WindowEvent):  
    """
    Push an Event into the event buss
    """ 
    
    WindowEventBuss.append(event)
    
def PollEventAndFlush():   
    """ 
    Pull all the events from the event buss and clear
    """ 
    
    events = [] 
    for event in WindowEventBuss:
        events.append(event)

    WindowEventBuss.clear() 
    return events