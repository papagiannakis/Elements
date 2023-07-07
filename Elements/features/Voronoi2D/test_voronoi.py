import unittest
import numpy as np

import Elements.features.Voronoi2D.voronoi as voronoi



class TestEntity(unittest.TestCase):

    def test_voronoi_diagram(self):
        num_points = 10
        point_list = voronoi.random_points_in_square(num_points,1)
        mesh_vertices, mesh_indices, mesh_color, point_list, point_indices, point_colors = voronoi.voronoi_diagram(point_list)

        self.assertEqual(num_points, len(point_list))
        self.assertGreater(len(mesh_vertices), 0)
        self.assertGreater(len(mesh_indices), 0)
        self.assertGreater(len(mesh_color), 0)