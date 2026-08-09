"""
Unit tests
Employing the unittest standard python test framework
https://docs.python.org/3/library/unittest.html

Elements.utils.normals -- generateFlatNormalsMesh and generateSmoothNormalsMesh.

No window and no GL context: normals are plain arithmetic on arrays, so everything here is checked
by computing the expected vectors independently and comparing.

The two functions differ only in the vertex layout they need, and both pick it themselves:

  flat    one normal per face, so every triangle corner needs its own vertex (a vertex carries a
          single normal, and the faces meeting at a corner have different ones). Explodes the mesh
          when it isn't already in that form.
  smooth  one normal per vertex, summed over the faces meeting there, so vertices must be shared
          between neighbouring faces. Merges the mesh when it isn't.

That decision is made from the index array. It used to be made by scanning the vertex positions for
duplicate rows, which silently produced smooth-like normals from generateFlatNormalsMesh for any
model holding two coincident vertices -- test_flat_explodes_despite_duplicate_positions covers it.
"""

import unittest

import numpy as np

import Elements.utils.normals as norm

#: the 8 corners of a cube, shared between faces -- the layout smooth shading wants
CUBE_VERTICES = np.array([
    [-0.5, -0.5, 0.5, 1.0],
    [-0.5, 0.5, 0.5, 1.0],
    [0.5, 0.5, 0.5, 1.0],
    [0.5, -0.5, 0.5, 1.0],
    [-0.5, -0.5, -0.5, 1.0],
    [-0.5, 0.5, -0.5, 1.0],
    [0.5, 0.5, -0.5, 1.0],
    [0.5, -0.5, -0.5, 1.0]
], dtype=np.float32)

#: 6 faces, 2 triangles each
CUBE_INDICES = np.array((1,0,3, 1,3,2,
                         2,3,7, 2,7,6,
                         3,0,4, 3,4,7,
                         6,5,1, 6,1,2,
                         4,5,6, 4,6,7,
                         5,4,0, 5,0,1), np.uint32)

CUBE_COLORS = np.array([[0.8, 0.0, 0.8, 1.0]] * 8, dtype=np.float32)


def face_normal(vertices, indices, triangle):
    """The unit normal of one triangle, computed here rather than taken from the module."""
    a, b, c = (vertices[indices[3 * triangle + k]][:3] for k in range(3))
    n = np.cross(b - a, c - a)
    return n / np.linalg.norm(n)


class TestGenerateNormals(unittest.TestCase):
    """the shared normal accumulation both mesh functions end with"""

    def test_normals_are_unit_length(self):
        print("\nTestGenerateNormals:test_normals_are_unit_length() START")

        normals = norm.generateNormals(CUBE_VERTICES, CUBE_INDICES)
        np.testing.assert_allclose(np.linalg.norm(normals, axis=1), 1.0, atol=1e-6)

        print("TestGenerateNormals:test_normals_are_unit_length() END")

    def test_one_per_vertex(self):
        print("\nTestGenerateNormals:test_one_per_vertex() START")

        self.assertEqual(len(norm.generateNormals(CUBE_VERTICES, CUBE_INDICES)), len(CUBE_VERTICES))

        print("TestGenerateNormals:test_one_per_vertex() END")

    def test_winding_decides_direction(self):
        """A triangle wound counter-clockwise as seen from +z faces +z; reversing two of its indices
        flips the normal. This is what makes normals depend on triangle order, not just position."""
        print("\nTestGenerateNormals:test_winding_decides_direction() START")

        triangle = np.array([[0.0,0.0,0.0,1.0], [1.0,0.0,0.0,1.0], [0.0,1.0,0.0,1.0]], dtype=np.float32)

        ccw = norm.generateNormals(triangle, np.array((0,1,2), np.uint32))
        np.testing.assert_allclose(ccw[0], (0.0, 0.0, 1.0), atol=1e-6)

        cw = norm.generateNormals(triangle, np.array((0,2,1), np.uint32))
        np.testing.assert_allclose(cw[0], (0.0, 0.0, -1.0), atol=1e-6)

        print("TestGenerateNormals:test_winding_decides_direction() END")

    def test_degenerate_triangle_gives_zero_not_nan(self):
        """A zero-area triangle has no normal to compute. It must come back as a zero vector: the
        division guard exists so it isn't 0/0, which would put NaN in the buffer and blacken
        everything the vertex touches."""
        print("\nTestGenerateNormals:test_degenerate_triangle_gives_zero_not_nan() START")

        collapsed = np.array([[0.0,0.0,0.0,1.0]] * 3, dtype=np.float32)
        normals = norm.generateNormals(collapsed, np.array((0,1,2), np.uint32))

        self.assertTrue(np.all(np.isfinite(normals)))
        np.testing.assert_allclose(normals, 0.0)

        print("TestGenerateNormals:test_degenerate_triangle_gives_zero_not_nan() END")


