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

import Elements.pyECSS.utilities as util
from Elements.pyECSS.System import System, TransformSystem, CameraSystem
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, Camera


class TestSystem(unittest.TestCase):
    def test_init(self):
        """
        default constructor of System class
        """
        print("\TestSystem:test_init() START")
        
        #mySystem = System(100, "baseSystem", "abstract")
        mySystem = System()
        mySystem.name = "baseSystem"
        mySystem.type = "abstract"
        mySystem.id = 100
        
        self.assertEqual(mySystem.name, "baseSystem")
        self.assertEqual(mySystem.type,"abstract")
        self.assertEqual(mySystem.id, 100)
        
        print("TestSystem:test_init() END")
        
    
class TestTransformSystem(unittest.TestCase):
    
    def test_getLocal2World(self):
        """
        System test_getLocal2World() test
        """
        print("TestTransformSystem:test_getLocal2World() START")
        gameObject = Entity("root", "Entity", "0")
        gameObject1 = Entity("node1", "Entity", "1")
        gameObject2 = Entity("node2", "Entity", "2")
        gameObject3 = Entity("node3", "Entity", "3")
        
        trans4 = BasicTransform("trans4", "BasicTransform", "7")
        trans5 = BasicTransform("trans5", "BasicTransform", "8")
        trans6 = BasicTransform("trans6", "BasicTransform", "9")
        transRoot = BasicTransform("transRoot", "BasicTransform", "0")
        
        myComponent = BasicTransform("myComponent", "BasicTransform", "100")
        mT = np.array([
            [1.0,0.0,0.0,1.0],
            [0.0,1.0,0.0,2.0],
            [0.0,0.0,1.0,3.0],
            [0.0,0.0,0.0,1.0],
        ],dtype=np.float,order='F')
        
        mT2 = np.array([
            [1.0,0.0,0.0,2.0],
            [0.0,1.0,0.0,3.0],
            [0.0,0.0,1.0,4.0],
            [0.0,0.0,0.0,1.0],
        ],dtype=np.float,order='F')
        
        mTf = np.array([
            [1.0,0.0,0.0,3.0],
            [0.0,1.0,0.0,5.0],
            [0.0,0.0,1.0,7.0],
            [0.0,0.0,0.0,1.0],
        ],dtype=np.float,order='F')
        
        myComponent.l2world = mT
        
        trans4.trs = util.translate(1.0, 2.0, 3.0)
        trans6.trs = util.translate(2.0, 3.0, 4.0)
        gameObject.add(gameObject1)
        gameObject.add(transRoot)
        gameObject1.add(gameObject2)
        gameObject2.add(gameObject3)
        gameObject1.add(trans6)
        gameObject2.add(trans4)
        gameObject3.add(trans5)
        
        """ Scenegraph
        root
            |
            node1, transRoot
            |   
            node2, trans6: translate(2,3,4)
                |       
                node3,  trans4: translate(1,2,3)
                    |
                    trans5
        """
        self.assertEqual(trans4, gameObject2.getChildByType("BasicTransform"))
        self.assertEqual(gameObject3, gameObject2.getChildByType("Entity"))
        self.assertIn(gameObject1, gameObject._children)
        self.assertEqual(gameObject2.getNumberOfChildren(), 2)
        
         #instantiate a new TransformSystem System to visit all scenegraph componets
        transUpdate = TransformSystem("transUpdate", "TransformSystem", "001")
        trans5.accept(transUpdate)
        #check if the local2World was correctly calculated upstream
        print(trans5.l2world)
        print(mT @ mT2)
        np.testing.assert_array_equal(mTf,trans5.l2world)
        
        #reapplhy the TransformSystem this time to another BasicTransform
        # to calculate its l2world
        trans6.accept(transUpdate)
        print(trans6.l2world)
        print(mT2)
        np.testing.assert_array_equal(mT2,trans6.l2world)
        
        print("TestTransformSystem:test_getLocal2World() END")
        
    def test_TransformSystem_use(self):
        """
        TransformSystem() use case test
        """
        print("TestTransformSySystem() START")
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
        
        #instantiate a new TransformSystem System to visit all scenegraph componets
        transUpdate = TransformSystem("transUpdate", "TransformSystem", "001")
        
        nodePath = []
        done_traversing = False
        while(not done_traversing):
            try:
                traversedComp = next(dfsIterator)
            except StopIteration:
                print("\n-------- end of Scene reached, traversed all Components!")
                done_traversing = True
            else:
                if (traversedComp is not None): #only if we reached end of Entity's children traversedComp is None
                    print(traversedComp)
                    
                    #accept a TransformSystem visitor System for each Component that can accept it (BasicTransform)
                    traversedComp.accept(transUpdate) #calls specific concrete Visitor's apply(), which calls specific concrete Component's update
                    #nodePath.append(traversedComp) #no need for this now
        #print("".join(str(nodePath)))
        
        print("TestTransformSySystem() END")
        

