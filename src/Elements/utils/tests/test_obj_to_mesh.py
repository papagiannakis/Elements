"""
Unit tests
Employing the unittest standard python test framework
https://docs.python.org/3/library/unittest.html

Elements.utils.obj_to_mesh -- the Wavefront .obj reader.

No window and no GL context. Most cases are tiny .obj files written to a temp directory, so what is
being tested is the parsing rather than any particular model; the last test loads every .obj bundled
with Elements, which is what caught the failures this reader was rewritten to fix.
"""

import tempfile
import unittest
from pathlib import Path

import numpy as np

from Elements.definitions import MODEL_DIR
from Elements.utils.obj_to_mesh import obj_to_mesh

#: a unit square as two triangles, written in the four face syntaxes .obj allows
SQUARE_VERTICES = """
v 0.0 0.0 0.0
v 1.0 0.0 0.0
v 1.0 1.0 0.0
v 0.0 1.0 0.0
"""


def write_obj(directory, name, text):
    path = Path(directory) / name
    path.write_text(text)
    return path


class TestFaceFormats(unittest.TestCase):
    """A face field may be v, v/vt, v//vn or v/vt/vn. Only the leading position index matters."""

    def test_all_four_formats_agree(self):
        print("\nTestFaceFormats:test_all_four_formats_agree() START")

        faces = {
            "position only": "f 1 2 3\nf 1 3 4\n",
            "v/vt": "f 1/1 2/2 3/3\nf 1/1 3/3 4/4\n",
            "v//vn": "f 1//1 2//2 3//3\nf 1//1 3//3 4//4\n",
            "v/vt/vn": "f 1/1/1 2/2/2 3/3/3\nf 1/1/1 3/3/3 4/4/4\n",
        }
        with tempfile.TemporaryDirectory() as tmp:
            expected = None
            for label, face_text in faces.items():
                path = write_obj(tmp, "square.obj", SQUARE_VERTICES + face_text)
                vertices, indices, colors = obj_to_mesh(path)
                self.assertEqual(len(vertices), 4, label)
                self.assertEqual(len(indices), 6, label)
                if expected is None:
                    expected = indices
                np.testing.assert_array_equal(indices, expected, err_msg=label)

        print("TestFaceFormats:test_all_four_formats_agree() END")

    def test_indices_are_zero_based(self):
        """.obj counts from 1, OpenGL from 0."""
        print("\nTestFaceFormats:test_indices_are_zero_based() START")

        with tempfile.TemporaryDirectory() as tmp:
            path = write_obj(tmp, "tri.obj", "v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n")
            _, indices, _ = obj_to_mesh(path)
            np.testing.assert_array_equal(indices, [0, 1, 2])

        print("TestFaceFormats:test_indices_are_zero_based() END")

    def test_negative_indices_count_back(self):
        """A negative index is relative to the vertices read so far: -1 is the most recent."""
        print("\nTestFaceFormats:test_negative_indices_count_back() START")

        with tempfile.TemporaryDirectory() as tmp:
            path = write_obj(tmp, "rel.obj", "v 0 0 0\nv 1 0 0\nv 0 1 0\nf -3 -2 -1\n")
            _, indices, _ = obj_to_mesh(path)
            np.testing.assert_array_equal(indices, [0, 1, 2])

        print("TestFaceFormats:test_negative_indices_count_back() END")


