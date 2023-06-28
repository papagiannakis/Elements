"""
Unit tests
Employing the unittest standard python test framework
https://docs.python.org/3/library/unittest.html
    
Elements.pyECSS (Entity Component Systems in a Scenegraph) package
@Copyright 2021-2022 Dr. George Papagiannakis

"""


import unittest
import time
import numpy as np

import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.System import System, TransformSystem, CameraSystem
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, Camera

from Elements.pyECSS.GA.GA_Component import GATransform
from Elements.pyECSS.GA.GATransformSystem import GATransformSystem
from Elements.pyECSS.GA.quaternion import Quaternion
from Elements.pyECSS.GA.dual_quaternion import DualQuaternion
from Elements.pyECSS.GA.GAutils import t_q_to_TR, extract_t_q_from_TR


class TestGAComponent(unittest.TestCase):
    
    def test_init(self):

        print("\TestGAComponent:test_init() START")
        
        myComponent = GATransform()
        myComponent.name = "myComponent"
        myComponent.type = "GATransform"
        myComponent.id = 101
        myComponent.trs = util.translate(1.0, 2.0, 3.0)
        mT = np.array([
            [1.0,0.0,0.0,1.0],
            [0.0,1.0,0.0,2.0],
            [0.0,0.0,1.0,3.0],
            [0.0,0.0,0.0,1.0],
        ],dtype=np.float64,order='F')
        
        self.assertEqual(myComponent.name, "myComponent")
        self.assertEqual(myComponent.type,"GATransform")
        self.assertEqual(myComponent.id, 101)
        np.testing.assert_array_equal(myComponent.trs,mT)
        
        print("TestGAComponent:test_init() END") 
    
    def test_constructors(self):
        print("\TestGAComponent:test_constructors() START")
        
        myComponent = GATransform(trs=util.translate(1.0, 2.0, 3.0))
        mT = np.array([
            [1.0,0.0,0.0,1.0],
            [0.0,1.0,0.0,2.0],
            [0.0,0.0,1.0,3.0],
            [0.0,0.0,0.0,1.0],
        ],dtype=np.float64,order='F')
        
        np.testing.assert_array_equal(myComponent.trs,mT)
        

        
        myq = Quaternion(1,2,3,4)
        myvec = [1.0, 2.0, 3.0]
        mydq = DualQuaternion.from_vector([1,2,3,4,5,6,7,8])
        TR = t_q_to_TR(myvec,[myq.x, myq.y, myq.z, myq.w]) # a CGA multivector from myq quaternion and myvec vector

        myComponent2 = GATransform(vec=myvec)
        np.testing.assert_array_equal(myComponent2._vec,myvec)

        myComponent3 = GATransform(q=myq)
        np.testing.assert_array_equal(myComponent3._q,myq)

        myComponent4 = GATransform(q=myq, vec = myvec)
        np.testing.assert_array_equal(myComponent4._q,myq)
        np.testing.assert_array_equal(myComponent4._vec,myvec)


        myComponent5 = GATransform(dq=mydq)
        np.testing.assert_array_equal(myComponent5._dq,mydq)

        myComponent6 = GATransform(rot = TR)
        np.testing.assert_array_equal(myComponent6._rot,TR)
        print("TestGAComponent:test_constructors() END") 

class test_GAutils(unittest.TestCase):
    def test_trans_quat_to_motor(self):
        print("test_GAutils:test_trans_quat_to_motor() START") 
        t = [1,2,3]
        q = [1,2,3,4] # x,y,z,w
        TR = t_q_to_TR(t,q)
        print (type(TR.value))
        TR_as_a_vec = np.array([4,0,0,0,0,0,-3,2,-2,-2,-1,-4,-4,-6,-6,0,0,0,0,0,0,0,0,0,0,0,7,7,0,0,0,0])
        np.testing.assert_array_equal(TR.value, TR_as_a_vec)        

        t1,q1 = extract_t_q_from_TR(TR)
        np.testing.assert_array_equal(t1,t)
        np.testing.assert_array_equal(q1,q)
        print("test_GAutils:test_trans_quat_to_motor() END") 

    def test_motor_to_trans_quat(self):
        print("test_GAutils:test_motor_to_trans_quat() START")
        t = [1,2,3]
        q = [1,2,3,4] # x,y,z,w
        TR = t_q_to_TR(t,q)
        t1,q1 = extract_t_q_from_TR(TR)

        np.testing.assert_array_equal(t1,t)
        np.testing.assert_array_equal(q1,q)
        print("test_GAutils:test_motor_to_trans_quat() END")


