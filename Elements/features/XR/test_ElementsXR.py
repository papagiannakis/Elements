import unittest
from Elements.features.XR.options import options, Blend_Mode
import xr
from Elements.pyGLV.GL.Scene import Scene
import time
import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyGLV.GL.Shader import InitGLShaderSystem, RenderGLShaderSystem
from Elements.pyECSS.System import  TransformSystem
from Elements.pyECSS.Component import BasicTransform
from Elements.features.XR.ElementsXR import ElementsXR_program

class TestElementsXR(unittest.TestCase):

    def setUp(self):
        """
        Initialize properties for unit-tests
        """
        self.options = options()

        self.scene = Scene()

        self.rootEntity = self.scene.world.createEntity(Entity(name="RooT"))

        # Systems
        self.transUpdate = self.scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
        self.renderUpdate = self.scene.world.createSystem(RenderGLShaderSystem())
        self.initUpdate = self.scene.world.createSystem(InitGLShaderSystem())


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
        
        Head = self.scene.world.createEntity(Entity(name="Head"))
        self.scene.world.addEntityChild(self.rootEntity,Head)
        trans_head = self.scene.world.addComponent(Head,BasicTransform(name="trans_head",trs=util.identity()))

        exit_loop = False

        program: ElementsXR_program
        program = ElementsXR_program()
        program.set_Head(Head)

        program.Initialize("ElementsXR Unit-test",self.initUpdate)

        while not exit_loop:
            self.scene.world.traverse_visit(self.transUpdate,self.scene.world.root)
            exit_loop = program.poll_events()

            if program.session_running:
                program.poll_actions()
                program.render_frame(self.renderUpdate)
            else:
                time.sleep(0.250)
