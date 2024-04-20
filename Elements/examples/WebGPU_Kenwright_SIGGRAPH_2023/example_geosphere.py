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
import Elements.pyECSS.math_utilities as util 

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

ti = []; # indices
tv = []; # vertices 
tc = []; # colors
tn = []; # normals

def addv( v ):
    # tv.append(v[0])
    # tv.append(v[1])
    # tv.append(v[2])  
    tv.append([v[0], v[1], v[2]])
    ti.append(len(ti))    

    
def addn( n ): 
    # tn.append(-n[0]) 
    # tn.append(-n[1]) 
    # tn.append(-n[2])  
    tn.append([-n[0], -n[1], -n[2]])

tet_r = [ 
    [ 1.0, 0.0, 0.0 ], 
    [-0.333333333333, 0.942809041582, 0.0], 
    [-0.333333333333,-0.471404520791, 0.816496580928],
    [ -0.333333333333, -0.471404520791, -0.816496580928 ] 
]; 

tris = [];
tris.append([tet_r[3], tet_r[1], tet_r[2]])
tris.append([tet_r[2], tet_r[0], tet_r[3]])
tris.append([tet_r[3], tet_r[0], tet_r[1]])
tris.append([tet_r[1], tet_r[0], tet_r[2]]) 

def mid ( a, b ): 
    return [
        (a[0] + b[0]) * 0.5, 
        (a[1] + b[1]) * 0.5, 
        (a[2] + b[2]) * 0.5, 
    ] 
    
def devide( depth, tri ): 
    if depth == 0: 
        addv( tri[0] ); addn( tri[0] );
        addv( tri[1] ); addn( tri[1] );
        addv( tri[2] ); addn( tri[2] ); 
    else:
        a = util.normalise(tri[0])
        b = util.normalise(tri[1])
        c = util.normalise(tri[2]) 
        
        ab = util.normalise(mid(a, b)) 
        bc = util.normalise(mid(b, c)) 
        ca = util.normalise(mid(c, a))
        
        devide( depth=depth-1, tri=[a, ab, ca]  )
        devide( depth=depth-1, tri=[b, bc, ab]  )
        devide( depth=depth-1, tri=[c, ca, bc]  )
        devide( depth=depth-1, tri=[ab, bc, ca] )


#depth / lod of 5 
for i in range(len(tris)):
    devide( 6, tri=tris[i] ) 
    
# for i in range(len(tv)):    
#     if i % 3 == 0: 
#         tc.append([0.5, 0.0, 0.0]) 
#     else:
#         tc.append([1.0, 0.0, 0.0])    

for i in range(len(tv)):
    tc.append([1.0, 1.0, 1.0])

# for i in range(int(len(tv) / 3)):    
#     tc.append([0.5, 0.0, 0.0]) 
    
    
vertex_data = np.array(tv, dtype=np.float32)
color_data = np.array(tc, dtype=np.float32) 
index_data = np.array(ti, dtype=np.uint32) 

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
    data=vertex_data, usage=wgpu.BufferUsage.VERTEX
)

color_buffer = device.create_buffer_with_data(
    data=color_data, usage=wgpu.BufferUsage.VERTEX
)  

# Create index buffer, and upload data
index_buffer = device.create_buffer_with_data(
    data=index_data, usage=wgpu.BufferUsage.INDEX
)

# WGSL example
shader_code = ShaderLoader(definitions.SHADER_DIR / "SIGGRAPH" / "Meshes" / "simple_mesh.wgsl");
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
                "array_stride": 3 * 4,
                "step_mode": wgpu.VertexStepMode.vertex,
                "attributes": [
                    {
                        "format": wgpu.VertexFormat.float32x3,
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
    render_pass.set_vertex_buffer(slot=1, buffer=color_buffer)
    for bind_group_id, bind_group in enumerate(bind_groups):
        render_pass.set_bind_group(bind_group_id, bind_group, [], 0, 99)
    render_pass.draw_indexed(index_data.size, 1, 0, 0, 0) 
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
