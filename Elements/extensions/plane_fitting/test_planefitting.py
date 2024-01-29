import unittest
import numpy as np
from skspatial.objects import Plane, Points

import Elements.features.plane_fitting.planefitting_base as planefitting_base


class TestEntity(unittest.TestCase):

    def test_generate_projection_lines(self):
        test_fitting_nodes = [[0, 0, 0], [1, 0, 0.5], [-1, 0.5, 1], [0.5, 0.5, 0.5], [-1, 1, 0.5], [1, 0.5, -1]]
        plane = Plane.best_fit(Points(test_fitting_nodes))

        projection_vertices, projection_colors, projection_indices = planefitting_base.generate_projection_lines(plane, test_fitting_nodes)

        self.assertIsNotNone(projection_vertices)
        self.assertIsNotNone(projection_colors)
        self.assertIsNotNone(projection_indices)

        self.assertEqual(len(test_fitting_nodes)*2, len(projection_vertices))
        self.assertEqual(len(test_fitting_nodes)*2, len(projection_colors))
        self.assertEqual(len(test_fitting_nodes)*2, len(projection_indices))
        

    def test_generate_planefitting_data(self):
        test_fitting_nodes = [[0, 0, 0], [1, 0, 0.5], [-1, 0.5, 1], [0.5, 0.5, 0.5], [-1, 1, 0.5], [1, 0.5, -1]]
        plane = Plane.best_fit(Points(test_fitting_nodes))

        fitting_vertices, fitting_colors, fitting_indices = planefitting_base.generate_planefitting_data(plane, test_fitting_nodes)

        self.assertIsNotNone(fitting_vertices)
        self.assertIsNotNone(fitting_colors)
        self.assertIsNotNone(fitting_indices)

        self.assertEqual(len(fitting_vertices), 4)
        self.assertEqual(len(fitting_vertices), len(fitting_colors))
        self.assertEqual(len(fitting_indices), 6)
        