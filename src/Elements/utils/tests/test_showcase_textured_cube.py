"""
Unit tests
Employing the unittest standard python test framework
https://docs.python.org/3/library/unittest.html

Elements.extensions.showcase.scene_helpers -- the textured cube of SceneBuilder.

No window and no GL context: SceneBuilder._add_entity is replaced, so what is tested is the mesh
that would be sent to the GPU. Every per-vertex array has to stay in step with the vertices, or
the image comes out scrambled.
"""

import unittest
from unittest import mock

import numpy as np

from Elements.extensions.showcase.scene_helpers import SceneBuilder


def build_textured_cube():
    builder = SceneBuilder(scene=None, root_entity=None)
    with mock.patch.object(SceneBuilder, "_add_entity") as add_entity:
        builder.add_textured_cube("Dice", position=(0, 0, 0))
    args, kwargs = add_entity.call_args
    _name, _trs, vertices, indices, colors, normals = args
    return vertices, indices, colors, normals, kwargs["uv"]


class TestTexturedCube(unittest.TestCase):
    def setUp(self):
        self.vertices, self.indices, self.colors, self.normals, self.uv = build_textured_cube()

    def test_every_vertex_attribute_has_one_row_per_vertex(self):
        n = len(self.vertices)
        self.assertEqual((len(self.colors), len(self.normals), len(self.uv)), (n, n, n))

    def test_indices_only_name_existing_vertices(self):
        self.assertEqual(len(self.indices), 36)
        self.assertLess(int(self.indices.max()), len(self.vertices))

    def test_normals_are_flat_unit_axes_pointing_away_from_the_centre(self):
        self.assertTrue(np.allclose(np.linalg.norm(self.normals, axis=1), 1.0))
        self.assertTrue(np.allclose(np.abs(self.normals).max(axis=1), 1.0))
        self.assertTrue(np.all(np.sum(self.normals * self.vertices[:, :3], axis=1) > 0.0))

    def test_every_face_shows_the_whole_image_once(self):
        """The 4 vertices of a face carry the 4 corners of the image, one each."""
        corners = {(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)}
        faces = {}
        for normal, uv in zip(map(tuple, np.round(self.normals, 3)), map(tuple, self.uv)):
            faces.setdefault(normal, []).append(uv)
        self.assertEqual(len(faces), 6)
        for normal, uvs in faces.items():
            self.assertEqual(len(uvs), 4, normal)
            self.assertEqual(set(uvs), corners, normal)


if __name__ == "__main__":
    unittest.main()
