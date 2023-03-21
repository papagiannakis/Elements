"""
Unit tests
Employing the unittest standard python test framework
https://docs.python.org/3/library/unittest.html
    
Elements.pyECSS (Entity Component Systems in a Scenegraph) package
@Copyright 2021-2022 Dr. George Papagiannakis

"""

import unittest
import numpy as np
from typing import List

from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import Component, BasicTransform, Camera, RenderMesh, CompNullIterator, BasicTransformDecorator

import Elements.pyECSS.utilities as util

class TestEntity(unittest.TestCase):
    
    def test_init(self):
        """
        Entity init() test
        """
        print("TestEntity:test_init() START")
        gameObject = Entity("root") 
        gameObject2 = Entity("gameObject2", "Group", 10)
        gameComponent = BasicTransform("Transform", "TRS", 200)
        gameComponent2 = BasicTransform()
        
        gameObject.add(gameObject2)
        gameObject2.add(gameComponent)
        gameObject.add(gameComponent2)
        
        print(gameObject) #prints root
        gameObject.print() #prints recursively all root children
        
        self.assertIsInstance(gameObject,Entity)
        self.assertIsInstance(gameObject._children, List)
        self.assertEqual(gameObject2._id,10)
        self.assertEqual(gameObject2.getChild(0),gameComponent)
        self.assertEqual(gameObject2.name, "gameObject2")
        self.assertEqual(gameObject2.type,"Group")
        self.assertEqual(gameObject2.id, 10)
        self.assertEqual(gameComponent2.type, "BasicTransform")
        
        gameObject2.remove(gameComponent)
        self.assertEqual(gameObject2.getChild(0), None)
        
        
        print("TestEntity:test_init() END")

    def test_add(self):
        """
        Entity add() test
        """
        print("TestEntity:test_add() START")
        gameObject = Entity()
        gameObject2 = Entity()
        gameObject.add(gameObject2)
        self.assertIn(gameObject2,gameObject._children)
        self.assertEqual(gameObject._children[0], gameObject2)
        #print("gameObject._children[0]" + gameObject._children[0])
        print("TestEntity:test_add() END")
    
    
    def test_remove(self):
        """
        Entity remove() test
        """
        print("TestEntity:test_remove() START")
        gameObject = Entity()
        gameObject2 = Entity()
        gameObject.add(gameObject2)
        gameObject.remove(gameObject2)
        self.assertNotIn(gameObject2, gameObject._children)
        #print("gameObject._children[0]" + gameObject._children[0])
        print("TestEntity:test_remove() END")
    
    def test_getChildParent(self):
        """
        Entity test_getChildParent() test
        """
        print("TestEntity:test_getChildParent() START")
        gameObject = Entity()
        gameObject2 = Entity()
        gameObject.add(gameObject2)
        self.assertIn(gameObject2, gameObject._children)
        self.assertEqual(gameObject2, gameObject.getChild(0))
        self.assertEqual(gameObject, gameObject2.getParent())
        self.assertEqual(gameObject, gameObject2.parent)
        self.assertNotEqual(gameObject2, gameObject2.parent)
        #print("gameObject._children[0]" + gameObject._children[0])
        print("TestEntity:test_getChildParent() END")
        
    def test_getNumberOfChildren(self):
        """
        Entity test_getNumberOfChildren() test
        """
        print("TestEntity:test_getNumberOfChildren() START")
        gameObject = Entity(0)
        gameObject1 = Entity(1)
        gameObject2 = Entity(2)
        gameObject3 = Entity(3)
        gameObject.add(gameObject1)
        gameObject1.add(gameObject2)
        gameObject2.add(gameObject3)
        self.assertIn(gameObject1, gameObject._children)
        print(f"test_getNumberOfChildren() scene: \n {gameObject.update()}")
        self.assertEqual(gameObject.getNumberOfChildren(), 1)
        #print("gameObject._children[0]" + gameObject._children[0])
        print("TestEntity:test_getNumberOfChildren() END")
    
    def test_getChildByType(self):
        """
        Entity test_getChildByType() test
        """
        print("TestEntity:test_getChildByType() START")
        gameObject = Entity("root", "Entity", "1")
        gameObject2 = Entity("node2", "Entity", "2")
        gameObject3 = Entity("node3", "Entity", "3")
        
        trans4 = BasicTransform("trans4", "BasicTransform", "7")
        trans5 = BasicTransform("trans5", "BasicTransform", "8")
        
        gameObject.add(gameObject2)
        gameObject2.add(gameObject3)
        gameObject2.add(trans4)
        gameObject3.add(trans5)
        
        self.assertEqual(trans4, gameObject2.getChildByType("BasicTransform"))
        self.assertEqual(gameObject3, gameObject2.getChildByType("Entity"))
        
        self.assertIn(gameObject2, gameObject._children)
        self.assertEqual(gameObject2.getNumberOfChildren(), 2)
        
        print("TestEntity:test_getChildByType() END")
    
    def test_isEntity(self):
        """
        Entity isEntity() test
        """
        print("TestEntity:test_isEntity() START")
        gameObject = Entity()
        self.assertEqual(gameObject.isEntity(), True)
        
        print("TestEntity:test_isEntity() END")
        
    def test_print(self):
        """
        Entity print() test
        """
        print("TestEntity:test_print() START")
        gameObject = Entity("root", "Group", "1")
        gameObject2 = Entity("node2", "Group", "2")
        gameObject3 = Entity("node3", "Group", "3")
        gameObject4 = Entity("node4", "Group", "4")
        gameObject5 = Entity("node5", "Group", "5")
        gameObject6 = Entity("node6", "Group", "6")
        trans4 = BasicTransform("trans4", "Transform", "7")
        trans5 = BasicTransform("trans5", "Transform", "8")
        trans6 = BasicTransform("trans6", "Transform", "9")
        gameObject.add(gameObject2)
        gameObject2.add(gameObject3)
        gameObject.add(gameObject4)
        gameObject2.add(gameObject5)
        gameObject3.add(gameObject6)
        gameObject4.add(trans4)
        gameObject5.add(trans5)
        gameObject6.add(trans6)
        
        self.assertIn(gameObject3, gameObject2._children)
        self.assertIn(trans5, gameObject5._children)
        gameObject.print()
        print("TestEntity:test_print() END")
        
    def test_EntityDfsIterator(self):
        """
        Entity EntityDfsIterator() test
        """
        print("TestEntity:test_EntityDfsIterator() START")
        gameObject = Entity("root", "Group", "1")
        gameObject2 = Entity("node2", "Group", "2")
        gameObject3 = Entity("node3", "Group", "3")
        gameObject4 = Entity("node4", "Group", "4")
        gameObject5 = Entity("node5", "Group", "5")
        gameObject6 = Entity("node6", "Group", "6")
        gameObject7 = Entity("node7", "Group", "7")
        trans4 = BasicTransform("trans4", "Transform", "7")
        trans5 = BasicTransform("trans5", "Transform", "8")
        trans6 = BasicTransform("trans6", "Transform", "9")
        gameObject.add(gameObject2)
        gameObject.add(gameObject4)
        gameObject.add(gameObject7)
        gameObject2.add(gameObject3)
        gameObject2.add(gameObject5)
        gameObject3.add(gameObject6)
        gameObject4.add(trans4)
        gameObject5.add(trans5)
        gameObject6.add(trans6)
        
        self.assertIn(gameObject2, gameObject._children)
        self.assertIn(gameObject4, gameObject._children)
        self.assertIn(trans4, gameObject4._children)
        self.assertIn(gameObject3, gameObject2._children)
        self.assertIn(trans5, gameObject5._children)
        
        #test the EntityDfsIterator to traverse the above ECS scenegraph
        dfsIterator = iter(gameObject)
        print(gameObject)
        
        nodePath = []
        done_traversing = False
        while(not done_traversing):
            try:
                traversedEntity = next(dfsIterator)
            except StopIteration:
                print("\n-------- end of Scene reached, traversed all Components!")
                done_traversing = True
            else:
                if (traversedEntity is not None):
                    print(traversedEntity)
                    nodePath.append(traversedEntity)
        
        print("".join(str(nodePath)))
        
        print("TestEntity:test_EntityDfsIterator() END")
        

