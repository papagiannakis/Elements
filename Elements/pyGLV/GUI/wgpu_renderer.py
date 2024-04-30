import wgpu
import glm
import numpy as np

from Elements.pyGLV.GL.wgpu_meshes import Buffers

class SimpleRenderer:
    def __init__(self, scene, canvas, device, present_context, render_texture_format): 
        self._scene = scene
        self._canvas = canvas
        self._device = device
        self._present_context = present_context
        self._render_texture_format = render_texture_format 

    def init(self):
        self._scene.init(device=self._device)

    def render(self):
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

        command_encoder = self._device.create_command_encoder()  
        for obj in self._scene._objects:
            obj.attachedMaterial.shader.update(command_encoder)

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

        for obj in self._scene._objects:  

            for uniformGroup in obj.attachedMaterial.uniformGroups.values():
                    uniformGroup.makeBindGroup(device=self._device) 

            obj.attachedMaterial.shader.update(command_encoder=command_encoder)   
            render_pipeline = obj.attachedMaterial.makePipeline(device=self._device, renderTextureFormat=self._render_texture_format) 

            render_pass.set_pipeline(render_pipeline)   

            if obj.mesh.hasIndices:
                render_pass.set_index_buffer(obj.mesh.bufferMap[Buffers.INDEX], wgpu.IndexFormat.uint32)  

                for attribute in obj.attachedMaterial.shader.attributes.values():
                    render_pass.set_vertex_buffer(slot=attribute.slot, buffer=obj.mesh.bufferMap[attribute.name])  

                for group in obj.attachedMaterial.uniformGroups.values(): 
                    render_pass.set_bind_group(group.groupIndex, group.bindGroup, [], 0, 99)  

                render_pass.draw_indexed(obj.mesh.numIndices, obj.instance_count, 0, 0, 0)  
                  
            else:
                for attribute in obj.attachedMaterial.shader.attributes.values():
                    render_pass.set_vertex_buffer(slot=attribute.slot, buffer=obj.mesh.bufferMap[attribute.name])  

                for group in obj.attachedMaterial.uniformGroups.values(): 
                    render_pass.set_bind_group(group.groupIndex, group.bindGroup, [], 0, 99)  

                render_pass.draw(obj.mesh.numVertices, obj.instance_count, 0, 0)    

        render_pass.end()
        self._device.queue.submit([command_encoder.finish()]) 

