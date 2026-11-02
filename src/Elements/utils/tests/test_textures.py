"""
Unit tests
Employing the unittest standard python test framework
https://docs.python.org/3/library/unittest.html

Elements.pyGLV.GL.Textures -- the flip option of Texture.

No window and no GL context: the OpenGL module used by Textures is replaced by a mock, so what is
tested is the pixel data that would be sent to the GPU, row by row.
"""

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from PIL import Image

import Elements.pyGLV.GL.Textures as Textures

RED = (255, 0, 0, 255)
BLUE = (0, 0, 255, 255)


def first_row_sent(gl_mock):
    """The RGBA of the first pixel of the first row that was handed to glTexImage2D."""
    pixels = gl_mock.glTexImage2D.call_args[0][8]
    return tuple(pixels[:4])


class TestTextureFlip(unittest.TestCase):
    def setUp(self):
        # a 2 x 2 image: red on the top row, blue on the bottom row, as displayed
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "two_rows.png"
        img = Image.new("RGBA", (2, 2))
        img.putdata([RED, RED, BLUE, BLUE])
        img.save(self.path)

    def tearDown(self):
        self.tmp.cleanup()

    def load(self, **kwargs):
        with mock.patch.object(Textures, "gl") as gl:
            Textures.Texture(self.path, **kwargs)
        return gl

    def test_default_is_flipped(self):
        """Unchanged behaviour: the bottom row of the picture is sent first, so v = 0 is the bottom."""
        self.assertEqual(first_row_sent(self.load()), BLUE)

    def test_flip_true_is_the_default(self):
        self.assertEqual(first_row_sent(self.load(flip=True)), BLUE)

    def test_flip_false_keeps_the_picture_as_displayed(self):
        """The top row is sent first, so v = 0 is the top and v = y / height."""
        self.assertEqual(first_row_sent(self.load(flip=False)), RED)

    def test_flip_does_not_change_the_size(self):
        gl = self.load(flip=False)
        args = gl.glTexImage2D.call_args[0]
        self.assertEqual((args[3], args[4]), (2, 2))

    def test_img_data_is_used_as_given(self):
        """flip only concerns files: raw bytes are never reordered."""
        data = bytes(RED + RED + BLUE + BLUE)
        for flip in (True, False):
            with mock.patch.object(Textures, "gl") as gl:
                Textures.Texture(img_data=(data, 2, 2), flip=flip)
            self.assertEqual(first_row_sent(gl), RED)


if __name__ == "__main__":
    unittest.main()
