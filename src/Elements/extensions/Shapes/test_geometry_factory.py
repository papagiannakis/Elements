import unittest

import Elements.extensions.Shapes.geometry_factory as geometry_factory


class TestGeometryFactory(unittest.TestCase):

    def test_cube(self):
        vertices, indices, colors, normals = geometry_factory.build_render_mesh("cube", {"scale": [1.0, 1.0, 1.0]})
        # 12 triangles, exploded to one vertex per triangle corner for flat shading
        self.assertEqual(len(vertices), 36)
        self.assertEqual(len(indices), 36)
        self.assertEqual(len(colors), 36)
        self.assertEqual(len(normals), 36)

    def test_sphere(self):
        vertices, indices, colors, normals = geometry_factory.build_render_mesh("sphere", {"lat": 4, "lon": 4})
        self.assertEqual(len(vertices), 14)  # 1 pole + 3 middle rings * 4 + 1 pole
        self.assertEqual(len(indices), 72)
        self.assertEqual(len(colors), 14)
        self.assertEqual(len(normals), 14)

    def test_cylinder(self):
        vertices, indices, colors, normals = geometry_factory.build_render_mesh("cylinder", {"segments": 4})
        self.assertEqual(len(vertices), 18)  # 2*4 side + (1+4) top cap + (1+4) bottom cap
        self.assertEqual(len(indices), 48)

    def test_cone(self):
        vertices, indices, colors, normals = geometry_factory.build_render_mesh("cone", {"segments": 4})
        self.assertEqual(len(vertices), 10)  # 1 apex + 4 side ring + (1+4) base cap
        self.assertEqual(len(indices), 24)

    def test_torus(self):
        vertices, indices, colors, normals = geometry_factory.build_render_mesh(
            "torus", {"major_segments": 4, "minor_segments": 4}
        )
        self.assertEqual(len(vertices), 16)  # major_segments * minor_segments
        self.assertEqual(len(indices), 96)

    def test_pyramid(self):
        vertices, indices, colors, normals = geometry_factory.build_render_mesh("pyramid", {})
        # hard-surface shape: exploded to one vertex per triangle corner, so vertices == indices
        self.assertEqual(len(vertices), 18)
        self.assertEqual(len(indices), 18)

    def test_triangular_pyramid(self):
        vertices, indices, colors, normals = geometry_factory.build_render_mesh("triangular_pyramid", {})
        self.assertEqual(len(vertices), 12)
        self.assertEqual(len(indices), 12)

    def test_plane(self):
        vertices, indices, colors, normals = geometry_factory.build_render_mesh("plane", {})
        self.assertEqual(len(vertices), 6)
        self.assertEqual(len(indices), 6)

    def test_flat_vs_smooth_dispatch(self):
        self.assertTrue(geometry_factory.shape_uses_flat_normals("cube"))
        self.assertFalse(geometry_factory.shape_uses_flat_normals("sphere"))

        # Smooth-shaded shapes keep their original (shared) vertex count.
        raw_vertices, _, _ = geometry_factory.create_geometry("cylinder", {"segments": 4})
        vertices, indices, _, _ = geometry_factory.build_render_mesh("cylinder", {"segments": 4})
        self.assertEqual(len(vertices), len(raw_vertices))
        self.assertLess(len(vertices), len(indices))

        # Flat-shaded (hard-surface) shapes explode to one vertex per triangle corner instead.
        raw_vertices, _, _ = geometry_factory.create_geometry("cube", {"scale": [1.0, 1.0, 1.0]})
        vertices, indices, _, _ = geometry_factory.build_render_mesh("cube", {"scale": [1.0, 1.0, 1.0]})
        self.assertGreater(len(vertices), len(raw_vertices))
        self.assertEqual(len(vertices), len(indices))

    def test_unsupported_shape_raises(self):
        with self.assertRaises(ValueError):
            geometry_factory.create_geometry("dodecahedron", {})

    def test_create_textured_cube(self):
        vertices, indices, uv = geometry_factory.create_textured_cube()
        # 6 faces * 6 indices (2 triangles), each corner given its own vertex/uv pair
        self.assertEqual(len(vertices), 36)
        self.assertEqual(len(indices), 36)
        self.assertEqual(len(uv), 36)

    def test_create_textured_mesh_dedicated_shape(self):
        vertices, indices, uv = geometry_factory.create_textured_mesh("cube", {"scale": [1.0, 1.0, 1.0]})
        # 4 unique vertices per face * 6 faces, via _textured_box's dedicated UV mapping
        self.assertEqual(len(vertices), 24)
        self.assertEqual(len(indices), 36)
        self.assertEqual(len(uv), len(vertices))

    def test_create_textured_mesh_fallback_projection(self):
        # torus has no dedicated _textured_* builder, so create_textured_mesh() falls back to a
        # spherical UV projection over its plain (untextured) geometry.
        params = {"major_segments": 4, "minor_segments": 4}
        raw_vertices, _, _ = geometry_factory.create_geometry("torus", params)
        vertices, indices, uv = geometry_factory.create_textured_mesh("torus", params)
        self.assertEqual(len(vertices), len(raw_vertices))
        self.assertEqual(len(uv), len(vertices))
        for u, v in uv:
            self.assertGreaterEqual(u, 0.0)
            self.assertLessEqual(u, 1.0)
            self.assertGreaterEqual(v, 0.0)
            self.assertLessEqual(v, 1.0)


if __name__ == "__main__":
    unittest.main()
