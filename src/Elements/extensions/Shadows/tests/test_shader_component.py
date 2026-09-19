import sys
from unittest.mock import patch

# Mock the OpenGL module globally for this file
class OpenGLPlaceholder:
    def __getattr__(self, name):
        return OpenGLPlaceholder()
    def __call__(self, *args, **kwargs):
        return None

sys.modules['OpenGL'] = OpenGLPlaceholder()
sys.modules['OpenGL.GL'] = OpenGLPlaceholder()

from Elements.extensions.Shadows.ShadowShader import ShadowShader
from Elements.definitions import SHADER_DIR

def test_shader_constructor():
    """
    Tests that the ShadowShader component is initialized correctly via its constructor.
    """
    # Define some dummy shader source strings
    dummy_vert_shader = "void main() { gl_Position = vec4(1.0); }"
    dummy_frag_shader = "void main() { gl_FragColor = vec4(1.0); }"

    # Instantiate the component
    shader = ShadowShader(name="TestShader", vertex_source=dummy_vert_shader, fragment_source=dummy_frag_shader)

    # Assert that the internal attributes were set correctly
    assert shader.name == "TestShader"
    assert shader._vertex_source == dummy_vert_shader
    assert shader._fragment_source == dummy_frag_shader
            
    # The OpenGL program ID should not be set before init() is called
    assert shader.glid is None

def test_shader_init_triggers_gl_calls():
    """
    Tests that calling the init() method triggers the expected OpenGL
    functions for shader compilation and linking.
    """
    # Setup the mock for the gl module inside the ShadowShader file
    with patch('Elements.extensions.Shadows.ShadowShader.gl') as mock_gl:
        mock_gl.glCreateProgram.return_value = 1
        mock_gl.glCreateShader.return_value = 10
        mock_gl.glGetShaderiv.return_value = 1
        mock_gl.glGetProgramiv.return_value = 1

        # Instantiate a basic shader
        shader = ShadowShader(name="TestInit")

        # Call the init method
        shader.init()

    # Assert that the core OpenGL functions were called
    mock_gl.glCreateProgram.assert_called_once()
    # one vertex, one fragment
    assert mock_gl.glCreateShader.call_count == 2
    assert mock_gl.glAttachShader.call_count == 2

    #Check it was called with the dummy ID
    mock_gl.glLinkProgram.assert_called_once_with(1)

    # The glid should now be set
    assert shader.glid == 1

def test_default_shaders_are_assigned():
    """
    Tests that if no shader source is provided, the component defaults
    to the Phong Directional shaders.
    """
    shader = ShadowShader(name="DefaultShader")
    
    assert shader._vertex_source is None
    assert shader._fragment_source is None

    # Patch gl and call init
    with patch('Elements.extensions.Shadows.ShadowShader.gl') as mock_gl:
        mock_gl.glGetShaderiv.return_value = 1
        mock_gl.glGetProgramiv.return_value = 1

        shader.init()

    # After init, the default sources should be assigned
    assert shader._vertex_source == (SHADER_DIR / "DirPhong.vert").read_text()
    assert shader._fragment_source == (SHADER_DIR / "DirPhong.frag").read_text()