class TestGATransformSystem(unittest.TestCase):
    def test_init(self):
        print("\nTestGATransformSystem:test_init() START")
        
        mySystem = GATransform("myGATrans", "BasicTransform", "2")
        mySystem.name = "myGATrans"
        mySystem.type = "GATransform"
        mySystem.id = 2
        
        self.assertEqual(mySystem.name, "myGATrans")
        self.assertEqual(mySystem.type,"GATransform")
        self.assertEqual(mySystem.id, 2)
        
        print("TestSystem:test_init() END")



    def test_acceptance(self):
        print("\nTestGATransformSystem:test_acceptance() START")
        a1 = GATransform(trs=util.scale(1,2,3))
        a2 = GATransform(q = Quaternion(0,1,0,1))
        q = Quaternion(0,1,0,1)
        # print(q.to_transformation_matrix())
        # q = Quaternion(0,1,0,1)
        b = GATransformSystem()
        a1.accept(b)
        a2.accept(b)
        print("\nTestGATransformSystem:test_acceptance() END")

    def test_functionality(self):
        print("\nTestGATransformSystem:test_functionality() START")

        mytrs = util.translate(4,5,6) @ util.scale(1,2,3) 
        a1 = GATransform(trs=mytrs)
        b = GATransformSystem()
        a1.accept(b)
        np.testing.assert_array_equal(a1.trs, mytrs)
        
        myq = Quaternion(0,1,0,1)
        a2 = GATransform(q = myq)
        self.assertEqual(a2.trs, None)
        a2.accept(b)
        np.testing.assert_array_equal(a2.trs, myq.to_transformation_matrix())


        a3 = GATransform(vec = np.array([1,2,3]))
        self.assertEqual(a3.trs, None)
        a3.accept(b)
        np.testing.assert_array_equal( a3.trs, np.array( [[1.,0.,0.,1.],[0.,1.,0.,2.],[0.,0.,1.,3.],[0.,0.,0.,1.]]) )

        print("\nTestGATransformSystem:test_functionality() END")
# class TestGATransformSystem(unittest.TestCase):
    
#     def test_getLocal2World(self):
#         """
#         System test_getLocal2World() test
#         """
#         print("TestTransformSystem:test_getLocal2World() START")
#         gameObject = Entity("root", "Entity", "0")
#         gameObject1 = Entity("node1", "Entity", "1")
#         gameObject2 = Entity("node2", "Entity", "2")
#         gameObject3 = Entity("node3", "Entity", "3")
        
#         trans4 = BasicTransform("trans4", "BasicTransform", "7")
#         trans5 = BasicTransform("trans5", "BasicTransform", "8")
#         trans6 = BasicTransform("trans6", "BasicTransform", "9")
#         transRoot = BasicTransform("transRoot", "BasicTransform", "0")
        
#         myComponent = BasicTransform("myComponent", "BasicTransform", "100")
#         mT = np.array([
#             [1.0,0.0,0.0,1.0],
#             [0.0,1.0,0.0,2.0],
#             [0.0,0.0,1.0,3.0],
#             [0.0,0.0,0.0,1.0],
#         ],dtype=np.float,order='F')
        
#         mT2 = np.array([
#             [1.0,0.0,0.0,2.0],
#             [0.0,1.0,0.0,3.0],
#             [0.0,0.0,1.0,4.0],
#             [0.0,0.0,0.0,1.0],
#         ],dtype=np.float,order='F')
        
#         mTf = np.array([
#             [1.0,0.0,0.0,3.0],
#             [0.0,1.0,0.0,5.0],
#             [0.0,0.0,1.0,7.0],
#             [0.0,0.0,0.0,1.0],
#         ],dtype=np.float,order='F')
        
#         myComponent.l2world = mT
        
#         trans4.trs = util.translate(1.0, 2.0, 3.0)
#         trans6.trs = util.translate(2.0, 3.0, 4.0)
#         gameObject.add(gameObject1)
#         gameObject.add(transRoot)
#         gameObject1.add(gameObject2)
#         gameObject2.add(gameObject3)
#         gameObject1.add(trans6)
#         gameObject2.add(trans4)
#         gameObject3.add(trans5)
        
