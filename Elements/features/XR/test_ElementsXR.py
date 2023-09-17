import unittest
from Elements.features.XR.ElementsXR import options, Blend_Mode, View_Configuration, Form_factor
import xr
from Elements.pyGLV.GL.Scene import Scene
import time
import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyECSS.System import  TransformSystem
from Elements.pyECSS.Component import BasicTransform, RenderMesh
from Elements.features.XR.ElementsXR import ElementsXR_program

class TestElementsXR(unittest.TestCase):

    def setUp(self):
        """
        Initialize properties for unit-tests
        """
        self.options = options()

        self.scene = Scene()

        self.rootEntity = self.scene.world.createEntity(Entity(name="RooT"))

        self.Head = self.scene.world.createEntity(Entity(name="Head"))
        self.scene.world.addEntityChild(self.rootEntity,self.Head)
        trans_head = self.scene.world.addComponent(self.Head,BasicTransform(name="trans_head",trs=util.translate(-22.0,-40.0,-22.0)))

        # Systems
        self.transUpdate = self.scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
        self.renderUpdate = self.scene.world.createSystem(RenderGLShaderSystem())
        self.initUpdate = self.scene.world.createSystem(InitGLShaderSystem())

        self.exit_loop = False

        self.program = ElementsXR_program()
        self.program.set_Head(self.Head)

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

    def test_empty_scene_XR(self):
        
        self.program.Initialize("ElementsXR Unit-test",self.initUpdate)

        while not self.exit_loop:
            if self.program.session_running:
                self.program.poll_actions()
                self.program.render_frame(self.renderUpdate)
            else:
                time.sleep(0.250)
