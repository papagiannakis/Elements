"""
VertexArray class
    
The VertexArray Compoment class is the dedicated to a specific type of data container Component
that of assembling, using and destroying OpenGL API vertex array and buffer objects

Based on the Composite and Iterator design patterns:

* https://refactoring.guru/design-patterns/composite
* https://github.com/faif/python-patterns/blob/master/patterns/structural/composite.py
* https://refactoring.guru/design-patterns/iterator
* https://github.com/faif/python-patterns/blob/master/patterns/behavioral/iterator.py

"""

from __future__         import annotations
from abc                import ABC, abstractmethod
from typing             import List

import OpenGL.GL as gl
import numpy as np

import Elements.pyECSS.System
from Elements.pyECSS.Component import Component, CompNullIterator
import atexit
from Elements.pyGLV.GL.FrameBuffer import FrameBuffer

class VertexArray(Component):
    """
    A concrete VertexArray class
    """
    def __init__(self, name=None, type=None, id=None, attributes=None, index=None, primitive = gl.GL_TRIANGLES, usage=gl.GL_STATIC_DRAW):
        """
        Initializes a VertexArray class
        """
        super().__init__(name, type, id)
        
        self._parent = self
        
        self._glid = None
        self._buffers = [] #store all GL buffers
        self._draw_command = None
        self._arguments = (0,0)
        self._attributes = attributes
        self._index = index
        self._usage = usage
        self._primitive = primitive #e.g. GL.GL_TRIANGLES
        atexit.register(self.__del__)
        #self.init(attributes, index, usage) #init after a valid GL context is active
    
    @property
    def glid(self):
        return self._glid
    
    @property
    def attributes(self):
        # vertex positions, colors, normals, texcoords lists
        return self._attributes
    
    @attributes.setter
    def attributes(self, value):
        self._attributes = value
    
    @property
    def index(self):
        return self._index
    
    @index.setter
    def index(self, value):
        self._index = value
    
    @property
    def usage(self):
        return self._usage
    
    @usage.setter
    def usage(self, value):
        self._usage = value
        
    @property
    def primitive(self):
        return self._primitive
    
    @primitive.setter
    def primitive(self, value):
        self._primitive = value
    
    def __del__(self):
        # using atexit to ensure correct destruction order and to avoid yielding errors and exceptions
        # see https://stackoverflow.com/questions/72238460/python-importerror-sys-meta-path-is-none-python-is-likely-shutting-down
        gl.glDeleteVertexArrays(1, [self._glid])
        gl.glDeleteBuffers(len(self._buffers), self._buffers)
    
    def draw(self):
        gl.glBindVertexArray(self._glid)
        self._draw_command(self._primitive, *self._arguments)
        
        gl.glBindVertexArray(0)
        
    def update(self):
        self.draw()
   
    def accept(self, system: Elements.pyECSS.System):
        """
        Accepts a class object to operate on the Component, based on the Visitor pattern.

        :param system: [a System object]
        :type system: [System]
        """
        system.apply2VertexArray(self)
    
    def init(self):
        """
        Extra method for extra initialisation pf VertexArray
        Vertex array from attributes and optional index array. 
        Vertex Attributes should be list of arrays with one row per vertex. 
        """
        # create and bind(use) a vertex array object
        self._glid = gl.glGenVertexArrays(1)
        gl.glBindVertexArray(self._glid)
        nb_primitives, size = 0, 0
        
        # load buffer per vertex attribute (in a list with index = shader layout)
        for loc, data in enumerate(self._attributes):
            if data is not None and len(data) : #check if it is empty
                # bind a new VBO, upload it to GPU, declare size and type
                self._buffers.append(gl.glGenBuffers(1))
                data = np.array(data, np.float32, copy=False)
                nb_primitives, size = data.shape
                gl.glEnableVertexAttribArray(loc)
                gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self._buffers[-1])
                gl.glBufferData(gl.GL_ARRAY_BUFFER, data, self._usage)
                gl.glVertexAttribPointer(loc, size, gl.GL_FLOAT, False, 0, None)
           
        
        #optionally create and upload an index buffer for this VBO         
        self._draw_command = gl.glDrawArrays
        self._arguments = (0, nb_primitives)
        if self._index is not None and len(self._index): #check if list is empty
            self._buffers += [gl.glGenBuffers(1)]
            index_buffer = np.array(self._index, np.int32, copy=False)
            gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self._buffers[-1])
            gl.glBufferData(gl.GL_ELEMENT_ARRAY_BUFFER, index_buffer, self._usage)
            self._draw_command = gl.glDrawElements
            self._arguments = (index_buffer.size, gl.GL_UNSIGNED_INT, None)
        
        # cleanup and unbind so no accidental subsequent state update
        gl.glBindVertexArray(0)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
    
    def __iter__(self) ->CompNullIterator:
        """ 
        A component does not have children to iterate, thus a NULL iterator
        """
        return CompNullIterator(self) 