class TestTriangulation(unittest.TestCase):

    def test_quad_becomes_two_triangles(self):
        print("\nTestTriangulation:test_quad_becomes_two_triangles() START")

        with tempfile.TemporaryDirectory() as tmp:
            path = write_obj(tmp, "quad.obj", SQUARE_VERTICES + "f 1 2 3 4\n")
            _, indices, _ = obj_to_mesh(path)

            self.assertEqual(len(indices), 6, "a quad is 2 triangles, not 1")
            np.testing.assert_array_equal(indices, [0, 1, 2, 0, 2, 3])   # fan from the first corner

        print("TestTriangulation:test_quad_becomes_two_triangles() END")

    def test_ngon_becomes_n_minus_two_triangles(self):
        print("\nTestTriangulation:test_ngon_becomes_n_minus_two_triangles() START")

        with tempfile.TemporaryDirectory() as tmp:
            hexagon = "".join("v %f %f 0.0\n" % (np.cos(a), np.sin(a))
                              for a in np.linspace(0, 2 * np.pi, 6, endpoint=False))
            path = write_obj(tmp, "hex.obj", hexagon + "f 1 2 3 4 5 6\n")
            _, indices, _ = obj_to_mesh(path)

            self.assertEqual(len(indices) // 3, 4)      # 6 - 2

        print("TestTriangulation:test_ngon_becomes_n_minus_two_triangles() END")


class TestTolerance(unittest.TestCase):
    """Real .obj files are full of things that are not vertices or faces."""

    def test_other_records_and_comments_are_skipped(self):
        print("\nTestTolerance:test_other_records_and_comments_are_skipped() START")

        text = ("# a comment\n"
                "mtllib thing.mtl\n"
                "o thing\n"
                "v 0 0 0\n"
                "vt 0.5 0.5\n"          # must not be read as a vertex
                "vn 0 1 0\n"            # nor this
                "v 1 0 0\n"
                "\n"
                "v 0 1 0\n"
                "g group1\n"
                "usemtl red\n"
                "s off\n"
                "f 1 2 3\n")
        with tempfile.TemporaryDirectory() as tmp:
            vertices, indices, _ = obj_to_mesh(write_obj(tmp, "noisy.obj", text))
            self.assertEqual(len(vertices), 3, "vt/vn/o/g must not become vertices")
            self.assertEqual(len(indices), 3)

        print("TestTolerance:test_other_records_and_comments_are_skipped() END")

    def test_extra_whitespace_and_tabs(self):
        print("\nTestTolerance:test_extra_whitespace_and_tabs() START")

        text = "v   0 0 0\nv\t1\t0\t0\nv  0  1  0\nf   1  2   3\n"
        with tempfile.TemporaryDirectory() as tmp:
            vertices, indices, _ = obj_to_mesh(write_obj(tmp, "spaced.obj", text))
            self.assertEqual(len(vertices), 3)
            self.assertEqual(len(indices), 3)

        print("TestTolerance:test_extra_whitespace_and_tabs() END")

    def test_a_broken_line_does_not_lose_the_file(self):
        print("\nTestTolerance:test_a_broken_line_does_not_lose_the_file() START")

        text = "v 0 0 0\nv 1 0 0\nv oops nope\nv 0 1 0\nf 1 2 3\nf 1 2\nf 1 2 x\n"
        with tempfile.TemporaryDirectory() as tmp:
            vertices, indices, _ = obj_to_mesh(write_obj(tmp, "broken.obj", text))
            self.assertEqual(len(vertices), 3)      # the malformed vertex is skipped
            self.assertEqual(len(indices), 3)       # so are the 2-vertex and non-numeric faces

        print("TestTolerance:test_a_broken_line_does_not_lose_the_file() END")

    def test_missing_file_raises(self):
        """Clearer than the old behaviour, which printed and returned None -- leaving the caller to
        fail on `a, b, c = None` instead."""
        print("\nTestTolerance:test_missing_file_raises() START")

        with self.assertRaises((FileNotFoundError, OSError)):
            obj_to_mesh("no_such_model_12345.obj")

        print("TestTolerance:test_missing_file_raises() END")


class TestReturnedArrays(unittest.TestCase):

    def test_shapes_dtypes_and_colours(self):
        print("\nTestReturnedArrays:test_shapes_dtypes_and_colours() START")

        colour = [0.25, 0.5, 0.75, 1.0]
        with tempfile.TemporaryDirectory() as tmp:
            path = write_obj(tmp, "tri.obj", "v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n")
            vertices, indices, colors = obj_to_mesh(path, color=colour)

        self.assertEqual(vertices.shape, (3, 4))            # homogeneous positions
        self.assertEqual(colors.shape, (3, 4))              # one per vertex
        self.assertEqual(vertices.dtype, np.float32)
        self.assertEqual(indices.dtype, np.uint32)          # matches GL_UNSIGNED_INT
        self.assertEqual(colors.dtype, np.float32)
        np.testing.assert_allclose(vertices[:, 3], 1.0)     # w
        for row in colors:
            np.testing.assert_allclose(row, colour)

        print("TestReturnedArrays:test_shapes_dtypes_and_colours() END")


class TestBundledModels(unittest.TestCase):
    """Every .obj shipped with Elements must load. 11 of these used to raise ValueError, because
    their faces are written v/vt/vn, and the quad-only one used to come out at half its triangles."""

    def test_every_bundled_obj_loads(self):
        print("\nTestBundledModels:test_every_bundled_obj_loads() START")

        models = sorted(MODEL_DIR.rglob("*.obj"))
        self.assertTrue(models, "no .obj models found under %s" % MODEL_DIR)

        for model in models:
            with self.subTest(model=model.name):
                vertices, indices, colors = obj_to_mesh(model)
                self.assertGreater(len(vertices), 0)
                self.assertGreater(len(indices), 0)
                self.assertEqual(len(indices) % 3, 0, "indices must be whole triangles")
                self.assertEqual(len(colors), len(vertices))
                self.assertLess(indices.max(), len(vertices), "index past the end of the vertices")

        print("Loaded %d bundled models" % len(models))
        print("TestBundledModels:test_every_bundled_obj_loads() END")

    def test_quad_model_keeps_all_its_surface(self):
        """pighighpoly1.obj is 100% quads: 1828 faces must become 3656 triangles, not 1828."""
        print("\nTestBundledModels:test_quad_model_keeps_all_its_surface() START")

        pig = MODEL_DIR / "pighighpoly1.obj"
        if not pig.exists():
            self.skipTest("pighighpoly1.obj not present")

        faces = sum(1 for line in pig.read_text(errors="ignore").splitlines()
                    if line.split()[:1] == ["f"])
        _, indices, _ = obj_to_mesh(pig)
        self.assertEqual(len(indices) // 3, 2 * faces)

        print("TestBundledModels:test_quad_model_keeps_all_its_surface() END")


if __name__ == "__main__":
    unittest.main(argv=[''], verbosity=3, exit=False)
