import unittest
import numpy as np

import  Elements.pyGLV.plotting.plotting_base as plotting_base

plot_boundaries = 1, -1, 1, -1 #max X, min X, max Y, min Y
f_x = 'x**2+x*4'
f_x_y = 'x**2+y**2'
func_detail = 30

class TestEntity(unittest.TestCase):

    def test_generate_plot2d_data(self):

        plotting2d_vertices, plotting2d_colors, plotting2d_indices = plotting_base.generate_plot2d_data(plot_boundaries, func_detail, f_x)

        self.assertIsNotNone(plotting2d_vertices)
        self.assertIsNotNone(plotting2d_colors)
        self.assertIsNotNone(plotting2d_indices)

        self.assertEqual(func_detail*2-4, len(plotting2d_vertices))
        self.assertEqual(len(plotting2d_vertices), len(plotting2d_colors))
        self.assertEqual(len(plotting2d_vertices), len(plotting2d_indices))
        

    def test_generate_plot3d_data(self):

        plotting3d_vertices, plotting3d_colors, plotting3d_indices, plotting3d_normals = plotting_base.generate_plot3d_data(plot_boundaries, func_detail, f_x_y)

        self.assertIsNotNone(plotting3d_vertices)
        self.assertIsNotNone(plotting3d_colors)
        self.assertIsNotNone(plotting3d_indices)
        self.assertIsNotNone(plotting3d_normals)

        self.assertEqual(len(plotting3d_vertices), len(plotting3d_colors))
        self.assertEqual(len(plotting3d_vertices), len(plotting3d_indices))
        self.assertEqual(len(plotting3d_vertices), len(plotting3d_normals))
