import unittest
import numpy as np

import Elements.extensions.bezier.bezier_base as bezier_base


class TestEntity(unittest.TestCase):

    def test_generate_bezier_data(self):
        test_bezier_control_nodes = [[0.5, 0.0, 0.0], [1.0, 5.0, 1.0]]
        test_render_detail = 100
        vertices, colors, indices = bezier_base.generate_bezier_data(test_bezier_control_nodes, test_render_detail)

        self.assertEqual(test_render_detail*2-2, len(vertices))
        self.assertIn(bezier_base.xyz_to_vertices(test_bezier_control_nodes)[0], vertices)
        self.assertIn(bezier_base.xyz_to_vertices(test_bezier_control_nodes)[-1], vertices)

        self.assertEqual(test_render_detail*2-2, len(colors))
        self.assertEqual(test_render_detail*2-2, len(indices))
