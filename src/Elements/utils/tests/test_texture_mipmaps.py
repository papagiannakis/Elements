"""
Unit tests
Employing the unittest standard python test framework
https://docs.python.org/3/library/unittest.html

Elements.pyGLV.GL.Textures -- the filters of Texture.

No window and no GL context: the OpenGL module used by Textures is replaced by a mock.
"""

import unittest
from unittest import mock

import Elements.pyGLV.GL.Textures as Textures


class TestTextureFilters(unittest.TestCase):
    def make_texture(self):
        with mock.patch.object(Textures, "gl") as gl:
            Textures.Texture(img_data=(bytes(4 * 4 * 4), 4, 4))
        return gl

    def test_minified_texture_samples_the_mipmaps(self):
        """The mipmaps are generated, so the minification filter has to read them: with plain GL_LINEAR a large
        image on a small object aliases and shimmers."""
        gl = self.make_texture()
        gl.glGenerateMipmap.assert_called_once()
        self.assertIn(mock.call(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR_MIPMAP_LINEAR),
                      gl.glTexParameteri.call_args_list)

    def test_magnification_stays_linear(self):
        gl = self.make_texture()
        self.assertIn(mock.call(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR),
                      gl.glTexParameteri.call_args_list)


if __name__ == "__main__":
    unittest.main()
