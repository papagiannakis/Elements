import unittest
import numpy as np

import Elements.features.Slicing.Slicing as Slicing


class TestEntity(unittest.TestCase):

    def test_slicing(self):
        test_vertices = np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0]])
        test_indices = np.array([[0, 1, 2]])

        result_vertices = Slicing.intersect(test_vertices, test_indices, 0.5)

        self.assertEqual(len(result_vertices) % 2, 0)