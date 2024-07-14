from __future__ import annotations
import wgpu 
import glm   
import numpy as np
from assertpy import assert_that

from Elements.pyECSS.wgpu_components import Component, RenderExclusiveComponent
from Elements.pyECSS.wgpu_entity import Entity
from Elements.pyGLV.GUI.wgpu_render_system import RenderSystem 
from Elements.pyGLV.GUI.wgpu_gpu_controller import GpuController
from Elements.pyGLV.GL.wgpu_texture import Texture, TextureLib 

SSAO_NOISE_SHADER = """ 
@group(0) @binding(0) var<storage, read> rotationBuffer : array<vec4<f32>>;
@group(0) @binding(1) var noiseTexture : texture_storage_2d<rgba16float, write>;

@compute @workgroup_size(1, 1, 1)
fn cs_main(@builtin(global_invocation_id) global_id : vec3<u32>) { 
    let index = global_id.x + global_id.y * 4;
    let rotation = rotationBuffer[index];
    textureStore(noiseTexture, vec2<i32>(global_id.xy), rotation);
}
"""

class SSAONoisePass(RenderSystem): 

    def on_create(self, entity: Entity, components: Component | list[Component]): 
        self.shader = GpuController().device.create_shader_module(code=SSAO_NOISE_SHADER);  

        self.storage: wgpu.GPUBuffer = GpuController().device.create_buffer(
            size=(4 * 4) * 16, usage=wgpu.BufferUsage.STORAGE | wgpu.BufferUsage.COPY_DST
        ) 
        
        bind_groups_layout_entries = [[]]   
        bind_groups_layout_entries[0].append(
            {
                "binding": 0,
                "visibility": wgpu.ShaderStage.COMPUTE,
                "buffer": {"type": wgpu.BufferBindingType.read_only_storage},
            }
        ) 
        bind_groups_layout_entries[0].append(
            {
                "binding": 1,
                "visibility": wgpu.ShaderStage.COMPUTE,
                "storage_texture": {"access": wgpu.StorageTextureAccess.write_only, "format": wgpu.TextureFormat.rgba16float},
            }
        ) 
        
        self.bind_group_layouts = [] 
        for layout_entries in bind_groups_layout_entries:
            bind_group_layout = GpuController().device.create_bind_group_layout(entries=layout_entries) 
            self.bind_group_layouts.append(bind_group_layout) 
            
        self.pipeline_layout = GpuController().device.create_pipeline_layout(bind_group_layouts=self.bind_group_layouts)

    def on_prepare(self, entity: Entity, components: Component | list[Component], command_encoder: wgpu.GPUCommandEncoder): 

        ssao_noise_rotations = [] 
        for i in range(1, 16):
            rotation = glm.vec4(
                np.random.random() * 2.0 - 1.0,
                np.random.random() * 2.0 - 1.0,
                0.0, 
                1.0 
            ) 
            ssao_noise_rotations.append(np.ascontiguousarray(rotation, dtype=np.float32))  

        ssao_noise_rotations_data = np.vstack(ssao_noise_rotations, dtype=np.float32)

        GpuController().device.queue.write_buffer(
            buffer=self.storage,
            buffer_offset=0,
            data=ssao_noise_rotations_data,
            data_offset=0,
            size=ssao_noise_rotations_data.nbytes
        )

        # We always have two bind groups, so we can play distributing our
        # resources over these two groups in different configurations.
        bind_groups_entries = [[]]
        bind_groups_entries[0].append(
            {
                "binding": 0,
                "resource": {
                    "buffer": self.storage,
                    "offset": 0,
                    "size": self.storage.size,
                },
            }
        )
        bind_groups_entries[0].append(
            {
                "binding": 1, 
                "resource": TextureLib().get_texture("ssao_noise_gfx").view
            }
        )

        # Create the wgou binding objects
        bind_groups = []

        for entries, layouts in zip(bind_groups_entries, self.bind_group_layouts):
            bind_groups.append(
                GpuController().device.create_bind_group(layout=layouts, entries=entries)
            ) 
        self.bind_groups = bind_groups 

        self.render_pipeline = GpuController().device.create_compute_pipeline(
            layout=self.pipeline_layout,
            compute={
                "module": self.shader,
                "entry_point": "cs_main"
            }
        )
    
    def on_render(self, entity: Entity, components: Component | list[Component], render_pass: wgpu.GPURenderPassEncoder | wgpu.GPUComputePassEncoder):   
        assert_that(
            (type(components) == RenderExclusiveComponent), 
            f"Only accepted entiy/component in blit stage is {RenderExclusiveComponent}"
        ).is_true()

        render_pass.set_pipeline(self.render_pipeline) 
        for bind_group_id, bind_group in enumerate(self.bind_groups):
            render_pass.set_bind_group(bind_group_id, bind_group, [], 0, 99)
        render_pass.dispatch_workgroups(4, 4, 1)