class TestComponent(unittest.TestCase):
    
    @unittest.skip("Component is ABC due to @abstractmethod update(), skipping the test")
    def test_init(self):
        #default constructor of Component class
        print("\nTestComponent:test_init() START")
        
        #myComponent = Component(100, "baseComponent", "abstract")
        myComponent = Component()
        myComponent.name = "baseComponent"
        myComponent.type = "abstract"
        myComponent.id = 100
        
        self.assertEqual(myComponent.name, "baseComponent")
        self.assertEqual(myComponent.type,"abstract")
        self.assertEqual(myComponent.id, 100)
        
        print("TestComponent:test_init() END")


class TestComponentDecorator(unittest.TestCase):
    def test_ComponentDecorator(self):
        
        print("TestComponentDecorator:test_ComponentDecorator START".center(100, '-'))
        myComponent = BasicTransform()
        myDecComp = BasicTransformDecorator(myComponent)
        
        self.assertEqual(myDecComp.component.name, "BasicTransform")
        self.assertEqual(myDecComp.component.type,"BasicTransform")
        
        print("TestComponentDecorator:test_ComponentDecorator END".center(100, '-'))

class TestBasicTransform(unittest.TestCase):
    
    def test_init(self):
        #default constructor of Component class
        print("\TestBasicTransform:test_init() START")
        
        myComponent = BasicTransform()
        myComponent.name = "myComponent"
        myComponent.type = "BasicTransform"
        myComponent.id = 101
        myComponent.trs = util.translate(1.0, 2.0, 3.0)
        mT = np.array([
            [1.0,0.0,0.0,1.0],
            [0.0,1.0,0.0,2.0],
            [0.0,0.0,1.0,3.0],
            [0.0,0.0,0.0,1.0],
        ],dtype=np.float,order='F')
        
        self.assertEqual(myComponent.name, "myComponent")
        self.assertEqual(myComponent.type,"BasicTransform")
        self.assertEqual(myComponent.id, 101)
        np.testing.assert_array_equal(myComponent.trs,mT)
        
        myComponent.print()
        print("TestBasicTransform:test_init() END") 
    
    
    def test_BasicTransform_compNullIterator(self):
        #test null iterator
        print("\nTestBasicTransform:test_BasicTransform_compNullIterator() START")
        
        myTrans = BasicTransform("myTrans", "BasicTransform", "1")
        myIter = iter(myTrans)
        
        self.assertIsInstance(myIter, CompNullIterator)
        self.assertEqual(next(myIter), None)
        
        print(myTrans)
        print("\nTestBasicTransform:test_BasicTransform_compNullIterator() END")
        

