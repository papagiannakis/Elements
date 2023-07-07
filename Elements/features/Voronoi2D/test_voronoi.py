import unittest
import numpy as np

import Elements.pyGLV.voronoi.voronoi as voronoi


class TestEntity(unittest.TestCase):

    def test_voronoi_diagram(self):
        num_points = 10
        mesh_vertices, mesh_indices, mesh_color, point_list, point_indices, point_colors = voronoi.voronoi_diagram(num_points)

        self.assertEqual(num_points, len(point_list))
        self.assertGreater(len(mesh_vertices), 0)
        self.assertGreater(len(mesh_indices), 0)
        self.assertGreater(len(mesh_color), 0)