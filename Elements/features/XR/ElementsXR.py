from Elements.pyGLV.GL.Shader import InitGLShaderSystem, RenderGLShaderSystem
from Elements.pyECSS.Entity import Entity
import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Component import BasicTransform, RenderMesh
from ctypes import Structure, c_int32, c_float, POINTER, byref, cast, c_void_p, pointer, Array
from Elements.features.XR.PlatformPlugin import createPlatformPlugin
from Elements.features.XR.GraphicsPlugin import OpenGLPlugin, create_xr_quaternion
from Elements.features.XR.options import options
import logging
import Elements.utils.normals as norm
from typing import Optional
import math
import sys
import enum
import numpy as np
import xr
import xr.raw_functions

logger = logging.getLogger()
stream = logging.StreamHandler(sys.stdout)
streamformat = logging.Formatter("%(asctime)s:%(message)s")
stream.setFormatter(streamformat)
logger.addHandler(stream)

class Swapchain(Structure):
    _fields_ = [
        ("handle", xr.Swapchain),
        ("width", c_int32),
        ("height", c_int32),
    ]

class Side(enum.IntEnum):
    LEFT = 0
    RIGHT = 1

class InputState(Structure):
        def __init__(self):
            super().__init__()
            self.hand_scale[:] = [1, 1]

        _fields_ = [
            ("action_set", xr.ActionSet),
            ("grab_action", xr.Action),
            ("pose_action", xr.Action),
            ("vibrate_action", xr.Action),
            ("quit_action", xr.Action),
            ("hand_subaction_path", xr.Path * len(Side)),
            ("hand_space", xr.Space * len(Side)),
            ("hand_scale", c_float * len(Side)),
            ("hand_active", xr.Bool32 * len(Side)),
        ]

class RayDirection:
    def __init__(self):
        self.origin = util.vec(0.0,0.0,0.0)
        self.direction = util.vec(0.0,0.0,0.0)

def get_xr_reference_space_create_info(reference_space_type_string: str) -> xr.ReferenceSpaceCreateInfo:
    create_info = xr.ReferenceSpaceCreateInfo(
        pose_in_reference_space=xr.Posef(), # Identity structure for xr that contains translation and rotation
    )
    space_type = reference_space_type_string.lower()
    if space_type == "View".lower():
        create_info.reference_space_type = xr.ReferenceSpaceType.VIEW
    elif space_type == "ViewFront".lower():
        pose = xr.Posef()
        pose.position[0] = 0
        pose.position[0] = 0
        pose.position[0] = -2
        create_info.pose_in_reference_space = pose
        create_info.reference_space_type = xr.ReferenceSpaceType.VIEW
    elif space_type == "Local".lower():
        create_info.reference_space_type = xr.ReferenceSpaceType.LOCAL
    elif space_type == "Stage".lower():
        create_info.reference_space_type = xr.ReferenceSpaceType.STAGE
    elif space_type == "StageLeft".lower():
        create_info.reference_space_type = xr.ReferenceSpaceType.STAGE
        pose = xr.Posef()

        pose.position[0] = -2
        pose.position[0] = 0
        pose.position[0] = 2

        pose.orientation.x = 0
        pose.orientation.y = math.sin(0)
        pose.orientation.z = 0
        pose.orientation.w = math.cos(0)
        create_info.pose_in_reference_space = pose
    elif space_type == "StageRight".lower():
        create_info.reference_space_type = xr.ReferenceSpaceType.STAGE
        pose = xr.Posef()

        pose.position[0] = 2
        pose.position[0] = 0
        pose.position[0] = -2

        pose.orientation.x = 0
        pose.orientation.y = math.sin(0)
        pose.orientation.z = 0
        pose.orientation.w = math.cos(0)
        create_info.pose_in_reference_space = pose
    elif space_type == "StageLeftRotated".lower():
        create_info.reference_space_type = xr.ReferenceSpaceType.STAGE
        pose = xr.Posef()

        pose.position[0] = -2
        pose.position[0] = 0.5
        pose.position[0] = -2

        pose.orientation.x = 0
        pose.orientation.y = math.sin((math.pi/3) * 0.5)
        pose.orientation.z = 0
        pose.orientation.w = math.cos((math.pi/3) * 0.5)
        create_info.pose_in_reference_space = pose
    elif space_type == "StageRightRotated".lower():
        create_info.reference_space_type = xr.ReferenceSpaceType.STAGE
        pose = xr.Posef()

        pose.position[0] = 2
        pose.position[0] = 0.5
        pose.position[0] = -2

        pose.orientation.x = 0
        pose.orientation.y = math.sin((-math.pi/3) * 0.5)
        pose.orientation.z = 0
        pose.orientation.w = math.cos((-math.pi/3) * 0.5)
        create_info.pose_in_reference_space = pose
    else:
        raise ValueError(f"Unknown reference space type '{reference_space_type_string}'")
    return create_info

def xr_debug_callback(
            severity: xr.DebugUtilsMessageSeverityFlagsEXT,
            _type: xr.DebugUtilsMessageTypeFlagsEXT,
            data: POINTER(xr.DebugUtilsMessengerCallbackDataEXT),
            _user_data: c_void_p) -> bool:
    d = data.contents
    return True

