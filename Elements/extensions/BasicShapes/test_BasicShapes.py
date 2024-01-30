import unittest
import numpy as np

import Elements.extensions.BasicShapes.BasicShapes as BasicShapes
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyECSS.Entity import Entity


class TestInitialization(unittest.TestCase):
    
    def setUp(self):
        scene = Scene()
        rootEntity = scene.world.createEntity(Entity(name="Root"))

    def test_cylinder(self):
        cylinder = BasicShapes.CylinderSpawn()
        self.assertEqual(len(cylinder.mesh.vertex_attributes[0]), 400) # vertices
        self.assertEqual(len(cylinder.mesh.vertex_index[0]), 2400) # indices

    def test_torus(self):
        torus = BasicShapes.TorusSpawn()
        # torus.spawn(self.rootEntity)
        self.assertEqual(len(torus.mesh.vertex_attributes[0]), 400) # vertices
        self.assertEqual(len(torus.mesh.vertex_index[0]), 2400) # indices
    
    def test_cube(self):
        cube = BasicShapes.CubeSpawn()
        # cube.spawn(self.rootEntity)
        self.assertEqual(len(cube.mesh.vertex_attributes[0]), 36) # vertices
        self.assertEqual(len(cube.mesh.vertex_index[0]), 36) # indices
    
    def test_sphere(self):
        sphere = BasicShapes.SphereSpawn()
        # sphere.spawn(self.rootEntity)
        self.assertEqual(len(sphere.mesh.vertex_attributes[0]), 400) # vertices
        self.assertEqual(len(sphere.mesh.vertex_index[0]), 2400) # indices