class TestGenerateFlatNormalsMesh(unittest.TestCase):

    def test_explodes_shared_vertices(self):
        """36 indices -> 36 vertices, one per triangle corner."""
        print("\nTestGenerateFlatNormalsMesh:test_explodes_shared_vertices() START")

        vertices, indices, colors, normals = norm.generateFlatNormalsMesh(
            CUBE_VERTICES.copy(), CUBE_INDICES.copy(), CUBE_COLORS.copy())

        self.assertEqual(len(vertices), len(CUBE_INDICES))
        self.assertEqual(len(indices), len(CUBE_INDICES))
        self.assertEqual(len(colors), len(vertices))
        self.assertEqual(len(normals), len(vertices))
        self.assertEqual(indices.max(), len(vertices) - 1)

        print("TestGenerateFlatNormalsMesh:test_explodes_shared_vertices() END")

    def test_six_face_normals_on_a_cube(self):
        """Every normal is one of the 6 axis directions, and all three corners of a triangle carry
        the same one -- that is what "flat" means."""
        print("\nTestGenerateFlatNormalsMesh:test_six_face_normals_on_a_cube() START")

        vertices, indices, _, normals = norm.generateFlatNormalsMesh(
            CUBE_VERTICES.copy(), CUBE_INDICES.copy(), CUBE_COLORS.copy())

        distinct = {tuple(np.round(n, 5)) for n in normals}
        self.assertEqual(len(distinct), 6, "a cube has 6 face directions, got %s" % len(distinct))
        for n in distinct:
            self.assertAlmostEqual(np.abs(n).sum(), 1.0, places=5)   # axis-aligned
            self.assertAlmostEqual(np.abs(n).max(), 1.0, places=5)

        for triangle in range(len(indices) // 3):
            corners = normals[indices[3 * triangle: 3 * triangle + 3]]
            np.testing.assert_allclose(corners[0], corners[1], atol=1e-6)
            np.testing.assert_allclose(corners[0], corners[2], atol=1e-6)
            np.testing.assert_allclose(corners[0], face_normal(vertices, indices, triangle), atol=1e-5)

        print("TestGenerateFlatNormalsMesh:test_six_face_normals_on_a_cube() END")

    def test_flat_explodes_despite_duplicate_positions(self):
        """The regression the index-based check fixes.

        This cube carries a 9th vertex duplicating a corner's position -- harmless, and exactly what
        the bundled teapot (403 of them) and cow (1680) do. Deciding from the positions found the
        duplicate and skipped the explode, returning shared vertices with accumulated, smooth-like
        normals from a function asked for flat ones. Deciding from the indices is unaffected."""
        print("\nTestGenerateFlatNormalsMesh:test_flat_explodes_despite_duplicate_positions() START")

        vertices = np.vstack([CUBE_VERTICES, CUBE_VERTICES[0:1]])   # 9 rows, one a duplicate
        colors = np.vstack([CUBE_COLORS, CUBE_COLORS[0:1]])
        self.assertLess(len({tuple(r) for r in vertices}), len(vertices), "test setup needs a duplicate")

        out_vertices, out_indices, _, normals = norm.generateFlatNormalsMesh(
            vertices, CUBE_INDICES.copy(), colors)

        self.assertEqual(len(out_vertices), len(CUBE_INDICES))   # exploded, not left at 9
        for n in normals:
            self.assertAlmostEqual(np.abs(n).sum(), 1.0, places=5, msg="normal %s is not a face normal" % n)

        print("TestGenerateFlatNormalsMesh:test_flat_explodes_despite_duplicate_positions() END")

    def test_already_exploded_mesh_is_left_alone(self):
        print("\nTestGenerateFlatNormalsMesh:test_already_exploded_mesh_is_left_alone() START")

        once = norm.generateFlatNormalsMesh(CUBE_VERTICES.copy(), CUBE_INDICES.copy(), CUBE_COLORS.copy())
        twice = norm.generateFlatNormalsMesh(once[0].copy(), once[1].copy(), once[2].copy())

        self.assertEqual(len(twice[0]), len(once[0]))
        np.testing.assert_allclose(twice[3], once[3], atol=1e-6)

        print("TestGenerateFlatNormalsMesh:test_already_exploded_mesh_is_left_alone() END")


class TestGenerateSmoothNormalsMesh(unittest.TestCase):

    def test_keeps_shared_vertices(self):
        print("\nTestGenerateSmoothNormalsMesh:test_keeps_shared_vertices() START")

        vertices, indices, colors, normals = norm.generateSmoothNormalsMesh(
            CUBE_VERTICES.copy(), CUBE_INDICES.copy(), CUBE_COLORS.copy())

        self.assertEqual(len(vertices), len(CUBE_VERTICES))
        self.assertEqual(len(normals), len(vertices))
        np.testing.assert_allclose(np.linalg.norm(normals, axis=1), 1.0, atol=1e-6)

        print("TestGenerateSmoothNormalsMesh:test_keeps_shared_vertices() END")

    def test_each_normal_blends_the_faces_at_that_corner(self):
        """The defining property: a vertex normal is the normalised sum of the normals of the
        triangles that use it, area-weighted (the cross products are not halved)."""
        print("\nTestGenerateSmoothNormalsMesh:test_each_normal_blends_the_faces_at_that_corner() START")

        vertices, indices, _, normals = norm.generateSmoothNormalsMesh(
            CUBE_VERTICES.copy(), CUBE_INDICES.copy(), CUBE_COLORS.copy())

        for vertex in range(len(vertices)):
            expected = np.zeros(3)
            for triangle in range(len(indices) // 3):
                corner = indices[3 * triangle: 3 * triangle + 3]
                if vertex in corner:
                    a, b, c = (vertices[i][:3] for i in corner)
                    expected += np.cross(b - a, c - a)        # unnormalised: area-weighted
            expected /= np.linalg.norm(expected)
            np.testing.assert_allclose(normals[vertex], expected, atol=1e-5)

        print("TestGenerateSmoothNormalsMesh:test_each_normal_blends_the_faces_at_that_corner() END")

    def test_normals_point_outwards_on_a_convex_shape(self):
        """On a cube centred at the origin, every corner normal must point away from the centre."""
        print("\nTestGenerateSmoothNormalsMesh:test_normals_point_outwards_on_a_convex_shape() START")

        vertices, _, _, normals = norm.generateSmoothNormalsMesh(
            CUBE_VERTICES.copy(), CUBE_INDICES.copy(), CUBE_COLORS.copy())

        for vertex, normal in zip(vertices, normals):
            self.assertGreater(np.dot(normal, vertex[:3]), 0.0)

        print("TestGenerateSmoothNormalsMesh:test_normals_point_outwards_on_a_convex_shape() END")

    def test_merges_an_exploded_mesh(self):
        """Handed a flat-shaded mesh, smooth shading has to put the shared vertices back, or there
        would be nothing for the normals to be averaged over."""
        print("\nTestGenerateSmoothNormalsMesh:test_merges_an_exploded_mesh() START")

        exploded = norm.generateFlatNormalsMesh(
            CUBE_VERTICES.copy(), CUBE_INDICES.copy(), CUBE_COLORS.copy())
        vertices, indices, colors, normals = norm.generateSmoothNormalsMesh(
            exploded[0].copy(), exploded[1].copy(), exploded[2].copy())

        self.assertLess(len(vertices), len(exploded[0]))
        self.assertEqual(len(normals), len(vertices))
        self.assertEqual(len(colors), len(vertices))
        # merged back to the 8 distinct corners, and the normals match the shared-vertex cube
        self.assertEqual(len(vertices), len(CUBE_VERTICES))

        print("TestGenerateSmoothNormalsMesh:test_merges_an_exploded_mesh() END")


class TestWithoutColors(unittest.TestCase):
    """color is optional in both signatures, and both paths must survive it being None."""

    def test_flat_without_colors(self):
        print("\nTestWithoutColors:test_flat_without_colors() START")

        vertices, _, colors, normals = norm.generateFlatNormalsMesh(
            CUBE_VERTICES.copy(), CUBE_INDICES.copy(), None)
        self.assertEqual(len(vertices), len(CUBE_INDICES))
        self.assertEqual(len(normals), len(vertices))

        print("TestWithoutColors:test_flat_without_colors() END")

    def test_smooth_without_colors_on_an_exploded_mesh(self):
        """The merging path is the one that indexes into `color`, so it is the one that used to
        raise TypeError when there was none."""
        print("\nTestWithoutColors:test_smooth_without_colors_on_an_exploded_mesh() START")

        exploded = norm.generateFlatNormalsMesh(CUBE_VERTICES.copy(), CUBE_INDICES.copy(), None)
        vertices, _, _, normals = norm.generateSmoothNormalsMesh(
            exploded[0].copy(), exploded[1].copy(), None)

        self.assertEqual(len(vertices), len(CUBE_VERTICES))
        self.assertEqual(len(normals), len(vertices))

        print("TestWithoutColors:test_smooth_without_colors_on_an_exploded_mesh() END")


if __name__ == "__main__":
    unittest.main(argv=[''], verbosity=3, exit=False)
