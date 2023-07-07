import unittest
import numpy as np

import Elements.features.BasicShapes.BasicShapes as BasicShapes


class TestEntity(unittest.TestCase):

    def test_slicing(self):
        cylinder = BasicShapes.CylinderSpawn()
        torus = BasicShapes.TorusSpawn()
        cube = BasicShapes.CubeSpawn()
        sphere = BasicShapes.SphereSpawn()