class ElementsXR_program:

    def __init__(self):
        "An openXR program in Elements"
        self.options = options() # Only Opaque is supported by the OpenXR runtime and/or windows platform
        self.platform_plugin = createPlatformPlugin()
        self.graphics_plugin = OpenGLPlugin(self.options)
        self.debug_callback = xr.PFN_xrDebugUtilsMessengerCallbackEXT(xr_debug_callback)

        self.instance = None
        self.session = None
        self.app_space = None
        self.form_factor = xr.FormFactor.HEAD_MOUNTED_DISPLAY
        self.system = None  # Higher level System class, not just ID

        self.config_views = []
        self.swapchains = []
        self.swapchain_image_buffers = []  # to keep objects alive
        self.swapchain_image_ptr_buffers = {}
        self.views = (xr.View * 2)(xr.View(), xr.View())
        self.color_swapchain_format = -1

        self.visualized_spaces = []

        # Application's current lifecycle state according to the runtime
        self.session_state = xr.SessionState.UNKNOWN
        self.session_running = False

        self.event_data_buffer = xr.EventDataBuffer()
        self.input = InputState()

        self.event_data_buffer = xr.EventDataBuffer()

        self.acceptable_blend_modes = [
            xr.EnvironmentBlendMode.OPAQUE,
            xr.EnvironmentBlendMode.ADDITIVE,
            xr.EnvironmentBlendMode.ALPHA_BLEND,
        ]

        #Head Entity
        self.head = None

        #Hand Entities
        self.hands = [Entity()] * 2

        #Ray Entities
        self.rays = [Entity()] * 2

        self.raycast = False
        self.hand_dist = 0.2

        #shows whether the controllers trigger buttons are pressed or not
        self.grab_values = [False, False]

        self.hand_trs = [util.identity(),util.identity()]

        self.gizmos_Mode = "Disappear"
        self.translate_gizmos = set()
        self.rotation_gizmos = set()
        self.scaling_gizmos = set()

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.input.action_set is not None:
            for hand in Side:
                if self.input.hand_space[hand] is not None:
                    xr.destroy_space(self.input.hand_space[hand])
                    self.input.hand_space[hand] = None
            xr.destroy_action_set(self.input.action_set)
            self.input.action_set = None
        for swapchain in self.swapchains:
            xr.destroy_swapchain(swapchain.handle)
        self.swapchains[:] = []
        for visualized_space in self.visualized_spaces:
            xr.destroy_space(visualized_space)
        self.visualized_spaces[:] = []
        if self.app_space is not None:
            xr.destroy_space(self.app_space)
            self.app_space = None
        if self.session is not None:
            xr.destroy_session(self.session)
            self.session = None
        if self.instance is not None:
            self.instance.destroy()
            self.instance = None

    def set_Head(self, _Head: Entity):
        """
        Setter method for Head Entity
        Arguments:
            self: self
            _Head: Head Entity
        Returns:
            None
        """
        self.head = _Head
        self.graphics_plugin.set_Head(_Head)

    def set_translation_gizmos(self,x: str,y: str,z: str):
        """
        """
        self.translate_gizmos.add(x)
        self.translate_gizmos.add(y)
        self.translate_gizmos.add(z)
        self.graphics_plugin.set_translation_gizmos(x,y,z)

    def set_rotation_gizmos(self,x: str,y: str,z: str):
        """
        """
        self.rotation_gizmos.add(x)
        self.rotation_gizmos.add(y)
        self.rotation_gizmos.add(z)
        self.graphics_plugin.set_rotation_gizmos(x,y,z)

    def set_scaling_gizmos(self,x: str,y: str,z: str,line_X: str,line_y: str,line_z: str):
        """
        """
        self.scaling_gizmos.add(x)
        self.scaling_gizmos.add(y)
        self.scaling_gizmos.add(z)
        self.scaling_gizmos.add(line_X)
        self.scaling_gizmos.add(line_y)
        self.scaling_gizmos.add(line_z)
        self.graphics_plugin.set_scaling_gizmos(x,y,z,line_X,line_y,line_z)

    def set_gizmos_mode(self, _mode: str):
        self.gizmos_Mode = _mode
        self.graphics_plugin.set_gizmos_mode(_mode)

    def Initialize(self, name: str, renderer : InitGLShaderSystem):
        """
        All Initializations packed inside a single method
        Arguments:
            self: self
            name: Application name
            renderer: System that initializes Entities on the scene
        Returns:
            None
        """
        self.createInstance(name)
        self.InitializeSystem()
        self.InitializeDevice(renderer)
        self.InitializeSession()
        self.create_Swapchains()

    def create_Swapchains(self):        
        """
        Create a Swapchain which requires coordinating with the graphics plugin to select the format, getting the system graphics
        properties, getting the view configuration and grabbing the resulting swapchain images.
        Arguments:
            self: self
        Returns:
            None
        """
        
        assert self.session is not None
        assert len(self.swapchains) == 0
        assert len(self.config_views) == 0

        system_properties = xr.get_system_properties(self.instance.handle, self.system.id)

        print("System Properties: "
                    f"Name={system_properties.system_name.decode()} "
                    f"VendorId={system_properties.vendor_id}")
        print("System Graphics Properties: "
                    f"MaxWidth={system_properties.graphics_properties.max_swapchain_image_width} "
                    f"MaxHeight={system_properties.graphics_properties.max_swapchain_image_height} "
                    f"MaxLayers={system_properties.graphics_properties.max_layer_count}")
        print("System Tracking Properties: "
                    f"OrientationTracking={bool(system_properties.tracking_properties.orientation_tracking)} "
                    f"PositionTracking={bool(system_properties.tracking_properties.position_tracking)}")

        self.config_views = xr.enumerate_view_configuration_views(
            instance=self.instance.handle,
            system_id=self.system.id,
            view_configuration_type=self.options.parsed["view_config_type"],
        )
        # Create and cache view buffer for xrLocateViews later.
        view_count = len(self.config_views)
        assert view_count == 2 # 2 eyes
        self.views = (xr.View * view_count)(*([xr.View()] * view_count))
        # Create the swapchain and get the images.
        # Select a swapchain format.
        swapchain_formats = xr.enumerate_swapchain_formats(self.session)
        self.color_swapchain_format = self.graphics_plugin.select_color_swapchain_format(swapchain_formats)
            
        formats_string = ""
        for sc_format in swapchain_formats:
            selected = sc_format == self.color_swapchain_format
            formats_string += " "
            if selected:
                formats_string += "["
                formats_string += f"{str(self.color_swapchain_format)}({sc_format})"
                formats_string += "]"
            else:
                formats_string += str(sc_format)
        print(f"Swapchain Formats: {formats_string}")
        
        # Create a swapchain for each view.
        for i, vp in enumerate(self.config_views):
            print("Creating swapchain for "
                            f"view {i} with dimensions "
                            f"Width={vp.recommended_image_rect_width} "
                            f"Height={vp.recommended_image_rect_height} "
                            f"SampleCount={vp.recommended_swapchain_sample_count}")

            # Create the swapchain.
            swapchain_create_info = xr.SwapchainCreateInfo(
                array_size=1,
                format=self.color_swapchain_format,
                width=vp.recommended_image_rect_width,
                height=vp.recommended_image_rect_height,
                mip_count=1,
                face_count=1,
                sample_count=self.graphics_plugin.get_supported_swapchain_sample_count(vp),
                usage_flags=xr.SwapchainUsageFlags.SAMPLED_BIT | xr.SwapchainUsageFlags.COLOR_ATTACHMENT_BIT,
            )

            swapchain = Swapchain(
                xr.create_swapchain(
                    session=self.session,
                    create_info=swapchain_create_info,
                ),
                swapchain_create_info.width,
                swapchain_create_info.height,
            )

            self.swapchains.append(swapchain)
            swapchain_image_buffer = xr.enumerate_swapchain_images(
                swapchain=swapchain.handle,
                element_type=self.graphics_plugin.swapchain_image_type,
            )
            
            # Keep the buffer alive by moving it into the list of buffers.
            self.swapchain_image_buffers.append(swapchain_image_buffer)
            capacity = len(swapchain_image_buffer)
            swapchain_image_ptr_buffer = (POINTER(xr.SwapchainImageBaseHeader) * capacity)()
            for ix in range(capacity):
                swapchain_image_ptr_buffer[ix] = cast(
                    byref(swapchain_image_buffer[ix]),
                    POINTER(xr.SwapchainImageBaseHeader)
                )
            self.swapchain_image_ptr_buffers[hash(swapchain.handle)] = swapchain_image_ptr_buffer
    
    def createInstance(self, name: str):
        """
        create instance of the OpenXR program
        Arguments:
            self: self
            name: Application name
        Returns:
            None
        """
        self.log_layers_and_extensions()

        assert self.instance is None

        # Create union of extensions required by platform and graphics plugins.
        extensions = []
        # Enable debug messaging
        discovered_extensions = xr.enumerate_instance_extension_properties()
        dumci = xr.DebugUtilsMessengerCreateInfoEXT()
        next_structure = self.platform_plugin.instance_create_extension
        ALL_SEVERITIES = (
                xr.DEBUG_UTILS_MESSAGE_SEVERITY_VERBOSE_BIT_EXT
                | xr.DEBUG_UTILS_MESSAGE_SEVERITY_INFO_BIT_EXT
                | xr.DEBUG_UTILS_MESSAGE_SEVERITY_WARNING_BIT_EXT
                | xr.DEBUG_UTILS_MESSAGE_SEVERITY_ERROR_BIT_EXT
        )

        ALL_TYPES = (
                xr.DEBUG_UTILS_MESSAGE_TYPE_GENERAL_BIT_EXT
                | xr.DEBUG_UTILS_MESSAGE_TYPE_VALIDATION_BIT_EXT
                | xr.DEBUG_UTILS_MESSAGE_TYPE_PERFORMANCE_BIT_EXT
                | xr.DEBUG_UTILS_MESSAGE_TYPE_CONFORMANCE_BIT_EXT
        )
        if xr.EXT_DEBUG_UTILS_EXTENSION_NAME in discovered_extensions:
            extensions.append(xr.EXT_DEBUG_UTILS_EXTENSION_NAME)
            dumci.message_severities = ALL_SEVERITIES
            dumci.message_types = ALL_TYPES
            dumci.user_data = None
            dumci.user_callback = self.debug_callback
            if next_structure is None:
                next_structure = cast(pointer(dumci), c_void_p)
            else:
                next_structure.next = cast(pointer(dumci), c_void_p)
        #
        extensions.extend(self.platform_plugin.instance_extensions)
        extensions.extend(self.graphics_plugin.instance_extensions)

        self.instance = xr.InstanceObject(
            enabled_extensions=extensions,
            application_name=name,
            application_version=xr.Version(0, 0, 1),
            next=next_structure,
        )
        self.log_instance_info()

    def InitializeSystem(self):
        """
        Select a System for the view configuration specified in the Options and initialize the graphics device for the selected
        system.
        Arguments:
            self: self
        Returns:
            None
        """
        assert self.instance is not None
        assert self.system is None
        form_factor = options.get_xr_form_factor(self.options.form_factor)
        self.system = xr.SystemObject(instance=self.instance, form_factor=form_factor)
        print(f"Using system {hex(self.system.id.value)} for form factor {str(form_factor)}")
        assert self.instance.handle is not None
        assert self.system.id is not None

    def InitializeDevice(self,
                         renderer : InitGLShaderSystem):
        self.log_view_configurations()
        """
        The graphics Plugin uses the initialization system to initialize the required objects for the scene
        Arguments:
            self: self
            renderer: System that initializes Entities on the scene
        Returns:
            None
        """
        self.graphics_plugin.initialize_device(self.instance.handle,self.system.id,renderer)

    def InitializeSession(self):
        """
        Create a Session and other basic session-level initialization.
        Arguments:
            self: self
        Returns:
            None
        """
        assert self.instance is not None
        assert self.instance.handle != xr.NULL_HANDLE
        assert self.session is None

        print(f"Creating session...")

        graphics_binding_pointer = cast(
            pointer(self.graphics_plugin.graphics_binding),
            c_void_p)
        create_info = xr.SessionCreateInfo(
            next=graphics_binding_pointer,
            system_id=self.system.id,
        )
        self.session = xr.create_session(
            instance=self.instance.handle,
            create_info=create_info,
        )
        self.log_reference_spaces()

        self.initialize_actions()
        
        self.create_visualized_spaces()
        self.app_space = xr.create_reference_space(
            session=self.session,
            create_info=get_xr_reference_space_create_info(self.options.app_space),
        )

    def initialize_actions(self):
        """ 
        Create an action set for various controllers
        Arguments:
            self: self
        Returns:
            None
        """
        action_set_info = xr.ActionSetCreateInfo(
            action_set_name="gameplay",
            localized_action_set_name="Gameplay",
            priority=0,
        )
        self.input.action_set = xr.create_action_set(self.instance.handle, action_set_info)
        # Get the XrPath for the left and right hands - we will use them as subaction paths.
        self.input.hand_subaction_path[Side.LEFT] = xr.string_to_path(
            self.instance.handle,
            "/user/hand/left")
        self.input.hand_subaction_path[Side.RIGHT] = xr.string_to_path(
            self.instance.handle,
            "/user/hand/right")
        # Create actions
        # Create an input action for grabbing objects with the left and right hands.
        self.input.grab_action = xr.create_action(
            action_set=self.input.action_set,
            create_info=xr.ActionCreateInfo(
                action_type=xr.ActionType.FLOAT_INPUT,
                action_name="grab_object",
                localized_action_name="Grab Object",
                count_subaction_paths=len(self.input.hand_subaction_path),
                subaction_paths=self.input.hand_subaction_path,
            ),
        )
        # Create an input action getting the left and right hand poses.
        self.input.pose_action = xr.create_action(
            action_set=self.input.action_set,
            create_info=xr.ActionCreateInfo(
                action_type=xr.ActionType.POSE_INPUT,
                action_name="hand_pose",
                localized_action_name="Hand Pose",
                count_subaction_paths=len(self.input.hand_subaction_path),
                subaction_paths=self.input.hand_subaction_path,
            ),
        )
        # Create output actions for vibrating the left and right controller.
        self.input.vibrate_action = xr.create_action(
            action_set=self.input.action_set,
            create_info=xr.ActionCreateInfo(
                action_type=xr.ActionType.VIBRATION_OUTPUT,
                action_name="vibrate_hand",
                localized_action_name="Vibrate Hand",
                count_subaction_paths=len(self.input.hand_subaction_path),
                subaction_paths=self.input.hand_subaction_path,
            ),
        )
        # Create input actions for quitting the session using the left and right controller.
        # Since it doesn't matter which hand did this, we do not specify subaction paths for it.
        # We will just suggest bindings for both hands, where possible.
        self.input.quit_action = xr.create_action(
            action_set=self.input.action_set,
            create_info=xr.ActionCreateInfo(
                action_type=xr.ActionType.BOOLEAN_INPUT,
                action_name="quit_session",
                localized_action_name="Quit Session",
                count_subaction_paths=0,
                subaction_paths=None,
            ),
        )

        select_path = [
            xr.string_to_path(self.instance.handle, "/user/hand/left/input/select/click"),
            xr.string_to_path(self.instance.handle, "/user/hand/right/input/select/click")]
        squeeze_value_path = [
            xr.string_to_path(self.instance.handle, "/user/hand/left/input/squeeze/value"),
            xr.string_to_path(self.instance.handle, "/user/hand/right/input/squeeze/value")]
        squeeze_force_path = [
            xr.string_to_path(self.instance.handle, "/user/hand/left/input/squeeze/force"),
            xr.string_to_path(self.instance.handle, "/user/hand/right/input/squeeze/force")]
        squeeze_click_path = [
            xr.string_to_path(self.instance.handle, "/user/hand/left/input/squeeze/click"),
            xr.string_to_path(self.instance.handle, "/user/hand/right/input/squeeze/click")]
        pose_path = [
            xr.string_to_path(self.instance.handle, "/user/hand/left/input/grip/pose"),
            xr.string_to_path(self.instance.handle, "/user/hand/right/input/grip/pose")]
        haptic_path = [
            xr.string_to_path(self.instance.handle, "/user/hand/left/output/haptic"),
            xr.string_to_path(self.instance.handle, "/user/hand/right/output/haptic")]
        menu_click_path = [
            xr.string_to_path(self.instance.handle, "/user/hand/left/input/menu/click"),
            xr.string_to_path(self.instance.handle, "/user/hand/right/input/menu/click")]
        b_click_path = [
            xr.string_to_path(self.instance.handle, "/user/hand/left/input/b/click"),
            xr.string_to_path(self.instance.handle, "/user/hand/right/input/b/click")]
        trigger_value_path = [
            xr.string_to_path(self.instance.handle, "/user/hand/left/input/trigger/value"),
            xr.string_to_path(self.instance.handle, "/user/hand/right/input/trigger/value")]
        
        # Suggest bindings for KHR Simple.
        khr_bindings = [
            # Fall back to a click input for the grab action.
            xr.ActionSuggestedBinding(self.input.grab_action, select_path[Side.LEFT]),
            xr.ActionSuggestedBinding(self.input.grab_action, select_path[Side.RIGHT]),
            xr.ActionSuggestedBinding(self.input.pose_action, pose_path[Side.LEFT]),
            xr.ActionSuggestedBinding(self.input.pose_action, pose_path[Side.RIGHT]),
            xr.ActionSuggestedBinding(self.input.quit_action, menu_click_path[Side.LEFT]),
            xr.ActionSuggestedBinding(self.input.quit_action, menu_click_path[Side.RIGHT]),
            xr.ActionSuggestedBinding(self.input.vibrate_action, haptic_path[Side.LEFT]),
            xr.ActionSuggestedBinding(self.input.vibrate_action, haptic_path[Side.RIGHT]),
        ]

        xr.suggest_interaction_profile_bindings(
            instance=self.instance.handle,
            suggested_bindings=xr.InteractionProfileSuggestedBinding(
                interaction_profile=xr.string_to_path(
                    self.instance.handle,
                    "/interaction_profiles/khr/simple_controller",
                ),
                count_suggested_bindings=len(khr_bindings),
                suggested_bindings=(xr.ActionSuggestedBinding * len(khr_bindings))(*khr_bindings),
            ),
        )
        
        # Suggest bindings for the Vive Controller.
        vive_bindings = [
            xr.ActionSuggestedBinding(self.input.grab_action, trigger_value_path[Side.LEFT]),
            xr.ActionSuggestedBinding(self.input.grab_action, trigger_value_path[Side.RIGHT]),
            xr.ActionSuggestedBinding(self.input.pose_action, pose_path[Side.LEFT]),
            xr.ActionSuggestedBinding(self.input.pose_action, pose_path[Side.RIGHT]),
            xr.ActionSuggestedBinding(self.input.quit_action, menu_click_path[Side.LEFT]),
            xr.ActionSuggestedBinding(self.input.quit_action, menu_click_path[Side.RIGHT]),
            xr.ActionSuggestedBinding(self.input.vibrate_action, haptic_path[Side.LEFT]),
            xr.ActionSuggestedBinding(self.input.vibrate_action, haptic_path[Side.RIGHT]),
        ]

        xr.suggest_interaction_profile_bindings(
            instance=self.instance.handle,
            suggested_bindings=xr.InteractionProfileSuggestedBinding(
                interaction_profile=xr.string_to_path(
                    self.instance.handle,
                    "/interaction_profiles/htc/vive_controller",
                ),
                count_suggested_bindings=len(vive_bindings),
                suggested_bindings=(xr.ActionSuggestedBinding * len(vive_bindings))(*vive_bindings),
            ),
        )

        # Suggest bindings for the Valve Index Controller.
        index_bindings = [
            xr.ActionSuggestedBinding(self.input.grab_action, squeeze_force_path[Side.LEFT]),
            xr.ActionSuggestedBinding(self.input.grab_action, squeeze_force_path[Side.RIGHT]),
            xr.ActionSuggestedBinding(self.input.pose_action, pose_path[Side.LEFT]),
            xr.ActionSuggestedBinding(self.input.pose_action, pose_path[Side.RIGHT]),
            xr.ActionSuggestedBinding(self.input.quit_action, b_click_path[Side.LEFT]),
            xr.ActionSuggestedBinding(self.input.quit_action, b_click_path[Side.RIGHT]),
            xr.ActionSuggestedBinding(self.input.vibrate_action, haptic_path[Side.LEFT]),
            xr.ActionSuggestedBinding(self.input.vibrate_action, haptic_path[Side.RIGHT]),
        ]

        xr.suggest_interaction_profile_bindings(
            instance=self.instance.handle,
            suggested_bindings=xr.InteractionProfileSuggestedBinding(
                interaction_profile=xr.string_to_path(
                    self.instance.handle,
                    "/interaction_profiles/valve/index_controller",
                ),
                count_suggested_bindings=len(index_bindings),
                suggested_bindings=(xr.ActionSuggestedBinding * len(index_bindings))(*index_bindings),
            ),
        )

        # Suggest bindings for the Windows Mixed Reality Controller.
        wmr_bindings = [
            xr.ActionSuggestedBinding(self.input.grab_action, squeeze_click_path[Side.LEFT]),
            xr.ActionSuggestedBinding(self.input.grab_action, squeeze_click_path[Side.RIGHT]),
            xr.ActionSuggestedBinding(self.input.pose_action, pose_path[Side.LEFT]),
            xr.ActionSuggestedBinding(self.input.pose_action, pose_path[Side.RIGHT]),
            xr.ActionSuggestedBinding(self.input.quit_action, menu_click_path[Side.LEFT]),
            xr.ActionSuggestedBinding(self.input.quit_action, menu_click_path[Side.RIGHT]),
            xr.ActionSuggestedBinding(self.input.vibrate_action, haptic_path[Side.LEFT]),
            xr.ActionSuggestedBinding(self.input.vibrate_action, haptic_path[Side.RIGHT]),
        ]

        xr.suggest_interaction_profile_bindings(
            instance=self.instance.handle,
            suggested_bindings=xr.InteractionProfileSuggestedBinding(
                interaction_profile=xr.string_to_path(
                    self.instance.handle,
                    "/interaction_profiles/microsoft/motion_controller",
                ),
                count_suggested_bindings=len(wmr_bindings),
                suggested_bindings=(xr.ActionSuggestedBinding * len(wmr_bindings))(*wmr_bindings),
            ),
        )

        # Suggest bindings for the Oculus Touch.
        oculus_bindings = [
            xr.ActionSuggestedBinding(self.input.grab_action, squeeze_value_path[Side.LEFT]),
            xr.ActionSuggestedBinding(self.input.grab_action, squeeze_value_path[Side.RIGHT]),
            xr.ActionSuggestedBinding(self.input.pose_action, pose_path[Side.LEFT]),
            xr.ActionSuggestedBinding(self.input.pose_action, pose_path[Side.RIGHT]),
            xr.ActionSuggestedBinding(self.input.quit_action, menu_click_path[Side.LEFT]),
            xr.ActionSuggestedBinding(self.input.vibrate_action, haptic_path[Side.LEFT]),
            xr.ActionSuggestedBinding(self.input.vibrate_action, haptic_path[Side.RIGHT]),
        ]

        xr.suggest_interaction_profile_bindings(
            instance=self.instance.handle,
            suggested_bindings=xr.InteractionProfileSuggestedBinding(
                interaction_profile=xr.string_to_path(
                    self.instance.handle,
                    "/interaction_profiles/oculus/touch_controller",
                ),
                count_suggested_bindings=len(oculus_bindings),
                suggested_bindings=(xr.ActionSuggestedBinding * len(oculus_bindings))(*oculus_bindings),
            ),
        )

        action_space_info = xr.ActionSpaceCreateInfo(
            action=self.input.pose_action,
            # pose_in_action_space # w already defaults to 1 in python...
            subaction_path=self.input.hand_subaction_path[Side.LEFT],
        )
        assert action_space_info.pose_in_action_space.orientation.w == 1
        self.input.hand_space[Side.LEFT] = xr.create_action_space(
            session=self.session,
            create_info=action_space_info,
        )
        action_space_info.subaction_path = self.input.hand_subaction_path[Side.RIGHT]
        self.input.hand_space[Side.RIGHT] = xr.create_action_space(
            session=self.session,
            create_info=action_space_info,
        )

        #I need to add more action_space_info here, for the other actions too

        xr.attach_session_action_sets(
            session=self.session,
            attach_info=xr.SessionActionSetsAttachInfo(
                count_action_sets=1,
                action_sets=pointer(self.input.action_set),
            ),
        )

    def next_event(self)-> Optional[Structure]:
        """
        Check if there is any available xr event
        Arguments:
            self: self
        Returns:
            True if there is an available event, False otherwise
        """
        head = self.event_data_buffer
        head.type = xr.StructureType.EVENT_DATA_BUFFER
        result = xr.raw_functions.xrPollEvent(self.instance.handle, byref(self.event_data_buffer))

        if result == xr.Result.SUCCESS:
            return head
        if result == xr.Result.EVENT_UNAVAILABLE:
            return None
        result2 = xr.check_result(result)
        raise result2
    
    def poll_events(self):
        """
        If there is an available xr event, check what type of event it is
        Arguments:
            self: self
        Returns:
            True to stop rendering, False otherwise
        """
        exit_render_loop = False
        while True:
            event = self.next_event()
            if event is None:
                break
            event_type = event.type
            if event_type == xr.StructureType.EVENT_DATA_INSTANCE_LOSS_PENDING:
                return True
            elif event_type == xr.StructureType.EVENT_DATA_SESSION_STATE_CHANGED:
                exit_render_loop= self.handle_event(event, exit_render_loop)
            elif event_type == xr.StructureType.EVENT_DATA_INTERACTION_PROFILE_CHANGED:
                self.log_action_source_name(self.input.grab_action, "Grab")
                self.log_action_source_name(self.input.quit_action, "Quit")
                self.log_action_source_name(self.input.pose_action, "Pose")
                self.log_action_source_name(self.input.vibrate_action, "Vibrate")

        return exit_render_loop

    def handle_event(self,event,exit_loop):
        """
        Handles an event, when there is one
        Arguments:
            self: self
            event: a certain openxr type that refers to a session's contents
            exit_loop: When this becomes True exit rendering loop
        Returns:
            None
        """
        event = cast(byref(event), POINTER(xr.EventDataSessionStateChanged)).contents
        old_state = self.session_state
        self.session_state = xr.SessionState(event.state)
        key = cast(self.session, c_void_p).value

        if event.session is not None and hash(event.session) != hash(self.session):
            return exit_loop
        if self.session_state == xr.SessionState.READY:
            assert self.session is not None
            xr.begin_session(
                session=self.session,
                begin_info=xr.SessionBeginInfo(
                    primary_view_configuration_type=self.options.parsed["view_config_type"],
                ),
            )
            self.session_running = True
        elif self.session_state == xr.SessionState.STOPPING:

            assert self.session is not None
            self.session_running = False
            xr.end_session(self.session)
        elif self.session_state == xr.SessionState.EXITING:
            exit_loop = True
        elif self.session_state == xr.SessionState.LOSS_PENDING:
            exit_loop = True
        return exit_loop

    def poll_actions(self):
        """
        Update poses and all other available controller actions
        Arguments: 
            self: self
        Returns:
            None
        """

        #If an application does not have focus it cannot get input from the controllers
        if self.session_state == xr.SessionState.FOCUSED:

            self.input.hand_active[:] = [xr.FALSE, xr.FALSE]
            # Sync actions
            active_action_set = xr.ActiveActionSet(self.input.action_set, xr.NULL_PATH)
            xr.sync_actions(
                self.session,
                xr.ActionsSyncInfo(
                    count_active_action_sets=1,
                    active_action_sets=pointer(active_action_set)
                ),
            )
            # Get pose and grab action state and start haptic vibrate when hand is 90% squeezed.
            for hand in Side:
                grab_value = xr.get_action_state_float(
                    self.session,
                    xr.ActionStateGetInfo(
                        action=self.input.grab_action,
                        subaction_path=self.input.hand_subaction_path[hand],
                    ),
                )
                if grab_value.is_active:
                    # Scale the rendered hand by 1.0f (open) to 0.5f (fully squeezed).
                    self.input.hand_scale[hand] = 1 - 0.3 * grab_value.current_state
                    
                    #grab value equals 1.0 when trigger is fully pressed
                    self.grab_values[hand] = (grab_value.current_state==1.0)

                    #uncomment these if you want the controllers to vibrate when the triggers are pressed
                    """
                    if grab_value.current_state > 0.9:
                        vibration = xr.HapticVibration(
                            amplitude=0.1,
                            duration=xr.MIN_HAPTIC_DURATION,
                            frequency=xr.FREQUENCY_UNSPECIFIED,
                        )
                        xr.apply_haptic_feedback(
                            session=self.session,
                            haptic_action_info=xr.HapticActionInfo(
                                action=self.input.vibrate_action,
                                subaction_path=self.input.hand_subaction_path[hand],
                            ),
                            haptic_feedback=cast(byref(vibration), POINTER(xr.HapticBaseHeader)).contents,
                        )
                    """

                pose_state = xr.get_action_state_pose(
                    session=self.session,
                    get_info=xr.ActionStateGetInfo(
                        action=self.input.pose_action,
                        subaction_path=self.input.hand_subaction_path[hand],
                    ),
                )
                self.input.hand_active[hand] = pose_state.is_active
            # There are no subaction paths specified for quit action, because we don't care which hand did it.
            quit_value = xr.get_action_state_boolean(
                session=self.session,
                get_info=xr.ActionStateGetInfo(
                    action=self.input.quit_action,
                    subaction_path=xr.NULL_PATH,
                ),
            )
            if quit_value.is_active and quit_value.changed_since_last_sync and quit_value.current_state:
                xr.request_exit_session(self.session)

    def getRays(self):
        """
        Returns ray's starting point and Direction from both controllers, if raycast is true
        Arguments:
            self: self
        Returns:
            None
        """
        if self.raycast==False:
            raise("Raycast is not Enabled")

        #TBC
        left_ray_mesh = np.array(self.rays[0].getChildByType(RenderMesh.getClassName()).vertex_attributes[0],copy=True)
        right_ray_mesh = np.array(self.rays[1].getChildByType(RenderMesh.getClassName()).vertex_attributes[0],copy=True)

        left_ray_transform = self.hands[Side.LEFT].getChildByType(BasicTransform.getClassName()).l2world
        right_ray_transform = self.hands[Side.RIGHT].getChildByType(BasicTransform.getClassName()).l2world

        left_ray_mesh = left_ray_mesh @ left_ray_transform
        right_ray_mesh = right_ray_mesh @ right_ray_transform

        for i in range(len(left_ray_mesh)):
            left_ray_mesh[i] = left_ray_mesh[i]/left_ray_mesh[i][3]

        for i in range(len(right_ray_mesh)):
            right_ray_mesh[i] = right_ray_mesh[i]/right_ray_mesh[i][3]
        
        ray_start_left = util.vec(left_ray_mesh[0][0],left_ray_mesh[0][1],left_ray_mesh[0][2])
        ray_end_left = util.vec(left_ray_mesh[1][0],left_ray_mesh[1][1],left_ray_mesh[1][2])


        ray_start_right = util.vec(right_ray_mesh[0][0],right_ray_mesh[0][1],right_ray_mesh[0][2])
        ray_end_right = util.vec(right_ray_mesh[1][0],right_ray_mesh[1][1],right_ray_mesh[1][2])

        #Note: this array must get an extra position when used on the Gizmos. Same goes for ray origins
        ray_direction_left = util.normalise(util.vec(ray_end_left[0] - ray_start_left[0],
                                                    ray_end_left[1] - ray_start_left[1],
                                                    ray_end_left[2] - ray_start_left[2]))
        
        ray_direction_right = util.normalise(util.vec(ray_end_right[0] - ray_start_right[0],
                                                    ray_end_right[1] - ray_start_right[1],
                                                    ray_end_right[2] - ray_start_right[2]))
        
        rays = [RayDirection()] * 2

        rays[0].origin = ray_start_left
        rays[0].direction = ray_direction_left
        rays[1].origin = ray_start_right
        rays[1].direction = ray_direction_right

        return rays
            
    def render_frame(self,renderer: RenderGLShaderSystem) -> None:
        """
        Create and submit a frame.
        Arguments:
            self: self
            renderer: Rendering System that the graphics plugin uses to update uniform variables
        Returns:
            None
        """
        assert self.session is not None
        frame_state = xr.wait_frame(
            session=self.session,
            frame_wait_info=xr.FrameWaitInfo(),
        )
        xr.begin_frame(self.session, xr.FrameBeginInfo())

        layers = []
        layer_flags = 0
        if self.options.environment_blend_mode == "AlphaBlend":
            layer_flags = xr.COMPOSITION_LAYER_BLEND_TEXTURE_SOURCE_ALPHA_BIT \
                | xr.COMPOSITION_LAYER_UNPREMULTIPLIED_ALPHA_BIT
        layer = xr.CompositionLayerProjection(
            space=self.app_space,
            layer_flags=layer_flags,
        )
        projection_layer_views = (xr.CompositionLayerProjectionView * 2)(
            xr.CompositionLayerProjectionView(),
            xr.CompositionLayerProjectionView())
        if frame_state.should_render:
            if self.render_layer(frame_state.predicted_display_time, projection_layer_views, layer,renderer):
                layers.append(byref(layer))

        xr.end_frame(
            session=self.session,
            frame_end_info=xr.FrameEndInfo(
                display_time=frame_state.predicted_display_time,
                environment_blend_mode=self.options.parsed["environment_blend_mode"],
                layers=layers,
            ),
        )

    def render_layer(self,
                     predicted_display_time: xr.Time,
            projection_layer_views: Array,
            layer: xr.CompositionLayerProjection,
            renderer: RenderGLShaderSystem
            ) -> bool:
        """
        """
        view_capacity_input = len(self.views)
        view_state, self.views = xr.locate_views(
            session=self.session,
            view_locate_info=xr.ViewLocateInfo(
                view_configuration_type=self.options.parsed["view_config_type"],
                display_time=predicted_display_time,
                space=self.app_space,
            ),
        )
        view_count_output = len(self.views)
        vsf = view_state.view_state_flags
        if (vsf & xr.VIEW_STATE_POSITION_VALID_BIT == 0
                or vsf & xr.VIEW_STATE_ORIENTATION_VALID_BIT == 0):
            return False  # There are no valid tracking poses for the views.
        assert view_count_output == view_capacity_input
        assert view_count_output == len(self.config_views)
        assert view_count_output == len(self.swapchains)
        assert view_count_output == len(projection_layer_views)

        #Update hands before rendering
        for hand in Side:
            space_location = xr.locate_space(
                space=self.input.hand_space[hand],
                base_space=self.app_space,
                time=predicted_display_time,
            )
            loc_flags = space_location.location_flags

            #if true then the program has focus -> it can take input from the controllers
            if (loc_flags & xr.SPACE_LOCATION_POSITION_VALID_BIT != 0
                    and loc_flags & xr.SPACE_LOCATION_ORIENTATION_VALID_BIT != 0):
                scale = 0.1 * self.input.hand_scale[hand]
                position = space_location.pose.position
                orientation = space_location.pose.orientation

                between_hands = self.hand_dist
                if not hand: #Left hand goes a bit to the left, while the right hand goes a bit to the right.
                    between_hands = -between_hands
                model = util.translate(position.x+0.8+between_hands,
                                    position.y-0.5,
                                    position.z+2.0) @ util.inverse(create_xr_quaternion(util.quaternion(orientation.x,
                                                                                                        orientation.y,
                                                                                                        orientation.z,
                                                                                                        orientation.w))) @ util.scale(scale,scale,scale)
                self.hands[hand].getChildByType(BasicTransform.getClassName()).trs = model

        # Render view to the appropriate part of the swapchain image.
        for i in range(view_count_output):
            view_swapchain = self.swapchains[i]
            swapchain_image_index = xr.acquire_swapchain_image(
                swapchain=view_swapchain.handle,
                acquire_info=xr.SwapchainImageAcquireInfo(),
            )
            xr.wait_swapchain_image(
                swapchain=view_swapchain.handle,
                wait_info=xr.SwapchainImageWaitInfo(timeout=xr.INFINITE_DURATION),
            )
            view = projection_layer_views[i]

            assert view.type == xr.StructureType.COMPOSITION_LAYER_PROJECTION_VIEW
            view.pose = self.views[i].pose
            view.fov = self.views[i].fov
            view.sub_image.swapchain = view_swapchain.handle
            view.sub_image.image_rect.offset[:] = [0, 0]
            view.sub_image.image_rect.extent[:] = [view_swapchain.width, view_swapchain.height ]
            swapchain_image_ptr = self.swapchain_image_ptr_buffers[hash(view_swapchain.handle)][swapchain_image_index]
            self.graphics_plugin.Render_View(
                view,
                swapchain_image_ptr,
                self.color_swapchain_format,
                renderer,
                False #mirror=i==0 #mirror left eye only
            )
            xr.release_swapchain_image(
                swapchain=view_swapchain.handle,
                release_info=xr.SwapchainImageReleaseInfo()
            )
        #layer.view_count = len(projection_layer_views)
        layer.views = projection_layer_views
        return True
    
    def create_visualized_spaces(self):
        """
        Creates available Visualized Spaces
        Arguments:
            self: self
        Returns:
            None
        """
        assert self.session is not None
        visualized_spaces = [
            "ViewFront", "Local", "Stage", "StageLeft", "StageRight",
            "StageLeftRotated", "StageRightRotated",
        ]
        for visualized_space in visualized_spaces:
            try:
                space = xr.create_reference_space(
                    session=self.session,
                    create_info=get_xr_reference_space_create_info(visualized_space)
                )
                self.visualized_spaces.append(space)
            except xr.XrException as exc:
                print(f"Failed to create reference space {visualized_space} with error {exc}")
                #logger.warning(f"Failed to create reference space {visualized_space} with error {exc}")

    #Below are some logging methods for the program's configuration

    def log_action_source_name(self, action: xr.Action, action_name: str):
        paths = xr.enumerate_bound_sources_for_action(
            session=self.session,
            enumerate_info=xr.BoundSourcesForActionEnumerateInfo(
                action=action,
            ),
        )
        source_name = ""
        for path in paths:
            all_flags = xr.INPUT_SOURCE_LOCALIZED_NAME_USER_PATH_BIT \
                        | xr.INPUT_SOURCE_LOCALIZED_NAME_INTERACTION_PROFILE_BIT \
                        | xr.INPUT_SOURCE_LOCALIZED_NAME_COMPONENT_BIT
            grab_source = xr.get_input_source_localized_name(
                session=self.session,
                get_info=xr.InputSourceLocalizedNameGetInfo(
                    source_path=path,
                    which_components=all_flags,
                ),
            )
            if len(grab_source) < 1:
                continue
            if len(source_name) > 0:
                source_name += " and "
            source_name += f"'{grab_source}'"
        print(f"{action_name} is bound to {source_name if len(source_name) > 0 else 'nothing'}")

    def log_environment_blend_mode(self, view_config_type):
        assert self.instance.handle is not None
        assert self.system.id is not None
        blend_modes = xr.enumerate_environment_blend_modes(self.instance.handle, self.system.id, view_config_type)
        print(f"Available Environment Blend Mode count : ({len(blend_modes)})")
        blend_mode_found = False
        for mode_value in blend_modes:
            mode = xr.EnvironmentBlendMode(mode_value)
            blend_mode_match = mode == self.options.parsed["environment_blend_mode"]
            print(f"Environment Blend Mode ({str(mode)}) : "
                        f"{'(Selected)' if blend_mode_match else ''}")
            blend_mode_found |= blend_mode_match
        assert blend_mode_found

    def log_instance_info(self):
        assert self.instance is not None
        assert self.instance.handle is not None
        instance_properties = self.instance.get_properties()
        print(f"Instance RuntimeName={instance_properties.runtime_name.decode()} "
              f"RuntimeVersion={xr.Version(instance_properties.runtime_version)}")
        
    @staticmethod
    def _log_extensions(layer_name: str, indent: int = 0):
        """Write out extension properties for a given api_layer."""
        extension_properties = xr.enumerate_instance_extension_properties(layer_name)
        indent_str = " " * indent
        print(f"{indent_str}Available Extensions ({len(extension_properties)})")
        for extension in extension_properties:
            print(f"{indent_str}  Name={extension.extension_name.decode()} SpecVersion={extension.extension_version}")

    def log_layers_and_extensions(self):
        # Log non-api_layer extensions
        #self._log_extensions(layer_name=None)
        # Log layers and any of their extensions
        layers = xr.enumerate_api_layer_properties()
        print(f"Available Layers: ({len(layers)})")
        for layer in layers:
            print(
                f"Name={layer.layer_name.decode()} "
                f"SpecVersion={self.xr_version_string()} "
                f"LayerVersion={layer.layer_version} "
                f"Description={layer.description.decode()}")
            self._log_extensions(layer_name=layer.layer_name.decode(), indent=4)

    def log_reference_spaces(self):
        assert self.session is not None
        spaces = xr.enumerate_reference_spaces(self.session)
        print(f"Available reference spaces: {len(spaces)}")
        for space in spaces:
            print(f"  Name: {str(xr.ReferenceSpaceType(space))}")

    def log_view_configurations(self):
        assert self.instance.handle is not None
        assert self.system.id is not None
        view_config_types = xr.enumerate_view_configurations(self.instance.handle, self.system.id)
        print(f"Available View Configuration Types: ({len(view_config_types)})")
        for view_config_type_value in view_config_types:
            view_config_type = xr.ViewConfigurationType(view_config_type_value)
            print(
                f"  View Configuration Type: {str(view_config_type)} "
                f"{'(Selected)' if view_config_type == self.options.parsed['view_config_type'] else ''}")
            view_config_properties = xr.get_view_configuration_properties(
                instance=self.instance.handle,
                system_id=self.system.id,
                view_configuration_type=view_config_type,
            )
            print(f"  View configuration FovMutable={bool(view_config_properties.fov_mutable)}")
            configuration_views = xr.enumerate_view_configuration_views(self.instance.handle, self.system.id,
                                                                        view_config_type)
            if configuration_views is None or len(configuration_views) < 1:
                print(f"Empty view configuration type")
            else:
                for i, view in enumerate(configuration_views):
                    print(
                        f"    View [{i}]: Recommended Width={view.recommended_image_rect_width} "
                        f"Height={view.recommended_image_rect_height} "
                        f"SampleCount={view.recommended_swapchain_sample_count}")
                    print(
                        f"    View [{i}]:     Maximum Width={view.max_image_rect_width} "
                        f"Height={view.max_image_rect_height} "
                        f"SampleCount={view.max_swapchain_sample_count}")
            self.log_environment_blend_mode(view_config_type)
    
    def log_action_source_name(self, action: xr.Action, action_name: str):
        paths = xr.enumerate_bound_sources_for_action(
            session=self.session,
            enumerate_info=xr.BoundSourcesForActionEnumerateInfo(
                action=action,
            ),
        )
        source_name = ""
        for path in paths:
            all_flags = xr.INPUT_SOURCE_LOCALIZED_NAME_USER_PATH_BIT \
                        | xr.INPUT_SOURCE_LOCALIZED_NAME_INTERACTION_PROFILE_BIT \
                        | xr.INPUT_SOURCE_LOCALIZED_NAME_COMPONENT_BIT
            grab_source = xr.get_input_source_localized_name(
                session=self.session,
                get_info=xr.InputSourceLocalizedNameGetInfo(
                    source_path=path,
                    which_components=all_flags,
                ),
            )
            if len(grab_source) < 1:
                continue
            if len(source_name) > 0:
                source_name += " and "
            source_name += f"'{grab_source}'"
        print(f"{action_name} is bound to {source_name if len(source_name) > 0 else 'nothing'}")

    @staticmethod
    def xr_version_string():
        return xr.XR_CURRENT_API_VERSION

def hash(key):
    hex(cast(key, c_void_p).value)