#         """ Scenegraph
#         root
#             |
#             node1, transRoot
#             |   
#             node2, trans6: translate(2,3,4)
#                 |       
#                 node3,  trans4: translate(1,2,3)
#                     |
#                     trans5
#         """
#         self.assertEqual(trans4, gameObject2.getChildByType("BasicTransform"))
#         self.assertEqual(gameObject3, gameObject2.getChildByType("Entity"))
#         self.assertIn(gameObject1, gameObject._children)
#         self.assertEqual(gameObject2.getNumberOfChildren(), 2)
        
#          #instantiate a new TransformSystem System to visit all scenegraph componets
#         transUpdate = TransformSystem("transUpdate", "TransformSystem", "001")
#         trans5.accept(transUpdate)
#         #check if the local2World was correctly calculated upstream
#         print(trans5.l2world)
#         print(mT @ mT2)
#         np.testing.assert_array_equal(mTf,trans5.l2world)
        
#         #reapplhy the TransformSystem this time to another BasicTransform
#         # to calculate its l2world
#         trans6.accept(transUpdate)
#         print(trans6.l2world)
#         print(mT2)
#         np.testing.assert_array_equal(mT2,trans6.l2world)
        
#         print("TestTransformSystem:test_getLocal2World() END")
        
#     # def test_TransformSystem_use(self):
#     #     """
#     #     TransformSystem() use case test
#     #     """
#     #     print("TestTransformSySystem() START")
#     #     gameObject = Entity("root", "Group", "1")
#     #     gameObject2 = Entity("node2", "Group", "2")
#     #     gameObject3 = Entity("node3", "Group", "3")
#     #     gameObject4 = Entity("node4", "Group", "4")
#     #     gameObject5 = Entity("node5", "Group", "5")
#     #     gameObject6 = Entity("node6", "Group", "6")
#     #     gameObject7 = Entity("node7", "Group", "7")
#     #     trans4 = BasicTransform("trans4", "Transform", "7")
#     #     trans5 = BasicTransform("trans5", "Transform", "8")
#     #     trans6 = BasicTransform("trans6", "Transform", "9")
#     #     gameObject.add(gameObject2)
#     #     gameObject.add(gameObject4)
#     #     gameObject.add(gameObject7)
#     #     gameObject2.add(gameObject3)
#     #     gameObject2.add(gameObject5)
#     #     gameObject3.add(gameObject6)
#     #     gameObject4.add(trans4)
#     #     gameObject5.add(trans5)
#     #     gameObject6.add(trans6)
        
#     #     self.assertIn(gameObject2, gameObject._children)
#     #     self.assertIn(gameObject4, gameObject._children)
#     #     self.assertIn(trans4, gameObject4._children)
#     #     self.assertIn(gameObject3, gameObject2._children)
#     #     self.assertIn(trans5, gameObject5._children)
        
#     #     #test the EntityDfsIterator to traverse the above ECS scenegraph
#     #     dfsIterator = iter(gameObject)
#     #     print(gameObject)
        
#     #     #instantiate a new TransformSystem System to visit all scenegraph componets
#     #     transUpdate = TransformSystem("transUpdate", "TransformSystem", "001")
        
#     #     nodePath = []
#     #     done_traversing = False
#     #     while(not done_traversing):
#     #         try:
#     #             traversedComp = next(dfsIterator)
#     #         except StopIteration:
#     #             print("\n-------- end of Scene reached, traversed all Components!")
#     #             done_traversing = True
#     #         else:
#     #             if (traversedComp is not None): #only if we reached end of Entity's children traversedComp is None
#     #                 print(traversedComp)
                    
#     #                 #accept a TransformSystem visitor System for each Component that can accept it (BasicTransform)
#     #                 traversedComp.accept(transUpdate) #calls specific concrete Visitor's apply(), which calls specific concrete Component's update
#     #                 #nodePath.append(traversedComp) #no need for this now
#     #     #print("".join(str(nodePath)))
        
#     #     print("TestTransformSySystem() END")
        

        
if __name__ == "__main__":
    unittest.main(argv=[''], verbosity=3, exit=False)