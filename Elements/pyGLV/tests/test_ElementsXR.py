import unittest
from Elements.pyGLV.XR.ElementsXR import options, Blend_Mode, View_Configuration, Form_factor
import xr

class TestElementsXR(unittest.TestCase):

    def setUp(self):
        """
        Initialize properties for unit-tests
        """
        self.options = options()

    def test_optionsXR(self):
        """
        Check whether changes in options take effect
        """

        self.assertIsNotNone(self.options)
        self.assertIsInstance(self.options.get_xr_environment_blend_mode(self.options.environment_blend_mode), xr.EnvironmentBlendMode)
        self.assertIsInstance(self.options.get_xr_form_factor(self.options.form_factor), xr.FormFactor)
        self.assertIsInstance(self.options.get_xr_view_configuration_type(self.options.view_configuration), xr.ViewConfigurationType)

        self.assertEquals(self.options.get_xr_environment_blend_mode_string(xr.EnvironmentBlendMode.OPAQUE),Blend_Mode.OPAQUE.value)
        self.assertEquals(self.options.get_xr_environment_blend_mode_string(xr.EnvironmentBlendMode.ADDITIVE),Blend_Mode.ADDITIVE.value)
        self.assertEquals(self.options.get_xr_environment_blend_mode_string(xr.EnvironmentBlendMode.ALPHA_BLEND),Blend_Mode.ALPHABLEND.value)
        
        self.options.set_environment_blend_mode(xr.EnvironmentBlendMode.ADDITIVE)
        self.assertEquals(self.options.parsed["environment_blend_mode"],xr.EnvironmentBlendMode.ADDITIVE)

        self.options.set_environment_blend_mode(xr.EnvironmentBlendMode.ALPHA_BLEND)
        self.assertEquals(self.options.parsed["environment_blend_mode"],xr.EnvironmentBlendMode.ALPHA_BLEND)

        self.options.set_environment_blend_mode(xr.EnvironmentBlendMode.OPAQUE)
        self.assertEquals(self.options.parsed["environment_blend_mode"],xr.EnvironmentBlendMode.OPAQUE)

