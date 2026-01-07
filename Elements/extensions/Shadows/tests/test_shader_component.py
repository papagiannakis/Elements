import unittest
from unittest.mock import MagicMock, patch
import sys

# Mock the OpenGL module to avoid needing a live graphics context
sys.modules['OpenGL'] = MagicMock()
sys.modules['OpenGL.GL'] = MagicMock()

# Import the class to be tested
from Elements.extensions.Shadows.ShadowShader import ShadowShader

class TestShaderComponent(unittest.TestCase):

    def test_shader_constructor(self):
        """
        Tests that the ShadowShader component is initialized correctly via its constructor.
        """
        # Define some dummy shader source strings
        dummy_vert_shader = "void main() { gl_Position = vec4(1.0); }"
        dummy_frag_shader = "void main() { gl_FragColor = vec4(1.0); }"

        # Instantiate the component
        shader = ShadowShader(
            name="TestShader",
            vertex_source=dummy_vert_shader,
            fragment_source=dummy_frag_shader
        )

        # Assert that the internal attributes were set correctly
        self.assertEqual(shader.name, "TestShader")
        self.assertEqual(shader._vertex_source, dummy_vert_shader)
        self.assertEqual(shader._fragment_source, dummy_frag_shader)
        
        # The OpenGL program ID should not be set before init() is called
        self.assertIsNone(shader.glid)

    @patch('Elements.extensions.Shadows.ShadowShader.gl')
    def test_shader_init_triggers_gl_calls(self, mock_gl):
        """
        Tests that calling the init() method triggers the expected OpenGL
        functions for shader compilation and linking.
        
        We "patch" the gl module within this test's scope to monitor its usage.
        """
        # We can give the mock functions return values if needed
        mock_gl.glCreateProgram.return_value = 1 # A dummy program ID
        mock_gl.glCreateShader.return_value = 10 # A dummy shader ID
        mock_gl.glGetShaderiv.return_value = 1 # Mock success status
        mock_gl.glGetProgramiv.return_value = 1 # Mock success status
        
        # Instantiate a basic shader
        shader = ShadowShader(name="TestInit")
        
        # Call the init method
        shader.init()

        # Assert that the core OpenGL functions were called
        mock_gl.glCreateProgram.assert_called_once()
        self.assertEqual(mock_gl.glCreateShader.call_count, 2) # one vertex, one fragment
        self.assertEqual(mock_gl.glAttachShader.call_count, 2)
        mock_gl.glLinkProgram.assert_called_once_with(1) # Check it was called with the dummy ID
        
        # The glid should now be set
        self.assertIsNotNone(shader.glid)
        self.assertEqual(shader.glid, 1)

    def test_default_shaders_are_assigned(self):
        """
        Tests that if no shader source is provided, the component defaults
        to the Phong Directional shaders.
        """
        shader = ShadowShader(name="DefaultShader")
        # Before init, the sources are None
        self.assertIsNone(shader._vertex_source)
        self.assertIsNone(shader._fragment_source)

        # Patch gl and call init
        with patch('Elements.extensions.Shadows.ShadowShader.gl') as mock_gl:
            mock_gl.glGetShaderiv.return_value = 1
            mock_gl.glGetProgramiv.return_value = 1
            shader.init()

        # After init, the default sources should be assigned
        self.assertEqual(shader._vertex_source, ShadowShader.VERT_DIR_PHONG)
        self.assertEqual(shader._fragment_source, ShadowShader.FRAG_DIR_PHONG)


if __name__ == '__main__':
    unittest.main()
