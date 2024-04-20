import time 

import glm

import wgpu    
import numpy as np   
import glfw
import Elements.definitions as definitions

from Elements.pyGLV.GUI.Viewer import GLFWWindow, RenderDecorator
from Elements.pyGLV.GL.Shader import ShaderLoader  
from Elements.pyECSS.Event import EventManager
from Elements.pyGLV.GUI.windowEvents import EventTypes 
from Elements.pyGLV.GUI.Viewer import button_map
from Elements.pyGLV.GUI.fps_cammera import cammera
from Elements.pyGLV.GL.wgpu_meshes import  obj_loader
import Elements.pyECSS.math_utilities as util 
from Elements.definitions import TEXTURE_DIR, MODEL_DIR
from Elements.pyGLV.GL.Textures import WGPUTexture 
import Elements.utils.normals as norm
from Elements.utils.obj_to_mesh import obj_to_mesh
# Create a canvas to render to
#canvas = WgpuCanvas(title="wgpu cube") 
canvas = GLFWWindow(windowHeight=1440, windowWidth=2560, wgpu=True, windowTitle="Wgpu Example")
canvas.init()
canvas.init_post() 

width = canvas._windowWidth 
height = canvas._windowHeight

# Create a wgpu device
adapter = wgpu.gpu.request_adapter(power_preference="high-performance")
device = adapter.request_device()

# Prepare present context
present_context = canvas.get_context()
render_texture_format = present_context.get_preferred_format(device.adapter)
present_context.configure(device=device, format=render_texture_format)  

obj_to_import = MODEL_DIR / "ImplantsTable" / "ImplantsTable.obj"
vertices, uvs = obj_loader(obj_to_import)

    
vertex_data = np.array(vertices, dtype=np.float32)
uv_data = np.array(uvs, dtype=np.float32)

uniform_dtype = np.dtype([
    ("proj", np.float32, (4, 4)),
    ("view", np.float32, (4, 4)),
    ("model", np.float32, (4, 4)),
]) 
    
model = glm.mat4x4(1.0)
scale = util.scale(0.5, 0.5, 0.5)

model = scale @ model;

# eye = glm.vec3(2.5, 2.5, 2.5) 
# target = glm.vec3(0.0, 0.0, 0.0)
# up = glm.vec3(0.0, 1.0, 0.0)
pos = glm.vec3(-5, 0, 1)
cam = cammera(pos, 0, 0);
view = cam.view;

ratio = width / height 
near = 0.001
far = 1000.0 

proj = glm.transpose(glm.perspectiveLH(glm.radians(60), ratio, near, far))

uniform_data = np.array((
    np.array(proj),
    np.array(view),
    np.array(model),
), dtype=uniform_dtype)

uniform_buffer = device.create_buffer(
    size=uniform_data.nbytes, usage=wgpu.BufferUsage.UNIFORM | wgpu.BufferUsage.COPY_DST
)

vertex_buffer = device.create_buffer_with_data(
    data=vertex_data, usage=wgpu.BufferUsage.VERTEX
)

uvs_buffer = device.create_buffer_with_data(
    data=uv_data, usage=wgpu.BufferUsage.VERTEX
)

texturePath = MODEL_DIR / "ImplantsTable" / "table_with_implants_01_Material__3_Albedo.png"
texture = WGPUTexture(device=device, filepath=texturePath)

sampler = device.create_sampler()

# WGSL example
shader_code = ShaderLoader(definitions.SHADER_DIR / "SIGGRAPH" / "Textures" / "simple_texture2.wgsl");
shader = device.create_shader_module(code=shader_code);

# We always have two bind groups, so we can play distributing our
# resources over these two groups in different configurations.
bind_groups_entries = [[]]
bind_groups_layout_entries = [[]]

bind_groups_entries[0].append(
    {
        "binding": 0,
        "resource": {
            "buffer": uniform_buffer,
            "offset": 0,
            "size": uniform_buffer.size,
        },
    }
)
bind_groups_layout_entries[0].append(
    {
        "binding": 0,
        "visibility": wgpu.ShaderStage.VERTEX | wgpu.ShaderStage.FRAGMENT,
        "buffer": {"type": wgpu.BufferBindingType.uniform},
    }
) 

