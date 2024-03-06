import time 

import wgpu  
import numpy as np

from Elements.pyGLV.GUI.Viewer import GLFWWindow
import Elements.pyECSS.math_utilities as util 

"""
This example renders a simple textured rotating cube.
"""

# test_example = true


# Create a canvas to render to
#canvas = WgpuCanvas(title="wgpu cube") 
canvas = GLFWWindow(windowHeight=800, windowWidth=1200, wgpu=True, windowTitle="Wgpu Example"); 
canvas.init()
canvas.init_post()

# Create a wgpu device
adapter = wgpu.gpu.request_adapter(power_preference="high-performance")
device = adapter.request_device()

# Prepare present context
present_context = canvas.get_context()
render_texture_format = present_context.get_preferred_format(device.adapter)
present_context.configure(device=device, format=render_texture_format)

#Simple Cube
vertexCube = np.array([
    [-1, -1, 1, 1.0],
    [-1, 1, 1, 1.0],
    [1, 1, 1, 1.0],
    [1, -1, 1, 1.0], 
    [-1, -1, -1, 1.0], 
    [-1, 1, -1, 1.0], 
    [1, 1, -1, 1.0], 
    [1, -1, -1, 1.0]
],dtype=np.float32) 
colorCube = np.array([
    [0.0, 0.0, 0.0, 1.0],
    [1.0, 0.0, 0.0, 1.0],
    [1.0, 1.0, 0.0, 1.0],
    [0.0, 1.0, 0.0, 1.0],
    [0.0, 0.0, 1.0, 1.0],
    [1.0, 0.0, 1.0, 1.0],
    [1.0, 1.0, 1.0, 1.0],
    [0.0, 1.0, 1.0, 1.0]
], dtype=np.float32)

#index arrays for above vertex Arrays

indexCube = np.array((1,0,3, 1,3,2, 
                  2,3,7, 2,7,6,
                  3,0,4, 3,4,7,
                  6,5,1, 6,1,2,
                  4,5,6, 4,6,7,
                  5,4,0, 5,0,1), np.uint32) #rhombus out of two triangles

# Use numpy to create a struct for the uniform
uniform_dtype = [("transform", "float32", (4, 4))]
uniform_data = np.zeros((), dtype=uniform_dtype)

# Create vertex buffer, and upload data
vertex_buffer = device.create_buffer_with_data(
    data=vertexCube, usage=wgpu.BufferUsage.VERTEX
) 

color_buffer = device.create_buffer_with_data(
    data=colorCube, usage=wgpu.BufferUsage.VERTEX
)

# Create index buffer, and upload data
index_buffer = device.create_buffer_with_data(
    data=indexCube, usage=wgpu.BufferUsage.INDEX
)

# Create uniform buffer - data is uploaded each frame
uniform_buffer = device.create_buffer(
    size=uniform_data.nbytes, usage=wgpu.BufferUsage.UNIFORM | wgpu.BufferUsage.COPY_DST
)

# WGSL version of the shader

# GLSL version of the above shader
vertex_shader = """   
#version 450

layout (location=0) in vec4 vPosition;
layout (location=1) in vec4 vColor;

out     vec4 color; 

layout (binding = 0) uniform mat4 modelViewProj;

void main()
{
    gl_Position = modelViewProj * vPosition;
    color = vColor;
}

"""

fragment_shader = """   
#version 450

in vec4 color;
out vec4 outputColor;

void main() {
    outputColor = color;
}

"""

#shader = device.create_shader_module(code=shader_source) 
#GLSL
Vshader = device.create_shader_module(code=vertex_shader, label="vert"); 
Fshader = device.create_shader_module(code=fragment_shader, label="frag"); 

#WGSL
# Vshader = device.create_shader_module(code=vshader); 
# Fshader = device.create_shader_module(code=fshader); 

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

# bind_groups_entries[0].append(
#     {
#         "binding": 1, 
#         "resource": texture_view
#     }
# ) 
# bind_groups_layout_entries[0].append(
#     {
#         "binding": 1,
#         "visibility": wgpu.ShaderStage.FRAGMENT,
#         "texture": {
#             "sample_type": wgpu.TextureSampleType.float,
#             "view_dimension": wgpu.TextureViewDimension.d2,
#         },
#     }
# )

# bind_groups_entries[0].append(
#     {
#         "binding": 2, 
#         "resource": sampler
#     }
# )
# bind_groups_layout_entries[0].append(
#     {
#         "binding": 2,
#         "visibility": wgpu.ShaderStage.FRAGMENT,
#         "sampler": {"type": wgpu.SamplerBindingType.filtering},
#     }
# )


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
        "module": Vshader,
        "entry_point": "main", 
        "buffers": [
            {
                "array_stride": vertexCube.shape[1] * 4,
                "step_mode": wgpu.VertexStepMode.vertex,
                "attributes": [
                    {
                        "format": wgpu.VertexFormat.float32x4,
                        "offset": 0,
                        "shader_location": 0,
                    },
                ],
            },
            {
                "array_stride": colorCube.shape[1] * 4, 
                "step_mode": wgpu.VertexStepMode.vertex, 
                "attributes": [
                    {
                        "format": wgpu.VertexFormat.float32x4,
                        "offset": 0,
                        "shader_location": 1,
                    },
                ]
            }
        ], 
    },
    primitive={
        "topology": wgpu.PrimitiveTopology.triangle_list,
        "front_face": wgpu.FrontFace.ccw,
        "cull_mode": wgpu.CullMode.none,
    },
    depth_stencil=None,
    multisample=None,
    fragment={
        "module": Fshader,
        "entry_point": "main",
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

# location = render_pipeline.get_bind_group(0).get_binding('modelViewProj')

# %% Setup the render function 
model = util.translate(0.0,0.0,0.0) @ util.scale(3, 3, 3)
eye = util.vec(1, 1, 1)
target = util.vec(0,0,0)
up = util.vec(0.0, 1.0, 0.0)
view = util.lookat(eye, target, up)


#projMat = util.perspective(50, 1.33, 0.1, 100.0)
projMat = util.ortho(-10.0, 10.0, -10.0, 10.0, -10, 10.0)

mvpMat =  projMat @ view @ model

def draw_frame():
    # Update uniform transform
    
    uniform_data["transform"] = mvpMat
    # Upload the uniform struct
    tmp_buffer = device.create_buffer_with_data(
        data=uniform_data, usage=wgpu.BufferUsage.COPY_SRC
    )

    command_encoder = device.create_command_encoder()
    command_encoder.copy_buffer_to_buffer(
        tmp_buffer, 0, uniform_buffer, 0, uniform_data.nbytes
    )

    current_texture_view = present_context.get_current_texture().create_view()
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
    )

    render_pass.set_pipeline(render_pipeline)
    render_pass.set_index_buffer(index_buffer, wgpu.IndexFormat.uint32)
    render_pass.set_vertex_buffer(slot=0, buffer=vertex_buffer) 
    render_pass.set_vertex_buffer(slot=1, buffer=color_buffer)
    for bind_group_id, bind_group in enumerate(bind_groups):
        render_pass.set_bind_group(bind_group_id, bind_group, [], 0, 99)
    render_pass.draw_indexed(indexCube.size, 1, 0, 0, 0)
    render_pass.end()

    device.queue.submit([command_encoder.finish()])

    canvas.request_draw()


canvas.request_draw(draw_frame)

while canvas.event_input_process():  
    if canvas._need_draw:
        canvas.display()
        canvas.display_post()