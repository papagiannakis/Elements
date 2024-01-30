import unittest
import numpy as np

import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.System import System
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform
from Elements.extensions.DummySystem.dummy_gravity import RigidBody, GravitySystem
from Elements.extensions.DummySystem.dummy_rotate import Rotate, RotateSystem


class TestDummyGravityComponent(unittest.TestCase):
    def test_constructors(self):
        print("\TestDummyGravityComponent:test_init() START")

        myComponent = RigidBody()
        myComponent.name = "myComponent"
        myComponent.type = "RigidBody"
        myComponent.id = 101
        myComponent.mass = 100
        myComponent.drag = 5
        myComponent.gravity = 10

        self.assertEqual(myComponent.name, "myComponent")
        self.assertEqual(myComponent.type, "RigidBody")
        self.assertEqual(myComponent.id, 101)
        self.assertEqual(myComponent.mass, 100)
        self.assertEqual(myComponent.drag, 5)
        self.assertEqual(myComponent.gravity, 10)

        myComponent2 = Rotate()
        myComponent2.name = "myComponent2"
        myComponent2.type = "RotateComponent"
        myComponent2.id = 102
        myComponent2.angles = [1, 2, 3]
        myComponent2.speed = 4

        self.assertEqual(myComponent2.name, "myComponent2")
        self.assertEqual(myComponent2.type, "RotateComponent")
        self.assertEqual(myComponent2.id, 102)
        np.testing.assert_array_almost_equal(myComponent2.angles, [1, 2, 3])
        self.assertEqual(myComponent2.speed, 4)

        myComponent3 = Rotate(angles=[1, 2, 3], speed=4)
        np.testing.assert_array_almost_equal(myComponent3.angles, [1, 2, 3])
        self.assertEqual(myComponent3.speed, 4)

        print("TestGAComponent:test_init() END")

    def test_acceptance(self):
        print("\nTestDummyGravityComponent:test_acceptance() START")
        a1 = RigidBody()
        a2 = Rotate()
        b = System()
        a1.accept(b)
        a2.accept(b)
        print("\nTestDummyGravityComponent:test_acceptance() END")

    def test_functionality(self):
        print("\nTestDummyGravityComponent:test_functionality() START")

        entity = Entity("root", "Entity", "0")
        transComponent = BasicTransform(trs=util.translate(1.0, 2.0, 3.0))
        print("transComponent.trs", transComponent.trs)
        entity.add(transComponent)
        myComponent = RigidBody()
        myComponent.mass = 100
        entity.add(myComponent)

        b = GravitySystem()
        myComponent.accept(b)
        self.assertEqual(myComponent.mass, 0)

        myComponent2 = Rotate()
        myComponent2.angles = [1, 2, 3]
        myComponent2.speed = 4
        entity.add(myComponent2)

        b2 = RotateSystem()
        myComponent2.accept(b2)
        
        np.testing.assert_raises( AssertionError, np.testing.assert_array_almost_equal, transComponent.trs, util.translate(1.0, 2.0, 3.0) )

        print("\nTestDummyGravityComponent:test_functionality() END")




if __name__ == "__main__":
    unittest.main(argv=[""], verbosity=3, exit=False)
