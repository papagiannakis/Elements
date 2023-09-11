"""
Test Scene Unit tests, part of the glGA SDK ECSS
    
glGA SDK v2021.0.5 ECSS (Entity Component System in a Scenegraph)
@Coopyright 2020-2021 George Papagiannakis

"""

import unittest
import numpy as np

import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Entity import Entity, EntityDfsIterator
from Elements.pyECSS.Component import BasicTransform, Camera
from Elements.pyECSS.System import System, TransformSystem, CameraSystem, RenderSystem
import Elements.pyECSS.ECSSManager

class TestECSSManager(unittest.TestCase):
    """[summary]

    :param unittest: [description]
    :type unittest: [type]
    """
    
    def setUp(self):
        """
        Sets up the ECSS both at ECSSManager level data structures
        as well as the underlying scenegraph
        
        mimicks the scenegraph created in TestCameraSystem setUp().
        
        hence we have two ways of setting up an ECSS: 
        a) High-level via the ECSSManager (recommended method)
        b) Low-level directly at scenegraph hierarchy level
        
        """
        self.WorldManager = Elements.pyECSS.ECSSManager.ECSSManager()
        self.WorldManager2 = Elements.pyECSS.ECSSManager.ECSSManager()
        
        """
        Rebuild the same scenegraph from test_System::TestCameraSystem class,
        via the ECSSManager:
        Scenegraph:
        
        root
            |                           |           |
            entityCam1,                 node4,      node3
            |-------|                    |           |----------|-----------|
            trans1, entityCam2           trans4     node5,      node6       trans3
            |       |                               |           |--------|
                    ortho, trans2                   trans5      node7    trans6
                                                                |
                                                                trans7
            
        """ 
        # Scenegraph with Entities, Components
        self.rootEntity = self.WorldManager.createEntity(Entity(name="RooT"))
        self.entityCam1 = self.WorldManager.createEntity(Entity(name="entityCam1"))
        self.WorldManager.addEntityChild(self.rootEntity, self.entityCam1)
        self.trans1 = self.WorldManager.addComponent(self.entityCam1, BasicTransform(name="trans1", trs=util.translate(1.0,2.0,3.0)))
        
        self.entityCam2 = self.WorldManager.createEntity(Entity(name="entityCam2"))
        self.WorldManager.addEntityChild(self.entityCam1, self.entityCam2)
        self.trans2 = self.WorldManager.addComponent(self.entityCam2, BasicTransform(name="trans2", trs=util.translate(2.0,3.0,4.0)))
        self.orthoCam = self.WorldManager.addComponent(self.entityCam2, Camera(util.ortho(-100.0, 100.0, -100.0, 100.0, 1.0, 100.0), "orthoCam","Camera","500"))
        
        self.node4 = self.WorldManager.createEntity(Entity(name="node4"))
        self.WorldManager.addEntityChild(self.rootEntity, self.node4)
        self.trans4 = self.WorldManager.addComponent(self.node4, BasicTransform(name="trans4"))
        
        self.node3 = self.WorldManager.createEntity(Entity(name="node3"))
        self.WorldManager.addEntityChild(self.rootEntity, self.node3)
        self.trans3 = self.WorldManager.addComponent(self.node3, BasicTransform(name="trans3", trs=util.translate(3.0,3.0,3.0)))
        
        self.node5 = self.WorldManager.createEntity(Entity(name="node5"))
        self.WorldManager.addEntityChild(self.node3, self.node5)
        self.trans5 = self.WorldManager.addComponent(self.node5, BasicTransform(name="trans5"))
        
        self.node6 = self.WorldManager.createEntity(Entity(name="node6"))
        self.WorldManager.addEntityChild(self.node3, self.node6)
        self.trans6 = self.WorldManager.addComponent(self.node6, BasicTransform(name="trans6", trs=util.translate(6.0,6.0,6.0)))
        
        self.node7 = self.WorldManager.createEntity(Entity(name="node7"))
        self.WorldManager.addEntityChild(self.node6, self.node7)
        self.trans7 = self.WorldManager.addComponent(self.node7, BasicTransform(name="trans7", trs=util.translate(7.0,7.0,7.0)))
        
        # Systems
        self.transUpdate = self.WorldManager.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
        self.camUpdate = self.WorldManager.createSystem(CameraSystem("camUpdate", "CameraUpdate", "200"))
        
        
    def test_init(self):
        """
        ECSSManager init components
        
        """
        
        print("TestECSSManager:test_init START".center(100, '-'))
        
        
        for key, value in self.WorldManager._entities_components.items():
            print("\n entity: ",key, ":: with components: ", value)
        
        self.assertEqual(id(self.WorldManager), id(self.WorldManager2))
        self.assertEqual(self.rootEntity, self.WorldManager._root)
        self.assertIsInstance(self.transUpdate, TransformSystem)
        self.assertIsInstance(self.camUpdate, CameraSystem)
        
        
        self.assertIn(self.entityCam1, self.rootEntity._children)
        self.assertIn(self.node4, self.rootEntity._children)
        self.assertIn(self.trans4, self.node4._children)
        self.assertIn(self.node3, self.rootEntity._children)
        self.assertIn(self.trans5, self.node5._children)
        self.assertIn(self.trans7, self.node7._children)
        self.assertIn(self.orthoCam, self.entityCam2._children)
        
        self.WorldManager._root.print()
        self.WorldManager.print()
        
        print("TestECSSManager:test_init END".center(100, '-'))
    
    
    def test_addComponent(self):
        """
        ECSSManager addComponent
        """
        
        print("TestECSSManager:test_addComponent START".center(100, '-'))
        
        compTrans = self.entityCam1.getChildByType(BasicTransform.getClassName())
        
        #add a new basicComponent at an Entity that already has one i.e. replace previous with same type
        self.trans8 = self.WorldManager.addComponent(self.entityCam2, BasicTransform(name="trans8", trs=util.translate(20.0,30.0,40.0)))
        
        self.assertEqual(self.entityCam1, self.entityCam2.parent)
        self.assertEqual(self.trans8.parent, self.entityCam2)
        self.assertIn(self.trans8, self.entityCam2._children)
        self.assertIn(self.trans8, self.WorldManager._components)
        self.assertNotIn(self.trans2, self.entityCam2._children)
        self.assertNotIn(self.trans2, self.WorldManager._components)
        self.assertIsInstance(self.trans8, BasicTransform)
        
        self.WorldManager.print()
        
        print("TestECSSManager:test_addComponent END".center(100, '-'))


    @unittest.skip("MKTODO, it should be revised, skipping the test")
    def test_traverse_visit(self):
        """
        ECSSManager traverse_visit
        """
        
        print("TestECSSManager:test_traverse_visit START".center(100, '-'))
        
        #run a l2w traversal
        self.WorldManager.traverse_visit(self.transUpdate, self.rootEntity)
        
        #run a camera traversal
        print("\n-- BEFORE calculating Mr2c camera matrix--")
        #self.orthoCam.accept(self.camUpdate)
        #print(self.orthoCam)
        self.WorldManager.traverse_visit_pre_camera(self.camUpdate, self.orthoCam)
        print("\n-- AFTER calculating Mr2c camera matrix--")
        self.WorldManager.traverse_visit(self.camUpdate, self.rootEntity)
        
        # ----- integration tests on the ECSSManager traversals and results ------
        
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
        
        self.assertIn(self.entityCam1, self.rootEntity._children)
        self.assertIn(self.node4, self.rootEntity._children)
        self.assertIn(self.trans4, self.node4._children)
        self.assertIn(self.node3, self.rootEntity._children)
        self.assertIn(self.trans5, self.node5._children)
        self.assertIn(self.trans7, self.node7._children)
        self.assertIn(self.orthoCam, self.entityCam2._children)
        # here are tests on r2cam, l2cam, l2world
        np.testing.assert_array_almost_equal(self.orthoCam.projMat,camOrthoMat, decimal=3)
        np.testing.assert_array_almost_equal(self.orthoCam.root2cam,mr2c,decimal=3)
        np.testing.assert_array_almost_equal(self.trans7.l2world,m7l2w,decimal=3)
        np.testing.assert_array_almost_equal(self.trans7.l2cam,m7l2c,decimal=3)
        
        self.WorldManager.print()
        
        print("TestECSSManager:test_traverse_visit END".center(100, '-'))
        
        
        
if __name__ == "__main__":
    unittest.main(argv=[''], verbosity=3, exit=False)