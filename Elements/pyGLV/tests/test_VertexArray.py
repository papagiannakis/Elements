"""
Unit tests
Employing the unittest standard python test framework
https://docs.python.org/3/library/unittest.html
    
Elements.pyGLV (Computer Graphics for Deep Learning and Scientific Visualization)
@Copyright 2021-2022 Dr. George Papagiannakis

"""

import unittest


from Elements.pyGLV.GL.VertexArray import VertexArray



class TestVertexArray(unittest.TestCase):
    
    def setUp(self):
        print("TestVertexArray:setUp START".center(100, '-'))
        
        self.myVertexArray = VertexArray()
        
        print("TestVertexArray:setUp END".center(100, '-'))
    
    def test_init(self):
        print("TestVertexArray:test_init START".center(100, '-'))
        
        self.assertEqual(self.myVertexArray.name, "VertexArray")
        self.assertEqual(self.myVertexArray.type,"VertexArray")
        
        print("TestVertexArray:test_init END".center(100, '-'))
    
    


if __name__ == "__main__":
    unittest.main(argv=[''], verbosity=3, exit=False)