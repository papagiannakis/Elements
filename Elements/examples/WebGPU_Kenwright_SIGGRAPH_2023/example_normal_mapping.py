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
from Elements.pyGLV.GUI.static_cammera import cammera  
from Elements.pyGLV.GL.wgpu_material import wgpu_material
import Elements.pyECSS.math_utilities as util  

from Elements.definitions import TEXTURE_DIR

# Create a canvas to render to
#canvas = WgpuCanvas(title="wgpu cube") 
canvas = GLFWWindow(windowHeight=800, windowWidth=1200, wgpu=True, windowTitle="Wgpu Example")
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

cubev = [
    { "p": [-1.0, -1.0, 1.0], "u":[0.0, 1.0], "c":[1.0, 0.0, 0.0], "n":[0.0, 0.0, 1.0], "t":[] },
    { "p": [1.0, -1.0, 1.0], "u":[1.0, 1.0], "c":[1.0, 0.0, 0.0], "n":[0.0, 0.0, 1.0], "t":[] },
    { "p": [-1.0, 1.0, 1.0], "u":[0.0, 0.0], "c":[1.0, 0.0, 0.0], "n":[0.0, 0.0, 1.0], "t":[] },
    { "p": [1.0, 1.0, 1.0], "u":[0.0, 1.0], "c":[1.0, 0.0, 0.0], "n":[0.0, 0.0, 1.0], "t":[] }, 
    
    { "p": [1.0, -1.0, 1.0], "u":[1.0, 0.0], "c":[0.0, 1.0, 0.0], "n":[-1.0, 0.0, 0.0], "t":[] },
    { "p": [1.0, -1.0, 1.0], "u":[0.0, 0.0], "c":[0.0, 1.0, 0.0], "n":[-1.0, 0.0, 0.0],"t":[] },
    { "p": [1.0, 1.0, 1.0], "u":[1.0, 1.0], "c":[0.0, 1.0, 0.0], "n":[-1.0, 0.0, 0.0], "t":[] },
    { "p": [1.0, 1.0, -1.0], "u":[0.0, 1.0], "c":[0.0, 1.0, 0.0], "n":[-1.0, 0.0, 0.0], "t":[] },
    
    { "p": [1.0, -1.0, -1.0], "u":[1.0, 0.0], "c":[0.0, 0.0, 1.0], "n":[0.0, 0.0, -1.0], "t":[] },
    { "p": [-1.0, -1.0, -1.0], "u":[0.0, 0.0], "c":[0.0, 0.0, 1.0], "n":[0.0, 0.0, -1.0], "t":[] },
    { "p": [1.0, 1.0, -1.0], "u":[1.0, 1.0], "c":[0.0, 0.0, 1.0], "n":[0.0, 0.0, -1.0], "t":[] },
    { "p": [-1.0, 1.0, -1.0], "u":[0.0, 1.0], "c":[0.0, 0.0, 1.0], "n":[0.0, 0.0, -1.0], "t":[] }, 
    
    { "p": [-1.0, -1.0, -1.0], "u":[1.0, 0.0], "c":[1.0, 0.0, 1.0], "n":[1.0, 0.0, 0.0], "t":[] },
    { "p": [-1.0, -1.0, 1.0], "u":[0.0, 0.0], "c":[1.0, 0.0, 1.0], "n":[1.0, 0.0, 0.0], "t":[] },
    { "p": [-1.0, 1.0, -1.0], "u":[1.0, 1.0], "c":[1.0, 0.0, 1.0], "n":[1.0, 0.0, 0.0], "t":[] },
    { "p": [-1.0, 1.0, -1.0], "u":[0.0, 1.0], "c":[1.0, 0.0, 1.0], "n":[1.0, 0.0, 0.0], "t":[] }, 
    
    { "p": [-1.0, -1.0, -1.0], "u":[0.0, 1.0], "c":[1.0, 1.0, 0.0], "n":[0.0, -1.0, 0.0], "t":[] },
    { "p": [-1.0, -1.0, 1.0], "u":[1.0, 1.0], "c":[1.0, 1.0, 0.0], "n":[0.0, -1.0, 0.0], "t":[] },
    { "p": [-1.0, 1.0, -1.0], "u":[0.0, 0.0], "c":[1.0, 1.0, 0.0], "n":[0.0, -1.0, 0.0], "t":[] },
    { "p": [-1.0, 1.0, -1.0], "u":[1.0, 0.0], "c":[1.0, 1.0, 0.0], "n":[0.0, -1.0, 0.0], "t":[] }, 
    
    { "p": [-1.0, 1.0, 1.0], "u":[0.0, 1.0], "c":[1.0, 1.0, 1.0], "n":[0.0, 1.0, 0.0], "t":[] },
    { "p": [1.0, 1.0, 1.0], "u":[1.0, 1.0], "c":[1.0, 1.0, 1.0], "n":[0.0, 1.0, 0.0], "t":[] },
    { "p": [-1.0, 1.0, -1.0], "u":[0.0, 0.0], "c":[1.0, 1.0, 1.0], "n":[0.0, 1.0, 0.0], "t":[] },
    { "p": [1.0, 1.0, -1.0], "u":[1.0, 0.0], "c":[1.0, 1.0, 1.0], "n":[0.0, 1.0, 0.0], "t":[] },
] 

