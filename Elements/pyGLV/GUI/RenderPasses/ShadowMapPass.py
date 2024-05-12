import wgpu
import glm
import numpy as np

from Elements.pyGLV.GL.Shader.wgpu_ShadowPrepass import ShadowPrepassShader
from Elements.pyGLV.GL.wgpu_material import Material  
from Elements.pyGLV.GL.wgpu_texture import Texture
from Elements.pyGLV.GL.wgpu_meshes import Buffers  

DEPTH_TEXTURE_SIZE = 2048 

class ShadowMapPass:
    def __init__(self, renderer):  
        self._renderer = renderer; 

    def onInit(self, command_encoder):
        self._shadow_prepass_mat = Material(
            tag="Shadow Prepass", 
            shader=ShadowPrepassShader(self._renderer._device)
        )

    def render(self, command_encoder):  
        texture = self._renderer._canvasContext
        texture_format = self._renderer._canvasContextFormat
        textureWidth = texture.width; 
        textureHeight = texture.height;

        self.colorBlend = [ 
            {   
                "format": texture_format,
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
                } 
            }
        ] 

        self.primitive = { 
            "topology": wgpu.PrimitiveTopology.triangle_list,
            "front_face": wgpu.FrontFace.ccw,
            "cull_mode": wgpu.CullMode.front,
        } 

        self.depth_stencil = {
            "format": wgpu.TextureFormat.depth32float,
            "depth_write_enabled": True,
            "depth_compare": wgpu.CompareFunction.less,
        }
        
        depth_texture : wgpu.GPUTexture = self._renderer._device.create_texture(
                label="depth_texture",
                size=[DEPTH_TEXTURE_SIZE, DEPTH_TEXTURE_SIZE, 1],
                mip_level_count=1,
                sample_count=1,
                dimension="2d",
                format=wgpu.TextureFormat.depth32float,
                usage=wgpu.TextureUsage.RENDER_ATTACHMENT | wgpu.TextureUsage.TEXTURE_BINDING
            ) 
        
        gfxTexture : wgpu.GPUTexture = self._renderer._device.create_texture( 
                label="gfx_texture",
                size=[DEPTH_TEXTURE_SIZE, DEPTH_TEXTURE_SIZE, 1],
                mip_level_count=1,
                sample_count=1,
                dimension="2d",
                format=texture_format,
                usage=wgpu.TextureUsage.RENDER_ATTACHMENT | wgpu.TextureUsage.TEXTURE_BINDING
        )

        depth_texture_view : wgpu.GPUTextureView = depth_texture.create_view(
            label="depth_texture_view",
            format=wgpu.TextureFormat.depth32float,
            dimension="2d",
            aspect=wgpu.TextureAspect.depth_only,
            base_mip_level=0,
            mip_level_count=1,
            base_array_layer=0,
            array_layer_count=1,
        ) 

        gfxTexture_view : wgpu.GPUTextureView = gfxTexture.create_view()

        self._renderer._shadowMapDepthTexture = depth_texture
        self._renderer._shadowMapDepthTextureView = depth_texture_view 

        # command_encoder = self._renderer._device.create_command_encoder()  

        current_texture_view = texture.create_view()
        render_pass = command_encoder.begin_render_pass( 
            color_attachments=[
                {
                    "view": gfxTexture_view,
                    "resolve_target": None,
                    "clear_value": (0.0, 0.0, 0.0, 1.0),
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

        for uniformGroup in self._shadow_prepass_mat.uniformGroups.values():
            uniformGroup.makeBindGroup(device=self._renderer._device)  

        render_pipeline = self._shadow_prepass_mat.makePipeline(device=self._renderer._device, renderPass=self) 

        for obj in self._renderer._scene._objects:   
            self._shadow_prepass_mat.shader.Models = obj.attachedMaterial.shader.Models
            self._shadow_prepass_mat.shader.update(command_encoder=command_encoder) 

            render_pass.set_pipeline(render_pipeline)   
            if obj.mesh.hasIndices:
                render_pass.set_index_buffer(obj.mesh.bufferMap[Buffers.INDEX], wgpu.IndexFormat.uint32)  

                for attribute in self._shadow_prepass_mat.shader.attributes.values():
                    render_pass.set_vertex_buffer(slot=attribute.slot, buffer=obj.mesh.bufferMap[attribute.name])  

                for group in self._shadow_prepass_mat.uniformGroups.values():
                    render_pass.set_bind_group(group.groupIndex, group.bindGroup, [], 0, 99)  

                render_pass.draw_indexed(obj.mesh.numIndices, obj.instance_count, 0, 0, 0)  
                  
            else:
                for attribute in self._shadow_prepass_mat.shader.attributes.values():
                    render_pass.set_vertex_buffer(slot=attribute.slot, buffer=obj.mesh.bufferMap[attribute.name])  

                for group in self._shadow_prepass_mat.uniformGroups.values():
                    render_pass.set_bind_group(group.groupIndex, group.bindGroup, [], 0, 99)  

                render_pass.draw(obj.mesh.numVertices, obj.instance_count, 0, 0)    

        render_pass.end()
        # self._renderer._device.queue.submit([command_encoder.finish()]) 

