import xr
import xr.raw_functions
from ctypes import Structure, c_int32, POINTER, byref, cast, c_void_p, pointer, Array
import logging
from typing import List, Optional, Dict
import math
from Elements.pyGLV.GL.Shader import InitGLShaderSystem, RenderGLShaderSystem
import sys

from Elements.features.XR.PlatformPlugin import createPlatformPlugin
from Elements.features.XR.GraphicsPlugin import OpenGLPlugin
from Elements.features.XR.options import options, Blend_Mode, View_Configuration, Form_factor

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

        self.acceptable_blend_modes = [
            xr.EnvironmentBlendMode.OPAQUE,
            xr.EnvironmentBlendMode.ADDITIVE,
            xr.EnvironmentBlendMode.ALPHA_BLEND,
        ]

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
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

    def Initialize(self, name: str, renderer : InitGLShaderSystem):
        """Pack all Initializations inside one method"""
        self.createInstance(name)
        self.InitializeSystem()
        self.InitializeDevice(renderer)
        self.InitializeSession()
        self.create_Swapchains()

    def create_Swapchains(self):        
        """
        Create a Swapchain which requires coordinating with the graphics plugin to select the format, getting the system graphics
        properties, getting the view configuration and grabbing the resulting swapchain images.
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
        "create an instance"
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
        "The graphics Plugin takes care of the initialization here"
        self.graphics_plugin.initialize_device(self.instance.handle,self.system.id,renderer)

    def InitializeSession(self):
        """Create a Session and other basic session-level initialization."""
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

        #TODO initialize actions for hands like grab
        #self.initialize_actions()
        
        self.create_visualized_spaces()
        self.app_space = xr.create_reference_space(
            session=self.session,
            create_info=get_xr_reference_space_create_info(self.options.app_space),
        )

    def initialize_actions(self):
        # Create an action set.
        pass

    def next_event(self)-> Optional[Structure]:
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

        return exit_render_loop

    def handle_event(self,event,exit_loop):
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

    def render_frame(self,renderer: RenderGLShaderSystem) -> None:
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
        layer.view_count = len(projection_layer_views)
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
                print(f"Failed to create reference space {visualized_space} with error {exc}")
                #logger.warning(f"Failed to create reference space {visualized_space} with error {exc}")

    #Below are some logging methods for the program's configuration

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
        pass

    @staticmethod
    def xr_version_string():
        return xr.XR_CURRENT_API_VERSION

def hash(key):
    hex(cast(key, c_void_p).value)