import wgpu
import glm
import numpy as np
from Elements.pyGLV.GL.wpgu_scene import Scene, DEFAULT_OBJ_BUFFER_DISC
from Elements.pyGLV.GL.wgpu_shader import BasicShader


class SimpleRenderer:
    def __init__(self, scene, canvas, device, present_context, render_texture_format): 
        self._scene = scene
        self._canvas = canvas
        self._device = device
        self._present_context = present_context
        self._render_texture_format = render_texture_format 
        self._shader = BasicShader(device)

        self._uniformData = None
        self._objectData = None

        self._view = None
        self._proj = None


    def init(self):
        self._shader.init()
        self._scene.init(device=self._device, materialBindGroupLayout=self._shader._materialGourpLayout)

        self._view = self._scene._cammera.view;

        ratio = self._canvas._windowWidth  / self._canvas._windowHeight
        near = 0.001
        far = 1000.0 
        self._proj = glm.transpose(glm.perspectiveLH(glm.radians(60), ratio, near, far))

        self._uniformData = np.array((
            np.array(self._proj),
            np.array(self._view),
        ), dtype=self._shader._uniformDiscriptor)


    def render(self):
        self._view = self._scene._cammera.view;

        ratio = self._canvas._windowWidth  / self._canvas._windowHeight
        near = 0.001
        far = 1000.0 
        self._proj = glm.transpose(glm.perspectiveLH(glm.radians(60), ratio, near, far))

        self._uniformData = np.array((
            np.array(self._proj),
            np.array(self._view),
        ), dtype=self._shader._uniformDiscriptor)

        objectData = []
        for obj in self._scene._objects:   
            for trs in obj.transforms: 
                trs = np.array( 
                    trs, 
                    dtype=np.float32
                )
                objectData.append(trs)     
                
        self._objectData = np.asarray(objectData) 

        temp_uniform = self._device.create_buffer_with_data(
            data=self._uniformData, usage=wgpu.BufferUsage.COPY_SRC
        ) 
        temp_obj = self._device.create_buffer_with_data(
            data=self._objectData, usage=wgpu.BufferUsage.COPY_SRC
        )

        command_encoder = self._device.create_command_encoder() 
        command_encoder.copy_buffer_to_buffer(
            temp_uniform, 0, self._shader._uniformBuffer, 0, self._uniformData.nbytes
        ) 
        command_encoder.copy_buffer_to_buffer(
            temp_obj, 0, self._shader._objectBuffer, 0, self._objectData.nbytes
        ) 
        texture = self._present_context.get_current_texture(); 
        textureWidth = texture.width; 
        textureHeight = texture.height; 
        
        depth_texture : wgpu.GPUTexture = self._device.create_texture(
                label="depth_texture",
                size=[textureWidth, textureHeight, 1],
                mip_level_count=1,
                sample_count=1,
                dimension="2d",
                format=wgpu.TextureFormat.depth24plus,
                usage=wgpu.TextureUsage.RENDER_ATTACHMENT
            )

        depth_texture_view : wgpu.GPUTextureView = depth_texture.create_view(
            label="depth_texture_view",
            format=wgpu.TextureFormat.depth24plus,
            dimension="2d",
            aspect=wgpu.TextureAspect.depth_only,
            base_mip_level=0,
            mip_level_count=1,
            base_array_layer=0,
            array_layer_count=1,
        )

        current_texture_view = texture.create_view()
        render_pass = command_encoder.begin_render_pass( 
            color_attachments=[
                {
                    "view": current_texture_view,
                    "resolve_target": None,
                    "clear_value": (0.1, 0.1, 0.1, 0),
                    "load_op": wgpu.LoadOp.clear,
                    "store_op": wgpu.StoreOp.store,
                }
            ],
            depth_stencil_attachment={
                    "view": depth_texture_view,
                    "depth_clear_value": 1.0,
                    "depth_load_op": wgpu.LoadOp.clear,
                    "depth_store_op": wgpu.StoreOp.store,
                    "depth_read_only": False,
                    "stencil_clear_value": 0,
                    "stencil_load_op": wgpu.LoadOp.clear,
                    "stencil_store_op": wgpu.StoreOp.store,
                    "stencil_read_only": True,
                },
        )

        objects_drawn = 0;  
        render_pipeline = self.make_render_pipeline(
            shader=self._shader._shaderContext, 
            groupLayouts=[self._shader._frameGroupLayout, self._shader._materialGourpLayout], 
            bufferDiscripor=DEFAULT_OBJ_BUFFER_DISC
        ) 

        for obj in self._scene._objects:
            render_pass.set_pipeline(render_pipeline)  
            render_pass.set_vertex_buffer(slot=0, buffer=obj.vertex_buffer) 
            render_pass.set_vertex_buffer(slot=1, buffer=obj.uvs_buffer) 
            render_pass.set_bind_group(0, self._shader._frameBindingGroup, [], 0, 99) 
            render_pass.set_bind_group(1, obj.material.bindGroup, [], 0, 99)
            render_pass.draw(len(obj.vertices), obj.instance_count, 0, objects_drawn) 
        
            objects_drawn += obj.instance_count

        render_pass.end()
        self._device.queue.submit([command_encoder.finish()]) 

        self._canvas.request_draw()


    def make_render_pipeline(self, shader, groupLayouts, bufferDiscripor):
        pipeline_layout = self._device.create_pipeline_layout(bind_group_layouts=groupLayouts)
        return self._device.create_render_pipeline(
        layout=pipeline_layout,
        vertex={
            "module": shader,
            "entry_point": "vs_main", 
            "buffers": bufferDiscripor,
        },
        primitive={
            "topology": wgpu.PrimitiveTopology.triangle_list,
            "front_face": wgpu.FrontFace.ccw,
            "cull_mode": wgpu.CullMode.none,
        },
        depth_stencil={
                "format": wgpu.TextureFormat.depth24plus,
                "depth_write_enabled": True,
                "depth_compare": wgpu.CompareFunction.less,
                "stencil_front": {
                    "compare": wgpu.CompareFunction.always,
                    "fail_op": wgpu.StencilOperation.keep,
                    "depth_fail_op": wgpu.StencilOperation.keep,
                    "pass_op": wgpu.StencilOperation.keep,
                },
                "stencil_back": {
                    "compare": wgpu.CompareFunction.always,
                    "fail_op": wgpu.StencilOperation.keep,
                    "depth_fail_op": wgpu.StencilOperation.keep,
                    "pass_op": wgpu.StencilOperation.keep,
                },
                "stencil_read_mask": 0,
                "stencil_write_mask": 0,
                "depth_bias": 0,
                "depth_bias_slope_scale": 0.0,
                "depth_bias_clamp": 0.0,
            },
        multisample=None,
        fragment={
            "module": shader,
            "entry_point": "fs_main",
            "targets": [
                {
                    "format": self._render_texture_format,
                    "blend": {
                        "alpha": (
                            wgpu.BlendFactor.one,
                            wgpu.BlendFactor.zero,
                            wgpu.BlendOperation.add,
                        ),
                        "color": (
                            wgpu.BlendFactor.one,
                            wgpu.BlendFactor.zero,
                            wgpu.BlendOperation.add,
                        ),
                    },
                }
            ],
        },
    )