class TestRenderMesh(unittest.TestCase):
    
    def test_init(self):
        #Default constructor for the basic RenderMesh class        
        print("\TestRenderMesh:test_init() START")
        
        myComponent = RenderMesh()
        myComponent.name = "BasicMesh"
        myComponent.type = "B"
        myComponent.id = 201
        
        self.assertEqual(myComponent.name, "BasicMesh")
        self.assertEqual(myComponent.type,"B")
        self.assertEqual(myComponent.id, 201)
        print(f"Called {myComponent.name} update(): {myComponent.update()}")
        print("TestRenderMesh:test_init() END")  

    def test_RenderMesh_compNullIterator(self):
        #test null iterator
        print("\nTestRenderMesh:test_RenderMesh_compNullIterator() START")
        
        myMesh = RenderMesh("myTrans", "RenderMesh", "2")
        myIter = iter(myMesh)
        
        self.assertIsInstance(myIter, CompNullIterator)
        self.assertEqual(next(myIter), None)
        
        print(myMesh)
        print("\nTestRenderMesh:test_RenderMesh_compNullIterator() END")


class TestCamera(unittest.TestCase):
    
    def test_init(self):
        #default constructor of Component class
        print("\TestCamera:test_init() START")
        
        myComponent = Camera(util.ortho(-100.0, 100.0, -100.0, 100.0, 1.0, 100.0))
        myComponent.name = "baseCamera"
        myComponent.type = "perspCam"
        myComponent.id = 100
        
        self.assertEqual(myComponent.name, "baseCamera")
        self.assertEqual(myComponent.type,"perspCam")
        self.assertEqual(myComponent.id, 100)
        np.testing.assert_array_equal(myComponent.root2cam,util.identity())
        np.testing.assert_array_equal(myComponent.projMat,util.ortho(-100.0, 100.0, -100.0, 100.0, 1.0, 100.0))
        #np.testing.assert_array_equal(myComponent.perspMat,perspective(90.0, 1, 0.1, 100))
        
        print("TestCamera:test_init() END")

    def test_update(self):
        #default update
        print("\TestCamera:test_update() START")
        
        myComponent = Camera(util.ortho(-100.0, 100.0, -100.0, 100.0, 1.0, 100.0))
        myComponent.name = "baseCamera"
        myComponent.type = "perspCam"
        myComponent.id = 100
        
        self.assertEqual(myComponent.name, "baseCamera")
        self.assertEqual(myComponent.type,"perspCam")
        self.assertEqual(myComponent.id, 100)
        
        myComponent.update(root2cam=util.identity())
        myComponent.projMat = util.identity()
        
        np.testing.assert_array_almost_equal(myComponent.root2cam,util.identity())
        np.testing.assert_array_almost_equal(myComponent.projMat,util.identity())
        #np.testing.assert_array_equal(myComponent.perspMat,identity())
        
        print("TestCamera:test_update() END")

if __name__ == "__main__":
    unittest.main(argv=[''], verbosity=3, exit=False)
        