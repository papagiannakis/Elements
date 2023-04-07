import xr
from ctypes import Structure, c_int32, POINTER, byref, cast, c_void_p, pointer, Array
import logging
from typing import List, Optional, Dict
import Elements.pyECSS.utilities as util
import math
import Elements.pyGLV.GL.Scene as Scene
import Elements.pyECSS.System as System
import Elements.pyECSS.Entity as Entity
from OpenGL import GL

import Elements.pyGLV.XR.PlatformPlugin as PlatformPlugin
from Elements.pyGLV.XR.PlatformPlugin import createPlatformPlugin
from Elements.pyGLV.XR.GraphicsPlugin import GraphicsPlugin, OpenGLPlugin

logger = logging.getLogger("XRprogram.OpenGLPlugin")

class Swapchain(Structure):
    _fields_ = [
        ("handle", xr.Swapchain),
        ("width", c_int32),
        ("height", c_int32),
    ]

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

class options:
    def __init__(self,graphics_plugin="OpenGL",form_factor="Hmd",View_config="Stereo",blend_mode="Opaque",space="Local"):
        "Initialize default options"
        self.graphics_plugin = graphics_plugin
        self.form_factor = form_factor
        self.view_configuration = View_config
        self.environment_blend_mode = blend_mode
        self.app_space = space
        self.parsed = {
            "form_factor": xr.FormFactor.HEAD_MOUNTED_DISPLAY,
            "view_config_type": xr.ViewConfigurationType.PRIMARY_STEREO,
            "environment_blend_mode": xr.EnvironmentBlendMode.OPAQUE,
        }

    @staticmethod
    def get_xr_environment_blend_mode(environment_blend_mode_string: str) -> xr.EnvironmentBlendMode:
        return {
            "Opaque": xr.EnvironmentBlendMode.OPAQUE,
            "Additive": xr.EnvironmentBlendMode.ADDITIVE,
            "AlphaBlend": xr.EnvironmentBlendMode.ALPHA_BLEND,
        }[environment_blend_mode_string]

    @staticmethod
    def get_xr_environment_blend_mode_string(environment_blend_mode: xr.EnvironmentBlendMode) -> str:
        return {
            xr.EnvironmentBlendMode.OPAQUE: "Opaque",
            xr.EnvironmentBlendMode.ADDITIVE: "Additive",
            xr.EnvironmentBlendMode.ALPHA_BLEND: "AlphaBlend",
        }[environment_blend_mode]

    @staticmethod
    def get_xr_form_factor(form_factor_string: str) -> xr.FormFactor:
        if form_factor_string == "Hmd":
            return xr.FormFactor.HEAD_MOUNTED_DISPLAY
        elif form_factor_string == "Handheld":
            return xr.FormFactor.HANDHELD_DISPLAY
        raise ValueError(f"Unknown form factor '{form_factor_string}'")

    @staticmethod
    def get_xr_view_configuration_type(view_configuration_string: str) -> xr.ViewConfigurationType:
        if view_configuration_string == "Mono":
            return xr.ViewConfigurationType.PRIMARY_MONO
        elif view_configuration_string == "Stereo":
            return xr.ViewConfigurationType.PRIMARY_STEREO
        raise ValueError(f"Unknown view configuration '{view_configuration_string}'")
    
    def set_environment_blend_mode(self, environment_blend_mode: xr.EnvironmentBlendMode) -> None:
        self.environment_blend_mode = self.get_xr_environment_blend_mode_string(environment_blend_mode)
        self.parsed["environment_blend_mode"] = environment_blend_mode

class ElementsXR_program:

    def __init__(self):
        "An openXR program in Elements"
        self.options = options()
        self.platform_plugin = createPlatformPlugin()
        self.graphics_plugin = OpenGLPlugin()
        self.debug_callback = xr.PFN_xrDebugUtilsMessengerCallbackEXT(xr_debug_callback)

        self.instance = None
        self.session = None
        self.app_space = None
        self.form_factor = xr.FormFactor.HEAD_MOUNTED_DISPLAY
        self.system = None  # Higher level System class, not just ID

        self.config_views = []
        self.swapchains = []
        self.swapchain_image_buffers = []  # to keep objects alive
        self.swapchain_image_ptr_buffers = {}  # m_swapchainImages
        self.views = (xr.View * 2)(xr.View(), xr.View())
        self.color_swapchain_format = -1

        self.visualized_spaces = []

        # Application's current lifecycle state according to the runtime
        self.session_state = xr.SessionState.UNKNOWN
        self.session_running = True #TODO this should initially be false and to be updated with another method

        self.event_data_buffer = xr.EventDataBuffer()

        self.acceptable_blend_modes = [
            xr.EnvironmentBlendMode.OPAQUE,
            xr.EnvironmentBlendMode.ADDITIVE,
            xr.EnvironmentBlendMode.ALPHA_BLEND,
        ]

    def create_Swapchains(self):        
        # Query and cache view configuration views.
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
            
        # Create a swapchain for each view.
        for i, vp in enumerate(self.config_views):
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
        "create an XR instance of this program"
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
            application_name="XRprogram",
            application_version=xr.Version(0, 0, 1),
            next=next_structure,
        )

    def InitializeSystem(self):
        """
        Select a System for the view configuration specified in the Options and initialize the graphics device for the selected
        system.
        """
        assert self.instance is not None
        assert self.system is None
        form_factor = options.get_xr_form_factor(self.options.form_factor)
        self.system = xr.SystemObject(instance=self.instance, form_factor=form_factor)
        assert self.instance.handle is not None
        assert self.system.id is not None

    def InitializeDevice(self):
        "The graphics Plugin takes care of the initialization here"
        self.graphics_plugin.initialize_device(self.instance.handle,self.system.id)

    def InitializeSession(self):
        assert self.instance is not None
        assert self.instance.handle != xr.NULL_HANDLE
        assert self.session is None
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
        #TODO initialize actions for hands like grab
        self.create_visualized_spaces()
        self.app_space = xr.create_reference_space(
            session=self.session,
            create_info=get_xr_reference_space_create_info(self.options.app_space),
        )

    def render_frame(self,renderer: System, scene: Scene) -> None:
        """Create and submit a frame."""
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
            if self.render_layer(frame_state.predicted_display_time, projection_layer_views, layer,renderer,scene):
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
            renderer: System,
            scene: Scene
            ) -> bool:
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

        #TODO: add code for rendering the hands here      
        
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
            view.sub_image.image_rect.extent[:] = [view_swapchain.width, view_swapchain.height, ]
            swapchain_image_ptr = self.swapchain_image_ptr_buffers[hash(view_swapchain.handle)][swapchain_image_index]
            self.graphics_plugin.render_view(
                view,
                swapchain_image_ptr,
                self.color_swapchain_format,
                scene,
                renderer
                # mirror=False,
            )
            xr.release_swapchain_image(
                swapchain=view_swapchain.handle,
                release_info=xr.SwapchainImageReleaseInfo()
            )
        layer.views = projection_layer_views
        return True
    
    def create_visualized_spaces(self):
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
                logger.warning(f"Failed to create reference space {visualized_space} with error {exc}")

def hash(key):
    hex(cast(key, c_void_p).value)