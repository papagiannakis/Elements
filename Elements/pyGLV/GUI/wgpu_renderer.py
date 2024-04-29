import wgpu
import glm
import numpy as np

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
        self._view = self._scene._cammera.view;

        ratio = self._canvas._windowWidth  / self._canvas._windowHeight
        near = 0.001
        far = 1000.0 
        self._proj = glm.transpose(glm.perspectiveLH(glm.radians(60), ratio, near, far)) 
        
        for obj in self._scene._objects: 
            obj.attachedMaterial.shader.setProj(data=self._proj)
            obj.attachedMaterial.shader.setView(data=self._view) 
            obj.attachedMaterial.shader.setModel(data=np.asarray(obj.transforms, dtype=np.float32))

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

        objects_drawn = 0
        for obj in self._scene._objects:  

            for key, uniformGroup in obj.attachedMaterial.uniformGroups.items():
                    uniformGroup.makeBindGroup(device=self._device) 

            obj.attachedMaterial.shader.update(command_encoder=command_encoder)   
            render_pipeline = obj.attachedMaterial.makePipeline(device=self._device, renderTextureFormat=self._render_texture_format) 

            render_pass.set_pipeline(render_pipeline)  
            render_pass.set_index_buffer(obj.mesh.bufferMap["indices"], wgpu.IndexFormat.uint32)
            render_pass.set_vertex_buffer(slot=0, buffer=obj.mesh.bufferMap["vertices"]) 
            render_pass.set_vertex_buffer(slot=1, buffer=obj.mesh.bufferMap["uvs"]) 
            render_pass.set_bind_group(0, obj.attachedMaterial.uniformGroups["frameGroup"].bindGroup, [], 0, 99) 
            render_pass.set_bind_group(1, obj.attachedMaterial.uniformGroups["materialGroup"].bindGroup, [], 0, 99)
            render_pass.draw_indexed(obj.mesh.numIndices, obj.instance_count, 0, 0, 0)   

        render_pass.end()
        self._device.queue.submit([command_encoder.finish()]) 