cubef = [
    0,1,3,      0,3,2,
    4,5,7,      4,7,6,
    8,9,11,     8,11,10,
    12,13,15,   12,15,14,
    16,17,19,   16,19,18,
    20,21,23,   20,23,22
] 

for i in range(0, len(cubef), 8): 
    v0 = cubev[ cubef[i+0] ]
    v1 = cubev[ cubef[i+1] ]
    v2 = cubev[ cubef[i+2] ] 
    
    edge0 = [ v1["p"][0] - v0["p"][0], v1["p"][1] - v0["p"][1], v1["p"][2] - v0["p"][2] ]
    edge1 = [ v2["p"][0] - v0["p"][0], v2["p"][1] - v0["p"][1], v2["p"][2] - v0["p"][2] ] 
    
    duv0 = [ v1["u"][0] - v0["u"][0], v1["u"][1] - v0["u"][1] ]
    duv1 = [ v2["u"][0] - v0["u"][0], v2["u"][1] - v0["u"][1] ] 
     
    #f = 1.0 / (duv0[0] * duv1[1] - duv1[0] * duv0[1]) 
    tangentx = 1 * (duv1[1] * edge0[0] - duv0[1] * edge1[0])
    tangenty = 1 * (duv1[1] * edge0[1] - duv0[1] * edge1[1])
    tangentz = 1 * (duv1[1] * edge0[2] - duv0[1] * edge1[2])
    
    cubev[ cubef[i+0] ]["t"] = [ tangentx, tangenty, tangentz ]
    cubev[ cubef[i+1] ]["t"] = [ tangentx, tangenty, tangentz ]
    cubev[ cubef[i+2] ]["t"] = [ tangentx, tangenty, tangentz ]
    
    
print("vertices", len(cubev)) 
print("faces", len(cubef))   

# min = { 'x': 1000.0, 'y':1000.0, 'z':1000.0 }
# max = { 'x': -1000.0, 'y': -1000.0, 'z': -1000.0 } 

# for i in range(0, len(cubev), 1):
#     min["x"] = np.min( min['x'], cubev[i]['p'][0] )
#     min["y"] = np.min( min['y'], cubev[i]['y'][1] )
#     min["z"] = np.min( min['z'], cubev[i]['z'][2] ) 
    
#     max["x"] = np.min( max['x'], cubev[i]['p'][0] )
#     max["y"] = np.min( max['y'], cubev[i]['y'][1] )
#     max["z"] = np.min( max['z'], cubev[i]['z'][2] ) 
    
# delta = { "x": (max["x"] - min["x"]), "y": (max['y'] - min['y']), "z": (max["z"] - min["z"]) } 
# middle = { "x": (min["x"] + delta["x"] * 0.5), "y": (min["y"] + delta["y"] * 0.5), "z": (min["z"] + delta["z"] * 0.5) }  
# dist = np.sqrt( delta["x"]*delta["x"] + delta["y"]*delta["y"] + delta["z"]*delta["z"] )

positionBuffer = []
colorBuffer = []
tcoordBuffer = []
normalBuffer = [] 
tangentBuffer = [] 
indexBuffer = []
 
array = { "v":[], "u":[], "n":[], "f":[], "t":[], "c":[] }  
for cube in cubev: 
    array["v"].append( cube["p"][0] )
    array["v"].append( cube["p"][1] )
    array["v"].append( cube["p"][2] ) 
    
    array["c"].append( cube["c"][0] )
    array["c"].append( cube["c"][1] )
    array["c"].append( cube["c"][2] ) 
 
    array["u"].append( cube["u"][0] ) 
    array["u"].append( cube["u"][1] )   
    
    array["n"].append( cube["n"][0] )
    array["n"].append( cube["n"][1] )
    array["n"].append( cube["n"][2] ) 
     
    array["t"].append( cube["t"][0] )
    array["t"].append( cube["t"][1] )
    array["t"].append( cube["t"][2] )  
    
for i in range(0, len(cubef[i])): 
    array["f"].append( cubef[i] )  
    
positions = np.array(array["v"], dtype=np.float32)
colors = np.array(array["c"], dtype=np.float32)
tcoords = np.array(array["u"], dtype=np.float32)
normals = np.array(array["n"], dtype=np.float32) 
tangents = np.array(array["t"], dtype=np.float32)
indices = np.array(array["f"], dtype=np.uint32)
 
uniform_dtype = np.dtype([
    ("proj", np.float32, (4, 4)),
    ("view", np.float32, (4, 4)),
    ("model", np.float32, (4, 4)),
]) 
    