bind_groups_entries[0].append(
    {
        "binding": 1, 
        "resource": sampler
    }
)
bind_groups_layout_entries[0].append(
    {
        "binding": 1,
        "visibility": wgpu.ShaderStage.FRAGMENT,
        "sampler": {"type": wgpu.SamplerBindingType.filtering},
    }
)
bind_groups_entries[0].append(
    {
        "binding": 2,
        "resource": texture.view
    } 
) 
bind_groups_layout_entries[0].append(
    {
        "binding": 2,
        "visibility": wgpu.ShaderStage.FRAGMENT,
        "texture": {  
            "sample_type": wgpu.TextureSampleType.float,
            "view_dimension": wgpu.TextureViewDimension.d2,
        },
    }
)

# Create the wgou binding objects
bind_group_layouts = []
bind_groups = []

for entries, layout_entries in zip(bind_groups_entries, bind_groups_layout_entries):
    bind_group_layout = device.create_bind_group_layout(entries=layout_entries)
    bind_group_layouts.append(bind_group_layout)
    bind_groups.append(
        device.create_bind_group(layout=bind_group_layout, entries=entries)
    )

pipeline_layout = device.create_pipeline_layout(bind_group_layouts=bind_group_layouts)


# %% The render pipeline

render_pipeline = device.create_render_pipeline(
    layout=pipeline_layout,
    vertex={
        "module": shader,
        "entry_point": "vs_main", 
        "buffers": [
            {
                "array_stride": 3 * 4,
                "step_mode": wgpu.VertexStepMode.vertex,
                "attributes": [
                    {
                        "format": wgpu.VertexFormat.float32x3,
                        "offset": 0,
                        "shader_location": 0,
                    },
                ],
            },
            {
                "array_stride": 2 * 4,
                "step_mode": wgpu.VertexStepMode.vertex,
                "attributes": [
                    {
                        "format": wgpu.VertexFormat.float32x2,
                        "offset": 0,
                        "shader_location": 1,
                    },
                ],
            },
        ], 
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
                "format": render_texture_format,
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

def draw_frame(): 
    global cam
    global proj  
    global canvas
    
    ratio = canvas._windowWidth/canvas._windowHeight
    near = 0.001
    far = 1000.0 

    proj = glm.transpose(glm.perspectiveLH(glm.radians(60), ratio, near, far))   
    view = cam.view
    
    uniform_data = np.array((
    np.array(proj),
    np.array(view),
    np.array(model),
    ), dtype=uniform_dtype) 
    
    # Upload the uniform struct
    tmp_buffer = device.create_buffer_with_data(
        data=uniform_data, usage=wgpu.BufferUsage.COPY_SRC
    )

    command_encoder = device.create_command_encoder()
    command_encoder.copy_buffer_to_buffer(
        tmp_buffer, 0, uniform_buffer, 0, uniform_data.nbytes
    )
    
    texture = present_context.get_current_texture(); 
    textureWidth = texture.width; 
    textureHeight = texture.height; 
      
    depth_texture : wgpu.GPUTexture = device.create_texture(
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

    render_pass.set_pipeline(render_pipeline)
    render_pass.set_vertex_buffer(slot=0, buffer=vertex_buffer) 
    render_pass.set_vertex_buffer(slot=1, buffer=uvs_buffer)
    for bind_group_id, bind_group in enumerate(bind_groups):
        render_pass.set_bind_group(bind_group_id, bind_group, [], 0, 99)
    # render_pass.draw_indexed(index_data.size, 1, 0, 0, 0) 
    render_pass.draw(len(vertex_data), 1, 0, 1)
    render_pass.end()

    device.queue.submit([command_encoder.finish()])

    canvas.request_draw()


canvas.request_draw(draw_frame)

while canvas._running: 
    _ = canvas.event_input_process();   
    cam.update(canvas)
                
    if canvas._need_draw:
        canvas.display()
        canvas.display_post() 
        
canvas.shutdown()
# %%