class TestCameraSystem(unittest.TestCase):
    
    def setUp(self):
        """init common Test parameters
        Scenegraph:
        
        root
            |                           |           |
            entityCam1,                 node4,      node3
            |-------|                    |           |----------|-----------|
            trans1, entityCam2           trans4     node5,      node6       trans3
            |       |                               |           |--------|
                    perspCam, trans2                trans5      node7    trans6
                                                                |
                                                                trans7
            
        """
        self.gameObject = Entity("root", "Group", 0)
        self.gameObject1 = Entity("entityCam1", "Group", 1)
        self.gameObject2 = Entity("entityCam2", "Group", 2)
        self.gameObject3 = Entity("node3", "Group", 3)
        self.gameObject4 = Entity("node4", "Group", 4)
        self.gameObject5 = Entity("node5", "Group", 5)
        self.gameObject6 = Entity("node6", "Group", 6)
        self.gameObject7 = Entity("node7", "Group", 7)
        self.trans1 = BasicTransform("trans1", "BasicTransform")
        self.trans2 = BasicTransform("trans2", "BasicTransform")
        self.trans3 = BasicTransform("trans3", "BasicTransform")
        self.trans4 = BasicTransform("trans4", "BasicTransform")
        self.trans5 = BasicTransform("trans5", "BasicTransform")
        self.trans6 = BasicTransform("trans6", "BasicTransform")
        self.trans7 = BasicTransform("trans7", "BasicTransform")
        self.perspCam = Camera(util.ortho(-100.0, 100.0, -100.0, 100.0, 1.0, 100.0), "perspCam","Camera","500")
        #for debug cam below
        #self.perspCam = Camera(util.translate(10.0,10.0,10.0), "perspCam","Camera","500")
        
        
        #setup transformations
        self.trans1.trs = util.translate(1.0,2.0,3.0)
        self.trans2.trs = util.translate(2.0,3.0,4.0)
        self.trans3.trs = util.translate(3.0,3.0,3.0)
        self.trans6.trs = util.translate(6.0,6.0,6.0)
        self.trans7.trs = util.translate(7.0,7.0,7.0)
        
        #camera sub-tree
        self.gameObject.add(self.gameObject1)
        self.gameObject1.add(self.trans1)
        self.gameObject1.add(self.gameObject2)
        self.gameObject2.add(self.perspCam)
        self.gameObject2.add(self.trans2)
        
        self.gameObject.add(self.gameObject4)
        self.gameObject4.add(self.trans4)
        
        self.gameObject.add(self.gameObject3)
        self.gameObject3.add(self.trans3)
        self.gameObject3.add(self.gameObject5)
        self.gameObject5.add(self.trans5)
        
        self.gameObject3.add(self.gameObject6)
        self.gameObject6.add(self.trans6)
        self.gameObject6.add(self.gameObject7)
        self.gameObject7.add(self.trans7)
        
        
    def tearDown(self):
        """ tidy up after Tests has run
        """
        pass
    
    @unittest.skip("MKTODO, it should be revised, skipping the test")
    def test_CameraSystem_use(self):
        """
        TestCameraSystem() use case test
        """
        print("test_CameraSystem_use() START")
        
        #test the EntityDfsIterator to traverse the above ECS scenegraph
        dfsIterator = iter(self.gameObject)
        #self.gameObject.print()
        #self.trans7.print()
        
        
        #instantiate a new TransformSystem System to visit all scenegraph componets
        transUpdate = TransformSystem("transUpdate", "TransformSystem", "001")
        camUpdate = CameraSystem("camUpdate", "CameraUpdate", "200")
        
        tic1 = time.perf_counter()
        print("------------------ This is the Scene:: l2w update traversal start-----------------")
        nodePath = []
        done_traversing_for_l2w_update = False
        while(not done_traversing_for_l2w_update):
            try:
                traversedComp = next(dfsIterator)
            except StopIteration:
                print("\n--- end of Scene reached, traversed all Components!---")
                done_traversing_for_l2w_update = True
            else:
                if (traversedComp is not None): #only if we reached end of Entity's children traversedComp is None
                    print(traversedComp)
                    #accept a TransformSystem visitor System for each Component that can accept it (BasicTransform)
                    traversedComp.accept(transUpdate) #calls specific concrete Visitor's apply(), which calls specific concrete Component's update
                    nodePath.append(traversedComp) #no need for this now
        #print("".join(str(nodePath)))
        # ------------------ This is the Scene:: l2w update traversal end-----------------
        toc1 = time.perf_counter()
        print(f"\n\n------------------ Scene l2w traversal took {(toc1 - tic1)*1000:0.4f} msecs -----------------")


        tic2 = time.perf_counter()
        print("\n\n------------------ This is the Scene:: camera traversal start-----------------")
        done_traversing_for_camera = False
        # new iterator to DFS scenegraph from root
        dfsIteratorCamera = iter(self.gameObject)
        #accept the CameraSystem directly first on the Camera to calculate is r2c (root2camera) matrix
        # as we have run before l2w, the camera's BasicTransform will have the l2w component needed for r2c
        # M2lc = Mr2c * Ml2w * V
        print("\n-- BEFORE calculating Mr2c camera matrix--")
        self.perspCam.accept(camUpdate)
        print(self.perspCam)
        print("\n-- AFTER calculating Mr2c camera matrix--")
        
        while(not done_traversing_for_camera):
            try:
                traversedCom = next(dfsIteratorCamera)
            except StopIteration:
                print("\n--- end of Scene reached, traversed all Components!---")
                done_traversing_for_camera = True
            else:
                if (traversedCom is not None): #only if we reached end of Entity's children traversedComp is None
                    print(traversedCom)
                    
                    #having calculated R2C and L2W, accept a CameraVisitor to calculate L2C (L2C=L2W*R2C)
                    traversedCom.accept(camUpdate)
        # ----------------- This is the Scene:: camera traversal end --------------------
        toc2 = time.perf_counter()
        print(f"\n\n----------------- Scene camera traversal took {(toc2 - tic1)*1000:0.4f} msecs -----------------")
        
        #print(f"\n\n----------------- Scene after all traversals: -----------------")
        #self.gameObject.print()
        
        #setup matrices for the unit tests
        camOrthoMat = util.ortho(-100.0, 100.0, -100.0, 100.0, 1.0, 100.0)
        #camOrthoMat = util.translate(10.0,10.0,10.0)
        trans1Mat = util.translate(1.0,2.0,3.0)
        trans2Mat = util.translate(2.0,3.0,4.0)
        trans3Mat = util.translate(3.0,3.0,3.0)
        trans6Mat = util.translate(6.0,6.0,6.0)
        trans7Mat = util.translate(7.0,7.0,7.0)
        
        # T2local2world = T2 @ T1
        trans2l2w = trans2Mat @ trans1Mat
        # Mroot2cam = (T1)^-1 @ (T2)^-1 @ P = (T2 @ T1)^-1 @ P = (T2local2world)^-1 @ P
        mr2c = util.inverse(trans2l2w) @ camOrthoMat
        # M7local2world = trans7 @ trans6 @ trans3
        m7l2w = trans7Mat @ trans6Mat @ trans3Mat
        #M7local2camera = Mroot2cam @ M2local2world @ Vertex (right to left)
        m7l2c = m7l2w @ mr2c
        
        #setup transformations
        #self.trans1.trs = util.translate(1.0,2.0,3.0)
        #self.trans2.trs = util.translate(2.0,3.0,4.0)
        #self.trans3.trs = util.translate(3.0,3.0,3.0)
        #self.trans6.trs = util.translate(6.0,6.0,6.0)
        #self.trans7.trs = util.translate(7.0,7.0,7.0)
        
        self.assertIn(self.gameObject1, self.gameObject._children)
        self.assertIn(self.gameObject4, self.gameObject._children)
        self.assertIn(self.trans4, self.gameObject4._children)
        self.assertIn(self.gameObject3, self.gameObject._children)
        self.assertIn(self.trans5, self.gameObject5._children)
        self.assertIn(self.trans7, self.gameObject7._children)
        self.assertIn(self.perspCam, self.gameObject2._children)
        self.assertEqual(self.gameObject._id,0)
        # here are tests on r2cam, l2cam, l2world
        np.testing.assert_array_almost_equal(self.perspCam.projMat,camOrthoMat, decimal=3)
        np.testing.assert_array_almost_equal(self.perspCam.root2cam,mr2c,decimal=3)
        np.testing.assert_array_almost_equal(self.trans7.l2world,m7l2w,decimal=3)
        np.testing.assert_array_almost_equal(self.trans7.l2cam,m7l2c,decimal=3)

        print(f"trans7.l2cam: \n{self.trans7.l2cam}")
        print(f"m7l2c: \n{m7l2c}")
        
        
        print("test_CameraSystem_use() END")

    @unittest.skip("MKTODO, it should be revised, skipping the test")
    def test_CameraSystem_MVP(self):
        """
        test_CameraSystem_MVP() use case test for model-view-projection matrices
        """
        print("test_CameraSystem_MVP() START")
        
        #test the EntityDfsIterator to traverse the above ECS scenegraph
        dfsIterator = iter(self.gameObject)
        #self.gameObject.print()
        #self.trans7.print()
        
        # 
        # MVP matrix calculation - 
        #
        model = util.translate(0.0,0.0,0.5)
        eye = util.vec(0.0, 1.0, -1.0)
        target = util.vec(0,0,0)
        up = util.vec(0.0, 1.0, 0.0)
        view = util.lookat(eye, target, up)
        #projMat = util.frustum(-10.0, 10.0,-10.0,10.0, -1.0, 10)
        #projMat = util.perspective(180.0, 1.333, 1, 10.0)
        #projMat = util.ortho(-10.0, 10.0, -10.0, 10.0, -1.0, 10.0)
        projMat = util.ortho(-5.0, 5.0, -5.0, 5.0, -1.0, 5.0)
        #mvpMat = projMat @ view @ model
        mvpMat = model @ view @projMat
        
        self.trans1.trs = model
        self.trans2.trs = view
        self.perspCam.projMat = projMat
        
        #instantiate a new TransformSystem System to visit all scenegraph componets
        transUpdate = TransformSystem("transUpdate", "TransformSystem", "001")
        camUpdate = CameraSystem("camUpdate", "CameraUpdate", "200")
        
        tic1 = time.perf_counter()
        print("------------------ This is the Scene:: l2w update traversal start-----------------")
        nodePath = []
        done_traversing_for_l2w_update = False
        while(not done_traversing_for_l2w_update):
            try:
                traversedComp = next(dfsIterator)
            except StopIteration:
                print("\n--- end of Scene reached, traversed all Components!---")
                done_traversing_for_l2w_update = True
            else:
                if (traversedComp is not None): #only if we reached end of Entity's children traversedComp is None
                    print(traversedComp)
                    #accept a TransformSystem visitor System for each Component that can accept it (BasicTransform)
                    traversedComp.accept(transUpdate) #calls specific concrete Visitor's apply(), which calls specific concrete Component's update
                    nodePath.append(traversedComp) #no need for this now
        #print("".join(str(nodePath)))
        # ------------------ This is the Scene:: l2w update traversal end-----------------
        toc1 = time.perf_counter()
        print(f"\n\n------------------ Scene l2w traversal took {(toc1 - tic1)*1000:0.4f} msecs -----------------")


        tic2 = time.perf_counter()
        print("\n\n------------------ This is the Scene:: camera traversal start-----------------")
        done_traversing_for_camera = False
        # new iterator to DFS scenegraph from root
        dfsIteratorCamera = iter(self.gameObject)
        #accept the CameraSystem directly first on the Camera to calculate is r2c (root2camera) matrix
        # as we have run before l2w, the camera's BasicTransform will have the l2w component needed for r2c
        # M2lc = Mr2c * Ml2w * V
        print("\n-- BEFORE calculating Mr2c camera matrix--")
        self.perspCam.accept(camUpdate)
        print(self.perspCam)
        print("\n-- AFTER calculating Mr2c camera matrix--")
        
        while(not done_traversing_for_camera):
            try:
                traversedCom = next(dfsIteratorCamera)
            except StopIteration:
                print("\n--- end of Scene reached, traversed all Components!---")
                done_traversing_for_camera = True
            else:
                if (traversedCom is not None): #only if we reached end of Entity's children traversedComp is None
                    print(traversedCom)
                    
                    #having calculated R2C and L2W, accept a CameraVisitor to calculate L2C (L2C=L2W*R2C)
                    traversedCom.accept(camUpdate)
        # ----------------- This is the Scene:: camera traversal end --------------------
        toc2 = time.perf_counter()
        print(f"\n\n----------------- Scene camera traversal took {(toc2 - tic1)*1000:0.4f} msecs -----------------")
        
        #print(f"\n\n----------------- Scene after all traversals: -----------------")
        #self.gameObject.print()
        
        #setup matrices for the unit tests
        camOrthoMat = util.ortho(-5.0, 5.0, -5.0, 5.0, -1.0, 5.0)
        #camOrthoMat = util.translate(10.0,10.0,10.0)
        trans1Mat = model
        trans2Mat = view
        trans3Mat = util.translate(3.0,3.0,3.0)
        trans6Mat = util.translate(6.0,6.0,6.0)
        trans7Mat = util.translate(7.0,7.0,7.0)
        
        # T2local2world = T2 @ T1
        trans2l2w = trans2Mat @ trans1Mat
        # Mroot2cam = (T1)^-1 @ (T2)^-1 @ P = (T2 @ T1)^-1 @ P = (T2local2world)^-1 @ P
        mr2c = util.inverse(trans2l2w) @ camOrthoMat
        # M7local2world = trans7 @ trans6 @ trans3
        m4l2w = self.trans4.l2world
        #M7local2camera = Mroot2cam @ M2local2world @ Vertex (right to left)
        #m4l2c = m4l2w @ mr2c
        m4l2c =  mr2c @ m4l2w
        
        #setup transformations
        #self.trans1.trs = util.translate(1.0,2.0,3.0)
        #self.trans2.trs = util.translate(2.0,3.0,4.0)
        #self.trans3.trs = util.translate(3.0,3.0,3.0)
        #self.trans6.trs = util.translate(6.0,6.0,6.0)
        #self.trans7.trs = util.translate(7.0,7.0,7.0)
        
        self.assertIn(self.gameObject1, self.gameObject._children)
        self.assertIn(self.gameObject4, self.gameObject._children)
        self.assertIn(self.trans4, self.gameObject4._children)
        self.assertIn(self.gameObject3, self.gameObject._children)
        self.assertIn(self.trans5, self.gameObject5._children)
        self.assertIn(self.trans7, self.gameObject7._children)
        self.assertIn(self.perspCam, self.gameObject2._children)
        self.assertEqual(self.gameObject._id,0)
        # here are tests on r2cam, l2cam, l2world
        np.testing.assert_array_almost_equal(self.perspCam.projMat,camOrthoMat, decimal=3)
        np.testing.assert_array_almost_equal(self.perspCam.root2cam,mr2c,decimal=3)
        np.testing.assert_array_almost_equal(self.trans4.l2world,m4l2w,decimal=3)
        np.testing.assert_array_almost_equal(self.trans4.l2cam,m4l2c,decimal=3)
        #np.testing.assert_array_almost_equal(mvpMat,m4l2c,decimal=3)

        print(f"trans4.l2cam: \n{self.trans4.l2cam}")
        print(f"m4l2c: \n{m4l2c}")
        
        
        print("test_CameraSystem_MVP() END")

        
if __name__ == "__main__":
    unittest.main(argv=[''], verbosity=3, exit=False)