model = glm.mat4x4(1.0)

eye = glm.vec3(2.5, 2.5, 2.5) 
target = glm.vec3(0.0, 0.0, 0.0)
up = glm.vec3(0.0, 1.0, 0.0) 
cam = cammera(eye=eye, target=target, up=up);
view = cam._updateCamera;

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
    data=positions, usage=wgpu.BufferUsage.VERTEX
)

color_buffer = device.create_buffer_with_data(
    data=colors, usage=wgpu.BufferUsage.VERTEX
)  

uv_buffer = device.create_buffer_with_data(
    data=tcoords, usage=wgpu.BufferUsage.VERTEX
) 

normal_buffer = device.create_buffer_with_data(
    data=normals, usage=wgpu.BufferUsage.VERTEX
)   

tangent_buffer = device.create_buffer_with_data(
    data=tangents, usage=wgpu.BufferUsage.VERTEX
)  

# Create index buffer, and upload data
index_buffer = device.create_buffer_with_data(
    data=indices, usage=wgpu.BufferUsage.INDEX
)  

texturePath0 = TEXTURE_DIR / "crateA-decal.jpg" 
texturePath1 = TEXTURE_DIR / "crateA-normal.jpg"
texture0 = wgpu_material(device=device, filepath=texturePath0)
texture1 = wgpu_material(device=device, filepath=texturePath1)

sampler = device.create_sampler()

# WGSL example
shader_code = ShaderLoader(definitions.SHADER_DIR / "SIGGRAPH" / "Normal_mapping" / "simple_normal_mapping.wgsl");
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
        "resource": texture0.view
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

bind_groups_entries[0].append(
    {
        "binding": 3,
        "resource": texture1.view
    } 
) 
bind_groups_layout_entries[0].append(
    {
        "binding": 3,
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
            {
                "array_stride": 3 * 4,
                "step_mode": wgpu.VertexStepMode.vertex,
                "attributes": [
                    {
                        "format": wgpu.VertexFormat.float32x3,
                        "offset": 0,
                        "shader_location": 2,
                    },
                ],
            }, 
            {
                "array_stride": 3 * 4,
                "step_mode": wgpu.VertexStepMode.vertex,
                "attributes": [
                    {
                        "format": wgpu.VertexFormat.float32x3,
                        "offset": 0,
                        "shader_location": 3,
                    },
                ],
            }, 
            {
                "array_stride": 3 * 4,
                "step_mode": wgpu.VertexStepMode.vertex,
                "attributes": [
                    {
                        "format": wgpu.VertexFormat.float32x3,
                        "offset": 0,
                        "shader_location": 4,
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
    view = cam._updateCamera
    
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
    render_pass.set_index_buffer(index_buffer, wgpu.IndexFormat.uint32)
    render_pass.set_vertex_buffer(slot=0, buffer=vertex_buffer) 
    render_pass.set_vertex_buffer(slot=1, buffer=uv_buffer)
    render_pass.set_vertex_buffer(slot=2, buffer=normal_buffer) 
    render_pass.set_vertex_buffer(slot=3, buffer=tangent_buffer)  
    render_pass.set_vertex_buffer(slot=4, buffer=color_buffer)  
    for bind_group_id, bind_group in enumerate(bind_groups):
        render_pass.set_bind_group(bind_group_id, bind_group, [], 0, 99)
    render_pass.draw_indexed(indices.size, 1, 0, 0, 0) 
    # render_pass.draw(3, 1, 0, 0)
    render_pass.end()

    device.queue.submit([command_encoder.finish()])

    canvas.request_draw()


canvas.request_draw(draw_frame)

mouse_noop_x_state = 0
mouse_noop_y_state = 0 

while canvas._running:
    width = canvas._windowWidth
    height = canvas._windowHeight  
    wcenter = width / 2
    hcenter = height / 2 
    
    event = canvas.event_input_process();   
    if event: 
        if glfw.get_key(canvas.gWindow, glfw.KEY_ESCAPE) == glfw.PRESS:  
            canvas._running = False

        if event.type == EventTypes.SCROLL:
                x = event.data["dx"]
                y = event.data["dy"]
                cam.cameraHandling(x,y,width,height)
            
        if event.type == EventTypes.MOUSE_MOTION:
            buttons = event.data["buttons"]   
            
            if button_map[glfw.MOUSE_BUTTON_2] in canvas._pointer_buttons:
                x = np.floor(event.data["x"] - mouse_noop_x_state) 
                y = np.floor(event.data["y"] - mouse_noop_y_state) 
                cam.cameraHandling(x, y, height, width) 
            else:
                mouse_noop_x_state = np.floor(event.data["x"])
                mouse_noop_y_state = np.floor(event.data["y"])
                
    if canvas._need_draw:
        canvas.display()
        canvas.display_post() 
        
canvas.shutdown()
# %%
